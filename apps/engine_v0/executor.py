"""
Executor for Engine V0
Handles trade execution in PAPER and LIVE modes
"""
import json
import hashlib
import time
from typing import List, Dict, Any

from config import MAX_ACTIONS_PER_TICK, ACTION_DEDUP_SECONDS


# Track executed actions with timestamps for temporal deduplication
_action_history: Dict[str, float] = {}


def _get_action_id(action: Dict[str, Any]) -> str:
    """Generate unique ID for action"""
    action_str = json.dumps(action, sort_keys=True)
    return hashlib.sha1(action_str.encode()).hexdigest()


def _is_duplicate(action_id: str, current_time: float) -> bool:
    """Check if action is duplicate within dedup window"""
    if action_id in _action_history:
        last_time = _action_history[action_id]
        if current_time - last_time < ACTION_DEDUP_SECONDS:
            return True
    return False


def execute(actions: List[Dict[str, Any]], live_trading: bool, hl_client=None) -> None:
    """
    Execute trading actions
    
    Args:
        actions: List of action dictionaries
        live_trading: Whether to execute live trades
        hl_client: HLClient instance for live trading (required if live_trading=True)
    """
    if not actions:
        print("[EXEC] actions=0")
        print("[EXEC] ok")
        return
    
    # Truncate if too many actions
    if len(actions) > MAX_ACTIONS_PER_TICK:
        print(f"[EXEC][LIMIT] truncated from {len(actions)} to {MAX_ACTIONS_PER_TICK}")
        actions = actions[:MAX_ACTIONS_PER_TICK]
    
    print(f"[EXEC] actions={len(actions)}")
    
    # Determine if PAPER or LIVE
    is_paper = not live_trading or hl_client is None
    
    if live_trading and hl_client is None:
        print("[EXEC][WARN] LIVE_TRADING=True but no hl_client provided, running as PAPER")
        is_paper = True
    
    # Process each action
    current_time = time.time()
    executed_count = 0
    
    for action in actions:
        # Check for duplicates using temporal window
        action_id = _get_action_id(action)
        if _is_duplicate(action_id, current_time):
            print(f"[EXEC][DEDUP] skipped duplicate action: {action.get('type', 'UNKNOWN')}")
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
            elif action_type == "CLOSE_PARTIAL":
                _execute_close_partial(action, is_paper, hl_client)
            elif action_type == "CANCEL_ORDER":
                _execute_cancel_order(action, is_paper, hl_client)
            elif action_type == "MODIFY_ORDER":
                _execute_modify_order(action, is_paper, hl_client)
            else:
                print(f"[EXEC][WARN] unknown action type: {action_type}")
                continue
            
            # Mark as executed with timestamp
            _action_history[action_id] = current_time
            executed_count += 1
            
        except Exception as e:
            print(f"[EXEC][ERROR] failed to execute {action_type}: {e}")
    
    print(f"[EXEC] ok (executed {executed_count}/{len(actions)})")
    
    # Clean old entries from history (older than dedup window)
    cutoff_time = current_time - ACTION_DEDUP_SECONDS
    _action_history.clear()  # Simple approach: clear all on each iteration
    # Alternative: {k: v for k, v in _action_history.items() if v >= cutoff_time}


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


def _execute_close_partial(action: Dict[str, Any], is_paper: bool, hl_client) -> None:
    """Execute CLOSE_PARTIAL action"""
    symbol = action.get("symbol", "?")
    pct = action.get("pct")
    size = action.get("size")
    
    if pct is not None:
        if is_paper:
            print(f"[PAPER] would CLOSE_PARTIAL {symbol} pct={pct:.1%}")
        else:
            print(f"[LIVE] closing partial {symbol} pct={pct:.1%}")
            # TODO: hl_client.close_position_market(symbol, pct)
    elif size is not None:
        if is_paper:
            print(f"[PAPER] would CLOSE_PARTIAL {symbol} size={size}")
        else:
            print(f"[LIVE] closing partial {symbol} size={size}")
            # TODO: hl_client.close_position_market_size(symbol, size)


def _execute_cancel_order(action: Dict[str, Any], is_paper: bool, hl_client) -> None:
    """Execute CANCEL_ORDER action"""
    order_id = action.get("order_id", "?")
    
    if is_paper:
        print(f"[PAPER] would CANCEL_ORDER id={order_id}")
    else:
        print(f"[LIVE] canceling order id={order_id}")
        # TODO: hl_client.cancel_order(order_id)


def _execute_modify_order(action: Dict[str, Any], is_paper: bool, hl_client) -> None:
    """Execute MODIFY_ORDER action"""
    order_id = action.get("order_id", "?")
    new_price = action.get("new_price")
    new_size = action.get("new_size")
    
    if is_paper:
        print(f"[PAPER] would MODIFY_ORDER id={order_id} price={new_price} size={new_size}")
    else:
        print(f"[LIVE] modifying order id={order_id}")
        # TODO: hl_client.modify_order(order_id, new_price, new_size)
