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
                    
                    # v10.2: Build trigger status for each position (BRACKET RECONCILE)
                    trigger_status_lines = []
                    for pos_symbol, pos_data in positions_by_symbol.items():
                        symbol_orders = open_orders_by_symbol.get(pos_symbol, [])
                        has_sl = False
                        has_tp = False
                        sl_price = None
                        tp_price = None
                        
                        for order in symbol_orders:
                            if order.get("reduceOnly"):
                                trigger_px = order.get("triggerPx") or order.get("trigger_px") or order.get("limitPx")
                                if trigger_px:
                                    trigger_px = float(trigger_px)
                                    entry_px = pos_data.get("entry_price", 0)
                                    pos_side = pos_data.get("side", "LONG")
                                    
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
                        
                        sl_str = f"SL=${sl_price:.2f}" if has_sl else "SL=MISSING!"
                        tp_str = f"TP=${tp_price:.2f}" if has_tp else "TP=MISSING!"
                        trigger_status_lines.append(f"  - {pos_symbol}: {sl_str} | {tp_str}")
                    
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
                        # Multi-timeframe candles and indicators
                        candles_by_symbol = {}
                        indicators_by_symbol = {}
                        
                        for symbol in snapshot_symbols[:3]:  # Limit to top 3 to avoid API spam
                            # Get candles for multiple timeframes
                            candles_15m = hl.get_candles(symbol, "15m", limit=50)
                            candles_1h = hl.get_candles(symbol, "1h", limit=50)
                            
                            candles_by_symbol[symbol] = {
                                "15m": candles_15m[-20:] if candles_15m else [],  # Last 20 for state size
                                "1h": candles_1h[-20:] if candles_1h else []
                            }
                            
                            # Calculate indicators from 15m (primary timeframe) if available
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
                        
                        # Orderbook for top symbols
                        orderbook_by_symbol = {}
                        for symbol in snapshot_symbols[:3]:
                            orderbook_by_symbol[symbol] = hl.get_orderbook(symbol, depth=5)
                        state["orderbook_by_symbol"] = orderbook_by_symbol
                        
                        # Funding info
                        funding_by_symbol = {}
                        for symbol in snapshot_symbols[:3]:
                            funding_by_symbol[symbol] = hl.get_funding_info(symbol)
                        state["funding_by_symbol"] = funding_by_symbol
                        
                        print(f"[VISION] candles={len(candles_by_symbol)} indicators={len(indicators_by_symbol)} orderbook={len(orderbook_by_symbol)}")
                        
                    except Exception as e:
                        print(f"[VISION][ERROR] market data failed: {e}")
                        import traceback
                        traceback.print_exc()
                        # Continue without vision data - don't crash
                    
                    # Log Hyperliquid status
                    prices_ok = len(prices)
                    positions_symbols = list(positions_by_symbol.keys())
                    print(f"[HL] snapshot symbols={len(snapshot_symbols)} prices_ok={prices_ok} positions={positions_symbols if positions_symbols else '[]'}")
                    print(f"[STATE] equity={summary['equity']:.2f} positions_count={summary['positions_count']}")
                    
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
