"""
Engine V0 - Main Loop
Trading bot engine with multi-symbol Hyperliquid integration and AI decisions
"""
import time
import sys
from datetime import datetime, timezone
from config import (
    LOOP_INTERVAL_SECONDS,
    SYMBOL,
    LIVE_TRADING,
    AI_ENABLED,
    AI_CALL_INTERVAL_SECONDS,
    LLM_MIN_SECONDS,
    LLM_STATE_CHANGE_THRESHOLD,
    PRICE_CHANGE_THRESHOLD,
    VOLATILITY_TRIGGER_PCT,
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
from data_sources import get_all_external_data

# v11.0: Telegram bot integration
try:
    from telegram_bot import (
        start_telegram_bot, 
        update_telegram_state, 
        is_ai_enabled, 
        should_panic_close,
        get_test_trade_request,
        clear_test_trade_request,
        send_test_trade_result
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("[TG][WARN] Telegram module not available, skipping")

# Dashboard API integration
try:
    from dashboard_api import update_dashboard_state
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    print("[DASHBOARD][WARN] Dashboard API not available")


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
        
        # Set hl_client reference for PnL tracker (used by Telegram)
        try:
            from pnl_tracker import set_hl_client
            set_hl_client(hl)
        except Exception as e:
            print(f"[PNL][WARN] Failed to set hl_client: {e}")
            
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
    
    # v12.6: Start Dashboard API server
    dashboard_api = None
    try:
        from dashboard_api import run_dashboard_server, update_dashboard_state, add_ai_action
        import os
        dashboard_port = int(os.environ.get("PORT", 8080))
        run_dashboard_server(port=dashboard_port)
        print(f"[BOOT] Dashboard server started on port {dashboard_port}")
        dashboard_api = True
    except Exception as e:
        print(f"[DASHBOARD][WARN] Failed to start: {e}")
        dashboard_api = None
    
    iteration = 0
    test_order_executed = False  # Flag to execute test order only once
    last_ai_call_time = 0  # Timestamp of last AI call
    last_state_hash = None  # For state-based throttle
    last_equity = 0.0  # Track equity changes
    rotate_offset = 0  # For ROTATE mode
    last_external_fetch = 0  # For data_sources throttle
    external_data = {}
    last_ai_price = 0.0 # Track price for volatility trigger
    last_candle_hour = -1  # v16: Track last hour for candle close sync

    
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
                    
                    # v13.0: Persist real equity history for the dashboard chart
                    try:
                        from pnl_tracker import save_pnl_snapshot
                        save_pnl_snapshot(summary["equity"])
                    except Exception as e:
                        print(f"[PNL][WARN] Failed to save snapshot: {e}")
                    
                    # Get positions by symbol
                    positions_by_symbol = hl.get_positions_by_symbol()
                    state["positions"] = positions_by_symbol
                    
                    # Get prices for snapshot symbols
                    prices = hl.get_prices(snapshot_symbols)
                    state["prices"] = prices
                    state["available_margin"] = summary["available"]  # Free collateral
                    
                    # v12.7: Calculate actual current buying power (leveraged available margin)
                    default_leverage = 40
                    state["leverage"] = default_leverage
                    state["available_margin"] = float(summary.get("available", 0))
                    state["buying_power"] = state["available_margin"] * default_leverage

                    
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
                    
                    # Build trigger status for each position
                    trigger_status_lines = []
                    
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
                                    
                                    # FIX: Determine if SL or TP based on trigger vs MARK price
                                    # BE SL can be ABOVE entry (with offset), so use mark price for comparison
                                    # For LONG: SL triggers when price DROPS to trigger_px
                                    # For SHORT: SL triggers when price RISES to trigger_px
                                    if pos_side == "LONG":
                                        # For LONG, if trigger is at or below current mark - it's a SL
                                        # (includes BE SL which is slightly above entry)
                                        if trigger_px <= mark_px or trigger_px < entry_px * 1.005:  # 0.5% tolerance
                                            has_sl = True
                                            sl_price = trigger_px
                                        else:
                                            has_tp = True
                                            tp_price = trigger_px
                                    else:  # SHORT
                                        # For SHORT, if trigger is at or above current mark - it's a SL
                                        if trigger_px >= mark_px or trigger_px > entry_px * 0.995:  # 0.5% tolerance
                                            has_sl = True
                                            sl_price = trigger_px
                                        else:
                                            has_tp = True
                                            tp_price = trigger_px
                        
                        # Build simple status line
                        sl_str = f"SL=${sl_price:.2f}" if has_sl else "SL=None"
                        tp_str = f"TP=${tp_price:.2f}" if has_tp else "TP=None"
                        trigger_status_lines.append(f"  - {pos_symbol}: {sl_str} | {tp_str} | PnL={pnl_pct:.2f}%")
                        
                        # Store position info for LLM context
                        if "position_details" not in state:
                            state["position_details"] = {}
                        state["position_details"][pos_symbol] = {
                            "pnl_pct": pnl_pct,
                            "entry_price": entry_px,
                            "current_sl": sl_price,
                            "current_tp": tp_price,
                            "side": pos_side
                        }
                    
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
                        # v12.0: Multi-symbol candles with 7 timeframes (micro to macro)
                        candles_by_symbol = {}
                        indicators_by_symbol = {}
                        
                        # v17: Optimized timeframes for H4 swing trading (removed 1m/5m noise)
                        TIMEFRAMES_CONFIG = {
                            "15m": 60,  # 15 hours - entry precision
                            "1h": 60,   # 2.5 days - swing structure
                            "4h": 60,   # 10 days - intermediate trend
                            "1d": 90,   # 3 months - primary trend
                            "1w": 52    # 1 year - macro context
                        }
                        
                        # v14.0: Optimized scan (Limit 4 symbols, priority to active positions, request spacing)
                        active_symbols = list(positions_by_symbol.keys())
                        scan_candidates = []
                        
                        # Add active positions first
                        for s in active_symbols:
                            if s in snapshot_symbols and s not in scan_candidates:
                                scan_candidates.append(s)
                        
                        # v17: Fill remaining slots with top snapshot symbols (limit 2 total for cost)
                        for s in snapshot_symbols:
                            if len(scan_candidates) >= 2:
                                break
                            if s not in scan_candidates:
                                scan_candidates.append(s)
                                
                        print(f"[VISION] Scanning {len(scan_candidates)} symbols: {scan_candidates}")

                        for symbol in scan_candidates:
                            candles_by_symbol[symbol] = {}
                            
                            # Fetch all timeframes
                            for tf, limit in TIMEFRAMES_CONFIG.items():
                                try:
                                    # Request spacing to prevent 429
                                    time.sleep(0.1) 
                                    candles = hl.get_candles(symbol, tf, limit=limit)
                                    candles_by_symbol[symbol][tf] = candles if candles else []
                                except Exception as e:
                                    print(f"[VISION][WARN] Failed to get {tf} candles for {symbol}: {e}")
                                    candles_by_symbol[symbol][tf] = []
                            
                            # Calculate indicators from 15m if available
                            symbol_15m = candles_by_symbol[symbol].get("15m", [])
                            if indicators_available and symbol_15m:
                                try:
                                    indicators_by_symbol[symbol] = calculate_indicators(symbol_15m)
                                except Exception as e:
                                    print(f"[VISION][WARN] indicators calc failed for {symbol}: {e}")
                                    indicators_by_symbol[symbol] = {}
                            else:
                                indicators_by_symbol[symbol] = {}
                        
                        state["candles_by_symbol"] = candles_by_symbol
                        state["indicators_by_symbol"] = indicators_by_symbol
                        
                        # Orderbook for scan candidates
                        orderbook_by_symbol = {}
                        for symbol in scan_candidates:
                            time.sleep(0.1)
                            orderbook_by_symbol[symbol] = hl.get_orderbook(symbol, depth=5)
                        state["orderbook_by_symbol"] = orderbook_by_symbol
                        
                        # Funding info for scan candidates
                        funding_by_symbol = {}
                        for symbol in scan_candidates:
                            time.sleep(0.1)
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
                                
                                # Factor 2: RSI - NEUTRAL scoring (just note extreme values)
                                # v13.0: No penalty for overbought/oversold - AI decides if it's opportunity or risk
                                if rsi > 70:
                                    score += 5  # Extreme = interesting, not penalty
                                    reasons.append("RSI>70")
                                elif rsi > 60:
                                    score += 5
                                    reasons.append("RSI bullish")
                                elif rsi < 30:
                                    score += 5  # Extreme = interesting, not penalty
                                    reasons.append("RSI<30")
                                elif rsi < 40:
                                    score += 5
                                    reasons.append("RSI bearish")
                                else:
                                    score += 0  # Neutral zone
                                
                                # Factor 3: MACD confirmation
                                # v14.0: Context-aware MACD - Differentiate Reversal vs Pullback
                                if macd_hist > 0 and trend in ["UP", "UP_STRONG"]:
                                    score += 10
                                    reasons.append("MACD+")
                                elif macd_hist < 0 and trend in ["DOWN", "DOWN_STRONG"]:
                                    score += 10
                                    reasons.append("MACD-")
                                # PULLBACK LOGIC: Strong trend + opposing MACD = Pullback Opportunity (Not Divergence)
                                elif macd_hist < 0 and trend == "UP_STRONG":
                                    score += 8  # High score for bullish pullback
                                    reasons.append("Bullish Pullback")
                                elif macd_hist > 0 and trend == "DOWN_STRONG":
                                    score += 8  # High score for bearish pullback
                                    reasons.append("Bearish Pullback")
                                else:
                                    score += 0  # weak or unclear divergence
                                    reasons.append("MACD mix")
                                
                                # Factor 4: Volume boost (+10 for high volume - more interesting)
                                if relative_volume > 1.5:
                                    score += 10
                                    reasons.append("high vol")
                                elif relative_volume > 1.2:
                                    score += 5
                                    reasons.append("vol+")
                                
                                # Factor 5: Volatility - HIGH ATR = more opportunity, not penalty
                                # v13.0: AI decides if volatility is good or bad
                                if atr_pct > 3.0:
                                    score += 5
                                    reasons.append("volatile")
                                
                                # Factor 6: Micro-conviction variance (prevents flat scores)
                                # RSI distance from 50 (normalized to range -2 to +2)
                                score += abs(rsi - 50) * 0.05  # Further from 50 = more interesting

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
                                "score": round(score, 1),
                                "reason": " + ".join(reasons[:2]) if reasons else ""
                            }
                        
                        state["market"] = {
                            "macro": external_data.get("macro", {}),
                            "btc_dominance": external_data.get("market", {}).get("btc_dominance", 0),
                            "fear_greed": external_data.get("fear_greed", {}).get("value", 50),
                            "market_cap": external_data.get("market", {}).get("market_cap", 0),
                            "top_symbols": [s for s in snapshot_symbols[:8]]
                        }
                        
                        state["symbol_briefs"] = symbol_briefs
                        
                        # v11.0: PROOF LOG with varied scores
                        top_symbols = sorted(symbol_briefs.items(), key=lambda x: x[1].get("score", 50), reverse=True)[:5]
                        bottom_symbols = sorted(symbol_briefs.items(), key=lambda x: x[1].get("score", 50))[:3]
                        top_str = " ".join([f"{s}:{int(b.get('score', 50))}" for s, b in top_symbols])
                        bottom_str = " ".join([f"{s}:{int(b.get('score', 50))}" for s, b in bottom_symbols])
                        
                        # Check for flat scores warning
                        all_scores = [b["score"] for b in symbol_briefs.values()]
                        scores_flat = len(set(all_scores)) <= 2
                        
                        if scores_flat:
                            print(f"[SCAN][WARN] scores_flat detected -> check indicator pipeline")
                            print(f"[SCAN][DEBUG] All scores: {all_scores}")
                            if symbols:
                                first_sym = symbols[0]
                                first_brief = symbol_briefs.get(first_sym, {})
                                print(f"[SCAN][DEBUG] {first_sym} detail: RSI={first_brief.get('rsi', '?')}, trend={first_brief.get('trend', '?')}, price=${first_brief.get('price', 0):.2f}")
                        print(f"[SCAN] top5=[{top_str}] bottom3=[{bottom_str}]")

                        
                    except Exception as e:
                        print(f"[VISION][ERROR] market data failed: {e}")
                        import traceback
                        traceback.print_exc()
                        # Continue without vision data - don't crash
                    
                    # v12.7: Fetch external data (F&G, News, Macro) - Throttle to 5 mins
                    if current_time - last_external_fetch > 300:
                        try:
                            print("[DATA] Fetching external market data (F&G, Macro, News)...")
                            external_data = get_all_external_data()
                            last_external_fetch = current_time
                        except Exception as e:
                            print(f"[DATA][ERROR] Failed to fetch external data: {e}")
                    
                    state["market_data"] = external_data
                    
                    # Log Hyperliquid status
                    prices_ok = len(prices)
                    positions_symbols = list(positions_by_symbol.keys())
                    print(f"[HL] snapshot symbols={len(snapshot_symbols)} prices_ok={prices_ok} positions={positions_symbols if positions_symbols else '[]'}")
                    print(f"[STATE] equity={summary['equity']:.2f} positions_count={summary['positions_count']} buying_power=${state.get('buying_power', 0):.0f}")
                    
                    # v11.0: Sync state to Telegram
                    if TELEGRAM_AVAILABLE:
                        update_telegram_state(state)
                    
                    # v12.6: Sync state to Dashboard API
                    if dashboard_api:
                        try:
                            # Build positions list for dashboard
                            dashboard_positions = []
                            for sym, pos in positions_by_symbol.items():
                                pos_detail = state.get("position_details", {}).get(sym, {})
                                mark_px = state.get("prices", {}).get(sym, pos.get("entry_price", 0))
                                dashboard_positions.append({
                                    "symbol": str(sym).upper(),
                                    "side": pos.get("side", "UNKNOWN"),
                                    "size": abs(float(pos.get("size", 0))),
                                    "entry_price": float(pos.get("entry_price", 0)),
                                    "mark_price": float(mark_px),
                                    "unrealized_pnl": float(pos.get("unrealized_pnl", 0)),
                                    "pnl_pct": pos_detail.get("pnl_pct", 0),
                                    "leverage": int(pos.get("leverage", 1)),
                                    "stop_loss": pos_detail.get("current_sl"),
                                    "take_profit": pos_detail.get("current_tp")
                                })
                            
                            # Build market data
                            market_data = state.get("market_data", {})
                            top_syms = [s for s, b in sorted(state.get("symbol_briefs", {}).items(), 
                                                              key=lambda x: x[1].get("score", 0), reverse=True)[:5]]
                            
                            update_dashboard_state({
                                "account": {
                                    "equity": summary["equity"],
                                    "balance": summary.get("balance", summary["equity"]),
                                    "buying_power": state.get("buying_power", 0),
                                    "positions_count": summary["positions_count"]
                                },
                                "positions": dashboard_positions,
                                "market": {
                                    "fear_greed": external_data.get("fear_greed", {}).get("value"),
                                    "btc_dominance": external_data.get("market", {}).get("btc_dominance", 0),
                                    "top_symbols": top_syms,
                                    "macro": external_data.get("macro", {}),
                                    "news": external_data.get("news", [])[:5]
                                }
                            })
                        except Exception as e:
                            pass  # Silent fail for dashboard

                    
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
                    # State-based throttle: call AI if state changed OR cooldown passed
                    time_since_last_call = current_time - last_ai_call_time
                    
                    # Calculate state change (equity, positions)
                    current_equity = state.get("equity", 0.0)
                    equity_change_pct = abs((current_equity - last_equity) / last_equity * 100) if last_equity > 0 else 100
                    positions_changed = len(state.get("positions", {})) != len(state.get("_last_positions", {}))
                    
                    # Calculate total unrealized PnL for sensitivity
                    total_unpnl = sum(p.get("unrealized_pnl", 0) for p in state.get("positions", {}).values())
                    
                    # v15.0: Price Volatility Trigger (Wake up on big moves even if no position)
                    current_price = state.get("prices", {}).get(SYMBOL, 0)
                    price_change_pct = 0
                    if last_ai_price > 0 and current_price > 0:
                        price_change_pct = abs((current_price - last_ai_price) / last_ai_price * 100)
                    
                    # Build sensitive state hash (positions + equity + unpnl + price_tier)
                    current_hash = f"{len(state.get('positions', {}))}_{current_equity:.1f}_{total_unpnl:.1f}_{int(current_price/100)}"
                    state_changed = current_hash != last_state_hash
                    
                    # Wake up if: Equity changed OR State changed OR Price moved > threshold
                    material_change = equity_change_pct >= LLM_STATE_CHANGE_THRESHOLD or state_changed or price_change_pct >= PRICE_CHANGE_THRESHOLD
                    
                    # v15.1: Extreme Volatility Bypass (bypass LLM_MIN_SECONDS if price moves > VOLATILITY_TRIGGER_PCT)
                    high_volatility = price_change_pct >= VOLATILITY_TRIGGER_PCT
                    
                    min_time_passed = time_since_last_call >= LLM_MIN_SECONDS
                    full_cooldown_passed = time_since_last_call >= AI_CALL_INTERVAL_SECONDS
                    
                    # v16: Candle Close Sync - trigger AI at 4h boundaries only (00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC)
                    current_hour = datetime.now(timezone.utc).hour
                    is_4h_boundary = (current_hour % 4 == 0)
                    candle_close_trigger = is_4h_boundary and (current_hour != last_candle_hour) and (last_candle_hour != -1)
                    if candle_close_trigger:
                        print(f"[LLM] 🕐 4H Candle close detected! Hour {last_candle_hour} → {current_hour} (UTC)")
                    
                    # Call AI if: (min time passed AND material change) OR (full cooldown passed) OR (high volatility) OR (candle close)
                    should_call_ai = (min_time_passed and material_change) or full_cooldown_passed or high_volatility or candle_close_trigger
                    
                    if should_call_ai:
                        try:
                            # Get AI decision
                            decision = llm.decide(state)
                            
                            # Store last decision with timestamp for Telegram
                            # Store last decision with timestamp for Telegram
                            state["last_decision"] = {
                                "timestamp": datetime.utcnow().isoformat(),
                                "summary": decision.get("summary", ""),
                                "confidence": decision.get("confidence", 0),
                                "actions": decision.get("actions", [])
                            }
                            
                            # v13.0: Update AI thoughts in dashboard
                            if dashboard_api:
                                try:
                                    from dashboard_api import add_ai_thought
                                    add_ai_thought({
                                        "summary": decision.get("summary", "No summary"),
                                        "confidence": decision.get("confidence", 0),
                                        "emoji": "🤖" if "TRADE" in decision.get("action_type", "") else "🧐"
                                    })
                                except:
                                    pass
                            
                            # Update tracking
                            last_ai_call_time = current_time
                            last_state_hash = current_hash
                            last_equity = current_equity
                            last_ai_price = current_price
                            last_candle_hour = current_hour  # v16: Update candle hour after AI call
                            
                            # Execute actions from LLM
                            actions = decision.get("actions", [])
                            if actions:
                                # Tag all actions as coming from LLM
                                for action in actions:
                                    action["source"] = "LLM"
                                    
                                    # INJECT MARKET DATA FOR TRADE JOURNAL
                                    sym = action.get("symbol")
                                    if sym:
                                        # 1. Indicators
                                        inds = state.get("indicators_by_symbol", {}).get(sym, {})
                                        action["_rsi"] = inds.get("rsi_14", 50)
                                        action["_trend"] = inds.get("trend", "UNKNOWN")
                                        action["_bos"] = inds.get("bos_status", "UNKNOWN") # check key in executor (it expects _bos)
                                        action["_choch"] = inds.get("choch_detected", False)
                                        action["_atr_pct"] = inds.get("atr_pct", 0)
                                        action["_relative_volume"] = inds.get("relative_volume", 1.0)
                                        
                                        # 2. Funding/OI
                                        funding = state.get("funding_by_symbol", {}).get(sym, {})
                                        if isinstance(funding, dict):
                                            # HL API usually returns string values
                                            try:
                                                action["_funding_rate"] = float(funding.get("fundingRate", 0))
                                                action["_open_interest"] = float(funding.get("openInterest", 0))
                                            except:
                                                pass
                                    
                                    # 3. Decision Context
                                    if "reason" not in action:
                                        action["reason"] = decision.get("summary", "AI Decision")
                                    if "confidence" not in action:
                                        action["confidence"] = decision.get("confidence", 0)

                                execute(actions, live_trading=LIVE_TRADING, hl_client=hl)
                            
                            # Log actions to dashboard
                            if dashboard_api:
                                for action in actions:
                                    add_ai_action({
                                        "type": action.get("type", "UNKNOWN"),
                                        "symbol": action.get("symbol", "ALL"),
                                        "side": action.get("side", ""),
                                        "reason": action.get("reason", decision.get("summary", "")),
                                        "confidence": decision.get("confidence", 0)
                                    })
                            
                        except Exception as e:
                            print(f"[LLM][ERROR] {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        remaining = LLM_MIN_SECONDS - time_since_last_call if not min_time_passed else AI_CALL_INTERVAL_SECONDS - time_since_last_call
                        # v16: Update candle hour even when skipping (for initialization)
                        if last_candle_hour == -1:
                            last_candle_hour = current_hour
                            print(f"[LLM] 🕐 Initialized candle hour tracking: {current_hour}h UTC")
                        print(f"[LLM] skipped (cooldown {max(0, remaining):.0f}s, state_changed={state_changed}, hour={current_hour}h)")
            
            # BLOCO 4: Test Trade Request Processing (from Telegram)
            if TELEGRAM_AVAILABLE and llm:
                test_request = get_test_trade_request()
                if test_request:
                    print(f"[TEST_TRADE] Processing request for {len(test_request['symbols'])} symbols")
                    
                    results = []
                    trades_executed = 0
                    holds = 0
                    
                    for symbol in test_request['symbols']:
                        try:
                            # Build state for this symbol
                            symbol_state = state.copy()
                            symbol_state['snapshot_symbols'] = [symbol]
                            
                            # Get AI decision for this symbol
                            print(f"[TEST_TRADE] Calling AI for {symbol}...")
                            decision = llm.decide(symbol_state)
                            
                            # Process decision
                            actions = decision.get("actions", [])
                            summary = decision.get("summary", "No summary")
                            confidence = decision.get("confidence", 0)
                            
                            if actions and any(a.get("type") != "NO_TRADE" for a in actions):
                                # Execute trade
                                execute(actions, live_trading=LIVE_TRADING, hl_client=hl)
                                trades_executed += 1
                                
                                # Get action details
                                trade_action = next((a for a in actions if a.get("type") != "NO_TRADE"), actions[0])
                                action_type = trade_action.get("type", "UNKNOWN")
                                side = trade_action.get("side", "")
                                
                                results.append(f"✅ {symbol}: {action_type} {side} (Conf: {confidence:.2f})")
                                results.append(f"   Razão: {summary[:60]}")
                            else:
                                # Hold
                                holds += 1
                                results.append(f"⏸️ {symbol}: HOLD (Conf: {confidence:.2f})")
                                results.append(f"   Razão: {summary[:60]}")
                            
                        except Exception as e:
                            results.append(f"❌ {symbol}: Erro - {str(e)[:50]}")
                            print(f"[TEST_TRADE][ERROR] {symbol}: {e}")
                    
                    # Build result message
                    result_text = (
                        f"🧪 *TEST TRADE CONCLUÍDO*\\n\\n"
                        f"Símbolos analisados: {len(test_request['symbols'])}\\n"
                        f"Trades executados: {trades_executed}\\n"
                        f"Holds: {holds}\\n\\n"
                        f"*Resultados:*\\n"
                        + "\\n".join(results)
                    )
                    
                    # Send result back to Telegram
                    send_test_trade_result(test_request['chat_id'], result_text)
                    
                    # Clear request
                    clear_test_trade_request()
                    
                    print(f"[TEST_TRADE] Completed: {trades_executed} trades, {holds} holds")
            
            # Update Dashboard state (sync with dashboard API)
            if DASHBOARD_AVAILABLE:
                try:
                    # Build positions with correct format including symbol
                    formatted_positions = []
                    for sym, pos in state.get("positions", {}).items():
                        pos_detail = state.get("position_details", {}).get(sym, {})
                        mark_px = state.get("prices", {}).get(sym, pos.get("entry_price", 0))
                        formatted_positions.append({
                            "symbol": str(sym).upper(),
                            "side": pos.get("side", "UNKNOWN"),
                            "size": abs(float(pos.get("size", 0))),
                            "entry_price": float(pos.get("entry_price", 0)),
                            "mark_price": float(mark_px),
                            "unrealized_pnl": float(pos.get("unrealized_pnl", 0)),
                            "pnl_pct": pos_detail.get("pnl_pct", 0),
                            "leverage": int(pos.get("leverage", 1)),
                        })
                    
                    update_dashboard_state({
                        "account": {
                            "equity": state.get("equity", 0),
                            "buying_power": state.get("available_margin", 0),  # Real Available Margin
                            "positions_count": len(state.get("positions", {}))
                        },
                        "positions": formatted_positions,
                        "market": state.get("market", {})
                    })
                except Exception as e:
                    print(f"[DASHBOARD][ERROR] {e}")
            
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


