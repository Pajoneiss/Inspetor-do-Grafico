"""
Technical Indicators Calculator for Engine V0
Calculates EMAs, RSI, ATR, and trend from candle data
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List


def calculate_indicators(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate technical indicators from candles
    
    Args:
        candles: List of candle dicts with t, o, h, l, c, v
    
    Returns:
        dict: Calculated indicators (Tier 2 complete)
    """
    try:
        if not candles or len(candles) < 50:
            return {
                "ema_9": 0,
                "ema_21": 0,
                "ema_50": 0,
                "ema_200": 0,
                "rsi_14": 50,
                "atr_14": 0,
                "atr_pct": 0,
                "trend": "neutral",
                "volatility": "unknown",
                "macd": 0,
                "macd_signal": 0,
                "macd_hist": 0,
                "bb_upper": 0,
                "bb_lower": 0,
                "bb_bandwidth": 0,
                "volume_ma": 0,
                "relative_volume": 1.0
            }
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        
        # Ensure numeric types
        df['close'] = pd.to_numeric(df['c'], errors='coerce')
        df['high'] = pd.to_numeric(df['h'], errors='coerce')
        df['low'] = pd.to_numeric(df['l'], errors='coerce')
        df['open'] = pd.to_numeric(df['o'], errors='coerce')
        df['volume'] = pd.to_numeric(df['v'], errors='coerce')
        
        # EMAs
        ema_9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema_21 = df['close'].ewm(span=21, adjust=False).mean().iloc[-1]
        ema_50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1] if len(df) >= 50 else ema_21
        ema_200 = df['close'].ewm(span=200, adjust=False).mean().iloc[-1] if len(df) >= 200 else ema_50
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]
        
        # MACD (12, 26, 9)
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        macd_signal = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - macd_signal
        
        macd = macd_line.iloc[-1]
        macd_sig = macd_signal.iloc[-1]
        macd_h = macd_hist.iloc[-1]
        
        # Bollinger Bands (20, 2)
        bb_period = 20
        bb_std = 2
        sma_20 = df['close'].rolling(window=bb_period).mean()
        std_20 = df['close'].rolling(window=bb_period).std()
        bb_upper = sma_20 + (std_20 * bb_std)
        bb_lower = sma_20 - (std_20 * bb_std)
        bb_bandwidth = ((bb_upper - bb_lower) / sma_20) * 100
        
        bb_up = bb_upper.iloc[-1]
        bb_low = bb_lower.iloc[-1]
        bb_bw = bb_bandwidth.iloc[-1]
        
        # Volume indicators
        volume_ma = df['volume'].rolling(window=20).mean().iloc[-1]
        current_volume = df['volume'].iloc[-1]
        relative_volume = current_volume / volume_ma if volume_ma > 0 else 1.0
        
        # Trend determination
        if ema_9 > ema_21 > ema_50:
            trend = "up"
        elif ema_9 < ema_21 < ema_50:
            trend = "down"
        else:
            trend = "neutral"
        
        # Volatility (ATR relative to price)
        current_price = df['close'].iloc[-1]
        atr_pct = (atr / current_price) * 100 if current_price > 0 else 0
        volatility = "high" if atr_pct > 2.0 else "normal" if atr_pct > 1.0 else "low"
        
        return {
            # Trend
            "ema_9": float(ema_9),
            "ema_21": float(ema_21),
            "ema_50": float(ema_50),
            "ema_200": float(ema_200),
            "trend": trend,
            
            # Momentum
            "rsi_14": float(rsi),
            "macd": float(macd),
            "macd_signal": float(macd_sig),
            "macd_hist": float(macd_h),
            
            # Volatility
            "atr_14": float(atr),
            "atr_pct": float(atr_pct),
            "volatility": volatility,
            "bb_upper": float(bb_up),
            "bb_lower": float(bb_low),
            "bb_bandwidth": float(bb_bw),
            
            # Volume
            "volume_ma": float(volume_ma),
            "relative_volume": float(relative_volume),
            
            # Price
            "price": float(current_price)
        }
        
    except Exception as e:
        print(f"[INDICATORS][ERROR] calculation failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "ema_9": 0,
            "ema_21": 0,
            "ema_50": 0,
            "ema_200": 0,
            "rsi_14": 50,
            "atr_14": 0,
            "atr_pct": 0,
            "trend": "neutral",
            "volatility": "unknown",
            "macd": 0,
            "macd_signal": 0,
            "macd_hist": 0,
            "bb_upper": 0,
            "bb_lower": 0,
            "bb_bandwidth": 0,
            "volume_ma": 0,
            "relative_volume": 1.0
        }
