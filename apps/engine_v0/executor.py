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


# ============================================================================
# BRACKET MANAGER HELPERS (Definitive Order Hygiene)
# ============================================================================

def _identify_reduce_only_orders(open_orders, symbol):
    """
    Identifica TODAS as ordens reduce-only trigger de um símbolo.
    Não tenta diferenciar SL de TP - cancela TUDO e recria.
    """
    triggers = []
    for o in open_orders:
        if o.get("coin") == symbol and o.get("reduceOnly") and o.get("triggerPx"):
            triggers.append(o)
    return triggers


def _cleanup_all_triggers(hl_client, symbol):
    """
    Cancela TODAS as ordens reduce-only trigger antes de recriar.
    Estratégia: Delete ALL, Create 1 (ao invés de tentar identificar qual é qual).
    Returns: número de ordens canceladas
    """
    try:
        open_orders = hl_client.get_open_orders()
        triggers = _identify_reduce_only_orders(open_orders, symbol)
        
        if triggers:
            print(f"[BRACKET] Cleaning {len(triggers)} reduce-only triggers for {symbol}")
            for t in triggers:
                try:
                    hl_client.cancel_order(symbol, t["oid"])
                    print(f"[BRACKET] Canceled oid={t['oid']} trigger_px={t.get('triggerPx')}")
                except Exception as e:
                    print(f"[BRACKET][WARN] Failed to cancel {t['oid']}: {e}")
            
            import time
            time.sleep(0.5)  # Propagation delay
        
        return len(triggers)
    except Exception as e:
        print(f"[BRACKET][ERROR] Cleanup failed for {symbol}: {e}")
        return 0


def _validate_and_adjust_trigger(symbol, trigger_price, position_side, mark_price, tick_sz, is_stop_loss):
    """
    Valida trigger price e ajusta se necessário para garantir ordem válida.
    Returns: (adjusted_trigger, is_valid)
    """
    from decimal import Decimal, ROUND_DOWN, ROUND_UP
    
    # Quantize to tick
    tick_decimal = Decimal(str(tick_sz))
    trigger_decimal = Decimal(str(trigger_price))
    
    # Round appropriately
    if is_stop_loss:
        # SL: Round conservatively (down for long, up for short)
        rounding = ROUND_DOWN if position_side == "LONG" else ROUND_UP
    else:
        # TP: Round optimistically (up for long, down for short)
        rounding = ROUND_UP if position_side == "LONG" else ROUND_DOWN
    
    quantized = float((trigger_decimal / tick_decimal).quantize(Decimal('1'), rounding=rounding) * tick_decimal)
    
    # Validate trigger side with epsilon buffer
    epsilon = max(float(tick_sz) * 2, mark_price * 0.001)  # 0.1% or 2 ticks
    
    if is_stop_loss:
        if position_side == "LONG":
            # Must be < mark
            if quantized >= mark_price:
                quantized = mark_price - epsilon
                quantized = float((Decimal(str(quantized)) / tick_decimal).quantize(Decimal('1'), rounding=ROUND_DOWN) * tick_decimal)
                print(f"[VALIDATE] Adjusted LONG SL from {trigger_price:.2f} to {quantized:.2f} (mark={mark_price:.2f})")
        else:
            # Must be > mark
            if quantized <= mark_price:
                quantized = mark_price + epsilon
                quantized = float((Decimal(str(quantized)) / tick_decimal).quantize(Decimal('1'), rounding=ROUND_UP) * tick_decimal)
                print(f"[VALIDATE] Adjusted SHORT SL from {trigger_price:.2f} to {quantized:.2f} (mark={mark_price:.2f})")
    else:
        # TP validation (reject if invalid, don't auto-adjust)
        if position_side == "LONG":
            if quantized <= mark_price:
                print(f"[VALIDATE][REJECT] LONG TP {quantized:.2f} <= mark {mark_price:.2f}")
                return None, False
        else:
            if quantized >= mark_price:
                print(f"[VALIDATE][REJECT] SHORT TP {quantized:.2f} >= mark {mark_price:.2f}")
                return None, False
    
    return quantized, True


