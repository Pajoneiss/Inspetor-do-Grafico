"""
Reconciler Module
Handles the reconciliation of trade journal state with actual exchange state.
Crucial for capturing passive exits (Stop Loss / Take Profit) that happen directly on the exchange.
"""
import time
from typing import List, Dict, Any

def reconcile_open_trades(hl_client, journal) -> None:
    """
    Check all OPEN trades in the journal.
    If a trade is OPEN in journal but NOT on exchange, it means it hit SL/TP.
    We must find the exit fill and record it to ensure stats are accurate.
    """
    try:
        # Get all OPEN trades from journal
        open_trades = journal.get_all_trades(status="OPEN")
        if not open_trades:
            return

        # Get actual open positions from exchange
        positions = hl_client.get_positions_by_symbol()
        
        # Get recent fills (history) to find exit details
        # We need enough history to cover potential recent closes
        recent_fills = hl_client.get_recent_fills(limit=50)
        
        for trade in open_trades:
            symbol = trade.get("symbol")
            trade_id = trade.get("trade_id")
            
            # 1. Check if position still exists on exchange
            if symbol in positions:
                pos = positions[symbol]
                if abs(float(pos.get("size", 0))) > 0:
                    # Still open, everything is fine
                    continue
            
            # 2. Position is GONE from exchange but OPEN in journal -> IT CLOSED!
            print(f"[RECONCILE] Found zombie trade {symbol} (ID: {trade_id}) - Closed on exchange but open in journal")
            
            # 3. Find the exit fill in recent history
            exit_fill = _find_last_fill(recent_fills, symbol)
            
            if exit_fill:
                exit_price = float(exit_fill.get("px", 0))
                # Determine if SL or TP based on price vs entry
                # This is an approximation since we don't know the exact trigger type from fill
                # But we can infer from profit/loss
                entry_price = trade.get("entry", {}).get("price", 0)
                side = trade.get("side", "LONG")
                
                is_win = False
                if side == "LONG":
                    is_win = exit_price > entry_price
                else:
                    is_win = exit_price < entry_price
                
                # Default reason
                reason = "Take Profit (Reconciled)" if is_win else "Stop Loss (Reconciled)"
                exit_type = "TP" if is_win else "SL"
                
                print(f"[RECONCILE] Found exit fill for {symbol}: price={exit_price} type={exit_type}")
                
                # 4. Record exit in journal
                journal.record_exit(
                    symbol=symbol,
                    exit_price=exit_price,
                    reason=reason,
                    exit_type=exit_type
                )
            else:
                print(f"[RECONCILE][WARN] Could not find exit fill for {symbol}. Closing with current market price fallback.")
                # Fallback: Close at current price if we can't find fill
                # This prevents "stuck" trades forever
                current_price = hl_client.get_last_price(symbol)
                if current_price:
                    journal.record_exit(
                        symbol=symbol,
                        exit_price=current_price,
                        reason="Force Close (Reconciled - No Fill Found)",
                        exit_type="MANUAL"
                    )

    except Exception as e:
        print(f"[RECONCILE][ERROR] Failed to reconcile: {e}")
        import traceback
        traceback.print_exc()

def _find_last_fill(fills: List[Dict], symbol: str) -> Dict:
    """Find the most recent fill for a symbol"""
    if not fills:
        return None
        
    for fill in fills:
        if fill.get("coin") == symbol:
            return fill
    return None
