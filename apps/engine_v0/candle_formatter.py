# Multi-Timeframe Candle Formatting Module
# v13.0: Enhanced with ATR, better structure info for AI decision making

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
    v13.0: Now includes ATR% for volatility-aware stop placement
    """
    candles_data = state.get("candles_by_symbol", {})
    candles_str = ""
    
    # Get symbols with open positions (prioritize these)
    position_symbols = set(state.get("positions", {}).keys())
    
    # v13.0: Reduced to 5 symbols max to avoid context overload
    # Prioritize: positions first, then top scorers
    all_symbols = list(candles_data.keys())
    prioritized = []
    
    # Add position symbols first
    for sym in all_symbols:
        if sym in position_symbols:
            prioritized.append(sym)
    
    # Add remaining symbols up to limit
    for sym in all_symbols:
        if sym not in prioritized and len(prioritized) < 5:
            prioritized.append(sym)
    
    counts = {sym: len(candles_data.get(sym, {})) for sym in prioritized}
    print(f"[CANDLES] Processing {len(prioritized)} symbols {prioritized} (Charts: {counts})")
    
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
    
    for symbol in prioritized:
        symbol_candles = candles_data[symbol]
        current_price = state.get("prices", {}).get(symbol, 0)
        
        # Show if this symbol has an open position
        has_position = symbol in position_symbols
        pos_marker = " 📍 [POSITION OPEN]" if has_position else ""
        
        candles_str += f"\n{'='*60}\n{symbol} @ ${current_price:.2f}{pos_marker}\n{'='*60}\n"
        
        for tf in TF_ORDER:
            if tf not in symbol_candles or not symbol_candles[tf]:
                continue
                
            candles = symbol_candles[tf]
            label = TF_LABELS.get(tf, tf)
            
            # Show last N closes based on timeframe
            display_count = {
                "1w": 12,  # Last 3 months
                "1d": 30,  # Last month
                "4h": 24,  # Last 4 days
                "1h": 24,  # Last day
                "15m": 20, # Last 5 hours
                "5m": 20,  # Last 1.5 hours
                "1m": 15   # Last 15 min
            }.get(tf, 20)
            
            recent = candles[-display_count:] if len(candles) >= display_count else candles
            
            # SAFETY: Filter out malformed candles
            valid_candles = [c for c in recent if isinstance(c, dict) and 'close' in c and 'high' in c and 'low' in c]
            
            if not valid_candles:
                candles_str += f"  {label}\n    (no valid data)\n"
                continue
            
            # STRUCTURAL ANALYSIS
            trend = identify_trend(candles)
            swing_high, swing_low = find_swing_points(candles)
            
            # Current price position
            current_close = valid_candles[-1]['close'] if valid_candles else current_price
            
            # Calculate H/L from ALL candles (not just displayed)
            high = max(c['high'] for c in candles if isinstance(c, dict) and 'high' in c)
            low = min(c['low'] for c in candles if isinstance(c, dict) and 'low' in c)
            
            # STRUCTURE INFO LINE
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

            # Calculate indicators for this timeframe - NOW WITH ATR%
            try:
                from indicators import calculate_indicators
                ind = calculate_indicators(candles)
                rsi_val = ind.get("rsi_14", 50)
                ema9 = ind.get("ema_9", 0)
                ema21 = ind.get("ema_21", 0)
                trend_val = ind.get("trend", "neutral").upper()
                atr_pct = ind.get("atr_pct", 0)
                macd_hist = ind.get("macd_hist", 0)
                relative_vol = ind.get("relative_volume", 1.0)
                
                # v13.0: Enhanced indicator line with ATR% for stop sizing
                macd_sign = "+" if macd_hist > 0 else "-" if macd_hist < 0 else "0"
                vol_str = f"Vol:{relative_vol:.1f}x" if relative_vol != 1.0 else ""
                
                indicator_str = f"    [Indicators] RSI:{rsi_val:.0f} | EMA9/21:{ema9:.2f}/{ema21:.2f} | ATR%:{atr_pct:.2f}% | MACD:{macd_sign} {vol_str}\n"
            except:
                indicator_str = ""
            
            if indicator_str:
                candles_str += indicator_str

            # Format closes as progression (reduced for clarity)
            closes = [c['close'] for c in valid_candles[-min(10, len(valid_candles)):]]  # Max 10 closes
            closes_str_formatted = []
            for c_val in closes:
                if tf in ["15m", "5m", "1m"]:
                    closes_str_formatted.append(f"{c_val:.2f}")
                else:
                    closes_str_formatted.append(f"{c_val:.0f}")
            closes_str = " → ".join(closes_str_formatted)
            
            candles_str += f"    Closes: {closes_str}\n"
    
    return candles_str
