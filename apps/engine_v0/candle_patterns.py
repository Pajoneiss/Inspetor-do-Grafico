"""
Candle Patterns Module
Detects common candlestick patterns
AI interprets significance - NO hardcoded trading rules
"""

from typing import Dict, Any, List, Optional


def detect_candle_patterns(candles: List[Dict], lookback: int = 10) -> Dict[str, Any]:
    """
    Detect candlestick patterns in recent candles.
    
    Patterns detected:
    - Engulfing (bullish/bearish)
    - Pin Bar / Hammer / Shooting Star
    - Doji
    - Inside Bar
    
    Returns:
        Dict with detected patterns and their locations
    """
    if not candles or len(candles) < 3:
        return {"patterns": [], "summary": "insufficient data"}
    
    recent = candles[-lookback:] if len(candles) >= lookback else candles
    patterns = []
    
    for i in range(1, len(recent)):
        try:
            current = recent[i]
            prev = recent[i-1]
            
            c_open = float(current.get('o', current.get('open', 0)))
            c_close = float(current.get('c', current.get('close', 0)))
            c_high = float(current.get('h', current.get('high', 0)))
            c_low = float(current.get('l', current.get('low', 0)))
            
            p_open = float(prev.get('o', prev.get('open', 0)))
            p_close = float(prev.get('c', prev.get('close', 0)))
            p_high = float(prev.get('h', prev.get('high', 0)))
            p_low = float(prev.get('l', prev.get('low', 0)))
            
            c_body = abs(c_close - c_open)
            c_range = c_high - c_low
            p_body = abs(p_close - p_open)
            
            # Candle direction
            c_bullish = c_close > c_open
            c_bearish = c_close < c_open
            p_bullish = p_close > p_open
            p_bearish = p_close < p_open
            
            age = len(recent) - i - 1  # How many candles ago
            
            # === ENGULFING ===
            # Bullish Engulfing: prev red, current green engulfs prev body
            if p_bearish and c_bullish and c_body > p_body * 1.1:
                if c_close > p_open and c_open < p_close:
                    patterns.append({
                        "type": "BULLISH_ENGULFING",
                        "age": age,
                        "price": c_close,
                        "strength": c_body / p_body if p_body > 0 else 1
                    })
            
            # Bearish Engulfing: prev green, current red engulfs prev body
            if p_bullish and c_bearish and c_body > p_body * 1.1:
                if c_open > p_close and c_close < p_open:
                    patterns.append({
                        "type": "BEARISH_ENGULFING",
                        "age": age,
                        "price": c_close,
                        "strength": c_body / p_body if p_body > 0 else 1
                    })
            
            # === PIN BAR / HAMMER / SHOOTING STAR ===
            if c_range > 0:
                upper_wick = c_high - max(c_open, c_close)
                lower_wick = min(c_open, c_close) - c_low
                
                # Hammer (bullish): Long lower wick, small body at top
                if lower_wick > c_body * 2 and upper_wick < c_body * 0.5:
                    patterns.append({
                        "type": "HAMMER",
                        "age": age,
                        "price": c_close,
                        "wick_ratio": lower_wick / c_body if c_body > 0 else 0
                    })
                
                # Shooting Star (bearish): Long upper wick, small body at bottom
                if upper_wick > c_body * 2 and lower_wick < c_body * 0.5:
                    patterns.append({
                        "type": "SHOOTING_STAR",
                        "age": age,
                        "price": c_close,
                        "wick_ratio": upper_wick / c_body if c_body > 0 else 0
                    })
            
            # === DOJI ===
            if c_range > 0 and c_body / c_range < 0.1:  # Body is less than 10% of range
                patterns.append({
                    "type": "DOJI",
                    "age": age,
                    "price": c_close
                })
            
            # === INSIDE BAR ===
            if c_high < p_high and c_low > p_low:
                patterns.append({
                    "type": "INSIDE_BAR",
                    "age": age,
                    "price": c_close,
                    "compression": c_range / (p_range if (p_range := p_high - p_low) > 0 else 1)
                })
                
            # === MORNING STAR (3 candles) ===
            # Red, Small Body (Gap Down ideally), Green (Gap Up ideally, closes > midpoint of first)
            # Simplified: Red, Small, Green taking out explicit gaps for crypto reliability
            if i >= 2:
                p2 = recent[i-2] # 2 candles ago
                p2_open = float(p2.get('o', p2.get('open', 0)))
                p2_close = float(p2.get('c', p2.get('close', 0)))
                p2_body = abs(p2_close - p2_open)
                p2_bearish = p2_close < p2_open
                
                # Check structure: Bearish -> Small -> Bullish
                if p2_bearish and p2_body > 0 and c_bullish:
                    # Middle candle (prev) should be small
                    if p_body < p2_body * 0.5 and p_body < c_body * 0.5:
                         # 3rd candle closes above midpoint of 1st candle
                         midpoint = (p2_open + p2_close) / 2
                         if c_close > midpoint:
                             patterns.append({
                                "type": "MORNING_STAR",
                                "age": age,
                                "price": c_close,
                                "strength": "HIGH"
                            })

            # === EVENING STAR (3 candles) ===
            # Green, Small Body, Red (closes < midpoint of first)
            if i >= 2:
                p2 = recent[i-2]
                p2_open = float(p2.get('o', p2.get('open', 0)))
                p2_close = float(p2.get('c', p2.get('close', 0)))
                p2_body = abs(p2_close - p2_open)
                p2_bullish = p2_close > p2_open
                
                if p2_bullish and p2_body > 0 and c_bearish:
                    if p_body < p2_body * 0.5 and p_body < c_body * 0.5:
                         midpoint = (p2_open + p2_close) / 2
                         if c_close < midpoint:
                             patterns.append({
                                "type": "EVENING_STAR",
                                "age": age,
                                "price": c_close,
                                "strength": "HIGH"
                            })

            # === THREE WHITE SOLDIERS ===
            # 3 consecutive green candles, each closing higher
            if i >= 2:
                p2 = recent[i-2]
                if (p2['close'] > p2['open'] and 
                    prev['close'] > prev['open'] and 
                    current['close'] > current['open']):
                    if (current['close'] > prev['close'] > p2['close']):
                         # Check bodies are decent size (not dojis)
                         if c_range > 0 and c_body/c_range > 0.5:
                             patterns.append({
                                "type": "3_WHITE_SOLDIERS",
                                "age": age,
                                "price": c_close
                            })

            # === THREE BLACK CROWS ===
            # 3 consecutive red candles, each closing lower
            if i >= 2:
                p2 = recent[i-2]
                if (p2['close'] < p2['open'] and 
                    prev['close'] < prev['open'] and 
                    current['close'] < current['open']):
                    if (current['close'] < prev['close'] < p2['close']):
                         if c_range > 0 and c_body/c_range > 0.5:
                             patterns.append({
                                "type": "3_BLACK_CROWS",
                                "age": age,
                                "price": c_close
                            })
                            
        except Exception:
            continue
    
    # Sort by recency (most recent first)
    patterns.sort(key=lambda x: x.get("age", 999))
    
    # Summary
    bullish_count = sum(1 for p in patterns if p["type"] in ["BULLISH_ENGULFING", "HAMMER"])
    bearish_count = sum(1 for p in patterns if p["type"] in ["BEARISH_ENGULFING", "SHOOTING_STAR"])
    
    bias = "BULLISH" if bullish_count > bearish_count else "BEARISH" if bearish_count > bullish_count else "NEUTRAL"
    
    return {
        "patterns": patterns[:5],  # Top 5 most recent
        "bullish_signals": bullish_count,
        "bearish_signals": bearish_count,
        "bias": bias
    }


def format_patterns_for_prompt(symbol: str, pattern_data: Dict) -> str:
    """Format candle patterns for LLM prompt"""
    if not pattern_data or not pattern_data.get("patterns"):
        return f"{symbol}: No patterns detected"
    
    patterns = pattern_data.get("patterns", [])
    bias = pattern_data.get("bias", "NEUTRAL")
    
    pattern_strs = [f"{p['type']}({p['age']}ago)" for p in patterns[:3]]
    
    return f"{symbol} PATTERNS ({bias}): " + " | ".join(pattern_strs) if pattern_strs else f"{symbol}: No patterns"
