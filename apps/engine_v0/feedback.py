"""
Feedback System for Engine V0
Tracks rejects, errors, and successful actions for AI observability
"""
import time
from typing import Dict, Any, List
from collections import deque


class FeedbackTracker:
    """Track execution feedback for AI learning"""
    
    def __init__(self, max_items: int = 10):
        """
        Initialize feedback tracker
        
        Args:
            max_items: Maximum items to keep in each queue
        """
        self.max_items = max_items
        self.rejects = deque(maxlen=max_items)
        self.errors = deque(maxlen=max_items)
        self.successes = deque(maxlen=max_items)
    
    def add_reject(self, action_type: str, symbol: str, reason: str):
        """Record a rejection"""
        self.rejects.append({
            "ts": time.time(),
            "action": action_type,
            "symbol": symbol,
            "reason": reason
        })
    
    def add_error(self, action_type: str, symbol: str, error_msg: str):
        """Record an error"""
        self.errors.append({
            "ts": time.time(),
            "action": action_type,
            "symbol": symbol,
            "error": error_msg
        })
    
    def add_success(self, action_type: str, symbol: str, details: str = ""):
        """Record a successful action"""
        self.successes.append({
            "ts": time.time(),
            "action": action_type,
            "symbol": symbol,
            "details": details
        })
    
    def get_recent_rejects(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get recent rejections"""
        items = list(self.rejects)
        if limit:
            items = items[-limit:]
        return items
    
    def get_recent_errors(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get recent errors"""
        items = list(self.errors)
        if limit:
            items = items[-limit:]
        return items
    
    def get_recent_successes(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get recent successes"""
        items = list(self.successes)
        if limit:
            items = items[-limit:]
        return items
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary counts"""
        return {
            "rejects_count": len(self.rejects),
            "errors_count": len(self.errors),
            "successes_count": len(self.successes)
        }


# Global feedback tracker instance
_feedback_tracker = FeedbackTracker()


def get_feedback_tracker() -> FeedbackTracker:
    """Get global feedback tracker instance"""
    return _feedback_tracker
