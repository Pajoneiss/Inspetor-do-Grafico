# Mock Enhanced Trade Log Example
# This shows the structure that llm_client.py should return

example_trade_log = {
    "timestamp": "2025-12-18T14:00:00Z",
    "trade_id": "BTC_LONG_20251218_140000",
    "symbol": "BTC",
    "action": "ENTRY",
    "side": "LONG",
    "entry_price": 104250.00,
    "size": 0.001,
    "leverage": 10,
    
    "strategy": {
        "name": "Breakout + Volume Confirmation",
        "timeframe": "1H",
        "setup_quality": 8.5,
        "confluence_factors": [
            "1H EMA9 > EMA21 (bullish)",
            "Price broke 104k resistance with volume",
            "4H trend aligned (higher highs)",
            "RSI 14 at 62 (healthy momentum)"
        ]
    },
    
    "entry_rationale": "Strong 1H breakout above 104k resistance with 2x average volume. 4H trend confirms bullish structure. Entry on retest of broken resistance now acting as support.",
    
    "risk_management": {
        "stop_loss": 103500.00,
        "stop_loss_reason": "Below recent swing low and broken resistance",
        "risk_usd": 0.75,
        "risk_pct": 0.72,
        
        "take_profit_1": 105000.00,
        "tp1_reason": "Previous swing high resistance",
        "tp1_size_pct": 50,
        
        "take_profit_2": 106500.00,
        "tp2_reason": "1H measured move target",
        "tp2_size_pct": 50,
        
        "breakeven_plan": {
            "enabled": True,
            "trigger": "When TP1 is hit",
            "move_to": 104300.00,
            "reason": "Lock in profit after 50% exit"
        },
        
        "trailing_stop": {
            "enabled": True,
            "activation": "After TP1",
            "distance": "1H ATR (approx $500)",
            "reason": "Let winners run with protection"
        }
    },
    
    "market_context": {
        "fear_greed": 17,
        "btc_dominance": 59.3,
        "trend_1h": "BULLISH",
        "trend_4h": "BULLISH",
        "trend_1d": "NEUTRAL"
    },
    
    "confidence": 0.85,
    "expected_outcome": "Target TP1 within 4-8 hours, TP2 within 12-24 hours if momentum sustains",
    
    "ai_notes": "High probability setup. Market structure is clean. Volume confirms breakout. Will monitor 4H close for continuation."
}
