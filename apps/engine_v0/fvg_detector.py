"""
Fair Value Gap (FVG) Detection Module
Detects price imbalances where candles didn't overlap
AI interprets significance - NO hardcoded trading rules
"""

from typing import Dict, Any, List


def find_fair_value_gaps(candles: List[Dict], lookback: int = 30, min_gap_pct: float = 0.1) -> List[Dict]:
    """
    Find Fair Value Gaps (imbalances) in price action.
    
    An FVG occurs when:
    - Bullish FVG: Candle 3's low > Candle 1's high (gap up)
    - Bearish FVG: Candle 3's high < Candle 1's low (gap down)
    
    Args:
        candles: List of OHLCV candles
        lookback: How many candles to analyze
        min_gap_pct: Minimum gap size as % of price to be significant
    
    Returns:
        List of FVG dicts with type, zone, size, filled status, age
    """
    if not candles or len(candles) < 5:
        return []
    
    recent = candles[-lookback:] if len(candles) >= lookback else candles
    current_price = float(recent[-1].get('c', recent[-1].get('close', 0)))
    fvgs = []
    
    for i in range(len(recent) - 2):
        candle_1 = recent[i]
        candle_2 = recent[i + 1]  # The impulse candle
        candle_3 = recent[i + 2]
        
        try:
            c1_high = float(candle_1.get('h', candle_1.get('high', 0)))
            c1_low = float(candle_1.get('l', candle_1.get('low', 0)))
            c2_high = float(candle_2.get('h', candle_2.get('high', 0)))
            c2_low = float(candle_2.get('l', candle_2.get('low', 0)))
            c3_high = float(candle_3.get('h', candle_3.get('high', 0)))
            c3_low = float(candle_3.get('l', candle_3.get('low', 0)))
        except (ValueError, TypeError):
            continue
        
        age = len(recent) - i - 2  # How many candles ago
        
        # Bullish FVG: Gap up - candle 3's low is above candle 1's high
        if c3_low > c1_high:
            gap_top = c3_low
            gap_bottom = c1_high
            gap_size = gap_top - gap_bottom
            gap_pct = (gap_size / current_price) * 100
            
            if gap_pct >= min_gap_pct:
                # Check if filled (price came back to fill the gap)
                filled = False
                for j in range(i + 3, len(recent)):
                    check_low = float(recent[j].get('l', recent[j].get('low', 0)))
                    if check_low <= gap_bottom:
                        filled = True
                        break
                
                fvgs.append({
                    "type": "BULLISH",
                    "gap_top": round(gap_top, 2),
                    "gap_bottom": round(gap_bottom, 2),
                    "gap_size_pct": round(gap_pct, 3),
                    "filled": filled,
                    "age_candles": age,
                    "midpoint": round((gap_top + gap_bottom) / 2, 2)
                })
        
        # Bearish FVG: Gap down - candle 3's high is below candle 1's low
        elif c3_high < c1_low:
            gap_top = c1_low
            gap_bottom = c3_high
            gap_size = gap_top - gap_bottom
            gap_pct = (gap_size / current_price) * 100
            
            if gap_pct >= min_gap_pct:
                # Check if filled
                filled = False
                for j in range(i + 3, len(recent)):
                    check_high = float(recent[j].get('h', recent[j].get('high', 0)))
                    if check_high >= gap_top:
                        filled = True
                        break
                
                fvgs.append({
                    "type": "BEARISH",
                    "gap_top": round(gap_top, 2),
                    "gap_bottom": round(gap_bottom, 2),
                    "gap_size_pct": round(gap_pct, 3),
                    "filled": filled,
                    "age_candles": age,
                    "midpoint": round((gap_top + gap_bottom) / 2, 2)
                })
    
    # Sort by size (most significant first), return top 5
    fvgs.sort(key=lambda x: x["gap_size_pct"], reverse=True)
    return fvgs[:5]


def analyze_fvg_zones(candles: List[Dict], lookback: int = 50) -> Dict[str, Any]:
    """
    Analyze FVG zones for a symbol.
    
    Returns:
        dict with:
        - unfilled_bullish: list of unfilled bullish FVGs (potential support)
        - unfilled_bearish: list of unfilled bearish FVGs (potential resistance)
        - nearest_bullish: closest unfilled bullish FVG to current price
        - nearest_bearish: closest unfilled bearish FVG to current price
        - current_price: for reference
    """
    fvgs = find_fair_value_gaps(candles, lookback)
    
    if not fvgs:
        return {
            "unfilled_bullish": [],
            "unfilled_bearish": [],
            "nearest_bullish": None,
            "nearest_bearish": None,
            "current_price": None,
            "total_fvgs": 0
        }
    
    current_price = float(candles[-1].get('c', candles[-1].get('close', 0)))
    
    unfilled_bullish = [f for f in fvgs if f["type"] == "BULLISH" and not f["filled"]]
    unfilled_bearish = [f for f in fvgs if f["type"] == "BEARISH" and not f["filled"]]
    
    # Find nearest FVGs
    nearest_bullish = None
    nearest_bearish = None
    
    # Bullish FVGs below price (potential support)
    bull_below = [f for f in unfilled_bullish if f["gap_top"] < current_price]
    if bull_below:
        nearest_bullish = max(bull_below, key=lambda x: x["gap_top"])
    
    # Bearish FVGs above price (potential resistance)
    bear_above = [f for f in unfilled_bearish if f["gap_bottom"] > current_price]
    if bear_above:
        nearest_bearish = min(bear_above, key=lambda x: x["gap_bottom"])
    
    return {
        "unfilled_bullish": unfilled_bullish,
        "unfilled_bearish": unfilled_bearish,
        "nearest_bullish": nearest_bullish,
        "nearest_bearish": nearest_bearish,
        "current_price": round(current_price, 2),
        "total_fvgs": len(fvgs)
    }


def format_fvg_for_prompt(symbol: str, fvg_data: Dict) -> str:
    """Format FVG data for LLM prompt"""
    if not fvg_data or fvg_data.get("total_fvgs", 0) == 0:
        return f"{symbol}: No FVGs detected"
    
    lines = [f"{symbol} FVG:"]
    
    # Nearest bullish (support)
    nb = fvg_data.get("nearest_bullish")
    if nb:
        lines.append(f"  BULL (support): ${nb['gap_bottom']:.0f}-${nb['gap_top']:.0f} ({nb['gap_size_pct']:.2f}%)")
    
    # Nearest bearish (resistance)
    nbear = fvg_data.get("nearest_bearish")
    if nbear:
        lines.append(f"  BEAR (resist): ${nbear['gap_bottom']:.0f}-${nbear['gap_top']:.0f} ({nbear['gap_size_pct']:.2f}%)")
    
    # Summary
    total_bull = len(fvg_data.get("unfilled_bullish", []))
    total_bear = len(fvg_data.get("unfilled_bearish", []))
    lines.append(f"  Unfilled: {total_bull} bullish, {total_bear} bearish")
    
    return "\n".join(lines) if len(lines) > 1 else f"{symbol}: No significant FVGs"
