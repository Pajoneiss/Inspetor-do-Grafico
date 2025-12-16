"""
Engine V0 - Main Loop
Trading bot engine with multi-symbol Hyperliquid integration and AI decisions
"""
import time
import sys
from datetime import datetime
from config import (
    LOOP_INTERVAL_SECONDS,
    SYMBOL,
    LIVE_TRADING,
    AI_ENABLED,
    AI_CALL_INTERVAL_SECONDS,
    FORCE_TEST_ORDER,
    TEST_ORDER_SIDE,
    TEST_ORDER_SIZE,
    TEST_ORDER_SYMBOL,
    SNAPSHOT_TOP_N,
    SNAPSHOT_MODE,
    ROTATE_PER_TICK,
    print_config
)
from hl_client import HLClient
from executor import execute

# v11.0: Telegram bot integration
try:
    from telegram_bot import start_telegram_bot, update_telegram_state, is_ai_enabled, should_panic_close
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("[TG][WARN] Telegram module not available, skipping")


def main():
    """Main bot loop"""
    print("[BOOT] Engine V0 starting...")
    print_config()
    print("[BOOT] ok")
    
    # Parse symbols from comma-separated list
    symbols = [s.strip().upper() for s in SYMBOL.split(",") if s.strip()]
    print(f"[BOOT] Parsed {len(symbols)} symbols: {symbols[:5]}..." if len(symbols) > 5 else f"[BOOT] Parsed {len(symbols)} symbols: {symbols}")
    
    # Determine test order symbol (first symbol if not specified)
    test_symbol = TEST_ORDER_SYMBOL if TEST_ORDER_SYMBOL else (symbols[0] if symbols else "BTC")
    
    # Initialize Hyperliquid client
    hl = None
    try:
        hl = HLClient()
        print("[BOOT] HLClient initialized")
    except Exception as e:
        print(f"[BOOT][ERROR] Failed to initialize HLClient: {e}")
        print("[BOOT] Continuing without Hyperliquid connection...")
    
    # Initialize LLM client (lazy load to avoid crash)
    llm = None
    if AI_ENABLED:
        try:
            # Lazy import to avoid crash if openai not installed
            from llm_client import LLMClient
            llm = LLMClient()
            print("[BOOT] LLMClient initialized")
        except ImportError as e:
            print(f"[LLM][WARN] disabled due to import error: {e}")
            print("[LLM][WARN] Install openai: pip install openai>=1.0.0")
        except Exception as e:
            print(f"[LLM][WARN] disabled due to init error: {e}")
            import traceback
            traceback.print_exc()
    
    # v11.0: Start Telegram bot in background
    if TELEGRAM_AVAILABLE:
        try:
            start_telegram_bot()
            print("[BOOT] Telegram bot started")
        except Exception as e:
            print(f"[TG][WARN] Failed to start: {e}")
    
    iteration = 0
    test_order_executed = False  # Flag to execute test order only once
    last_ai_call_time = 0  # Timestamp of last AI call
    rotate_offset = 0  # For ROTATE mode

    
    try:
        while True:
            iteration += 1
            current_time = time.time()
            print(f"\n[LOOP] tick {iteration}")
            
            # Determine snapshot symbols based on mode
            if SNAPSHOT_MODE == "ALL":
                snapshot_symbols = symbols
            elif SNAPSHOT_MODE == "ROTATE":
                # Rotate through symbols
                snapshot_symbols = symbols[rotate_offset:rotate_offset + ROTATE_PER_TICK]
                rotate_offset = (rotate_offset + ROTATE_PER_TICK) % len(symbols)
            else:  # TOP_N (default)
                snapshot_symbols = symbols[:SNAPSHOT_TOP_N]
            
            # Initialize state for this iteration
            state = {
                "time": datetime.now().isoformat(),
                "equity": 0.0,
                "positions_count": 0,
                "positions": {},  # Will be dict[symbol, {...}]
                "open_orders_count": 0,
                "prices": {},
                "symbols": symbols,  # Full allowlist
                "snapshot_symbols": snapshot_symbols,  # Current snapshot
                "live_trading": LIVE_TRADING
            }
            
            # BLOCO 1 + 3.5: Hyperliquid integration with multi-symbol
            if hl and snapshot_symbols:
                try:
                    # Get account summary
                    summary = hl.get_account_summary()
                    state["equity"] = summary["equity"]
                    state["positions_count"] = summary["positions_count"]
                    
                    # Get positions by symbol
                    positions_by_symbol = hl.get_positions_by_symbol()
                    state["positions"] = positions_by_symbol
                    
                    # Get prices for snapshot symbols
                    prices = hl.get_prices(snapshot_symbols)
                    state["prices"] = prices
                    state["available_margin"] = summary["available"]  # Free collateral
                    
                    # v10.2: Calculate buying power with leverage (default 40x for BTC)
                    default_leverage = 40
                    state["leverage"] = default_leverage
                    state["buying_power"] = state["equity"] * default_leverage

                    
                    # Get constraints for snapshot symbols
                    constraints_by_symbol = {}
                    for sym in snapshot_symbols:
                        constraints_by_symbol[sym] = hl.get_symbol_constraints(sym)
                    state["constraints_by_symbol"] = constraints_by_symbol
                    
                    # Get recent fills
                    recent_fills = hl.get_recent_fills(limit=10)
                    state["recent_fills"] = recent_fills
                    
                    # Get open orders (MCP-first)
                    open_orders = hl.get_open_orders()
                    state["open_orders"] = open_orders
                    state["open_orders_count"] = len(open_orders)
                    
                    # Group open orders by symbol
                    open_orders_by_symbol = {}
                    for order in open_orders:
                        coin = order.get("coin", "")
                        if coin not in open_orders_by_symbol:
                            open_orders_by_symbol[coin] = []
                        open_orders_by_symbol[coin].append(order)
                    state["open_orders_by_symbol"] = open_orders_by_symbol
                    
                    # v11.0: Build trigger status + BE telemetry for each position
                    trigger_status_lines = []
                    BE_TRIGGER_PCT = 0.30  # 0.30% profit to arm breakeven
                    BE_OFFSET_BPS = 2  # 0.02% offset for fees
                    
                    for pos_symbol, pos_data in positions_by_symbol.items():
                        symbol_orders = open_orders_by_symbol.get(pos_symbol, [])
                        has_sl = False
                        has_tp = False
                        sl_price = None
                        tp_price = None
                        
                        entry_px = pos_data.get("entry_price", 0)
                        mark_px = state.get("prices", {}).get(pos_symbol, entry_px)
                        pos_side = pos_data.get("side", "LONG")
                        pnl_pct = pos_data.get("unrealized_pnl_pct", 0)
                        
                        # Calculate PnL % if not provided
                        if entry_px > 0 and mark_px > 0 and pnl_pct == 0:
                            if pos_side == "LONG":
                                pnl_pct = ((mark_px - entry_px) / entry_px) * 100
                            else:
                                pnl_pct = ((entry_px - mark_px) / entry_px) * 100
                        
                        for order in symbol_orders:
                            if order.get("reduceOnly"):
                                trigger_px = order.get("triggerPx") or order.get("trigger_px") or order.get("limitPx")
                                if trigger_px:
                                    trigger_px = float(trigger_px)
                                    
                                    # Determine if SL or TP based on position side and trigger direction
                                    if pos_side == "LONG":
                                        if trigger_px < entry_px:
                                            has_sl = True
                                            sl_price = trigger_px
                                        else:
                                            has_tp = True
                                            tp_price = trigger_px
                                    else:  # SHORT
                                        if trigger_px > entry_px:
                                            has_sl = True
                                            sl_price = trigger_px
                                        else:
                                            has_tp = True
                                            tp_price = trigger_px
                        
                        # BE Telemetry - compute status
                        be_target = entry_px * (1 + BE_OFFSET_BPS/10000) if pos_side == "LONG" else entry_px * (1 - BE_OFFSET_BPS/10000)
                        
                        if pnl_pct >= BE_TRIGGER_PCT:
                            if has_sl and sl_price and abs(sl_price - be_target) / entry_px < 0.001:
                                be_status = "EXECUTED"
                            else:
                                be_status = "TRIGGERED"
                        elif pnl_pct > 0:
                            be_status = "ARMED"
                        else:
                            be_status = "INACTIVE"
                        
                        # Build status line
                        sl_str = f"SL=${sl_price:.2f}" if has_sl else "SL=MISSING!"
                        tp_str = f"TP=${tp_price:.2f}" if has_tp else "TP=MISSING!"
                        be_str = f"BE={be_status}({pnl_pct:.2f}%)"
                        trigger_status_lines.append(f"  - {pos_symbol}: {sl_str} | {tp_str} | {be_str}")
                        
                        # Log BE every tick
                        print(f"[BE] {pos_symbol} status={be_status} pnl={pnl_pct:.2f}% trigger={BE_TRIGGER_PCT}% be_target=${be_target:.2f} current_sl=${sl_price if sl_price else 'NONE'}")
                        
                        # v11.0: BE AUTO-EXECUTION - Move SL to breakeven when TRIGGERED
                        ENABLE_BE_EXECUTION = True  # Enable auto-execution
                        if ENABLE_BE_EXECUTION and be_status == "TRIGGERED":
                            # SL is worse than breakeven, need to move it
                            if pos_side == "LONG" and (sl_price is None or sl_price < be_target):
                                state["be_actions"] = state.get("be_actions", [])
                                state["be_actions"].append({
                                    "type": "SET_STOP_LOSS",
                                    "symbol": pos_symbol,
                                    "stop_price": be_target,
                                    "reason": "BE auto-execution"
                                })
                                # Set BE protection to prevent LLM from downgrading this SL
                                try:
                                    from be_protection import set_be_protection
                                    set_be_protection(pos_symbol, be_target, pos_side)
                                except ImportError:
                                    pass
                                print(f"[BE][EXEC] Queued SL move to breakeven ${be_target:.2f} for {pos_symbol}")
                            elif pos_side == "SHORT" and (sl_price is None or sl_price > be_target):
                                state["be_actions"] = state.get("be_actions", [])
                                state["be_actions"].append({
                                    "type": "SET_STOP_LOSS",
                                    "symbol": pos_symbol,
                                    "stop_price": be_target,
                                    "reason": "BE auto-execution"
                                })
                                # Set BE protection to prevent LLM from downgrading this SL
                                try:
                                    from be_protection import set_be_protection
                                    set_be_protection(pos_symbol, be_target, pos_side)
                                except ImportError:
                                    pass
                                print(f"[BE][EXEC] Queued SL move to breakeven ${be_target:.2f} for {pos_symbol}")
                    
                    state["trigger_status"] = "\n".join(trigger_status_lines) if trigger_status_lines else "(no positions)"

                    
                    # Add feedback (rejects, errors, successes)

                    from feedback import get_feedback_tracker
                    feedback = get_feedback_tracker()
                    state["last_rejects"] = feedback.get_recent_rejects(limit=10)
                    state["last_errors"] = feedback.get_recent_errors(limit=10)
                    state["last_successes"] = feedback.get_recent_successes(limit=10)
                    
                    # MARKET VISION: Candles + Indicators + Orderbook (Anti-Fantasy)
                    # Resilient to import errors - graceful degradation
                    try:
                        from indicators import calculate_indicators
                        indicators_available = True
                    except ImportError as e:
                        print(f"[VISION][WARN] indicators disabled: {e}")
                        indicators_available = False
                    except Exception as e:
                        print(f"[VISION][WARN] indicators import failed: {e}")
                        indicators_available = False
                    
                    try:
                        # v10.3: Multi-symbol candles and indicators
                        candles_by_symbol = {}
                        indicators_by_symbol = {}
                        
                        # Candles/indicators for top 5 symbols (avoid API spam)
                        for symbol in snapshot_symbols[:5]:
                            # Get candles for multiple timeframes
                            candles_15m = hl.get_candles(symbol, "15m", limit=50)
                            candles_1h = hl.get_candles(symbol, "1h", limit=50)
                            
                            candles_by_symbol[symbol] = {
                                "15m": candles_15m[-20:] if candles_15m else [],
                                "1h": candles_1h[-20:] if candles_1h else []
                            }
                            
                            # Calculate indicators from 15m if available
                            if indicators_available and candles_15m:
                                try:
                                    indicators_by_symbol[symbol] = calculate_indicators(candles_15m)
                                except Exception as e:
                                    print(f"[VISION][WARN] indicators calc failed for {symbol}: {e}")
                                    indicators_by_symbol[symbol] = {}
                            else:
                                indicators_by_symbol[symbol] = {}
                        
                        state["candles_by_symbol"] = candles_by_symbol
                        state["indicators_by_symbol"] = indicators_by_symbol
                        
                        # Orderbook for top 5 symbols
                        orderbook_by_symbol = {}
                        for symbol in snapshot_symbols[:5]:
                            orderbook_by_symbol[symbol] = hl.get_orderbook(symbol, depth=5)
                        state["orderbook_by_symbol"] = orderbook_by_symbol
                        
                        # Funding info for top 5
                        funding_by_symbol = {}
                        for symbol in snapshot_symbols[:5]:
                            funding_by_symbol[symbol] = hl.get_funding_info(symbol)
                        state["funding_by_symbol"] = funding_by_symbol
                        
                        # v11.0: BUILD REAL SYMBOL BRIEFS WITH VARIED SCORING
                        symbol_briefs = {}
                        for symbol in snapshot_symbols:
                            price = state["prices"].get(symbol, 0)
                            ind = indicators_by_symbol.get(symbol, {})
                            
                            # Get real indicator values (correct keys from indicators.py)
                            ema_9 = ind.get("ema_9", 0)
                            ema_21 = ind.get("ema_21", 0)
                            ema_50 = ind.get("ema_50", 0)
                            rsi = ind.get("rsi_14", 50)  # FIX: was "rsi", should be "rsi_14"
                            macd_hist = ind.get("macd_hist", 0)
                            atr_pct = ind.get("atr_pct", 0)
                            trend_str = ind.get("trend", "neutral")
                            relative_volume = ind.get("relative_volume", 1.0)
                            
                            # Multi-factor scoring (0-100)
                            score = 50  # Base score
                            reasons = []
                            
                            if price > 0 and ema_21 > 0:
                                # Factor 1: EMA alignment (+/- 15 points)
                                if ema_9 > ema_21 > ema_50:
                                    score += 15
                                    trend = "UP_STRONG"
                                    reasons.append("EMA aligned bullish")
                                elif ema_9 > ema_21:
                                    score += 8
                                    trend = "UP"
                                    reasons.append("EMA9>21")
                                elif ema_9 < ema_21 < ema_50:
                                    score += 15  # Good for shorts too
                                    trend = "DOWN_STRONG"
                                    reasons.append("EMA aligned bearish")
                                elif ema_9 < ema_21:
                                    score += 8
                                    trend = "DOWN"
                                    reasons.append("EMA9<21")
                                else:
                                    trend = "RANGE"
                                    reasons.append("ranging")
                                
                                # Factor 2: RSI momentum (+/- 20 points)
                                if rsi > 70:
                                    score -= 10  # Overbought penalty
                                    reasons.append("overbought")
                                elif rsi > 60:
                                    score += 10
                                    reasons.append("RSI strong")
                                elif rsi < 30:
                                    score -= 10  # Oversold penalty
                                    reasons.append("oversold")
                                elif rsi < 40:
                                    score += 10  # Good for shorts
                                    reasons.append("RSI weak")
                                else:
                                    score += 0  # Neutral zone
                                
                                # Factor 3: MACD confirmation (+/- 10 points)
                                if macd_hist > 0 and trend in ["UP", "UP_STRONG"]:
                                    score += 10
                                    reasons.append("MACD+")
                                elif macd_hist < 0 and trend in ["DOWN", "DOWN_STRONG"]:
                                    score += 10
                                    reasons.append("MACD-")
                                elif (macd_hist > 0 and trend.startswith("DOWN")) or (macd_hist < 0 and trend.startswith("UP")):
                                    score -= 5  # Divergence penalty
                                    reasons.append("MACD diverge")
                                
                                # Factor 4: Volume boost (+5 max)
                                if relative_volume > 1.5:
                                    score += 5
                                    reasons.append("high vol")
                                
                                # Factor 5: Volatility penalty (-5 if too high)
                                if atr_pct > 3.0:
                                    score -= 5
                                    reasons.append("high ATR")
                                
                                # Clamp score
                                score = max(0, min(100, score))
                                momentum = "STRONG" if rsi > 60 or rsi < 40 else "NEUTRAL"
                            else:
                                trend = "UNKNOWN"
                                momentum = "UNKNOWN"
                                score = 25  # Unknown gets low score, not 50
                                reasons.append("no data")
                            
                            symbol_briefs[symbol] = {
                                "price": round(price, 2) if price < 1000 else round(price, 0),
                                "trend": trend,
                                "momentum": momentum,
                                "rsi": round(rsi, 1),
                                "score": round(score, 0),
                                "reason": " + ".join(reasons[:2]) if reasons else ""
                            }
                        
                        state["symbol_briefs"] = symbol_briefs
                        
                        # v11.0: PROOF LOG with varied scores
                        top_symbols = sorted(symbol_briefs.items(), key=lambda x: x[1]["score"], reverse=True)[:5]
                        bottom_symbols = sorted(symbol_briefs.items(), key=lambda x: x[1]["score"])[:3]
                        top_str = " ".join([f"{s}:{int(b['score'])}" for s, b in top_symbols])
                        bottom_str = " ".join([f"{s}:{int(b['score'])}" for s, b in bottom_symbols])
                        
                        # Check for flat scores warning
                        all_scores = [b["score"] for b in symbol_briefs.values()]
                        scores_flat = len(set(all_scores)) <= 2
                        
                        if scores_flat:
                            print(f"[SCAN][WARN] scores_flat detected → check indicator pipeline")
                        print(f"[SCAN] top5=[{top_str}] bottom3=[{bottom_str}]")

                        
                    except Exception as e:
                        print(f"[VISION][ERROR] market data failed: {e}")
                        import traceback
                        traceback.print_exc()
                        # Continue without vision data - don't crash
                    
                    # Log Hyperliquid status
                    prices_ok = len(prices)
                    positions_symbols = list(positions_by_symbol.keys())
                    print(f"[HL] snapshot symbols={len(snapshot_symbols)} prices_ok={prices_ok} positions={positions_symbols if positions_symbols else '[]'}")
                    print(f"[STATE] equity={summary['equity']:.2f} positions_count={summary['positions_count']} buying_power=${state.get('buying_power', 0):.0f}")
                    
                    # v11.0: Sync state to Telegram
                    if TELEGRAM_AVAILABLE:
                        update_telegram_state(state)

                    
                except Exception as e:
                    print(f"[HL][ERROR] {e}")
                    import traceback
                    traceback.print_exc()
            
            # BLOCO 2: Test executor with forced action (only first iteration)
            if FORCE_TEST_ORDER and not test_order_executed:
                print("[TEST][PAPER] forcing 1 test order (PAPER mode enforced)")
                
                # Create test action
                test_actions = [{
                    "type": "PLACE_ORDER",
                    "symbol": test_symbol,
                    "side": TEST_ORDER_SIDE,
                    "size": TEST_ORDER_SIZE,
                    "orderType": "MARKET"
                }]
                
                # Execute in PAPER mode (override LIVE_TRADING for test)
                execute(test_actions, live_trading=False, hl_client=hl)
                
                test_order_executed = True
            
            # BLOCO 3 + 3.5: AI decision engine with multi-symbol state
            elif AI_ENABLED:
                if llm is None:
                    print("[LLM] skipped (not available)")
                else:
                    # Check cooldown
                    time_since_last_call = current_time - last_ai_call_time
                    
                    if time_since_last_call >= AI_CALL_INTERVAL_SECONDS:
                        try:
                            # v11.0: Execute BE actions FIRST (before LLM)
                            be_actions = state.get("be_actions", [])
                            if be_actions:
                                print(f"[BE] Executing {len(be_actions)} breakeven actions")
                                execute(be_actions, live_trading=LIVE_TRADING, hl_client=hl)
                                state["be_actions"] = []  # Clear after execution
                            
                            # Get AI decision
                            decision = llm.decide(state)
                            
                            # Update last call time
                            last_ai_call_time = current_time
                            
                            # Execute actions (pass hl_client for proper LIVE/PAPER detection)
                            actions = decision.get("actions", [])
                            if actions:
                                execute(actions, live_trading=LIVE_TRADING, hl_client=hl)

                            
                        except Exception as e:
                            print(f"[LLM][ERROR] {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        remaining = AI_CALL_INTERVAL_SECONDS - time_since_last_call
                        print(f"[LLM] skipped (cooldown {remaining:.0f}s)")
            
            # Sleep until next iteration
            time.sleep(LOOP_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Received interrupt signal")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
