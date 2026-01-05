"""
Multi-Timeframe Data Fetcher
Provides 1h, 4h, 1d candle context for AI decision making
"""
from typing import Dict, List, Any
from datetime import datetime, timedelta


class MultiTimeframeData:
    def __init__(self, hl_client):
        self.hl_client = hl_client
        self.timeframes = {
            "1h": {"interval": "1h", "lookback_bars": 24},  # 24 hours
            "4h": {"interval": "4h", "lookback_bars": 42},  # 7 days
            "1d": {"interval": "1d", "lookback_bars": 30}   # 30 days
        }
    
    def get_mtf_context(self, symbol: str) -> Dict[str, Any]:
        """Get multi-timeframe context for a symbol"""
        context = {}
        
        for tf_name, tf_config in self.timeframes.items():
            try:
                candles = self._fetch_candles(
                    symbol,
                    tf_config["interval"],
                    tf_config["lookback_bars"]
                )
                
                if candles and len(candles) >= 2:
                    analysis = self._analyze_timeframe(candles)
                    context[tf_name] = analysis
                else:
                    context[tf_name] = {"error": "insufficient_data"}
            except Exception as e:
                print(f"[MTF] Error fetching {tf_name} for {symbol}: {e}")
                context[tf_name] = {"error": str(e)}
        
        return context
    
    def _fetch_candles(self, symbol: str, interval: str, bars: int) -> List[Dict]:
        """Fetch candles from Hyperliquid"""
        try:
            # Calculate time range
            now = int(datetime.now().timestamp() * 1000)
            
            # Map intervals to milliseconds
            interval_ms = {
                "1h": 3600000,
                "4h": 14400000,
                "1d": 86400000
            }
            
            ms_per_bar = interval_ms.get(interval, 3600000)
            start_time = now - (ms_per_bar * bars)
            
            # Fetch from HL client
            candles = self.hl_client.get_candles(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=now
            )
            
            return candles if candles else []
        except Exception as e:
            print(f"[MTF] Candle fetch error: {e}")
            return []
    
    def _analyze_timeframe(self, candles: List[Dict]) -> Dict[str, Any]:
        """Analyze single timeframe for trend and context"""
        if not candles or len(candles) < 2:
            return {"error": "no_data"}
        
        # Get latest candle
        latest = candles[-1]
        prev = candles[-2]
        
        # Extract OHLCV
        try:
            open_price = float(latest.get("o", latest.get("open", 0)))
            high = float(latest.get("h", latest.get("high", 0)))
            low = float(latest.get("l", latest.get("low", 0)))
            close = float(latest.get("c", latest.get("close", 0)))
            
            prev_close = float(prev.get("c", prev.get("close", 0)))
            
            # Calculate simple trend (last 5 candles)
            recent_candles = candles[-5:]
            closes = [float(c.get("c", c.get("close", 0))) for c in recent_candles if c.get("c") or c.get("close")]
            
            if len(closes) >= 2:
                trend = "BULLISH" if closes[-1] > closes[0] else "BEARISH" if closes[-1] < closes[0] else "NEUTRAL"
                trend_strength = abs((closes[-1] - closes[0]) / closes[0] * 100)
            else:
                trend = "NEUTRAL"
                trend_strength = 0
            
            # Candle type
            candle_type = "BULLISH" if close > open_price else "BEARISH" if close < open_price else "DOJI"
            
            # Change from previous
            change_pct = ((close - prev_close) / prev_close * 100) if prev_close > 0 else 0
            
            return {
                "price": close,
                "change_pct": round(change_pct, 2),
                "trend": trend,
                "trend_strength": round(trend_strength, 2),
                "candle_type": candle_type,
                "high": high,
                "low": low,
                "range_pct": round(((high - low) / close * 100), 2) if close > 0 else 0
            }
        except Exception as e:
            print(f"[MTF] Analysis error: {e}")
            return {"error": "analysis_failed"}
    
    def format_for_prompt(self, symbol: str, mtf_context: Dict[str, Any]) -> str:
        """Format MTF data for AI prompt"""
        if not mtf_context:
            return f"{symbol}: No multi-timeframe data available"
        
        lines = [f"\n**{symbol} Multi-Timeframe Analysis:**"]
        
        for tf_name in ["1d", "4h", "1h"]:  # Top-down
            tf_data = mtf_context.get(tf_name, {})
            
            if tf_data.get("error"):
                lines.append(f"- {tf_name}: Data unavailable")
                continue
            
            trend = tf_data.get("trend", "?")
            change = tf_data.get("change_pct", 0)
            trend_str = tf_data.get("trend_strength", 0)
            
            emoji = "📈" if trend == "BULLISH" else "📉" if trend == "BEARISH" else "➖"
            
            lines.append(
                f"- {tf_name}: {emoji} {trend} "
                f"({change:+.2f}% last candle, trend strength {trend_str:.1f}%)"
            )
        
        # Confluence detection
        trends = [mtf_context.get(tf, {}).get("trend") for tf in ["1d", "4h", "1h"]]
        if all(t == "BULLISH" for t in trends):
            lines.append("✅ **CONFLUENCE**: All timeframes BULLISH")
        elif all(t == "BEARISH" for t in trends):
            lines.append("✅ **CONFLUENCE**: All timeframes BEARISH")
        elif len(set(trends)) == 3:
            lines.append("🔄 **DIVERGENCE**: Timeframes not aligned")
        
        return "\n".join(lines)


# Singleton
_mtf_fetcher = None

def get_mtf_data(hl_client, symbol: str) -> Dict[str, Any]:
    """Get multi-timeframe data for symbol"""
    global _mtf_fetcher
    if _mtf_fetcher is None:
        _mtf_fetcher = MultiTimeframeData(hl_client)
    return _mtf_fetcher.get_mtf_context(symbol)

def format_mtf_for_prompt(hl_client, symbol: str) -> str:
    """Get formatted MTF string for AI prompt"""
    global _mtf_fetcher
    if _mtf_fetcher is None:
        _mtf_fetcher = MultiTimeframeData(hl_client)
    mtf_data = _mtf_fetcher.get_mtf_context(symbol)
    return _mtf_fetcher.format_for_prompt(symbol, mtf_data)
