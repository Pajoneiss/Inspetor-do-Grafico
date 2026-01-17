"""
Session Levels Module
Calculates session highs/lows for Asia, London, NY sessions
AI interprets significance - NO hardcoded trading rules
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List


# Session hours in UTC
SESSIONS = {
    "ASIA": {"start": 0, "end": 8},
    "LONDON": {"start": 8, "end": 16},
    "NY": {"start": 13, "end": 21}
}


def calculate_session_levels(candles_1h: List[Dict]) -> Dict[str, Any]:
    """
    Calculate session highs/lows from 1H candles.
    
    Returns:
        Dict with high/low for each session today
    """
    if not candles_1h or len(candles_1h) < 24:
        return {}
    
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    result = {}
    current_price = float(candles_1h[-1].get('c', candles_1h[-1].get('close', 0)))
    
    for session_name, hours in SESSIONS.items():
        session_start = today_start + timedelta(hours=hours["start"])
        session_end = today_start + timedelta(hours=hours["end"])
        
        # Find candles within this session
        session_candles = []
        for candle in candles_1h:
            try:
                # Get candle timestamp
                ts = candle.get('t', candle.get('time', 0))
                if isinstance(ts, (int, float)):
                    if ts > 1e12:  # milliseconds
                        candle_time = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                    else:
                        candle_time = datetime.fromtimestamp(ts, tz=timezone.utc)
                else:
                    continue
                
                # Check if within session
                if session_start <= candle_time < session_end:
                    session_candles.append(candle)
            except:
                continue
        
        if session_candles:
            highs = [float(c.get('h', c.get('high', 0))) for c in session_candles]
            lows = [float(c.get('l', c.get('low', 0))) for c in session_candles]
            
            session_high = max(highs) if highs else 0
            session_low = min(lows) if lows else 0
            
            # Check if session is active
            is_active = session_start <= now < session_end
            
            result[session_name] = {
                "high": session_high,
                "low": session_low,
                "range": session_high - session_low if session_high and session_low else 0,
                "active": is_active,
                "price_position": "ABOVE" if current_price > session_high else "BELOW" if current_price < session_low else "WITHIN"
            }
    
    result["current_price"] = current_price
    
    return result


def format_session_levels_for_prompt(symbol: str, session_data: Dict) -> str:
    """Format session levels for LLM prompt"""
    if not session_data:
        return f"{symbol}: No session levels"
    
    lines = [f"{symbol} SESSION LEVELS (today):"]
    
    for session in ["ASIA", "LONDON", "NY"]:
        if session in session_data:
            s = session_data[session]
            status = "🟢ACTIVE" if s.get("active") else ""
            pos = s.get("price_position", "")
            lines.append(f"  {session}{status}: H=${s['high']:.0f} L=${s['low']:.0f} ({pos})")
    
    return "\n".join(lines) if len(lines) > 1 else f"{symbol}: No session data"
