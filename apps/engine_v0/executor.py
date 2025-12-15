"""
Executor for Engine V0
Handles trade execution in PAPER and LIVE modes
"""
import json
import hashlib
from typing import List, Dict, Any, Set

from config import MAX_ACTIONS_PER_TICK


# Track executed actions per iteration to avoid duplicates
_executed_actions: Set[str] = set()


def _get_action_id(action: Dict[str, Any]) -> str:
    """Generate unique ID for action"""
    action_str = json.dumps(action, sort_keys=True)
    return hashlib.sha1(action_str.encode()).hexdigest()


def execute(actions: List[Dict[str, Any]], live_trading: bool, hl_client=None) -> None:
    """
    Execute trading actions
    
    Args:
        actions: List of action dictionaries
        live_trading: Whether to execute live trades (PAPER-only in BLOCO 2-3)
        hl_client: HLClient instance for live trading (optional)
    """
    global _executed_actions
    
    if not actions:
        print("[EXEC] actions=0")
        print("[EXEC] ok")
        return
    
    # Truncate if too many actions
    if len(actions) > MAX_ACTIONS_PER_TICK:
        print(f"[EXEC][WARN] actions truncated from {len(actions)} to {MAX_ACTIONS_PER_TICK}")
        actions = actions[:MAX_ACTIONS_PER_TICK]
    
    print(f"[EXEC] actions={len(actions)}")
    
    # BLOCO 2-3: Always run as PAPER, even if live_trading=True
    # BLOCO 4: Will use live_trading flag
    is_paper = not live_trading or hl_client is None
    
    if live_trading and hl_client is None:
        print("[EXEC][WARN] LIVE_TRADING=True but no hl_client provided, running as PAPER")
        is_paper = True
    
    # Process each action
    executed_count = 0
    for action in actions:
        # Check for duplicates
        action_id = _get_action_id(action)
        if action_id in _executed_actions:
            print(f"[EXEC][WARN] skipping duplicate action: {action.get('type', 'UNKNOWN')}")
            continue
        
        action_type = action.get("type", "UNKNOWN")
        
        try:
            if action_type == "PLACE_ORDER":
                _execute_place_order(action, is_paper, hl_client)
            elif action_type == "CLOSE_POSITION":
                _execute_close_position(action, is_paper, hl_client)
            elif action_type == "MOVE_STOP_TO_BREAKEVEN":
                _execute_move_stop_to_breakeven(action, is_paper, hl_client)
            elif action_type == "SET_STOP_LOSS":
                _execute_set_stop_loss(action, is_paper, hl_client)
            elif action_type == "SET_TAKE_PROFIT":
                _execute_set_take_profit(action, is_paper, hl_client)
            elif action_type == "CANCEL_ALL":
                _execute_cancel_all(action, is_paper, hl_client)
            else:
                print(f"[EXEC][WARN] unknown action type: {action_type}")
                continue
            
            # Mark as executed
            _executed_actions.add(action_id)
            executed_count += 1
            
        except Exception as e:
            print(f"[EXEC][ERROR] failed to execute {action_type}: {e}")
    
    print(f"[EXEC] ok (executed {executed_count}/{len(actions)})")
    
    # Clear executed actions for next iteration
    _executed_actions.clear()


def _execute_place_order(action: Dict[str, Any], is_paper: bool, hl_client) -> None:
    """Execute PLACE_ORDER action"""
    symbol = action.get("symbol", "?")
    side = action.get("side", "?")
    size = action.get("size", 0)
    order_type = action.get("orderType", "MARKET")
    
    if is_paper:
        print(f"[PAPER] would PLACE_ORDER {symbol} {side} size={size} type={order_type}")
    else:
        print(f"[LIVE] placing order {symbol} {side} size={size} type={order_type}")
        # TODO: hl_client.place_market_order(symbol, side, size)


def _execute_close_position(action: Dict[str, Any], is_paper: bool, hl_client) -> None:
    """Execute CLOSE_POSITION action"""
    symbol = action.get("symbol", "?")
    pct = action.get("pct", 1.0)
    order_type = action.get("orderType", "MARKET")
    
    if is_paper:
        print(f"[PAPER] would CLOSE_POSITION {symbol} pct={pct:.1%} type={order_type}")
    else:
        print(f"[LIVE] closing position {symbol} pct={pct:.1%}")
        # TODO: hl_client.close_position_market(symbol, pct)


def _execute_move_stop_to_breakeven(action: Dict[str, Any], is_paper: bool, hl_client) -> None:
    """Execute MOVE_STOP_TO_BREAKEVEN action"""
    symbol = action.get("symbol", "?")
    
    if is_paper:
        print(f"[PAPER] would MOVE_STOP_TO_BREAKEVEN {symbol}")
    else:
        print(f"[LIVE] moving stop to breakeven {symbol}")
        # TODO: hl_client.move_stop_to_breakeven(symbol)


def _execute_set_stop_loss(action: Dict[str, Any], is_paper: bool, hl_client) -> None:
    """Execute SET_STOP_LOSS action"""
    symbol = action.get("symbol", "?")
    stop_price = action.get("stop_price", 0)
    
    if is_paper:
        print(f"[PAPER] would SET_STOP_LOSS {symbol} stop=${stop_price:.2f}")
    else:
        print(f"[LIVE] setting stop loss {symbol} stop=${stop_price:.2f}")
        # TODO: hl_client.set_stop_loss(symbol, stop_price)


def _execute_set_take_profit(action: Dict[str, Any], is_paper: bool, hl_client) -> None:
    """Execute SET_TAKE_PROFIT action"""
    symbol = action.get("symbol", "?")
    tp_price = action.get("tp_price", 0)
    
    if is_paper:
        print(f"[PAPER] would SET_TAKE_PROFIT {symbol} tp=${tp_price:.2f}")
    else:
        print(f"[LIVE] setting take profit {symbol} tp=${tp_price:.2f}")
        # TODO: hl_client.set_take_profit(symbol, tp_price)


def _execute_cancel_all(action: Dict[str, Any], is_paper: bool, hl_client) -> None:
    """Execute CANCEL_ALL action"""
    symbol = action.get("symbol")
    
    if is_paper:
        print(f"[PAPER] would CANCEL_ALL {symbol if symbol else 'all symbols'}")
    else:
        print(f"[LIVE] canceling all orders {symbol if symbol else 'all symbols'}")
        # TODO: hl_client.cancel_all(symbol)