def _post_execution_assert(hl_client, symbol, action_type):
    """
    Verifica hygiene pós-execução:
    - Position exists → max 2 triggers (1 SL + 1 TP)
    - No position → 0 triggers
    """
    try:
        positions = hl_client.get_positions_by_symbol()
        open_orders = hl_client.get_open_orders()
        
        triggers = _identify_reduce_only_orders(open_orders, symbol)
        
        has_position = symbol in positions and abs(float(positions[symbol].get("size", 0))) > 0
        
        if has_position:
            # Should have exactly 0-2 triggers (1 SL + 1 TP max)
            if len(triggers) > 2:
                print(f"[ASSERT][FAIL] {symbol} has {len(triggers)} triggers (expected <=2) after {action_type}")
                print(f"[ASSERT] Triggers: {[{'oid': t.get('oid'), 'px': t.get('triggerPx')} for t in triggers]}")
                # Emergency cleanup
                print(f"[ASSERT] Emergency cleanup triggered")
                _cleanup_all_triggers(hl_client, symbol)
            else:
                print(f"[ASSERT][OK] {symbol} has {len(triggers)} triggers after {action_type}")
        else:
            # No position → should have 0 triggers
            if triggers:
                print(f"[ASSERT][CLEANUP] {symbol} has {len(triggers)} orphan triggers (no position)")
                _cleanup_all_triggers(hl_client, symbol)
                
    except Exception as e:
        print(f"[ASSERT][ERROR] {e}")


