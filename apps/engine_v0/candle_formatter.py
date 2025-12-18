# Multi-Timeframe Candle Formatting Module
# v12.0: 7 timeframes for complete micro-to-macro visibility

def format_multi_timeframe_candles(state):
    """
    Format 7 timeframes (1m/5m/15m/1h/4h/1D/1W) for LLM analysis
    Displays in macro→micro order for top-down analysis
    """
    candles_data = state.get("candles_by_symbol", {})
    candles_str = ""
    
    # Timeframe display order (macro to micro for context-first analysis)
    TF_ORDER = ["1w", "1d", "4h", "1h", "15m", "5m", "1m"]
    TF_LABELS = {
        "1w": "MACRO (1 year context)",
        "1d": "TREND (3 months primary)",
        "4h": "SWING+ (1 week intermediate)",
        "1h": "SWING (2 days structure)",
        "15m": "ENTRY (10 hours precision)",
        "5m": "SCALP (5 hours setups)",
        "1m": "MICRO (1 hour confirmation)"
    }
    
    # Show top 3 symbols (token optimization)
    for symbol in list(candles_data.keys())[:3]:
        symbol_candles = candles_data[symbol]
        current_price = state.get("prices", {}).get(symbol, 0)
        
        candles_str += f"\n{'='*60}\n{symbol} @ ${current_price:.2f}\n{'='*60}\n"
        
        for tf in TF_ORDER:
            if tf not in symbol_candles or not symbol_candles[tf]:
                continue
                
            candles = symbol_candles[tf]
            label = TF_LABELS.get(tf, tf)
            
            # Show last N closes based on timeframe
            display_count = {
                "1w": 8,   # Last 8 weeks
                "1d": 12,  # Last 12 days
                "4h": 10,  # Last 40 hours
                "1h": 12,  # Last 12 hours
                "15m": 10, # Last 150 min
                "5m": 8,   # Last 40 min
                "1m": 6    # Last 6 min
            }.get(tf, 10)
            
            recent = candles[-display_count:] if len(candles) >= display_count else candles
            
            # Format closes as progression
            closes_str = " -> ".join([f"{c['close']:.2f}" if tf in ["15m", "5m", "1m"] else f"{c['close']:.0f}" 
                                     for c in recent[-min(display_count, len(recent)):]])
            
            # Calculate H/L from ALL candles (not just displayed)
            high = max(c['high'] for c in candles)
            low = min(c['low'] for c in candles)
            range_str = f"H/L: {high:.2f}/{low:.2f}" if tf in ["15m", "5m", "1m"] else f"H/L: {high:.0f}/{low:.0f}"
            
            candles_str += f"  {label}\n"
            candles_str += f"    {closes_str}\n"
            candles_str += f"    {range_str}\n"
    
    return candles_str
