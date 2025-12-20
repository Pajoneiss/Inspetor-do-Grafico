"""
Market Structure Detection Module (SMC - Smart Money Concepts)
Detects institutional market structure patterns
AI interprets significance - NO hardcoded trading rules
"""

def detect_trend(candles, lookback=10):
    """
    Detect trend based on Higher Highs/Higher Lows or Lower Highs/Lower Lows
    
    Returns: "BULLISH", "BEARISH", "RANGE", or "UNKNOWN"
    """
    if not candles or len(candles) < lookback:
        return "UNKNOWN"
    
    recent = candles[-lookback:]
    highs = [c['high'] for c in recent]
    lows = [c['low'] for c in recent]
    
    # Find swing points (local maxima/minima)
    swing_highs = []
    swing_lows = []
    
    for i in range(1, len(recent) - 1):
        # Swing high: higher than neighbors
        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
            swing_highs.append(highs[i])
        # Swing low: lower than neighbors
        if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
            swing_lows.append(lows[i])
    
    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return "UNKNOWN"
    
    # Check for HH/HL (bullish) or LH/LL (bearish)
    higher_highs = swing_highs[-1] > swing_highs[-2]
    higher_lows = swing_lows[-1] > swing_lows[-2]
    lower_highs = swing_highs[-1] < swing_highs[-2]
    lower_lows = swing_lows[-1] < swing_lows[-2]
    
    if higher_highs and higher_lows:
        return "BULLISH"
    elif lower_highs and lower_lows:
        return "BEARISH"
    else:
        return "RANGE"


def detect_break_of_structure(candles, trend, lookback=20):
    """
    Detect Break of Structure (BOS)
    - In uptrend: price breaks above previous swing high
    - In downtrend: price breaks below previous swing low
    
    Returns: "UP", "DOWN", or None
    """
    if not candles or len(candles) < lookback or trend == "UNKNOWN":
        return None
    
    recent = candles[-lookback:]
    current_price = recent[-1]['close']
    
    # Find recent swing high/low
    highs = [c['high'] for c in recent[:-1]]  # Exclude current
    lows = [c['low'] for c in recent[:-1]]
    
    if trend == "BULLISH":
        # Look for break above recent swing high
        recent_swing_high = max(highs[-10:]) if len(highs) >= 10 else max(highs)
        if current_price > recent_swing_high:
            return "UP"
    elif trend == "BEARISH":
        # Look for break below recent swing low
        recent_swing_low = min(lows[-10:]) if len(lows) >= 10 else min(lows)
        if current_price < recent_swing_low:
            return "DOWN"
    
    return None


def detect_change_of_character(candles, trend, lookback=15):
    """
    Detect Change of Character (CHoCH) - early reversal signal
    - In uptrend: fails to make HH, makes LH instead
    - In downtrend: fails to make LL, makes HL instead
    
    Returns: True if CHoCH detected, False otherwise
    """
    if not candles or len(candles) < lookback or trend == "UNKNOWN":
        return False
    
    recent = candles[-lookback:]
    
    # Get last 3 swing points
    highs = [c['high'] for c in recent]
    lows = [c['low'] for c in recent]
    
    swing_highs = []
    swing_lows = []
    
    for i in range(1, len(recent) - 1):
        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
            swing_highs.append((i, highs[i]))
        if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
            swing_lows.append((i, lows[i]))
    
    if trend == "BULLISH" and len(swing_highs) >= 2:
        # CHoCH in uptrend: recent high is lower than previous high
        if swing_highs[-1][1] < swing_highs[-2][1]:
            return True
    elif trend == "BEARISH" and len(swing_lows) >= 2:
        # CHoCH in downtrend: recent low is higher than previous low
        if swing_lows[-1][1] > swing_lows[-2][1]:
            return True
    
    return False


