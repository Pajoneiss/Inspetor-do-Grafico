"""
Divergence Detection Module
Detects price/indicator divergences and timeframe conflicts
AI interprets significance - NO hardcoded trading rules
"""

def detect_price_rsi_divergence(candles, rsi_values, lookback=5):
    """
    Detect bullish/bearish divergence between price and RSI
    
    Returns: "BULLISH", "BEARISH", or None
    """
    if not candles or not rsi_values or len(candles) < lookback or len(rsi_values) < lookback:
        return None
    
    # Get recent price action
    recent_prices = [c['close'] for c in candles[-lookback:]]
    recent_rsi = rsi_values[-lookback:]
    
    # Bullish divergence: price making lower lows, RSI making higher lows
    price_trend = "DOWN" if recent_prices[-1] < recent_prices[0] else "UP"
    rsi_trend = "DOWN" if recent_rsi[-1] < recent_rsi[0] else "UP"
    
    if price_trend == "DOWN" and rsi_trend == "UP":
        # Price down, RSI up = bullish divergence
        return "BULLISH"
    elif price_trend == "UP" and rsi_trend == "DOWN":
        # Price up, RSI down = bearish divergence
        return "BEARISH"
    
    return None


def detect_timeframe_conflict(candles_higher_tf, candles_lower_tf):
    """
    Detect when lower timeframe contradicts higher timeframe
    
    Returns: dict with conflict info or None
    """
    if not candles_higher_tf or not candles_lower_tf:
        return None
    
    # Simple trend detection based on recent candles
    def get_trend(candles, lookback=3):
        if len(candles) < lookback:
            return "UNKNOWN"
        recent = candles[-lookback:]
        closes = [c['close'] for c in recent]
        if closes[-1] > closes[0] * 1.005:  # 0.5% threshold
            return "BULLISH"
        elif closes[-1] < closes[0] * 0.995:
            return "BEARISH"
        return "NEUTRAL"
    
    higher_trend = get_trend(candles_higher_tf)
    lower_trend = get_trend(candles_lower_tf)
    
    # Detect conflict
    if higher_trend == "BULLISH" and lower_trend == "BEARISH":
        return {
            "type": "REVERSAL_WARNING",
            "higher_tf": "BULLISH",
            "lower_tf": "BEARISH",
            "interpretation": "Higher TF bullish but lower TF showing bearish pressure"
        }
    elif higher_trend == "BEARISH" and lower_trend == "BULLISH":
        return {
            "type": "REVERSAL_WARNING",
            "higher_tf": "BEARISH",
            "lower_tf": "BULLISH",
            "interpretation": "Higher TF bearish but lower TF showing bullish pressure"
        }
    
    return None


def analyze_divergences(symbol_data):
    """
    Analyze all divergences for a symbol
    
    Args:
        symbol_data: dict with candles and indicators for multiple timeframes
        
    Returns:
        dict with divergence analysis
    """
    result = {}
    
    # Price vs RSI divergences
    for tf in ['15m', '1h', '4h']:
        if tf in symbol_data and 'candles' in symbol_data[tf] and 'rsi' in symbol_data[tf]:
            div = detect_price_rsi_divergence(
                symbol_data[tf]['candles'],
                symbol_data[tf]['rsi']
            )
            if div:
                result[f'price_rsi_{tf}'] = div
    
    # Timeframe conflicts
    if '1h' in symbol_data and '15m' in symbol_data:
        conflict = detect_timeframe_conflict(
            symbol_data['1h'].get('candles', []),
            symbol_data['15m'].get('candles', [])
        )
        if conflict:
            result['tf_conflict_1h_vs_15m'] = conflict
    
    if '4h' in symbol_data and '1h' in symbol_data:
        conflict = detect_timeframe_conflict(
            symbol_data['4h'].get('candles', []),
            symbol_data['1h'].get('candles', [])
        )
        if conflict:
            result['tf_conflict_4h_vs_1h'] = conflict
    
    return result if result else None
