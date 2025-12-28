"""
PnL Tracker using Hyperliquid Portfolio API
Real PnL data from the exchange, not calculated from snapshots.
"""
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List

# Cache
_pnl_cache: Optional[Dict[str, Any]] = None
_pnl_cache_time: float = 0
PNL_CACHE_TTL = 120  # 2 minutes
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "pnl_history.json")
MAX_HISTORY_POINTS = 1000  # Keep last 1000 points

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


def save_pnl_snapshot(equity: float):
    """Save current equity snapshot to history file"""
    import json
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = []
            
    # Add new point
    history.append({
        "time": datetime.now(timezone.utc).isoformat(),
        "value": round(equity, 2)
    })
    
    # Keep last N points
    history = history[-MAX_HISTORY_POINTS:]
    
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f)
    except Exception as e:
        print(f"[PNL] Failed to save history: {e}")


def get_pnl_history(hl_client=None, current_equity: float = 0, period: str = '24H') -> List[Dict[str, Any]]:
    """
    Get historical equity points for the chart.
    Reads from pnl_history.json if available, otherwise generates fallback.
    
    Args:
        hl_client: Hyperliquid client (optional)
        current_equity: Current equity value (optional)
        period: Time window to filter ('24H', '7D', '30D', 'ALL')
    """
    import json
    
    points = []
    
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                raw_history = json.load(f)
                if raw_history:
                    now = datetime.now(timezone.utc)
                    cutoff_time = now
                    
                    # Determine cutoff based on period
                    if period == '24H':
                        cutoff_time = now - timedelta(hours=24)
                    elif period == '7D':
                        cutoff_time = now - timedelta(days=7)
                    elif period == '30D':
                        cutoff_time = now - timedelta(days=30)
                    else: # ALL
                        cutoff_time = datetime.min.replace(tzinfo=timezone.utc)
                    
                    filtered_history = []
                    for point in raw_history:
                        try:
                            # Parse time
                            # Handle different ISO formats just in case
                            t_str = point['time'].replace('Z', '+00:00')
                            dt = datetime.fromisoformat(t_str)
                            
                            if dt >= cutoff_time:
                                # Format for display
                                if period == '24H':
                                    display_time = dt.strftime("%H:%M")
                                else:
                                    display_time = dt.strftime("%d/%m") # Date for longer periods
                                    
                                filtered_history.append({
                                    "time": display_time,
                                    "value": point['value'],
                                    "full_time": point['time'] # Keep full time for sorting/checking
                                })
                        except Exception as e:
                            continue
                            
                    points = filtered_history
        except Exception as e:
            print(f"[PNL] Error reading/filtering history file: {e}")

    # If we have real points, return them
    if points:
        return points

    # Fallback to generated if no file exists yet (Mock Data)
    pnl_data = get_pnl_windows(hl_client)
    
    # Adjust fallback generation based on period
    pnl_val = 0
    hours = 24
    
    if period == '7D':
        pnl_val = pnl_data.get("7d", {}).get("pnl", 0)
        hours = 24 * 7
    elif period == '30D':
        pnl_val = pnl_data.get("30d", {}).get("pnl", 0)
        hours = 24 * 30
    elif period == 'ALL':
        pnl_val = pnl_data.get("allTime", {}).get("pnl", 0)
        hours = 24 * 60 # Mock 60 days for all time
    else:
        pnl_val = pnl_data.get("24h", {}).get("pnl", 0)
        hours = 24
        
    if not isinstance(pnl_val, (int, float)):
        pnl_val = 0

    # Use provided equity or try to fetch it
    equity = current_equity
    if equity == 0:
        from config import HYPERLIQUID_WALLET_ADDRESS
        if hl_client or _hl_client_ref:
            client = hl_client or _hl_client_ref
            try:
                user_state = client.info.user_state(HYPERLIQUID_WALLET_ADDRESS)
                equity = float(user_state.get("marginSummary", {}).get("accountValue", 0))
            except:
                pass
    
    if equity == 0:
        equity = 100 # Default fallback for empty accounts
        
    start_equity = equity - pnl_val
    points = []
    now = datetime.now(timezone.utc)
    
    # Generate points (more points for longer periods)
    num_points = 25
    if period != '24H':
        num_points = 50
        
    for i in range(num_points + 1):
        step = i / float(num_points)
        time_offset = hours * (1 - step)
        point_time = now - timedelta(hours=time_offset)
        
        # Simple linear progression with some noise
        noise = (i % 3 - 1) * (abs(pnl_val) * 0.05) if pnl_val != 0 else (i % 3 - 1) * 0.1
        val = start_equity + (pnl_val * step) + noise
        
        # Format
        if period == '24H':
            t_fmt = "%H:%M"
        else:
            t_fmt = "%d/%m"
            
        points.append({
            "time": point_time.strftime(t_fmt),
            "value": round(val, 2)
        })
        
    return points


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
