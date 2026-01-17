"""
Pivot Points Module
Calculates classic pivot points (daily, weekly)
AI interprets significance - NO hardcoded trading rules
"""

from typing import Dict, Any, List


def calculate_pivot_points(candles: List[Dict], period: str = "daily") -> Dict[str, Any]:
    """
    Calculate classic pivot points from previous period's OHLC.
    
    Formula:
    - Pivot (P) = (H + L + C) / 3
    - R1 = (2 * P) - L
    - R2 = P + (H - L)
    - R3 = H + 2 * (P - L)
    - S1 = (2 * P) - H
    - S2 = P - (H - L)
    - S3 = L - 2 * (H - P)
    
    Args:
        candles: Daily or Weekly candles
        period: "daily" or "weekly"
    
    Returns:
        Dict with pivot levels
    """
    if not candles or len(candles) < 2:
        return {}
    
    # Use previous complete candle for pivot calculation
    prev_candle = candles[-2]
    current_candle = candles[-1]
    
    try:
        high = float(prev_candle.get('h', prev_candle.get('high', 0)))
        low = float(prev_candle.get('l', prev_candle.get('low', 0)))
        close = float(prev_candle.get('c', prev_candle.get('close', 0)))
        current_price = float(current_candle.get('c', current_candle.get('close', 0)))
        
        if high == 0 or low == 0 or close == 0:
            return {}
        
        # Calculate pivot point
        pivot = (high + low + close) / 3
        
        # Resistance levels
        r1 = (2 * pivot) - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        
        # Support levels
        s1 = (2 * pivot) - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        # Determine current price position
        if current_price > r2:
            position = "ABOVE_R2"
        elif current_price > r1:
            position = "ABOVE_R1"
        elif current_price > pivot:
            position = "ABOVE_PIVOT"
        elif current_price > s1:
            position = "BELOW_PIVOT"
        elif current_price > s2:
            position = "BELOW_S1"
        else:
            position = "BELOW_S2"
        
        return {
            "period": period,
            "pivot": round(pivot, 2),
            "r1": round(r1, 2),
            "r2": round(r2, 2),
            "r3": round(r3, 2),
            "s1": round(s1, 2),
            "s2": round(s2, 2),
            "s3": round(s3, 2),
            "current_price": round(current_price, 2),
            "position": position,
            "prev_high": round(high, 2),
            "prev_low": round(low, 2)
        }
    except Exception as e:
        return {}


def format_pivots_for_prompt(symbol: str, daily_pivots: Dict, weekly_pivots: Dict) -> str:
    """Format pivot points for LLM prompt"""
    lines = []
    
    if daily_pivots:
        d = daily_pivots
        lines.append(f"{symbol} DAILY PIVOTS ({d.get('position', '?')}): P=${d.get('pivot', 0):.0f} | S1=${d.get('s1', 0):.0f} S2=${d.get('s2', 0):.0f} | R1=${d.get('r1', 0):.0f} R2=${d.get('r2', 0):.0f}")
    
    if weekly_pivots:
        w = weekly_pivots
        lines.append(f"{symbol} WEEKLY PIVOTS: P=${w.get('pivot', 0):.0f} | S1=${w.get('s1', 0):.0f} | R1=${w.get('r1', 0):.0f}")
    
    return "\n".join(lines) if lines else f"{symbol}: No pivot data"