# ============================================================================
# EXISTING CODE
# ============================================================================


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
        action_type = action.get("type", "UNKNOWN")
        symbol = action.get("symbol", "?")
        
        # Check for duplicates using intent-based deduplication
        intent_key = _get_intent_key(action)
        if _is_intent_duplicate(intent_key, action_type, current_time):
            ttl = _get_intent_ttl(action_type)
            last_time = _intent_history.get(intent_key, current_time)
            ttl_remaining = int(ttl - (current_time - last_time))
            print(f"[SAFEGUARD] intent_dedup skip intent={intent_key} ttl_remaining={ttl_remaining}s")
            skipped_count += 1
            continue
        
        # Circuit breaker: Check add limit for PLACE_ORDER
        if action_type == "PLACE_ORDER":
            # Clean old add timestamps (>1 hour)
            if symbol not in _adds_history:
                _adds_history[symbol] = []
            
            cutoff = current_time - 3600
            _adds_history[symbol] = [ts for ts in _adds_history[symbol] if ts > cutoff]
            
            # Check limit
            if len(_adds_history[symbol]) >= MAX_POSITION_ADDS_PER_HOUR:
                print(f"[SAFEGUARD] add_limit_reached symbol={symbol} adds_60m={len(_adds_history[symbol])} max={MAX_POSITION_ADDS_PER_HOUR}")
                failed_count += 1
                continue
        
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
            
            
            # Count based on result: True=success, False=failed, None=skipped
            if action_success is True:
                _intent_history[intent_key] = current_time
                
                # Track adds for circuit breaker
                if action_type == "PLACE_ORDER":
                    if symbol not in _adds_history:
                        _adds_history[symbol] = []
                    _adds_history[symbol].append(current_time)
                
                success_count += 1
            elif action_success is False:
                failed_count += 1
            else:  # None = skipped
                skipped_count += 1
            
        except Exception as e:
            print(f"[EXEC][ERROR] failed to execute {action_type}: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1
    
    # Honest logging
    total = len(actions)
    print(f"[EXEC] done success={success_count} failed={failed_count} skipped={skipped_count} total={total}")
    
    # Clean old entries from intent history
    # Keep entries within max TTL window (TRIGGER_DEDUP_SECONDS is longest)
    cutoff_time = current_time - max(PLACE_ORDER_DEDUP_SECONDS, TRIGGER_DEDUP_SECONDS, ACTION_DEDUP_SECONDS)
    _intent_history.clear()  # Simple approach for now
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
        
        # DEFAULT TARGET LEVERAGE (Majors 50x, Alts 20x)
        majors = ["BTC", "ETH", "SOL"]
        default_lev = 50 if symbol in majors else 20
        target_leverage = int(normalized.get("leverage", default_lev))
        margin_mode = normalized.get("margin_mode", "isolated")
        
        # 1. ALWAYS ENSURE LEVERAGE/MARGIN MODE
        try:
            is_cross = (margin_mode == "cross")
            print(f"[LIVE] Ensuring {target_leverage}x {margin_mode} for {symbol}...")
            hl_client.update_leverage(symbol, target_leverage, is_cross)
            time.sleep(0.5)
        except Exception as e:
            print(f"[LIVE][WARN] Update leverage failed: {e}")
            
        # 2. MARGIN CHECK & DYNAMIC SIZING
        # Get account state
        account_state = hl_client.get_account_state()
        if account_state:
            margin_summary = account_state.get("marginSummary", {})
            account_value = float(margin_summary.get("accountValue", 0))
            total_margin_used = float(margin_summary.get("totalMarginUsed", 0))
            available_margin = max(0.0, account_value - total_margin_used)
            
            price = float(price)
            current_size = normalized["size"]
            required_notional = current_size * price
            
            # Buying Power = Available Margin * Leverage * Buffer (90%)
            buying_power = available_margin * target_leverage * 0.90
            
            print(f"[LIVE] Margin Calc: Avail=${available_margin:.2f} Lev={target_leverage}x Power=${buying_power:.2f} Req=${required_notional:.2f}")

            # ADD-ON GATE: Block small adds if no power
            positions = hl_client.get_positions_by_symbol()
            if symbol in positions and abs(float(positions[symbol].get("size", 0))) > 0:
                 if buying_power < 10.0:
                      print(f"[LIVE][REJECT] Add-on blocked. Available buying power ${buying_power:.2f} < $10 min")
                      return

            if required_notional > buying_power:
                print(f"[LIVE][WARN] Insufficient buying power for size={current_size} (${required_notional:.2f})")
                
                # Dynamic Sizing: Clamp to max possible
                adj_size = buying_power / price
                adj_notional = adj_size * price
                
                # Check Min Notional ($10)
                if adj_notional < 10.0:
                    print(f"[LIVE][REJECT] Account too small for min trade ($10). Max Power=${buying_power:.2f}")
                    return
                
                # Normalize adjusted size
                constraints = hl_client.get_symbol_constraints(symbol)
                sz_decimals = constraints.get("szDecimals", 5) if constraints else 5
                from decimal import Decimal, ROUND_DOWN
                size_decimal = Decimal(str(adj_size))
                size_factor = Decimal(10) ** sz_decimals
                normalized_adj_size = float((size_decimal * size_factor).quantize(Decimal('1'), rounding=ROUND_DOWN) / size_factor)
                
                print(f"[LIVE] Adjusted size from {current_size} to {normalized_adj_size} (${normalized_adj_size*price:.2f})")
                normalized["size"] = normalized_adj_size
                current_size = normalized_adj_size
            
            # Final Check
            required_margin = (current_size * price) / target_leverage
            if available_margin < required_margin:
                 print(f"[LIVE][REJECT] Still insufficient margin after adjust. Avail=${available_margin:.2f} Need=${required_margin:.2f}")
                 return

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
    """
    Check if exchange response indicates success
    CRITICAL: resting = success (trigger order accepted, waiting)
              filled = success (order executed)
              error = failure
    """
    if not resp:
        return False
    
    # Check status field
    if resp.get("status") == "error":
        return False
    
    if resp.get("status") != "ok":
        return False
    
    # Check for statuses in response data
    response_data = resp.get("response", {})
    if isinstance(response_data, dict):
        data = response_data.get("data", {})
        if isinstance(data, dict):
            statuses = data.get("statuses", [])
            if statuses:
                for status in statuses:
                    if isinstance(status, dict):
                        # CRITICAL: resting = SUCCESS (trigger order accepted)
                        if "resting" in status:
                            oid = status["resting"].get("oid", "?")
                            print(f"[EXEC] order resting oid={oid} (SUCCESS)")
                            return True
                        
                        # filled = SUCCESS
                        if "filled" in status:
                            return True
                        
                        # error = FAILURE
                        if "error" in status:
                            return False
    
    # If status is ok and no error found, treat as success
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
    
    # LIVE execution - convert to SET_STOP_LOSS with SAFE TRIGGER
    try:
        positions = hl_client.get_positions_by_symbol()
        
        if symbol not in positions:
            print(f"[LIVE][WARN] MOVE_STOP_TO_BREAKEVEN {symbol} skipped - no position")
            return
        
        position = positions[symbol]
        entry_price = float(position["entry_price"])
        position_size = abs(float(position["size"]))
        position_side = position["side"] # LONG or SHORT
        
        # Get mark price for validation
        mark_price = hl_client.get_last_price(symbol)
        if not mark_price:
            print(f"[LIVE][ERROR] MOVE_STOP_TO_BREAKEVEN {symbol} - failed to get mark price")
            return

        # Constraints for rounding
        constraints = hl_client.get_symbol_constraints(symbol)
        tick_sz = constraints.get("tickSz", 1.0)
        
        # Calculate Safe Trigger with Epsilon
        # Epsilon = 0.05% of mark or 1 tick, whichever is larger
        epsilon = max(float(tick_sz), mark_price * 0.0005)
        
        if position_side == "LONG":
            # For LONG, SL must be < Mark.
            # We want BE = Entry. But if Entry >= Mark, we must lower it.
            # Safe Trigger = min(Entry, Mark - epsilon)
            raw_trigger = min(entry_price, mark_price - epsilon)
        else:
            # For SHORT, SL must be > Mark.
            # Safe Trigger = max(Entry, Mark + epsilon)
            raw_trigger = max(entry_price, mark_price + epsilon)
            
        # Quantize
        from decimal import Decimal, ROUND_DOWN, ROUND_UP
        tick_decimal = Decimal(str(tick_sz))
        # Round down for LONG SL (safer), Up for SHORT SL? 
        # Actually standard quantize is fine, but strictly staying on side matters.
        # Let's use simple quantize.
        trigger_px = float((Decimal(str(raw_trigger)) / tick_decimal).quantize(Decimal('1'), rounding=ROUND_DOWN) * tick_decimal)
        
        print(f"[LIVE] MOVE_STOP_TO_BREAKEVEN {symbol} entry=${entry_price:.2f} mark=${mark_price:.2f} safe_trigger=${trigger_px:.2f}")

        # Construct Action for SET_STOP_LOSS
        sl_action = {
            "type": "SET_STOP_LOSS",
            "symbol": symbol,
            "stop_price": trigger_px
        }
        
        # Delegate to SET_STOP_LOSS handler (which already has dedupe logic!)
        _execute_set_stop_loss(sl_action, is_paper, hl_client)
        
    except Exception as e:
        print(f"[LIVE][ERROR] MOVE_STOP_TO_BREAKEVEN {symbol} failed: {e}")
        import traceback
        traceback.print_exc()



def _execute_set_stop_loss(action: Dict[str, Any], is_paper: bool, hl_client) -> bool:
    """Execute SET_STOP_LOSS action with trigger price quantization and validation"""
    symbol = action.get("symbol", "?")
    stop_price = action.get("stop_price", 0)
    
    if is_paper:
        print(f"[PAPER] would SET_STOP_LOSS {symbol} stop=${stop_price:.2f}")
        return True
    
    # LIVE execution with trigger price validation
    try:
        positions = hl_client.get_positions_by_symbol()
        
        if symbol not in positions:
            print(f"[LIVE][WARN] SET_STOP_LOSS {symbol} skipped - no position")
            return None  # Skipped, not failed
        
        position = positions[symbol]
        
        # CRITICAL FIX: get_positions_by_symbol returns "size" not "szi"
        position_size = position.get("size", 0)
        position_side = position.get("side", "UNKNOWN")
        
        print(f"[DEBUG] {symbol} position: size={position_size} side={position_side}")
        
        if position_size == 0:
            print(f"[LIVE][WARN] SET_STOP_LOSS {symbol} skipped - zero position size")
            return None  # Skipped
        
        # Get mark price and constraints for validation
        mark_price = hl_client.get_last_price(symbol)
        if not mark_price:
            print(f"[LIVE][ERROR] SET_STOP_LOSS {symbol} - failed to get mark price")
            return False
        
        constraints = hl_client.get_symbol_constraints(symbol)
        tick_sz = constraints.get("tickSz", 1.0)
        
        # BRACKET MANAGER: Use validator helper
        trigger_px_quantized, is_valid = _validate_and_adjust_trigger(
            symbol, stop_price, position_side, mark_price, tick_sz, is_stop_loss=True
        )
        
        if not is_valid or trigger_px_quantized is None:
            print(f"[LIVE][REJECT] SET_STOP_LOSS {symbol} - validation failed")
            return False
        
        print(f"[LIVE] SET_STOP_LOSS {symbol} stop=${trigger_px_quantized:.2f} size={position_size} side={position_side}")
        
        # BRACKET MANAGER: Cleanup ALL triggers before creating new one
        cleaned_count = _cleanup_all_triggers(hl_client, symbol)
        print(f"[BRACKET] Cleaned {cleaned_count} triggers before SET_STOP_LOSS")

        # Place trigger order
        resp = hl_client.place_trigger_order(
            symbol=symbol,
            is_buy=(position_side == "SHORT"),
            trigger_price=trigger_px_quantized,
            size=position_size,
            is_stop_loss=True
        )
        
        print(f"[LIVE] resp={_format_resp(resp)}")
        
        success = _parse_response_success(resp)
        
        if not success:
            error_msg = _extract_error_message(resp)
            print(f"[LIVE][REJECT] {symbol} exchange_error={error_msg}")
            return False
        
        # POST-EXECUTION ASSERT
        _post_execution_assert(hl_client, symbol, "SET_STOP_LOSS")
        
        _post_verify(hl_client, symbol, "SET_STOP_LOSS")
        return True
        
    except Exception as e:
        print(f"[LIVE][ERROR] SET_STOP_LOSS {symbol} failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def _execute_set_take_profit(action: Dict[str, Any], is_paper: bool, hl_client) -> bool:
    """Execute SET_TAKE_PROFIT action with trigger price quantization and idempotent check"""
    symbol = action.get("symbol", "?")
    tp_price = action.get("tp_price", 0)
    
    if is_paper:
        print(f"[PAPER] would SET_TAKE_PROFIT {symbol} tp=${tp_price:.2f}")
        return True
    
    # LIVE execution with trigger price validation
    try:
        positions = hl_client.get_positions_by_symbol()
        
        if symbol not in positions:
            print(f"[LIVE][WARN] SET_TAKE_PROFIT {symbol} skipped - no position")
            return False
        
        position = positions[symbol]
        # CRITICAL FIX: get_positions_by_symbol returns "size" not "szi"
        position_size = position.get("size", 0)
        position_side = position.get("side", "UNKNOWN")
        
        print(f"[DEBUG] {symbol} position: size={position_size} side={position_side}")
        
        if position_size == 0:
            print(f"[LIVE][WARN] SET_TAKE_PROFIT {symbol} skipped - zero position size")
            return None  # Skipped
        
        # Get mark price and constraints for validation
        mark_price = hl_client.get_last_price(symbol)
        if not mark_price:
            print(f"[LIVE][ERROR] SET_TAKE_PROFIT {symbol} - failed to get mark price")
            return False
        
        constraints = hl_client.get_symbol_constraints(symbol)
        tick_sz = constraints.get("tickSz", 1.0)
        
        # Quantize trigger price to tick size
        from decimal import Decimal, ROUND_DOWN
        trigger_px_decimal = Decimal(str(tp_price))
        tick_decimal = Decimal(str(tick_sz))
        trigger_px_quantized = float((trigger_px_decimal / tick_decimal).quantize(Decimal('1'), rounding=ROUND_DOWN) * tick_decimal)
        
        # VALIDATE TRIGGER SIDE
        if position_side == "LONG":
            # TP for LONG must be above mark price
            if trigger_px_quantized <= mark_price:
                print(f"[LIVE][REJECT] SET_TAKE_PROFIT {symbol} reason=invalid_trigger_side LONG_TP must be > mark (mark={mark_price} trigger={trigger_px_quantized})")
                return False
        else:  # SHORT
            # TP for SHORT must be below mark price
            if trigger_px_quantized >= mark_price:
                print(f"[LIVE][REJECT] SET_TAKE_PROFIT {symbol} reason=invalid_trigger_side SHORT_TP must be < mark (mark={mark_price} trigger={trigger_px_quantized})")
                return False
        
        print(f"[LIVE] SET_TAKE_PROFIT {symbol} tp=${trigger_px_quantized:.2f} size={position_size} side={position_side}")
        
        # Get open orders for checks
        open_orders = hl_client.get_open_orders()
        open_orders_for_symbol = [o for o in open_orders if o.get("coin") == symbol]
        
        # PROTECTIVE ORDER MANAGER: Find existing TPs
        existing_tp_orders = []
        for o in open_orders_for_symbol:
            is_reduce = o.get("reduceOnly", False)
            trig_px = float(o.get("triggerPx", 0) or 0)
            
            # Heuristic v2: LONG TP > Mark, SHORT TP < Mark
            if is_reduce and trig_px > 0:
                if position_side == "LONG" and trig_px > mark_price:
                    existing_tp_orders.append(o)
                elif position_side == "SHORT" and trig_px < mark_price:
                    existing_tp_orders.append(o)

        # IDEMPOTENT CHECK
        for tp_order in existing_tp_orders:
            order_trigger_px = float(tp_order.get("triggerPx", 0))
            price_diff_pct = abs(order_trigger_px - trigger_px_quantized) / trigger_px_quantized * 100
            if price_diff_pct < 0.2:
                 print(f"[IDEMP] skip SET_TAKE_PROFIT {symbol} - equivalent TP exists oid={tp_order['oid']} px={order_trigger_px}")
                 return True

        # REPLACEMENT LOGIC
        if existing_tp_orders:
            print(f"[SMART] Canceling {len(existing_tp_orders)} old TPs for {symbol} to replace with new ${trigger_px_quantized:.2f}")
            for tp_to_cancel in existing_tp_orders:
                try:
                    hl_client.cancel_order(symbol, tp_to_cancel["oid"])
                except Exception as e:
                    print(f"[SMART][WARN] Failed to cancel old TP {tp_to_cancel['oid']}: {e}")
            import time; time.sleep(0.5)

        # CHECK LIMITS AFTER CANCEL
        remaining_count = len(open_orders_for_symbol) - len(existing_tp_orders)
        
        if remaining_count >= MAX_OPEN_ORDERS_PER_SYMBOL:
             print(f"[CIRCUIT] skip SET_TAKE_PROFIT {symbol} - still full {remaining_count} >= {MAX_OPEN_ORDERS_PER_SYMBOL} (removed {len(existing_tp_orders)} TPs)")
             return None
        
        # IDEMPOTENT CHECK: if similar trigger exists, skip
        for order in open_orders:
            if order.get("coin") == symbol:
                order_trigger_px = float(order.get("triggerPx", 0) or 0)
                is_reduce_only = order.get("reduceOnly", False)
                
                # If reduce_only trigger within 0.5% of our target price, skip
                if is_reduce_only and order_trigger_px > 0:
                    price_diff_pct = abs(order_trigger_px - trigger_px_quantized) / trigger_px_quantized * 100
                    if price_diff_pct < 0.5:
                        print(f"[IDEMP] skip SET_TAKE_PROFIT {symbol} - similar trigger exists oid={order.get('oid', '?')} px={order_trigger_px}")
                        return True  # Return success to prevent retry
        
        # Place trigger order
        resp = hl_client.place_trigger_order(
            symbol=symbol,
            is_buy=(position_side == "SHORT"),  # Buy to close short, sell to close long
            trigger_price=trigger_px_quantized,
            size=position_size,
            is_stop_loss=False  # This is take profit
        )
        
        print(f"[LIVE] resp={_format_resp(resp)}")
        
        success = _parse_response_success(resp)
        
        if not success:
            error_msg = _extract_error_message(resp)
            print(f"[LIVE][REJECT] {symbol} exchange_error={error_msg}")
            return False
        
        _post_verify(hl_client, symbol, "SET_TAKE_PROFIT")
        return True
        
    except Exception as e:
        print(f"[LIVE][ERROR] SET_TAKE_PROFIT {symbol} failed: {e}")
        import traceback
        traceback.print_exc()
        traceback.print_exc()


def _execute_cancel_all(action: Dict[str, Any], is_paper: bool, hl_client) -> bool:
    """Execute CANCEL_ALL_ORDERS action (Safe)"""
    symbol = action.get("symbol")
    
    if is_paper:
        print(f"[PAPER] would CANCEL_ALL {symbol if symbol else 'all symbols'}")
        return True
    
    # LIVE execution
    if not symbol:
        print("[LIVE][WARN] CANCEL_ALL requires symbol")
        return False
        
    # Check if there are orders to cancel first
    try:
        open_orders = hl_client.get_open_orders()
        open_orders_for_symbol = [o for o in open_orders if o.get("coin") == symbol]
        
        if not open_orders_for_symbol:
            print(f"[LIVE] CANCEL_ALL_ORDERS {symbol} skipped (0 open orders)")
            return True
            
    except Exception as e:
        print(f"[LIVE][WARN] failed to check open orders for cancel: {e}")
    
    print(f"[LIVE] canceling all orders {symbol}")
    try:
        resp = hl_client.cancel_all_orders(symbol)
        print(f"[LIVE] resp={_format_resp(resp)}")
        return True
    except Exception as e:
        print(f"[LIVE][ERROR] CANCEL_ALL_ORDERS {symbol} failed: {e}")
        return False


def _execute_close_partial(action, is_paper, hl_client):
    """Execute CLOSE_PARTIAL action with min notional validation"""
    symbol = action.get("symbol", "?")
    pct = action.get("pct")
    
    if not pct:
        pct = 0.5  # Default to 50%
        print(f"[EXEC][WARN] CLOSE_PARTIAL {symbol} missing pct, defaulting to 50%")
    
    if is_paper:
        print(f"[PAPER] CLOSE_PARTIAL {symbol} pct={pct}")
        return True
    
    # LIVE execution with min notional validation
    try:
        positions = hl_client.get_positions_by_symbol()
        
        if symbol not in positions:
            print(f"[LIVE][WARN] CLOSE_PARTIAL {symbol} skipped - no position")
            return False
        
        position = positions[symbol]
        # CRITICAL FIX: use "size" not "szi"
        position_size = abs(float(position.get("size", 0)))
        
        if position_size == 0:
            print(f"[LIVE][WARN] CLOSE_PARTIAL {symbol} skipped - zero size")
            return False
        
        # Calculate close size
        close_size = position_size * (pct / 100.0)
        
        # Get mark price for notional calculation
        mark_price = hl_client.get_last_price(symbol)
        if not mark_price:
            print(f"[LIVE][ERROR] CLOSE_PARTIAL {symbol} - failed to get mark price")
            return False
        
        # Calculate notional value
        close_notional = close_size * mark_price
        
        # MIN NOTIONAL VALIDATION
        if close_notional < MIN_NOTIONAL_USD:
            print(f"[LIVE][REJECT] CLOSE_PARTIAL {symbol} reason=min_notional close_notional=${close_notional:.2f} min=${MIN_NOTIONAL_USD}")
            
            # Check if full position meets min notional
            full_notional = position_size * mark_price
            if full_notional >= MIN_NOTIONAL_USD:
                print(f"[LIVE][WARN] CLOSE_PARTIAL {symbol} adjusted to CLOSE_FULL (full_notional=${full_notional:.2f})")
                # Close full position instead
                close_size = position_size
                close_notional = full_notional
            else:
                print(f"[LIVE][REJECT] CLOSE_PARTIAL {symbol} skipped - even full position below min notional")
                return False
        
        # Get constraints for size normalization
        constraints = hl_client.get_symbol_constraints(symbol)
        sz_decimals = constraints.get("szDecimals", 5)
        
        # Normalize size
        from decimal import Decimal, ROUND_DOWN
        size_decimal = Decimal(str(close_size))
        size_factor = Decimal(10) ** sz_decimals
        close_size_normalized = float((size_decimal * size_factor).quantize(Decimal('1'), rounding=ROUND_DOWN) / size_factor)
        
        print(f"[LIVE] CLOSE_PARTIAL {symbol} pct={pct} size={close_size_normalized} notional=${close_notional:.2f}")
        
        # Execute close
        resp = hl_client.close_position(symbol, close_size_normalized)
        print(f"[LIVE] resp={_format_resp(resp)}")
        
        success = _parse_response_success(resp)
        
        if not success:
            error_msg = _extract_error_message(resp)
            print(f"[LIVE][REJECT] {symbol} exchange_error={error_msg}")
            return False
        
        _post_verify(hl_client, symbol, "CLOSE_PARTIAL")
        return True
        
    except Exception as e:
        print(f"[LIVE][ERROR] CLOSE_PARTIAL {symbol} failed: {e}")
        import traceback
        traceback.print_exc()
        return False


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
