"""
Fibonacci Analysis Module
Calculates retracement and extension levels from swing points
AI interprets significance - NO hardcoded trading rules
"""

from typing import Dict, Any, List, Optional


def find_swing_points(candles: List[Dict], lookback: int = 50) -> Dict[str, Optional[float]]:
    """
    Find the most significant swing high and swing low in recent candles.
    
    Returns: {swing_high, swing_low, swing_high_idx, swing_low_idx}
    """
    if not candles or len(candles) < 5:
        return {"swing_high": None, "swing_low": None, "swing_high_idx": None, "swing_low_idx": None}
    
    recent = candles[-lookback:] if len(candles) >= lookback else candles
    
    # Find swing highs (local maxima)
    swing_highs = []
    swing_lows = []
    
    for i in range(2, len(recent) - 2):
        high = float(recent[i].get('h', recent[i].get('high', 0)))
        low = float(recent[i].get('l', recent[i].get('low', 0)))
        
        # Check if it's a swing high (higher than 2 candles on each side)
        prev_highs = [float(recent[j].get('h', recent[j].get('high', 0))) for j in range(i-2, i)]
        next_highs = [float(recent[j].get('h', recent[j].get('high', 0))) for j in range(i+1, i+3)]
        
        if high > max(prev_highs) and high > max(next_highs):
            swing_highs.append((i, high))
        
        # Check if it's a swing low
        prev_lows = [float(recent[j].get('l', recent[j].get('low', 0))) for j in range(i-2, i)]
        next_lows = [float(recent[j].get('l', recent[j].get('low', 0))) for j in range(i+1, i+3)]
        
        if low < min(prev_lows) and low < min(next_lows):
            swing_lows.append((i, low))
    
    # Get the most significant (highest high, lowest low)
    swing_high = max(swing_highs, key=lambda x: x[1]) if swing_highs else None
    swing_low = min(swing_lows, key=lambda x: x[1]) if swing_lows else None
    
    return {
        "swing_high": swing_high[1] if swing_high else None,
        "swing_low": swing_low[1] if swing_low else None,
        "swing_high_idx": swing_high[0] if swing_high else None,
        "swing_low_idx": swing_low[0] if swing_low else None
    }


def calculate_fibonacci_levels(candles: List[Dict], lookback: int = 50) -> Dict[str, Any]:
    """
    Calculate Fibonacci retracement and extension levels.
    
    Returns:
        dict with:
        - swing_high, swing_low: anchor points
        - retracements: dict of level -> price
        - extensions: dict of level -> price  
        - current_price: latest close
        - price_position: where price is relative to fib levels
        - trend_context: "UPTREND" if swing_low before swing_high, else "DOWNTREND"
    """
    if not candles or len(candles) < 10:
        return {
            "swing_high": None,
            "swing_low": None,
            "retracements": {},
            "extensions": {},
            "current_price": None,
            "price_position": None,
            "trend_context": "UNKNOWN"
        }
    
    # Find swing points
    swings = find_swing_points(candles, lookback)
    swing_high = swings["swing_high"]
    swing_low = swings["swing_low"]
    swing_high_idx = swings["swing_high_idx"]
    swing_low_idx = swings["swing_low_idx"]
    
    if swing_high is None or swing_low is None:
        return {
            "swing_high": None,
            "swing_low": None,
            "retracements": {},
            "extensions": {},
            "current_price": None,
            "price_position": None,
            "trend_context": "UNKNOWN"
        }
    
    # Determine trend context
    if swing_low_idx is not None and swing_high_idx is not None:
        trend_context = "UPTREND" if swing_low_idx < swing_high_idx else "DOWNTREND"
    else:
        trend_context = "UNKNOWN"
    
    # Calculate range
    price_range = swing_high - swing_low
    
    # Fibonacci ratios
    fib_retracement_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]
    fib_extension_ratios = [1.0, 1.272, 1.618, 2.0, 2.618]
    
    retracements = {}
    extensions = {}
    
    if trend_context == "UPTREND":
        # In uptrend, retracements are below swing high
        for ratio in fib_retracement_ratios:
            retracements[ratio] = round(swing_high - (price_range * ratio), 2)
        # Extensions are above swing high
        for ratio in fib_extension_ratios:
            extensions[ratio] = round(swing_low + (price_range * ratio), 2)
    else:  # DOWNTREND
        # In downtrend, retracements are above swing low
        for ratio in fib_retracement_ratios:
            retracements[ratio] = round(swing_low + (price_range * ratio), 2)
        # Extensions are below swing low
        for ratio in fib_extension_ratios:
            extensions[ratio] = round(swing_high - (price_range * ratio), 2)
    
    # Current price
    current_price = float(candles[-1].get('c', candles[-1].get('close', 0)))
    
    # Determine price position relative to fibs
    price_position = None
    all_levels = sorted(list(retracements.values()) + [swing_high, swing_low])
    
    for i in range(len(all_levels) - 1):
        if all_levels[i] <= current_price <= all_levels[i + 1]:
            price_position = f"between ${all_levels[i]:.0f} and ${all_levels[i+1]:.0f}"
            break
    
    if price_position is None:
        if current_price > max(all_levels):
            price_position = f"above all levels (>${max(all_levels):.0f})"
        else:
            price_position = f"below all levels (<${min(all_levels):.0f})"
    
    return {
        "swing_high": round(swing_high, 2),
        "swing_low": round(swing_low, 2),
        "retracements": retracements,
        "extensions": extensions,
        "current_price": round(current_price, 2),
        "price_position": price_position,
        "trend_context": trend_context
    }


def format_fibonacci_for_prompt(symbol: str, fib_data: Dict) -> str:
    """Format Fibonacci data for LLM prompt"""
    if not fib_data or fib_data.get("swing_high") is None:
        return f"{symbol}: No Fibonacci data available"
    
    lines = [f"{symbol} FIB ({fib_data['trend_context']}):"]
    lines.append(f"  Range: ${fib_data['swing_low']:.0f} - ${fib_data['swing_high']:.0f}")
    
    # Key retracement levels
    ret = fib_data.get("retracements", {})
    if ret:
        ret_str = " | ".join([f"{k}: ${v:.0f}" for k, v in sorted(ret.items())])
        lines.append(f"  Ret: {ret_str}")
    
    # Key extension levels
    ext = fib_data.get("extensions", {})
    if ext:
        ext_str = " | ".join([f"{k}: ${v:.0f}" for k, v in list(sorted(ext.items()))[:3]])
        lines.append(f"  Ext: {ext_str}")
    
    lines.append(f"  Price: ${fib_data['current_price']:.0f} ({fib_data['price_position']})")
    
    return "\n".join(lines)
