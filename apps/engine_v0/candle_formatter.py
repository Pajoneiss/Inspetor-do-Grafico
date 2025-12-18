# Multi-Timeframe Candle Formatting Module
# v12.1: 7 timeframes with structural analysis for LLM clarity

def identify_trend(candles):
    """
    Simple trend identification: compare recent vs older price action
    Returns: "UP ↑" / "DOWN ↓" / "SIDEWAYS ↔" / "?"
    """
    if not candles or len(candles) < 10:
        return "?"
    
    # Compare first third vs last third averages
    third = len(candles) // 3
    first_third = [c['close'] for c in candles[:third] if isinstance(c, dict) and 'close' in c]
    last_third = [c['close'] for c in candles[-third:] if isinstance(c, dict) and 'close' in c]
    
    if not first_third or not last_third:
        return "?"
    
    first_avg = sum(first_third) / len(first_third)
    last_avg = sum(last_third) / len(last_third)
    
    diff_pct = ((last_avg - first_avg) / first_avg) * 100
    
    if diff_pct > 1.0:
        return "UP ↑"
    elif diff_pct < -1.0:
        return "DOWN ↓"
    else:
        return "SIDEWAYS ↔"

def find_swing_points(candles):
    """
    Find recent swing high and swing low
    Returns: (swing_high, swing_low) or (None, None)
    """
    if not candles or len(candles) < 5:
        return None, None
    
    valid = [c for c in candles if isinstance(c, dict) and 'high' in c and 'low' in c]
    if not valid:
        return None, None
    
    # Simple swing detection: highest high and lowest low in recent period
    swing_high = max(c['high'] for c in valid[-20:]) if len(valid) >= 20 else max(c['high'] for c in valid)
    swing_low = min(c['low'] for c in valid[-20:]) if len(valid) >= 20 else min(c['low'] for c in valid)
    
    return swing_high, swing_low

def format_multi_timeframe_candles(state):
    """
    Format 7 timeframes (1m/5m/15m/1h/4h/1D/1W) for LLM analysis
    Displays in macro→micro order for top-down analysis
    """
    candles_data = state.get("candles_by_symbol", {})
    candles_str = ""
    
    # DEBUG: Log what we received
    print(f"[CANDLES] Received {len(candles_data)} symbols: {list(candles_data.keys())}")
    for sym in list(candles_data.keys())[:3]:
        tfs = candles_data.get(sym, {})
        print(f"[CANDLES] {sym} has {len(tfs)} timeframes: {list(tfs.keys())}")
        for tf, candles in tfs.items():
            print(f"[CANDLES]   {tf}: {len(candles)} candles")
    
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
            
            # SAFETY: Filter out malformed candles
            valid_candles = [c for c in recent if isinstance(c, dict) and 'close' in c and 'high' in c and 'low' in c]
            
            if not valid_candles:
                candles_str += f"  {label}\n    (no valid data)\n"
                continue
            
            # 🆕 STRUCTURAL ANALYSIS
            trend = identify_trend(candles)
            swing_high, swing_low = find_swing_points(candles)
            
            # Current price position
            current_close = valid_candles[-1]['close'] if valid_candles else current_price
            
            # Format closes as progression
            closes_str = " -> ".join([f"{c['close']:.2f}" if tf in ["15m", "5m", "1m"] else f"{c['close']:.0f}" 
                                     for c in valid_candles[-min(display_count, len(valid_candles)):]])
            
            # Calculate H/L from ALL candles (not just displayed)
            high = max(c['high'] for c in candles if isinstance(c, dict) and 'high' in c)
            low = min(c['low'] for c in candles if isinstance(c, dict) and 'low' in c)
            
            # 🆕 STRUCTURE INFO LINE
            structure_parts = [f"Trend: {trend}"]
            if swing_high and swing_low:
                sh_str = f"{swing_high:.2f}" if tf in ["15m", "5m", "1m"] else f"{swing_high:.0f}"
                sl_str = f"{swing_low:.2f}" if tf in ["15m", "5m", "1m"] else f"{swing_low:.0f}"
                structure_parts.append(f"SwingH: {sh_str}")
                structure_parts.append(f"SwingL: {sl_str}")
                
                # Position in range
                range_pct = ((current_close - swing_low) / (swing_high - swing_low)) * 100 if swing_high > swing_low else 50
                if range_pct > 70:
                    structure_parts.append("📍 Near High")
                elif range_pct < 30:
                    structure_parts.append("📍 Near Low")
                else:
                    structure_parts.append("📍 Mid-Range")
            
            structure_str = " | ".join(structure_parts)
            
            candles_str += f"  {label}\n"
            candles_str += f"    {structure_str}\n"
            candles_str += f"    {closes_str}\n"
    
    return candles_str
