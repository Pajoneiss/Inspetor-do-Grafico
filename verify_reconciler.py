"""
Verify Reconciler
Simulates a scenario where a trade is OPEN in the journal but CLOSED on the exchange (e.g. hit TP).
Checks if reconciler correctly updates the journal.
"""
import sys
import os
import time

# Add apps path to sys.path
sys.path.append(os.path.join(os.getcwd(), "apps", "engine_v0"))

from reconciler import reconcile_open_trades

# Mock HL Client
class MockHLClient:
    def __init__(self):
        self.positions = {} # Empty means no positions (trade closed)
        self.fills = [
            {
                "coin": "BTC",
                "px": "65000.0", # Exit price
                "sz": "0.1",
                "side": "B", # Bot bought to close short? Or sold to close long?
                "time": time.time() * 1000
            }
        ]
    
    def get_positions_by_symbol(self):
        return self.positions

    def get_recent_fills(self, limit=50):
        return self.fills
        
    def get_last_price(self, symbol):
        return 65000.0

# Mock Journal
class MockJournal:
    def __init__(self):
        self.trades = {
            "trade1": {
                "trade_id": "trade1",
                "symbol": "BTC",
                "status": "OPEN",
                "entry": {
                    "price": 60000.0, # Long from 60k
                    "size": 0.1
                },
                "side": "LONG"
            }
        }
        self.exit_recorded = False
    
    def get_all_trades(self, status=None):
        if status == "OPEN":
            return [t for t in self.trades.values() if t["status"] == "OPEN"]
        return list(self.trades.values())
        
    def record_exit(self, symbol, exit_price, reason, exit_type):
        print(f"[MOCK_JOURNAL] Recording Exit: {symbol} @ {exit_price} ({reason}) [{exit_type}]")
        self.exit_recorded = {
            "symbol": symbol,
            "exit_price": exit_price,
            "reason": reason,
            "exit_type": exit_type
        }
        self.trades["trade1"]["status"] = "CLOSED"

def main():
    print("--- Starting Reconciler Verification ---")
    
    # Setup Mocks
    hl = MockHLClient()
    journal = MockJournal()
    
    print(f"Initial State: {len(journal.get_all_trades('OPEN'))} open trades")
    
    # Run Reconciler
    reconcile_open_trades(hl, journal)
    
    # Check Result
    if journal.exit_recorded:
        print("\n[SUCCESS] Reconciler detected the closed trade!")
        print(f"Details: {journal.exit_recorded}")
    else:
        print("\n[FAIL] Reconciler did NOT record the exit.")

if __name__ == "__main__":
    main()
