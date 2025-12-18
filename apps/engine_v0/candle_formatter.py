# Multi-Timeframe Candle Formatting Module
# This generates the comprehensive candle data string for LLM consumption

def format_multi_timeframe_candles(state):
    """
    Format ALL available candles across all timeframes for complete market structure visibility
    User requirement: See 200 candles minimum to identify structure autonomously
    """
    candles_data = state.get("candles_by_symbol", {})
    candles_str = ""
    
   # Show ALL symbols (not filtered)
    for symbol in candles_data.keys():
        symbol_candles = candles_data[symbol]
        current_price = state.get("prices", {}).get(symbol, 0)
        
        candles_str += f"\n━━━ {symbol} @ ${current_price:.2f} ━━━\n"
        
        # 4H timeframe - Last 30 candles (5 days of trend context)
        if "4h" in symbol_candles and symbol_candles["4h"]:
            c4h = symbol_candles["4h"]
            candles_str += f"  4H ({len(c4h)} bars): "
            # Show last 12 closes for readability
            closes = [f"{c['close']:.0f}" for c in c4h[-12:]]
            candles_str += " → ".join(closes)
            # Full range for structure
            h = max(c['high'] for c in c4h)
            l = min(c['low'] for c in c4h)
            candles_str += f" | H/L: {h:.0f}/{l:.0f}\n"
        
        # 1H timeframe - Last 24 candles (full day intraday structure)
        if "1h" in symbol_candles and symbol_candles["1h"]:
            c1h = symbol_candles["1h"]
            candles_str += f"  1H ({len(c1h)} bars): "
            # Show last 16 closes
            closes = [f"{c['close']:.0f}" for c in c1h[-16:]]
            candles_str += " → ".join(closes)
            # Full range
            h = max(c['high'] for c in c1h)
            l = min(c['low'] for c in c1h)
            candles_str += f" | H/L: {h:.0f}/{l:.0f}\n"
        
        # 15M timeframe - ALL 20 candles (5 hours entry precision)
        if "15m" in symbol_candles and symbol_candles["15m"]:
            c15m = symbol_candles["15m"]
            candles_str += f"  15M ({len(c15m)} bars): "
            # Show ALL candles with full precision
            closes = [f"{c['close']:.2f}" for c in c15m]
            candles_str += " → ".join(closes)
            # Full range with decimals
            h = max(c['high'] for c in c15m)
            l = min(c['low'] for c in c15m)
            candles_str += f" | H/L: {h:.2f}/{l:.2f}\n"
    
    return candles_str
