"""
Executor for Engine V0
Handles trade execution in PAPER and LIVE modes
"""
import json
import hashlib
import time
from typing import List, Dict, Any

from config import (
    LIVE_TRADING,
    MAX_ACTIONS_PER_TICK,
    ACTION_DEDUP_SECONDS,
    MIN_NOTIONAL_USD,
    PLACE_ORDER_DEDUP_SECONDS,
    TRIGGER_DEDUP_SECONDS,
    MAX_OPEN_ORDERS_PER_SYMBOL,
    MAX_POSITION_ADDS_PER_HOUR
)


def _format_resp(resp: Any) -> str:
    """Format response as compact JSON for logging"""
    if isinstance(resp, dict):
        return json.dumps(resp, separators=(',', ':'))
    return str(resp)


# Track executed actions with intent-based deduplication
_intent_history: Dict[str, float] = {}  # {intent_key: timestamp}
_adds_history: Dict[str, List[float]] = {}  # {symbol: [timestamps]}


def _get_intent_key(action: Dict[str, Any]) -> str:
    """Generate intent key for deduplication (by intention, not exact params)"""
    action_type = action.get("type", "UNKNOWN")
    symbol = action.get("symbol", "?")
    
    if action_type == "PLACE_ORDER":
        side = action.get("side", "?")
        return f"PLACE_ORDER:{symbol}:{side}"
    elif action_type in ("SET_STOP_LOSS", "SET_TAKE_PROFIT", "MOVE_STOP_TO_BREAKEVEN"):
        return f"{action_type}:{symbol}"
    elif action_type == "CLOSE_PARTIAL":
        pct = action.get("pct", action.get("size", "?"))
        return f"CLOSE_PARTIAL:{symbol}:{pct}"
    else:
        # Fallback to hash for other types
        action_str = json.dumps(action, sort_keys=True)
        return hashlib.sha1(action_str.encode()).hexdigest()


def _get_intent_ttl(action_type: str) -> int:
    """Get TTL for intent based on action type"""
    if action_type == "PLACE_ORDER":
        return PLACE_ORDER_DEDUP_SECONDS
    elif action_type in ("SET_STOP_LOSS", "SET_TAKE_PROFIT", "MOVE_STOP_TO_BREAKEVEN"):
        return TRIGGER_DEDUP_SECONDS
    else:
        return ACTION_DEDUP_SECONDS


