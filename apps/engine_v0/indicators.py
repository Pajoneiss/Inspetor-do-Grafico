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
        dict: Calculated indicators
    """
    try:
        if not candles or len(candles) < 50:
            return {
                "ema_9": 0,
                "ema_21": 0,
                "ema_50": 0,
                "rsi": 50,
                "atr": 0,
                "trend": "neutral",
                "volatility": "unknown"
            }
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        
        # Ensure numeric types
        df['close'] = pd.to_numeric(df['c'], errors='coerce')
        df['high'] = pd.to_numeric(df['h'], errors='coerce')
        df['low'] = pd.to_numeric(df['l'], errors='coerce')
        df['open'] = pd.to_numeric(df['o'], errors='coerce')
        
        # EMAs
        ema_9 = df['close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema_21 = df['close'].ewm(span=21, adjust=False).mean().iloc[-1]
        ema_50 = df['close'].ewm(span=50, adjust=False).mean().iloc[-1] if len(df) >= 50 else ema_21
        
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
            "ema_9": float(ema_9),
            "ema_21": float(ema_21),
            "ema_50": float(ema_50),
            "rsi": float(rsi),
            "atr": float(atr),
            "atr_pct": float(atr_pct),
            "trend": trend,
            "volatility": volatility,
            "price": float(current_price)
        }
        
    except Exception as e:
        print(f"[INDICATORS][ERROR] calculation failed: {e}")
        return {
            "ema_9": 0,
            "ema_21": 0,
            "ema_50": 0,
            "rsi": 50,
            "atr": 0,
            "trend": "neutral",
            "volatility": "unknown"
        }
