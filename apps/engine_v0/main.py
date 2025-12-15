"""
Engine V0 - Main Loop
Trading bot engine with Hyperliquid integration and AI decisions
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
    
    try:
        while True:
            iteration += 1
            current_time = time.time()
            print(f"\n[LOOP] tick {iteration}")
            
            # Initialize state for this iteration
            state = {
                "time": datetime.now().isoformat(),
                "equity": 0.0,
                "positions_count": 0,
                "positions": [],
                "open_orders_count": 0,
                "price": None,
                "symbol": symbols[0] if symbols else "BTC",
                "live_trading": LIVE_TRADING
            }
            
            # BLOCO 1: Hyperliquid integration
            if hl and symbols:
                try:
                    # Get account summary
                    summary = hl.get_account_summary()
                    state["equity"] = summary["equity"]
                    state["positions_count"] = summary["positions_count"]
                    
                    # Get positions (for richer state)
                    positions = hl.get_positions()
                    state["positions"] = [
                        {
                            "symbol": p["coin"],
                            "side": "LONG" if p["size"] > 0 else "SHORT",
                            "size": abs(p["size"]),
                            "entry_price": p["entry_price"],
                            "unrealized_pnl": p["unrealized_pnl"]
                        }
                        for p in positions
                    ]
                    
                    # Get price for first symbol (to avoid rate limits)
                    first_symbol = symbols[0]
                    price = hl.get_last_price(first_symbol)
                    state["price"] = price
                    state["symbol"] = first_symbol
                    
                    # Log Hyperliquid status
                    print(f"[HL] ok equity={summary['equity']:.2f} positions={summary['positions_count']} price_{first_symbol}={price}")
                    
                except Exception as e:
                    print(f"[HL][ERROR] {e}")
            
            # BLOCO 2: Test executor with forced action (only first iteration)
            if FORCE_TEST_ORDER and not test_order_executed:
                print("[TEST] forcing 1 test order (PAPER)")
                
                # Create test action
                test_actions = [{
                    "type": "PLACE_ORDER",
                    "symbol": test_symbol,
                    "side": TEST_ORDER_SIDE,
                    "size": TEST_ORDER_SIZE,
                    "orderType": "MARKET"
                }]
                
                # Execute (always PAPER, no hl_client passed)
                execute(test_actions, live_trading=LIVE_TRADING, hl_client=None)
                
                test_order_executed = True
            
            # BLOCO 3: AI decision engine
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
                            
                            # Execute actions (PAPER for now, no hl_client)
                            actions = decision.get("actions", [])
                            if actions:
                                execute(actions, live_trading=LIVE_TRADING, hl_client=None)
                            
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
