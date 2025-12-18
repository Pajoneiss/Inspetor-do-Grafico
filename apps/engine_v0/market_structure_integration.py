"""
Market Structure Integration for Main Loop
Add this code to main.py where state is built before LLM call
"""

# Add this import at the top of main.py:
# from market_structure import analyze_market_structure

# Add this code after candles are fetched and before LLM is called:
"""
# Calculate market structure for top symbols
if 'candles_by_symbol' in state:  # If candles are available
    market_structure = {}
    
    for symbol in state.get('snapshot_symbols', [])[:5]:  # Top 5 symbols
        # Get candles for this symbol across timeframes
        symbol_candles = {}
        
        # Collect candles from state (adjust keys based on actual structure)
        for tf in ['1h', '15m', '5m']:
            candle_key = f'{symbol}_{tf}'
            if candle_key in state.get('candles_by_symbol', {}):
                symbol_candles[tf] = state['candles_by_symbol'][candle_key]
        
        # Analyze structure if we have data
        if symbol_candles:
            from market_structure import analyze_market_structure
            market_structure[symbol] = analyze_market_structure(symbol_candles)
    
    # Add to state
    if market_structure:
        state['market_structure'] = market_structure
        print(f"[STRUCTURE] Analyzed {len(market_structure)} symbols")
"""

# SIMPLIFIED VERSION (if candles structure is different):
"""
# Minimal integration - just add empty structure for now
# This ensures prompt doesn't break, actual data will come later
state['market_structure'] = {}
print("[STRUCTURE] Market structure module ready (data pending)")
"""
