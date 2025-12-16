"""
PnL Tracker using Hyperliquid Portfolio API
Real PnL data from the exchange, not calculated from snapshots.
"""
import os
import time
from typing import Dict, Any, Optional
from datetime import datetime

# Cache
_pnl_cache: Optional[Dict[str, Any]] = None
_pnl_cache_time: float = 0
PNL_CACHE_TTL = 120  # 2 minutes

# Global hl_client reference (set by main.py)
_hl_client_ref = None


def set_hl_client(client):
    """Set the hl_client reference for PnL fetching"""
    global _hl_client_ref
    _hl_client_ref = client
    print("[PNL] hl_client reference set")


def get_pnl_from_hyperliquid(hl_client=None) -> Dict[str, Any]:
    """
    Get real PnL from Hyperliquid Portfolio API.
    Uses caching to avoid excessive API calls.
    
    Returns:
        dict with windows: 24h, 7d, 30d, allTime
    """
    global _pnl_cache, _pnl_cache_time, _hl_client_ref
    
    now = time.time()
    
    # Return cached if fresh
    if _pnl_cache and now - _pnl_cache_time < PNL_CACHE_TTL:
        return _pnl_cache
    
    # Use global reference if no client passed
    if hl_client is None:
        hl_client = _hl_client_ref
    
    # Need to fetch fresh data
    if hl_client is None:
        return _get_empty_pnl("no hl_client")
    
    try:
        portfolio = hl_client.get_portfolio_pnl()
        
        if "error" in portfolio:
            print(f"[PNL][WARN] Portfolio error: {portfolio['error']}")
            return _get_empty_pnl(portfolio["error"])
        
        result = {
            "24h": {"pnl": portfolio.get("day", 0), "pnl_pct": "N/A"},
            "7d": {"pnl": portfolio.get("week", 0), "pnl_pct": "N/A"},
            "30d": {"pnl": portfolio.get("month", 0), "pnl_pct": "N/A"},
            "90d": {"pnl": "N/A", "pnl_pct": "N/A"},  # Not directly available
            "180d": {"pnl": "N/A", "pnl_pct": "N/A"},  # Not directly available
            "365d": {"pnl": "N/A", "pnl_pct": "N/A"},  # Not directly available
            "allTime": {"pnl": portfolio.get("allTime", 0), "pnl_pct": "N/A"},
            "current_equity": "N/A",
            "unrealized": "N/A",
            "source": "hyperliquid",
            "cached_at": datetime.now().isoformat()
        }
        
        # Cache the result
        _pnl_cache = result
        _pnl_cache_time = now
        
        return result
        
    except Exception as e:
        print(f"[PNL][ERROR] Failed to get PnL: {e}")
        return _get_empty_pnl(str(e))


def _get_empty_pnl(reason: str = "") -> Dict[str, Any]:
    """Return empty PnL structure with reason"""
    return {
        "24h": {"pnl": f"N/A ({reason})" if reason else "N/A", "pnl_pct": "N/A"},
        "7d": {"pnl": "N/A", "pnl_pct": "N/A"},
        "30d": {"pnl": "N/A", "pnl_pct": "N/A"},
        "90d": {"pnl": "N/A", "pnl_pct": "N/A"},
        "180d": {"pnl": "N/A", "pnl_pct": "N/A"},
        "365d": {"pnl": "N/A", "pnl_pct": "N/A"},
        "allTime": {"pnl": "N/A", "pnl_pct": "N/A"},
        "source": "error"
    }


def get_pnl_windows(hl_client=None) -> Dict[str, Any]:
    """
    Main entry point for PnL windows.
    Alias for get_pnl_from_hyperliquid for backward compatibility.
    """
    return get_pnl_from_hyperliquid(hl_client)


def format_pnl_windows_for_telegram(pnl_data: Dict[str, Any]) -> str:
    """Format PnL windows for Telegram message"""
    lines = ["📊 *PnL por Janela:*"]
    
    for window in ["24h", "7d", "30d", "allTime"]:
        data = pnl_data.get(window, {})
        pnl = data.get("pnl", "N/A")
        
        if isinstance(pnl, (int, float)):
            emoji = "🟢" if pnl >= 0 else "🔴"
            lines.append(f"  {window}: {emoji} ${pnl:+.2f}")
        else:
            lines.append(f"  {window}: {pnl}")
    
    return "\n".join(lines)
