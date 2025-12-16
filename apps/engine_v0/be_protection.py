"""
BE Protection Module
Stores BE protection state per symbol to prevent LLM from downgrading BE SL.
"""
from typing import Dict, Optional
from datetime import datetime

# Global BE protection state
# Format: {symbol: {"be_target": float, "position_side": str, "set_at": datetime}}
_be_protection: Dict[str, Dict] = {}


def set_be_protection(symbol: str, be_target: float, position_side: str):
    """
    Mark a symbol as BE-protected. The SL should not go below be_target for LONG
    or above be_target for SHORT.
    """
    _be_protection[symbol] = {
        "be_target": be_target,
        "position_side": position_side,
        "set_at": datetime.now()
    }
    print(f"[BE][PROTECT] {symbol} be_target=${be_target:.2f} side={position_side}")


def clear_be_protection(symbol: str):
    """Clear BE protection for a symbol (after position closed)"""
    if symbol in _be_protection:
        del _be_protection[symbol]
        print(f"[BE][PROTECT] Cleared protection for {symbol}")


def get_be_protection(symbol: str) -> Optional[Dict]:
    """Get BE protection for a symbol, or None if not protected"""
    return _be_protection.get(symbol)


def is_sl_worse_than_be(symbol: str, proposed_sl: float) -> bool:
    """
    Check if a proposed SL is worse than the BE target.
    Returns True if the SL would violate BE protection.
    
    For LONG: proposed_sl < be_target is WORSE
    For SHORT: proposed_sl > be_target is WORSE
    """
    protection = _be_protection.get(symbol)
    if not protection:
        return False  # No protection, allow any SL
    
    be_target = protection["be_target"]
    position_side = protection["position_side"]
    
    if position_side == "LONG":
        # For LONG, lower SL is worse
        if proposed_sl < be_target - 1.0:  # Allow $1 tolerance
            print(f"[BE][GATE] BLOCKED {symbol}: proposed SL ${proposed_sl:.2f} < BE target ${be_target:.2f}")
            return True
    else:
        # For SHORT, higher SL is worse
        if proposed_sl > be_target + 1.0:  # Allow $1 tolerance
            print(f"[BE][GATE] BLOCKED {symbol}: proposed SL ${proposed_sl:.2f} > BE target ${be_target:.2f}")
            return True
    
    return False


def get_all_protections() -> Dict[str, Dict]:
    """Get all active BE protections (for debugging)"""
    return _be_protection.copy()
