"""
Engine V0 - Main Loop
Simple trading bot engine with basic loop structure
"""
import time
import sys
from config import (
    LOOP_INTERVAL_SECONDS,
    print_config
)


def main():
    """Main bot loop"""
    print("[BOOT] Engine V0 starting...")
    print_config()
    print("[BOOT] ok")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            print(f"\n[LOOP] tick {iteration}")
            
            # TODO: Add Hyperliquid integration (BLOCO 1)
            # TODO: Add AI decision engine (BLOCO 3)
            # TODO: Add executor (BLOCO 2)
            
            # Sleep until next iteration
            time.sleep(LOOP_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Received interrupt signal")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
