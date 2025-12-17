"""
AI Thinking Context for Dashboard
Returns current AI strategy, market view, and position rationale
"""
from typing import Dict, Any
import time


# Global AI context state (updated by main loop)
_ai_context = {
    "last_update": 0,
    "market_view": "Analyzing market conditions...",
    "current_strategy": "No active strategy",
    "position_rationale": {},
    "recent_decisions": [],
    "confidence": 0.0
}


def update_ai_context(
    market_view: str = None,
    strategy: str = None,
    position_rationale: Dict[str, str] = None,
    decision: Dict[str, Any] = None,
    confidence: float = None
):
    """Update AI context from main loop"""
    global _ai_context
    
    if market_view:
        _ai_context["market_view"] = market_view
    if strategy:
        _ai_context["current_strategy"] = strategy
    if position_rationale:
        _ai_context["position_rationale"] = position_rationale
    if decision:
        _ai_context["recent_decisions"].insert(0, {
            "timestamp": int(time.time()),
            "decision": decision
        })
        # Keep only last 10 decisions
        _ai_context["recent_decisions"] = _ai_context["recent_decisions"][:10]
    if confidence is not None:
        _ai_context["confidence"] = confidence
    
    _ai_context["last_update"] = int(time.time())


def get_ai_context() -> Dict[str, Any]:
    """Get current AI thinking context"""
    return _ai_context.copy()
