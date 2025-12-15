"""
Order Normalizer for Engine V0
Ensures orders comply with Hyperliquid constraints
"""
import json
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal, ROUND_DOWN

from config import MIN_NOTIONAL_USD, AUTO_CAP_LEVERAGE


def normalize_place_order(
    action: Dict[str, Any],
    price: float,
    constraints: Dict[str, Any],
    min_notional_usd: float = MIN_NOTIONAL_USD,
    auto_cap_leverage: bool = AUTO_CAP_LEVERAGE
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Normalize PLACE_ORDER action to comply with exchange constraints
    
    Args:
        action: Original action dict
        price: Current market price
        constraints: Symbol constraints {szDecimals, maxLeverage, onlyIsolated}
        min_notional_usd: Minimum notional value
        auto_cap_leverage: Whether to auto-cap leverage
    
    Returns:
        (normalized_action, reject_reason)
        - If normalized_action is None, order was rejected (see reject_reason)
        - If normalized_action is dict, order is valid and normalized
    """
    symbol = action.get("symbol", "?")
    side = action.get("side", "BUY")
    size = action.get("size")
    notional_usd = action.get("notional_usd")
    leverage = action.get("leverage")
    margin_mode = action.get("margin_mode")
    
    sz_decimals = constraints.get("szDecimals", 3)
    max_leverage = constraints.get("maxLeverage", 50)
    only_isolated = constraints.get("onlyIsolated", False)
    
    # Calculate size if notional_usd is given
    if notional_usd is not None and size is None:
        if price <= 0:
            return None, f"invalid_price price={price}"
        size = notional_usd / price
    
    if size is None or size <= 0:
        return None, "missing_or_invalid_size"
    
    # Calculate notional
    notional = size * price
    
    # Check min notional
    if notional < min_notional_usd:
        # Adjust size to meet min notional
        size = min_notional_usd / price
        notional = size * price
        print(f"[NORM] {symbol} size adjusted to meet min_notional=${min_notional_usd:.2f} new_size={size:.6f}")
    
    # Round size to szDecimals
    size_decimal = Decimal(str(size))
    size_rounded = float(size_decimal.quantize(
        Decimal(10) ** -sz_decimals,
        rounding=ROUND_DOWN
    ))
    
    if size_rounded != size:
        print(f"[NORM] {symbol} size rounded from {size:.6f} to {size_rounded:.6f} (szDecimals={sz_decimals})")
        size = size_rounded
    
    # Re-check notional after rounding
    notional = size * price
    if notional < min_notional_usd:
        return None, f"size_too_small_after_rounding notional=${notional:.2f} min=${min_notional_usd:.2f}"
    
    # Handle leverage
    if leverage is not None:
        if leverage > max_leverage:
            if auto_cap_leverage:
                print(f"[NORM] {symbol} leverage capped req={leverage} applied={max_leverage}")
                leverage = max_leverage
            else:
                return None, f"leverage_above_max req={leverage} max={max_leverage}"
    
    # Handle margin mode
    if only_isolated and margin_mode != "isolated":
        print(f"[NORM] {symbol} forcing isolated margin (onlyIsolated=true)")
        margin_mode = "isolated"
    
    # Build normalized action
    normalized = {
        "type": "PLACE_ORDER",
        "symbol": symbol,
        "side": side,
        "size": size,
        "orderType": action.get("orderType", "MARKET"),
        "reduce_only": action.get("reduce_only", False)
    }
    
    if leverage is not None:
        normalized["leverage"] = leverage
    
    if margin_mode is not None:
        normalized["margin_mode"] = margin_mode
    
    if action.get("limit_price") is not None:
        normalized["limit_price"] = action.get("limit_price")
    
    return normalized, None


def format_action_compact(action: Dict[str, Any]) -> str:
    """Format action as compact JSON for logging"""
    return json.dumps(action, separators=(',', ':'))


def format_response_compact(resp: Any) -> str:
    """Format response as compact JSON for logging"""
    if isinstance(resp, dict):
        return json.dumps(resp, separators=(',', ':'))
    return str(resp)