def find_order_blocks(candles, lookback=30):
    """
    Find Order Blocks - last candle before strong move
    These are zones where institutions likely entered
    
    Returns: list of order blocks with price and type
    """
    if not candles or len(candles) < lookback:
        return []
    
    recent = candles[-lookback:]
    order_blocks = []
    
    for i in range(len(recent) - 5):  # Need at least 5 candles ahead
        candle = recent[i]
        next_candles = recent[i+1:i+6]
        
        # Bullish order block: last red candle before strong up move
        if candle['close'] < candle['open']:  # Red candle
            # Check if next 3-5 candles moved up significantly
            move_up = sum(1 for c in next_candles[:3] if c['close'] > c['open'])
            price_gain = (next_candles[2]['close'] - candle['close']) / candle['close']
            
            if move_up >= 2 and price_gain > 0.01:  # 1% move
                order_blocks.append({
                    'price': (candle['low'] + candle['high']) / 2,
                    'type': 'BULLISH',
                    'strength': price_gain
                })
        
        # Bearish order block: last green candle before strong down move
        elif candle['close'] > candle['open']:  # Green candle
            move_down = sum(1 for c in next_candles[:3] if c['close'] < c['open'])
            price_drop = (candle['close'] - next_candles[2]['close']) / candle['close']
            
            if move_down >= 2 and price_drop > 0.01:
                order_blocks.append({
                    'price': (candle['low'] + candle['high']) / 2,
                    'type': 'BEARISH',
                    'strength': price_drop
                })
    
    # Return top 3 strongest order blocks
    order_blocks.sort(key=lambda x: x['strength'], reverse=True)
    return order_blocks[:3]


def find_liquidity_zones(candles, lookback=50):
    """
    Find Liquidity Zones - areas with clustered swing highs/lows
    These are where stops are likely placed
    
    Returns: list of liquidity zone prices
    """
    if not candles or len(candles) < lookback:
        return []
    
    recent = candles[-lookback:]
    
    # Find all swing highs and lows
    swing_levels = []
    
    for i in range(1, len(recent) - 1):
        # Swing high
        if recent[i]['high'] > recent[i-1]['high'] and recent[i]['high'] > recent[i+1]['high']:
            swing_levels.append(recent[i]['high'])
        # Swing low
        if recent[i]['low'] < recent[i-1]['low'] and recent[i]['low'] < recent[i+1]['low']:
            swing_levels.append(recent[i]['low'])
    
    if not swing_levels:
        return []
    
    # Cluster nearby levels (within 0.5%)
    swing_levels.sort()
    liquidity_zones = []
    current_cluster = [swing_levels[0]]
    
    for level in swing_levels[1:]:
        if (level - current_cluster[-1]) / current_cluster[-1] < 0.005:  # Within 0.5%
            current_cluster.append(level)
        else:
            # Save cluster average
            if len(current_cluster) >= 2:  # At least 2 touches
                liquidity_zones.append(sum(current_cluster) / len(current_cluster))
            current_cluster = [level]
    
    # Don't forget last cluster
    if len(current_cluster) >= 2:
        liquidity_zones.append(sum(current_cluster) / len(current_cluster))
    
    return liquidity_zones[:5]  # Top 5 zones


def analyze_market_structure(symbol_data):
    """
    Analyze complete market structure for a symbol across timeframes
    
    Args:
        symbol_data: dict with candles for multiple timeframes
        Example: {
            '1h': [candles],
            '15m': [candles],
            '5m': [candles]
        }
    
    Returns:
        dict with market structure analysis
    """
    result = {}
    
    # v13.0: Now includes 15m for entry-level order blocks
    for tf in ['4h', '1h', '15m', '5m']:
        if tf not in symbol_data or not symbol_data[tf]:
            continue
        
        candles = symbol_data[tf]
        
        # Detect trend
        trend = detect_trend(candles)
        
        # Detect BOS
        bos = detect_break_of_structure(candles, trend)
        
        # Detect CHoCH
        choch = detect_change_of_character(candles, trend)
        
        # Find order blocks (now includes 15m for entry precision)
        order_blocks = []
        if tf in ['4h', '1h', '15m']:
            order_blocks = find_order_blocks(candles)
        
        # Find liquidity zones (now includes 15m)
        liquidity_zones = []
        if tf in ['4h', '1h', '15m']:
            liquidity_zones = find_liquidity_zones(candles)
        
        result[tf] = {
            'trend': trend,
            'last_bos': bos,
            'choch_detected': choch,
            'order_blocks': order_blocks,
            'liquidity_zones': liquidity_zones
        }
    
    return result
