"""
Trade Journal - Logs every AI decision for learning
"""
import json
import time
from typing import Dict, Any, List
from pathlib import Path


class TradeJournal:
    def __init__(self, journal_path: str = "data/trade_journal.jsonl"):
        self.journal_path = Path(journal_path)
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_decision(
        self,
        symbol: str,
        action_type: str,
        decision_summary: str,
        confidence: float,
        market_context: Dict[str, Any] = None,
        position_before: Dict[str, Any] = None,
        entry_price: float = None,
        exit_price: float = None,
        pnl: float = None,
        side: str = None
    ):
        """Log a trading decision"""
        entry = {
            "timestamp": int(time.time()),
            "symbol": symbol,
            "action_type": action_type,
            "decision_summary": decision_summary,
            "confidence": confidence,
            "market_context": market_context or {},
            "position_before": position_before or {},
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "side": side,
            "outcome": None  # Will be filled later
        }
        
        # Append to journal
        with open(self.journal_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        return entry
    
    def get_recent_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent trades from journal"""
        if not self.journal_path.exists():
            return []
        
        trades = []
        with open(self.journal_path, "r") as f:
            for line in f:
                try:
                    trades.append(json.loads(line.strip()))
                except:
                    pass
        
        return trades[-limit:]
    
    def get_win_loss_stats(self, symbol: str = None, days: int = 7) -> Dict[str, Any]:
        """Calculate win/loss statistics"""
        trades = self.get_recent_trades(limit=1000)
        
        # Filter by symbol and time
        cutoff_time = int(time.time()) - (days * 86400)
        filtered = [
            t for t in trades
            if t.get("pnl") is not None
            and t.get("timestamp", 0) >= cutoff_time
            and (symbol is None or t.get("symbol") == symbol)
        ]
        
        if not filtered:
            return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0, "avg_pnl": 0}
        
        wins = [t for t in filtered if t.get("pnl", 0) > 0]
        losses = [t for t in filtered if t.get("pnl", 0) <= 0]
        
        total_pnl = sum(t.get("pnl", 0) for t in filtered)
        
        return {
            "total": len(filtered),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": (len(wins) / len(filtered) * 100) if filtered else 0,
            "avg_pnl": total_pnl / len(filtered) if filtered else 0,
            "total_pnl": total_pnl
        }


# Singleton
_journal = None

def get_trade_journal() -> TradeJournal:
    """Get global trade journal instance"""
    global _journal
    if _journal is None:
        _journal = TradeJournal()
    return _journal

def log_trade(symbol: str, action: str, summary: str, confidence: float, **kwargs):
    """Quick log function"""
    journal = get_trade_journal()
    return journal.log_decision(symbol, action, summary, confidence, **kwargs)
