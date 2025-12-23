
import sys
import os

# Add root and engine path to sys.path to allow imports
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_path)
sys.path.append(os.path.join(root_path, 'apps', 'engine_v0'))

from apps.engine_v0.data_sources import (
    fetch_altcoin_season,
    fetch_eth_gas,
    fetch_cmc_gainers_losers,
    fetch_economic_calendar,
    fetch_funding_rates
)

def run_checks():
    print("=== VERIFYING NEWS TAB DATA ===\n")

    # 1. Altcoin Season
    print("--- Altcoin Season ---")
    try:
        res = fetch_altcoin_season()
        print(f"Result: {res}")
        if res.get("index") > 0 or res.get("blockchaincenter", {}).get("season_index") > 0:
            print("OK - Altcoin Season OK")
        else:
            print("FAIL - Altcoin Season returned 0 (Check scraping)")
    except Exception as e:
        print(f"FAIL - Altcoin Season Failed: {e}")
    print("\n")

    # 2. ETH Gas
    print("--- ETH Gas ---")
    try:
        res = fetch_eth_gas()
        print(f"Result: {res}")
        if res.get("standard") > 0 or res.get("fast") > 0:
            print("OK - ETH Gas OK")
        else:
            print("FAIL - ETH Gas returned 0/None")
    except Exception as e:
        print(f"FAIL - ETH Gas Failed: {e}")
    print("\n")

    # 3. Gainers/Losers
    print("--- Gainers/Losers ---")
    try:
        res = fetch_cmc_gainers_losers()
        gainers = res.get("gainers", [])
        losers = res.get("losers", [])
        print(f"Gainers: {len(gainers)}, Losers: {len(losers)}")
        if gainers:
            print(f"Sample Gainer: {gainers[0]}")
        if losers:
            print(f"Sample Loser: {losers[0]}")
            
        if gainers and losers:
            print("OK - Gainers/Losers OK")
        else:
            print("FAIL - Gainers/Losers Empty (Check API/Fallbacks)")
    except Exception as e:
        print(f"FAIL - Gainers/Losers Failed: {e}")
    print("\n")

    # 4. Economic Calendar
    print("--- Economic Calendar ---")
    try:
        res = fetch_economic_calendar()
        print(f"Events found: {len(res)}")
        if res:
            print(f"Sample Event: {res[0]}")
            if "Unavailable" not in str(res[0].get("event", "")):
                print("OK - Economic Calendar OK")
            else:
                 print("WARN - Economic Calendar returned generic fallback")
        else:
            print("FAIL - Economic Calendar Empty")
    except Exception as e:
        print(f"FAIL - Economic Calendar Failed: {e}")
    print("\n")
    
    # 5. Funding Rates
    print("--- Funding Rates ---")
    try:
        res = fetch_funding_rates()
        rates = res.get("funding_rates", [])
        print(f"Rates found: {len(rates)}")
        if rates:
             print(f"Sample: {rates[0]}")
             print("OK - Funding Rates OK")
        else:
             print("FAIL - Funding Rates Empty")
    except Exception as e:
        print(f"FAIL - Funding Rates Failed: {e}")

if __name__ == "__main__":
    run_checks()
