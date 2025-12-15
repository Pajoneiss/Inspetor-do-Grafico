"""
Executor for Engine V0
Handles trade execution in PAPER and LIVE modes
"""
from typing import List, Dict, Any


def execute(actions: List[Dict[str, Any]], live_trading: bool) -> None:
    """
    Execute trading actions
    
    Args:
        actions: List of action dictionaries with schema:
            {"type": "PLACE_ORDER", "symbol": "BTC", "side": "BUY", "size": 0.001, "orderType": "MARKET"}
        live_trading: Whether to execute live trades (IGNORED in BLOCO 2 - always PAPER)
    """
    if not actions:
        print("[EXEC] actions=0")
        print("[EXEC] ok")
        return
    
    print(f"[EXEC] actions={len(actions)}")
    
    # BLOCO 2: Always run as PAPER, even if live_trading=True
    if live_trading:
        print("[EXEC][WARN] LIVE_TRADING=True but BLOCO2 is PAPER-only.")
    
    # Process each action
    for action in actions:
        action_type = action.get("type", "UNKNOWN")
        
        if action_type == "PLACE_ORDER":
            symbol = action.get("symbol", "?")
            side = action.get("side", "?")
            size = action.get("size", 0)
            order_type = action.get("orderType", "MARKET")
            
            print(f"[PAPER] would PLACE_ORDER {symbol} {side} size={size} type={order_type}")
        else:
            print(f"[PAPER] would execute {action_type}: {action}")
    
    print("[EXEC] ok")
