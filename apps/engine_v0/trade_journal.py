"""
Trade Journal for ML - Phase 1
Structured logging of all trades with market conditions for future analysis
"""
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from threading import Lock

# Journal file path
JOURNAL_FILE = os.path.join(os.path.dirname(__file__), "data", "trade_journal.json")


class TradeJournal:
    """
    Trade Journal for structured trade logging.
    Captures entry/exit with full market snapshot for ML analysis.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton pattern for thread-safe global access"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._trades: Dict[str, Dict] = {}  # trade_id -> trade data
        self._open_trades: Dict[str, str] = {}  # symbol -> trade_id (for quick lookup)
        self._file_lock = Lock()
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(JOURNAL_FILE), exist_ok=True)
        
        # Load existing journal
        self._load()
        self._initialized = True
        print(f"[JOURNAL] Initialized with {len(self._trades)} trades, {len(self._open_trades)} open")
    
    def _load(self):
        """Load journal from file"""
        try:
            if os.path.exists(JOURNAL_FILE):
                with open(JOURNAL_FILE, 'r') as f:
                    data = json.load(f)
                    self._trades = data.get("trades", {})
                    
                    # Rebuild open trades index
                    self._open_trades = {}
                    for trade_id, trade in self._trades.items():
                        if trade.get("status") == "OPEN":
                            self._open_trades[trade["symbol"]] = trade_id
                    
                    print(f"[JOURNAL] Loaded {len(self._trades)} trades from disk")
        except Exception as e:
            print(f"[JOURNAL][ERROR] Failed to load: {e}")
            self._trades = {}
            self._open_trades = {}
    
    def _save(self):
        """Save journal to file"""
        try:
            with self._file_lock:
                with open(JOURNAL_FILE, 'w') as f:
                    json.dump({
                        "trades": self._trades,
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    }, f, indent=2, default=str)
        except Exception as e:
            print(f"[JOURNAL][ERROR] Failed to save: {e}")
    
    def record_entry(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        size: float,
        leverage: int,
        reason: str,
        confidence: float,
        market_snapshot: Dict[str, Any]
    ) -> str:
        """
        Record a new trade entry.
        
        Args:
            symbol: Trading symbol (e.g., "BTC")
            side: "LONG" or "SHORT"
            entry_price: Entry price
            size: Position size in asset units
            leverage: Leverage used
            reason: AI's reasoning for the trade
            confidence: AI confidence (0-1)
            market_snapshot: Current market conditions
            
        Returns:
            trade_id: Unique identifier for this trade
        """
        trade_id = str(uuid.uuid4())[:8]
        
        # Close any existing open trade for this symbol
        if symbol in self._open_trades:
            print(f"[JOURNAL][WARN] Closing stale open trade for {symbol}")
            self.record_exit(
                symbol=symbol,
                exit_price=entry_price,
                reason="Replaced by new position",
                exit_type="REPLACED"
            )
        
        trade = {
            "trade_id": trade_id,
            "symbol": symbol,
            "side": side.upper(),
            "status": "OPEN",
            
            "entry": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "price": entry_price,
                "size": size,
                "leverage": leverage,
                "reason": reason,
                "confidence": confidence
            },
            
            "exit": None,
            "result": None,
            
            "market_snapshot_entry": self._sanitize_snapshot(market_snapshot),
            "market_snapshot_exit": None,
            
            "tags": self._generate_tags(side, confidence, market_snapshot)
        }
        
        self._trades[trade_id] = trade
        self._open_trades[symbol] = trade_id
        self._save()
        
        print(f"[JOURNAL] 📝 Entry recorded: {trade_id} | {symbol} {side} @ ${entry_price:.2f}")
        return trade_id
    
    def record_exit(
        self,
        symbol: str,
        exit_price: float,
        reason: str,
        exit_type: str = "AI_EXIT",
        market_snapshot: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict]:
        """
        Record a trade exit.
        
        Args:
            symbol: Trading symbol
            exit_price: Exit price
            reason: Reason for exit
            exit_type: "TP" | "SL" | "MANUAL" | "AI_EXIT" | "REPLACED"
            market_snapshot: Current market conditions (optional)
            
        Returns:
            Completed trade data or None if no open trade found
        """
        if symbol not in self._open_trades:
            print(f"[JOURNAL][WARN] No open trade for {symbol} to close")
            return None
        
        trade_id = self._open_trades[symbol]
        trade = self._trades.get(trade_id)
        
        if not trade:
            print(f"[JOURNAL][ERROR] Trade {trade_id} not found")
            del self._open_trades[symbol]
            return None
        
        # Calculate result
        entry_price = trade["entry"]["price"]
        size = trade["entry"]["size"]
        side = trade["side"]
        
        if side == "LONG":
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        else:  # SHORT
            pnl_pct = ((entry_price - exit_price) / entry_price) * 100
        
        pnl_usd = (pnl_pct / 100) * (size * entry_price)
        
        entry_time = datetime.fromisoformat(trade["entry"]["timestamp"].replace('Z', '+00:00'))
        exit_time = datetime.now(timezone.utc)
        duration_minutes = (exit_time - entry_time).total_seconds() / 60
        
        # Update trade
        trade["status"] = exit_type if exit_type in ["TP", "SL"] else "CLOSED"
        trade["exit"] = {
            "timestamp": exit_time.isoformat(),
            "price": exit_price,
            "reason": reason,
            "type": exit_type
        }
        trade["result"] = {
            "pnl_usd": round(pnl_usd, 2),
            "pnl_pct": round(pnl_pct, 2),
            "duration_minutes": round(duration_minutes, 1),
            "win": pnl_usd > 0
        }
        trade["market_snapshot_exit"] = self._sanitize_snapshot(market_snapshot) if market_snapshot else None
        
        # Remove from open trades
        del self._open_trades[symbol]
        self._save()
        
        win_emoji = "✅" if pnl_usd > 0 else "❌"
        print(f"[JOURNAL] {win_emoji} Exit recorded: {trade_id} | {symbol} | PnL: ${pnl_usd:.2f} ({pnl_pct:.2f}%)")
        
        return trade
    
    def get_trade_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Get open trade for a symbol"""
        if symbol not in self._open_trades:
            return None
        return self._trades.get(self._open_trades[symbol])
    
    def get_all_trades(self, limit: int = 50, status: str = None) -> List[Dict]:
        """
        Get all trades, most recent first.
        
        Args:
            limit: Maximum number of trades to return
            status: Filter by status ("OPEN", "CLOSED", "TP", "SL")
        """
        trades = list(self._trades.values())
        
        if status:
            trades = [t for t in trades if t.get("status") == status]
        
        # Sort by entry timestamp, most recent first
        trades.sort(
            key=lambda t: t.get("entry", {}).get("timestamp", ""),
            reverse=True
        )
        
        return trades[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Calculate trading statistics.
        
        Returns:
            Dict with win_rate, avg_pnl, total_trades, etc.
        """
        closed_trades = [t for t in self._trades.values() if t.get("result")]
        
        if not closed_trades:
            return {
                "total_trades": len(self._trades),
                "open_trades": len(self._open_trades),
                "closed_trades": 0,
                "win_rate": 0,
                "avg_pnl_pct": 0,
                "total_pnl_usd": 0,
                "avg_duration_minutes": 0,
                "best_trade_pct": 0,
                "worst_trade_pct": 0
            }
        
        wins = [t for t in closed_trades if t["result"]["win"]]
        
        pnl_list = [t["result"]["pnl_pct"] for t in closed_trades]
        pnl_usd_list = [t["result"]["pnl_usd"] for t in closed_trades]
        duration_list = [t["result"]["duration_minutes"] for t in closed_trades]
        
        return {
            "total_trades": len(self._trades),
            "open_trades": len(self._open_trades),
            "closed_trades": len(closed_trades),
            "wins": len(wins),
            "losses": len(closed_trades) - len(wins),
            "win_rate": round(len(wins) / len(closed_trades) * 100, 1),
            "avg_pnl_pct": round(sum(pnl_list) / len(pnl_list), 2),
            "total_pnl_usd": round(sum(pnl_usd_list), 2),
            "avg_duration_minutes": round(sum(duration_list) / len(duration_list), 1),
            "best_trade_pct": round(max(pnl_list), 2),
            "worst_trade_pct": round(min(pnl_list), 2)
        }
    
    def export_csv(self) -> str:
        """Export journal to CSV format string"""
        headers = [
            "trade_id", "symbol", "side", "status",
            "entry_time", "entry_price", "entry_confidence",
            "exit_time", "exit_price", "exit_type",
            "pnl_usd", "pnl_pct", "duration_min", "win",
            "funding_rate", "open_interest", "relative_volume", "rsi", "trend"
        ]
        
        lines = [",".join(headers)]
        
        for trade in self._trades.values():
            entry = trade.get("entry", {})
            exit_data = trade.get("exit", {})
            result = trade.get("result", {})
            snapshot = trade.get("market_snapshot_entry", {})
            
            row = [
                trade.get("trade_id", ""),
                trade.get("symbol", ""),
                trade.get("side", ""),
                trade.get("status", ""),
                entry.get("timestamp", ""),
                str(entry.get("price", "")),
                str(entry.get("confidence", "")),
                exit_data.get("timestamp", "") if exit_data else "",
                str(exit_data.get("price", "")) if exit_data else "",
                exit_data.get("type", "") if exit_data else "",
                str(result.get("pnl_usd", "")) if result else "",
                str(result.get("pnl_pct", "")) if result else "",
                str(result.get("duration_minutes", "")) if result else "",
                str(result.get("win", "")) if result else "",
                str(snapshot.get("funding_rate", "")),
                str(snapshot.get("open_interest", "")),
                str(snapshot.get("relative_volume", "")),
                str(snapshot.get("rsi_14", "")),
                snapshot.get("trend", "")
            ]
            lines.append(",".join(row))
        
        return "\n".join(lines)
    
    def _sanitize_snapshot(self, snapshot: Optional[Dict]) -> Dict:
        """Ensure snapshot has expected fields"""
        if not snapshot:
            return {}
        
        return {
            "funding_rate": snapshot.get("funding_rate", 0),
            "open_interest": snapshot.get("open_interest", 0),
            "relative_volume": snapshot.get("relative_volume", 1.0),
            "rsi_14": snapshot.get("rsi_14", 50),
            "ema_trend": snapshot.get("trend", "UNKNOWN"),
            "bos_status": snapshot.get("bos_status", "UNKNOWN"),
            "choch_detected": snapshot.get("choch_detected", False),
            "atr_pct": snapshot.get("atr_pct", 0)
        }
    
    def _generate_tags(self, side: str, confidence: float, snapshot: Dict) -> List[str]:
        """Auto-generate tags based on trade conditions"""
        tags = []
        
        # Confidence tags
        if confidence >= 0.8:
            tags.append("high_confidence")
        elif confidence <= 0.6:
            tags.append("low_confidence")
        
        # Market condition tags
        funding = snapshot.get("funding_rate", 0)
        if funding > 0.03:
            tags.append("high_funding_long")
            if side == "LONG":
                tags.append("against_funding")
        elif funding < -0.03:
            tags.append("high_funding_short")
            if side == "SHORT":
                tags.append("against_funding")
        
        volume = snapshot.get("relative_volume", 1.0)
        if volume > 1.5:
            tags.append("high_volume")
        elif volume < 0.7:
            tags.append("low_volume")
        
        rsi = snapshot.get("rsi_14", 50)
        if rsi > 70:
            tags.append("overbought")
        elif rsi < 30:
            tags.append("oversold")
        
        bos = snapshot.get("bos_status", "")
        if bos == "UP":
            tags.append("bullish_structure")
        elif bos == "DOWN":
            tags.append("bearish_structure")
        
        if snapshot.get("choch_detected"):
            tags.append("choch_present")
        
        return tags


# Singleton instance for global access
journal = TradeJournal()


def get_journal() -> TradeJournal:
    """Get the global TradeJournal instance"""
    return journal



def record_ai_intent(
    symbol: str,
    side: str,
    size: float,
    entry_price: float,
    leverage: int = 1,
    stop_loss: float = None,
    take_profit_1: float = None,
    reason: str = "",
    confidence: float = 0.0
):
    """
    Record AI trading intent for tracking (not actual execution)
    This is called when AI makes a decision, before execution
    """
    try:
        timestamp = datetime.now(timezone.utc).isoformat()
        
        intent_data = {
            "timestamp": timestamp,
            "symbol": symbol,
            "side": side,
            "size": size,
            "entry_price": entry_price,
            "leverage": leverage,
            "stop_loss": stop_loss,
            "take_profit_1": take_profit_1,
            "reason": reason,
            "confidence": confidence,
            "status": "intent"  # Not executed yet
        }
        
        # Log for tracking
        print(f"[JOURNAL] AI Intent recorded: {symbol} {side} @ ${entry_price} (conf={confidence:.2f})")
        
        # Could save to file or DB here if needed
        # For now, just log it
        
        return True
    except Exception as e:
        print(f"[JOURNAL] Failed to record AI intent: {e}")
        return False

def get_recent_trades_for_ai(limit: int = 10) -> Dict[str, Any]:
    """
    Get recent trade history formatted for AI context.
    This gives the AI information about its own performance - NO RULES, just data.
    
    Returns:
        Dict with recent trades summary and per-symbol performance
    """
    j = get_journal()
    all_trades = j.get_all_trades(limit=50)  # Get more for stats
    stats = j.get_stats()
    
    # Format recent trades (last N)
    recent = []
    for trade in all_trades[:limit]:
        result = trade.get("result", {})
        entry = trade.get("entry", {})
        exit_data = trade.get("exit", {})
        
        recent.append({
            "symbol": trade.get("symbol"),
            "side": trade.get("side"),
            "status": trade.get("status"),
            "entry_price": entry.get("price"),
            "exit_price": exit_data.get("price") if exit_data else None,
            "pnl_pct": result.get("pnl_pct") if result else None,
            "pnl_usd": result.get("pnl_usd") if result else None,
            "duration_min": result.get("duration_minutes") if result else None,
            "win": result.get("win") if result else None,
            "exit_type": exit_data.get("type") if exit_data else None,
            "confidence": entry.get("confidence"),
            "reason": entry.get("reason", "")[:100]  # Truncate
        })
    
    # Per-symbol performance (last 24h)
    from datetime import datetime, timezone, timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    
    symbol_stats = {}
    for trade in all_trades:
        symbol = trade.get("symbol")
        result = trade.get("result")
        entry_time = trade.get("entry", {}).get("timestamp", "")
        
        if not result or not entry_time:
            continue
            
        try:
            trade_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
            if trade_time < cutoff:
                continue
        except:
            continue
        
        if symbol not in symbol_stats:
            symbol_stats[symbol] = {"trades": 0, "wins": 0, "total_pnl": 0}
        
        symbol_stats[symbol]["trades"] += 1
        if result.get("win"):
            symbol_stats[symbol]["wins"] += 1
        symbol_stats[symbol]["total_pnl"] += result.get("pnl_usd", 0)
    
    # Calculate win rate per symbol
    for sym, data in symbol_stats.items():
        data["win_rate"] = round(data["wins"] / data["trades"] * 100, 1) if data["trades"] > 0 else 0
        data["total_pnl"] = round(data["total_pnl"], 2)
    
    return {
        "overall_stats": {
            "total_trades": stats.get("total_trades", 0),
            "win_rate": stats.get("win_rate", 0),
            "avg_pnl_pct": stats.get("avg_pnl_pct", 0),
            "total_pnl_usd": stats.get("total_pnl_usd", 0),
            "best_trade_pct": stats.get("best_trade_pct", 0),
            "worst_trade_pct": stats.get("worst_trade_pct", 0),
            "avg_duration_min": stats.get("avg_duration_minutes", 0)
        },
        "last_24h_by_symbol": symbol_stats,
        "recent_trades": recent
    }