def _is_intent_duplicate(intent_key: str, action_type: str, current_time: float) -> bool:
    """Check if intent is duplicate within TTL window"""
    if intent_key in _intent_history:
        last_time = _intent_history[intent_key]
        ttl = _get_intent_ttl(action_type)
        if current_time - last_time < ttl:
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
    
    # Process each action with honest counting
    current_time = time.time()
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for action in actions:
        # Check for duplicates using temporal window
        action_id = _get_action_id(action)
        if _is_duplicate(action_id, current_time):
            print(f"[EXEC][DEDUP] skipped duplicate action: {action.get('type', 'UNKNOWN')}")
            skipped_count += 1
            continue
        
        action_type = action.get("type", "UNKNOWN")
        action_success = False
        
        try:
            if action_type == "PLACE_ORDER":
                action_success = _execute_place_order(action, is_paper, hl_client)
            elif action_type == "CLOSE_POSITION":
                action_success = _execute_close_position(action, is_paper, hl_client)
            elif action_type == "MOVE_STOP_TO_BREAKEVEN":
                action_success = _execute_move_stop_to_breakeven(action, is_paper, hl_client)
            elif action_type == "SET_STOP_LOSS":
                action_success = _execute_set_stop_loss(action, is_paper, hl_client)
            elif action_type == "SET_TAKE_PROFIT":
                action_success = _execute_set_take_profit(action, is_paper, hl_client)
            elif action_type == "CANCEL_ALL":
                action_success = _execute_cancel_all(action, is_paper, hl_client)
            elif action_type == "CLOSE_PARTIAL":
                action_success = _execute_close_partial(action, is_paper, hl_client)
            elif action_type == "CANCEL_ORDER":
                action_success = _execute_cancel_order(action, is_paper, hl_client)
            elif action_type == "MODIFY_ORDER":
                action_success = _execute_modify_order(action, is_paper, hl_client)
            else:
                print(f"[EXEC][WARN] unknown action type: {action_type}")
                failed_count += 1
                continue
            
            # Count based on actual success
            if action_success:
                _action_history[action_id] = current_time
                success_count += 1
            else:
                failed_count += 1
            
        except Exception as e:
            print(f"[EXEC][ERROR] failed to execute {action_type}: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1
    
    # Honest logging
    total = len(actions)
    print(f"[EXEC] done success={success_count} failed={failed_count} skipped={skipped_count} total={total}")
    
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
        return
    
    # LIVE execution
    try:
        # Import normalizer functions
        from normalizer import normalize_place_order
        
        # Get current price and constraints
        price = hl_client.get_last_price(symbol)
        if not price:
            print(f"[LIVE][ERROR] failed to get price for {symbol}")
            return
        
        constraints = hl_client.get_symbol_constraints(symbol)
        
        # Normalize order
        normalized, reject_reason = normalize_place_order(action, price, constraints)
        
        if normalized is None:
            print(f"[REJECT] {symbol} reason={reject_reason}")
            return
        
        # Log before execution
        print(f"[LIVE] action=PLACE_ORDER payload={_format_resp(normalized)}")
        
        # Set leverage if specified
        leverage = normalized.get("leverage")
        margin_mode = normalized.get("margin_mode", "isolated")
        
        if leverage:
            is_cross = (margin_mode == "cross")
            lev_resp = hl_client.update_leverage(symbol, leverage, is_cross)
            print(f"[LIVE] leverage set: {leverage}x {margin_mode} resp={_format_resp(lev_resp)}")
        
        # Execute market order
        is_buy = (side == "BUY")
        
        resp = hl_client.place_market_order(
            symbol=symbol,
            is_buy=is_buy,
            size=normalized["size"]
        )
        
        # Log response
        print(f"[LIVE] resp={_format_resp(resp)}")
        
        # Parse response to detect rejections
        success = _parse_response_success(resp)
        
        if not success:
            error_msg = _extract_error_message(resp)
            print(f"[LIVE][REJECT] {symbol} exchange_error={error_msg}")
            return
        
        # Post-verification only if successful
        _post_verify(hl_client, symbol, "PLACE_ORDER")
        
    except Exception as e:
        print(f"[LIVE][ERROR] PLACE_ORDER {symbol} failed: {e}")
        import traceback
        traceback.print_exc()


def _parse_response_success(resp: dict) -> bool:
    """Check if exchange response indicates success"""
    if not resp:
        return False
    
    # Check status field
    if resp.get("status") == "error":
        return False
    
    if resp.get("status") != "ok":
        return False
    
    # Check for errors in response data
    response_data = resp.get("response", {})
    if isinstance(response_data, dict):
        data = response_data.get("data", {})
        if isinstance(data, dict):
            statuses = data.get("statuses", [])
            if statuses:
                # Check if any status has error
                for status in statuses:
                    if isinstance(status, dict) and "error" in status:
                        return False
    
    return True


def _extract_error_message(resp: dict) -> str:
    """Extract error message from response"""
    if resp.get("status") == "error":
        return str(resp.get("response", "unknown_error"))
    
    response_data = resp.get("response", {})
    if isinstance(response_data, dict):
        data = response_data.get("data", {})
        if isinstance(data, dict):
            statuses = data.get("statuses", [])
            if statuses:
                for status in statuses:
                    if isinstance(status, dict) and "error" in status:
                        return str(status["error"])
    
    return "unknown_error"


def _post_verify(hl_client, symbol: str, action_type: str) -> None:
    """Post-execution verification"""
    try:
        # Get current positions
        positions = hl_client.get_positions_by_symbol()
        
        # Get recent fills
        fills = hl_client.get_recent_fills(limit=5)
        
        # Log verification
        positions_count = len(positions)
        positions_compact = {k: f"{v['side']} {v['size']}" for k, v in list(positions.items())[:3]}
        
        print(f"[VERIFY] positions_count={positions_count} positions={positions_compact}")
        
        if fills:
            fills_compact = [{
                "coin": f.get("coin", "?"),
                "side": f.get("side", "?"),
                "sz": f.get("sz", 0)
            } for f in fills[:3]]
            print(f"[VERIFY] last_fills={fills_compact}")
        else:
            print(f"[VERIFY] last_fills=[]")
        
        # Warning if no position after PLACE_ORDER
        if action_type == "PLACE_ORDER" and symbol not in positions:
            print(f"[VERIFY][WARN] No position for {symbol} after LIVE order. Likely reject (min notional/decimals/margin/leverage). Check resp above.")
        
    except Exception as e:
        print(f"[VERIFY][ERROR] {e}")


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
        return
    
    # LIVE execution - convert to SET_STOP_LOSS at entry price
    try:
        positions = hl_client.get_positions_by_symbol()
        
        if symbol not in positions:
            print(f"[LIVE][WARN] MOVE_STOP_TO_BREAKEVEN {symbol} skipped - no position")
            return
        
        position = positions[symbol]
        entry_price = position["entry_price"]
        
        print(f"[LIVE] MOVE_STOP_TO_BREAKEVEN {symbol} entry=${entry_price:.2f}")
        
        # Convert to SET_STOP_LOSS action
        set_sl_action = {
            "type": "SET_STOP_LOSS",
            "symbol": symbol,
            "stop_price": entry_price
        }
        
        # Execute SET_STOP_LOSS
        _execute_set_stop_loss(set_sl_action, is_paper=False, hl_client=hl_client)
        
    except Exception as e:
        print(f"[LIVE][ERROR] MOVE_STOP_TO_BREAKEVEN {symbol} failed: {e}")
        import traceback
        traceback.print_exc()


def _execute_set_stop_loss(action: Dict[str, Any], is_paper: bool, hl_client) -> None:
    """Execute SET_STOP_LOSS action"""
    symbol = action.get("symbol", "?")
    stop_price = action.get("stop_price", 0)
    
    if is_paper:
        print(f"[PAPER] would SET_STOP_LOSS {symbol} stop=${stop_price:.2f}")
        return
    
    # LIVE execution
    try:
        # Get current position to determine size and side
        positions = hl_client.get_positions_by_symbol()
        
        if symbol not in positions:
            print(f"[LIVE][WARN] SET_STOP_LOSS {symbol} skipped - no position")
            return
        
        position = positions[symbol]
        position_size = position["size"]
        position_side = position["side"]
        
        # Stop loss triggers opposite side
        # LONG position -> SELL trigger, SHORT position -> BUY trigger
        is_buy_trigger = (position_side == "SHORT")
        
        print(f"[LIVE] SET_STOP_LOSS {symbol} stop=${stop_price:.2f} size={position_size}")
        
        # Place trigger order
        resp = hl_client.place_trigger_order(
            symbol=symbol,
            is_buy=is_buy_trigger,
            trigger_price=stop_price,
            size=position_size,
            is_stop_loss=True,
            reduce_only=True
        )
        
        print(f"[LIVE] resp={_format_resp(resp)}")
        
        # Parse response
        success = _parse_response_success(resp)
        
        if not success:
            error_msg = _extract_error_message(resp)
            print(f"[LIVE][REJECT] {symbol} exchange_error={error_msg}")
            return
        
    except Exception as e:
        print(f"[LIVE][ERROR] SET_STOP_LOSS {symbol} failed: {e}")
        import traceback
        traceback.print_exc()


def _execute_set_take_profit(action: Dict[str, Any], is_paper: bool, hl_client) -> None:
    """Execute SET_TAKE_PROFIT action"""
    symbol = action.get("symbol", "?")
    tp_price = action.get("tp_price", 0)
    
    if is_paper:
        print(f"[PAPER] would SET_TAKE_PROFIT {symbol} tp=${tp_price:.2f}")
        return
    
    # LIVE execution
    try:
        # Get current position to determine size and side
        positions = hl_client.get_positions_by_symbol()
        
        if symbol not in positions:
            print(f"[LIVE][WARN] SET_TAKE_PROFIT {symbol} skipped - no position")
            return
        
        position = positions[symbol]
        position_size = position["size"]
        position_side = position["side"]
        
        # Take profit triggers opposite side
        # LONG position -> SELL trigger, SHORT position -> BUY trigger
        is_buy_trigger = (position_side == "SHORT")
        
        print(f"[LIVE] SET_TAKE_PROFIT {symbol} tp=${tp_price:.2f} size={position_size}")
        
        # Place trigger order
        resp = hl_client.place_trigger_order(
            symbol=symbol,
            is_buy=is_buy_trigger,
            trigger_price=tp_price,
            size=position_size,
            is_stop_loss=False,  # This is take profit
            reduce_only=True
        )
        
        print(f"[LIVE] resp={_format_resp(resp)}")
        
        # Parse response
        success = _parse_response_success(resp)
        
        if not success:
            error_msg = _extract_error_message(resp)
            print(f"[LIVE][REJECT] {symbol} exchange_error={error_msg}")
            return
        
    except Exception as e:
        print(f"[LIVE][ERROR] SET_TAKE_PROFIT {symbol} failed: {e}")
        import traceback
        traceback.print_exc()


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
    
    if is_paper:
        if pct is not None:
            print(f"[PAPER] would CLOSE_PARTIAL {symbol} pct={pct:.1%}")
        elif size is not None:
            print(f"[PAPER] would CLOSE_PARTIAL {symbol} size={size}")
        return
    
    # LIVE execution
    try:
        # Get current position to calculate size
        positions = hl_client.get_positions_by_symbol()
        
        if symbol not in positions:
            print(f"[LIVE][WARN] CLOSE_PARTIAL {symbol} skipped - no position")
            return
        
        position = positions[symbol]
        position_size = position["size"]
        
        # Calculate size to close
        if pct is not None:
            close_size = position_size * pct
        elif size is not None:
            close_size = min(size, position_size)  # Don't close more than we have
        else:
            print(f"[LIVE][ERROR] CLOSE_PARTIAL {symbol} - no pct or size specified")
            return
        
        print(f"[LIVE] CLOSE_PARTIAL {symbol} size={close_size:.6f}")
        
        # Use market_close
        resp = hl_client.close_position_market(symbol, size=close_size)
        
        print(f"[LIVE] resp={_format_resp(resp)}")
        
        # Parse response
        success = _parse_response_success(resp)
        
        if not success:
            error_msg = _extract_error_message(resp)
            print(f"[LIVE][REJECT] {symbol} exchange_error={error_msg}")
            return
        
        _post_verify(hl_client, symbol, "CLOSE_PARTIAL")
        
    except Exception as e:
        print(f"[LIVE][ERROR] CLOSE_PARTIAL {symbol} failed: {e}")
        import traceback
        traceback.print_exc()


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
