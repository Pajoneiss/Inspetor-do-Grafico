"""
Session Awareness for Trading
Provides market session context (informational, not restrictive)
"""
from datetime import datetime, timezone
from typing import Dict, Any


# Trading Sessions (UTC times)
SESSIONS = {
    "ASIA": {
        "start": 0,   # 00:00 UTC (Tokyo open ~00:00, Hong Kong ~01:00)
        "end": 8,     # 08:00 UTC
        "description": "Asian session - Tokyo, Hong Kong, Singapore",
        "characteristics": [
            "Generally lower volume than London/NY",
            "BTC often ranges unless major news",
            "Good for mean reversion setups",
            "Altcoins may have larger spreads"
        ]
    },
    "LONDON": {
        "start": 8,   # 08:00 UTC (London open)
        "end": 16,    # 16:00 UTC
        "description": "European session - London, Frankfurt",
        "characteristics": [
            "Higher volume, increased volatility",
            "Often continues Asia's direction or reverses",
            "Good for breakout strategies",
            "Major news releases (ECB, UK data)"
        ]
    },
    "NEW_YORK": {
        "start": 13,  # 13:00 UTC (NY open 08:00 EST)
        "end": 21,    # 21:00 UTC (NY close 16:00 EST)
        "description": "US session - New York",
        "characteristics": [
            "Highest volume period globally",
            "Most volatile, especially at open",
            "US economic data releases",
            "Institutional activity peak"
        ]
    },
    "OVERLAP_LONDON_NY": {
        "start": 13,  # 13:00 UTC
        "end": 16,    # 16:00 UTC
        "description": "London-NY overlap - Peak liquidity",
        "characteristics": [
            "HIGHEST liquidity and volume",
            "Best for trend-following",
            "Sharp moves common",
            "Tight spreads"
        ]
    },
    "QUIET": {
        "start": 21,  # 21:00 UTC
        "end": 0,     # 00:00 UTC (next day)
        "description": "Inter-session period - Low activity",
        "characteristics": [
            "Lowest volume of the day",
            "Tight ranges common",
            "Avoid large positions",
            "Good for planning, not executing"
        ]
    }
}


def get_current_session() -> Dict[str, Any]:
    """
    Get the current trading session with context.
    
    Returns:
        Dict with session name, description, characteristics, and timing info
    """
    now = datetime.now(timezone.utc)
    current_hour = now.hour
    
    # Check for overlap first (most important)
    if 13 <= current_hour < 16:
        session_name = "OVERLAP_LONDON_NY"
    elif 0 <= current_hour < 8:
        session_name = "ASIA"
    elif 8 <= current_hour < 13:
        session_name = "LONDON"
    elif 13 <= current_hour < 21:
        session_name = "NEW_YORK"
    else:  # 21 <= current_hour < 24
        session_name = "QUIET"
    
    session = SESSIONS[session_name]
    
    # Calculate time remaining in session
    end_hour = session["end"]
    if end_hour == 0:
        end_hour = 24
    
    hours_remaining = end_hour - current_hour
    if hours_remaining < 0:
        hours_remaining += 24
    
    # Is it weekend? (Saturday after 00:00 UTC to Sunday 24:00 UTC)
    is_weekend = now.weekday() >= 5  # Saturday=5, Sunday=6
    
    return {
        "session": session_name,
        "description": session["description"],
        "characteristics": session["characteristics"],
        "current_time_utc": now.strftime("%H:%M UTC"),
        "hours_remaining": hours_remaining,
        "is_weekend": is_weekend,
        "day_of_week": now.strftime("%A")
    }


def format_session_for_prompt() -> str:
    """
    Format session info for inclusion in LLM prompt.
    This is INFORMATIONAL - does not restrict trading.
    """
    session_info = get_current_session()
    
    # Build characteristics string
    chars = "\n".join([f"  - {c}" for c in session_info["characteristics"]])
    
    weekend_warning = ""
    if session_info["is_weekend"]:
        weekend_warning = "\n⚠️ WEEKEND: Lower liquidity expected, wider spreads possible."
    
    return f"""📍 CURRENT SESSION: {session_info["session"]}
Time: {session_info["current_time_utc"]} ({session_info["day_of_week"]})
Description: {session_info["description"]}
Hours remaining in session: {session_info["hours_remaining"]}h
{weekend_warning}
Session Characteristics (CONTEXT, not rules):
{chars}

NOTE: This is CONTEXTUAL information. You are NOT restricted from trading in any session.
Use this to inform your decisions, not limit them."""


# Quick test
if __name__ == "__main__":
    print(format_session_for_prompt())
