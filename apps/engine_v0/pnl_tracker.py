"""
Equity Snapshots Storage for PnL Windows
Simple JSON-based storage for tracking equity over time.
"""
import os
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Storage file path
SNAPSHOTS_FILE = os.path.join(os.path.dirname(__file__), "equity_snapshots.json")
SNAPSHOT_INTERVAL_SECONDS = 300  # 5 minutes

# In-memory cache
_snapshots: List[Dict[str, Any]] = []
_last_snapshot_time: float = 0


def _load_snapshots():
    """Load snapshots from file"""
    global _snapshots
    if os.path.exists(SNAPSHOTS_FILE):
        try:
            with open(SNAPSHOTS_FILE, 'r') as f:
                _snapshots = json.load(f)
                # Clean up old snapshots (keep only last 365 days)
                cutoff = time.time() - (365 * 24 * 3600)
                _snapshots = [s for s in _snapshots if s.get("ts", 0) > cutoff]
        except Exception as e:
            print(f"[PNL][WARN] Failed to load snapshots: {e}")
            _snapshots = []


def _save_snapshots():
    """Save snapshots to file"""
    try:
        with open(SNAPSHOTS_FILE, 'w') as f:
            json.dump(_snapshots, f)
    except Exception as e:
        print(f"[PNL][WARN] Failed to save snapshots: {e}")


def record_equity_snapshot(equity: float, realized_pnl: float = 0):
    """
    Record equity snapshot if enough time has passed since last snapshot.
    
    Args:
        equity: Current account equity
        realized_pnl: Realized PnL (if available)
    """
    global _last_snapshot_time, _snapshots
    
    now = time.time()
    if now - _last_snapshot_time < SNAPSHOT_INTERVAL_SECONDS:
        return  # Not time yet
    
    # Load if empty
    if not _snapshots:
        _load_snapshots()
    
    # Add new snapshot
    snapshot = {
        "ts": now,
        "dt": datetime.now().isoformat(),
        "equity": equity,
        "realized": realized_pnl
    }
    _snapshots.append(snapshot)
    _last_snapshot_time = now
    
    # Keep last 365 days worth (~105k snapshots at 5min interval)
    # For safety, limit to 200k entries
    if len(_snapshots) > 200000:
        _snapshots = _snapshots[-100000:]
    
    _save_snapshots()
    print(f"[PNL] Snapshot recorded: equity=${equity:.2f}")


def get_pnl_windows() -> Dict[str, Dict[str, Any]]:
    """
    Calculate PnL for various time windows.
    
    Returns:
        {
            "24h": {"pnl": float, "pnl_pct": float, "start_equity": float},
            "7d": {...},
            "30d": {...},
            "90d": {...},
            "180d": {...},
            "365d": {...},
            "current_equity": float,
            "unrealized": float
        }
    """
    global _snapshots
    
    if not _snapshots:
        _load_snapshots()
    
    if not _snapshots:
        return {
            "24h": {"pnl": "N/A", "pnl_pct": "N/A"},
            "7d": {"pnl": "N/A", "pnl_pct": "N/A"},
            "30d": {"pnl": "N/A", "pnl_pct": "N/A"},
            "90d": {"pnl": "N/A", "pnl_pct": "N/A"},
            "180d": {"pnl": "N/A", "pnl_pct": "N/A"},
            "365d": {"pnl": "N/A", "pnl_pct": "N/A"},
            "current_equity": "N/A",
            "unrealized": "N/A"
        }
    
    now = time.time()
    current_equity = _snapshots[-1]["equity"] if _snapshots else 0
    
    windows = {
        "24h": 24 * 3600,
        "7d": 7 * 24 * 3600,
        "30d": 30 * 24 * 3600,
        "90d": 90 * 24 * 3600,
        "180d": 180 * 24 * 3600,
        "365d": 365 * 24 * 3600
    }
    
    result = {
        "current_equity": current_equity,
        "unrealized": 0  # Will be updated from state
    }
    
    for window_name, seconds in windows.items():
        target_time = now - seconds
        
        # Find closest snapshot to target time
        closest = None
        for s in _snapshots:
            if s["ts"] <= target_time:
                closest = s
            else:
                break
        
        if closest:
            start_equity = closest["equity"]
            pnl = current_equity - start_equity
            pnl_pct = (pnl / start_equity * 100) if start_equity > 0 else 0
            result[window_name] = {
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "start_equity": start_equity
            }
        else:
            result[window_name] = {"pnl": "N/A", "pnl_pct": "N/A"}
    
    return result


def format_pnl_windows_for_telegram(pnl_data: Dict[str, Any]) -> str:
    """Format PnL windows for Telegram message"""
    lines = ["📊 *PnL por Janela:*"]
    
    for window in ["24h", "7d", "30d", "90d", "180d", "365d"]:
        data = pnl_data.get(window, {})
        pnl = data.get("pnl", "N/A")
        pnl_pct = data.get("pnl_pct", "N/A")
        
        if isinstance(pnl, float):
            emoji = "🟢" if pnl >= 0 else "🔴"
            lines.append(f"  {window}: {emoji} ${pnl:+.2f} ({pnl_pct:+.2f}%)")
        else:
            lines.append(f"  {window}: {pnl}")
    
    return "\n".join(lines)
