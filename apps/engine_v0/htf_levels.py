"""
HTF Key Levels Module
Calculates Weekly and Monthly highs/lows as key liquidity targets
AI interprets significance - NO hardcoded trading rules
"""

from typing import Dict, Any, List, Optional


def calculate_htf_levels(candles_weekly: List[Dict], candles_monthly: List[Dict]) -> Dict[str, Any]:
    """
    Calculate HTF (Higher Timeframe) key levels.
    
    These are significant levels where:
    - Weekly highs/lows = Short-term liquidity targets
    - Monthly highs/lows = Major liquidity targets
    - Previous week/month levels = Key S/R zones
    
    Args:
        candles_weekly: Weekly candles
        candles_monthly: Monthly candles
    
    Returns:
        Dict with weekly and monthly levels
    """
    result = {
        "weekly": {},
        "monthly": {},
        "current_price": None
    }
    
    # Weekly levels
    if candles_weekly and len(candles_weekly) >= 2:
        try:
            current_week = candles_weekly[-1]
            prev_week = candles_weekly[-2]
            
            result["weekly"] = {
                "current_high": float(current_week.get('h', current_week.get('high', 0))),
                "current_low": float(current_week.get('l', current_week.get('low', 0))),
                "prev_high": float(prev_week.get('h', prev_week.get('high', 0))),
                "prev_low": float(prev_week.get('l', prev_week.get('low', 0))),
            }
            
            # 4-week range (swing context)
            if len(candles_weekly) >= 4:
                last_4_weeks = candles_weekly[-4:]
                highs = [float(c.get('h', c.get('high', 0))) for c in last_4_weeks]
                lows = [float(c.get('l', c.get('low', 0))) for c in last_4_weeks]
                result["weekly"]["range_high"] = max(highs)
                result["weekly"]["range_low"] = min(lows)
                
            result["current_price"] = float(current_week.get('c', current_week.get('close', 0)))
        except Exception as e:
            pass
    
    # Monthly levels
    if candles_monthly and len(candles_monthly) >= 2:
        try:
            current_month = candles_monthly[-1]
            prev_month = candles_monthly[-2]
            
            result["monthly"] = {
                "current_high": float(current_month.get('h', current_month.get('high', 0))),
                "current_low": float(current_month.get('l', current_month.get('low', 0))),
                "prev_high": float(prev_month.get('h', prev_month.get('high', 0))),
                "prev_low": float(prev_month.get('l', prev_month.get('low', 0))),
            }
            
            # 3-month range (macro context)
            if len(candles_monthly) >= 3:
                last_3_months = candles_monthly[-3:]
                highs = [float(c.get('h', c.get('high', 0))) for c in last_3_months]
                lows = [float(c.get('l', c.get('low', 0))) for c in last_3_months]
                result["monthly"]["range_high"] = max(highs)
                result["monthly"]["range_low"] = min(lows)
        except Exception as e:
            pass
    
    return result


def format_htf_levels_for_prompt(symbol: str, htf_data: Dict) -> str:
    """Format HTF levels for LLM prompt"""
    if not htf_data:
        return f"{symbol}: No HTF levels"
    
    lines = [f"{symbol} KEY LEVELS:"]
    
    weekly = htf_data.get("weekly", {})
    if weekly:
        w_high = weekly.get("current_high", 0)
        w_low = weekly.get("current_low", 0)
        pw_high = weekly.get("prev_high", 0)
        pw_low = weekly.get("prev_low", 0)
        lines.append(f"  Weekly: H=${w_high:.0f} L=${w_low:.0f} | Prev: H=${pw_high:.0f} L=${pw_low:.0f}")
    
    monthly = htf_data.get("monthly", {})
    if monthly:
        m_high = monthly.get("current_high", 0)
        m_low = monthly.get("current_low", 0)
        pm_high = monthly.get("prev_high", 0)
        pm_low = monthly.get("prev_low", 0)
        lines.append(f"  Monthly: H=${m_high:.0f} L=${m_low:.0f} | Prev: H=${pm_high:.0f} L=${pm_low:.0f}")
    
    return "\n".join(lines) if len(lines) > 1 else f"{symbol}: No HTF levels"
