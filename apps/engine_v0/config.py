"""
Configuration loader for Engine V0
Loads environment variables with safe defaults
"""
import os

# Trading Configuration
SYMBOL = os.getenv("SYMBOL", "BTC")
LOOP_INTERVAL_SECONDS = int(os.getenv("LOOP_INTERVAL_SECONDS", "10"))
LIVE_TRADING = os.getenv("LIVE_TRADING", "false").lower() == "true"
AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"

# AI Configuration
AI_MODEL = os.getenv("AI_MODEL") or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
AI_LANGUAGE = os.getenv("AI_LANGUAGE", "english").lower() # 'english' or 'portuguese'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# External APIs
CMC_API_KEY = os.getenv("CMC_API_KEY", "6356c1e6bffd4582bd013608d544225a")  # CoinMarketCap API key
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "")

# ============================================================
# 🔴 ANTI-CHURN: Increased intervals to prevent overtrading
# ============================================================
AI_CALL_INTERVAL_SECONDS = int(os.getenv("AI_CALL_INTERVAL_SECONDS", "900"))  # 15 min (was 300)
LLM_MIN_SECONDS = int(os.getenv("LLM_MIN_SECONDS", "600"))  # 10 min minimum between AI calls (was 180)
LLM_STATE_CHANGE_THRESHOLD = float(os.getenv("LLM_STATE_CHANGE_THRESHOLD", "1.0"))  # 1% change to force call (was 0.5)
MAX_ACTIONS_PER_TICK = int(os.getenv("MAX_ACTIONS_PER_TICK", "3"))  # Reduced from 25
ACTION_DEDUP_SECONDS = int(os.getenv("ACTION_DEDUP_SECONDS", "300"))  # 5 min dedup (was 30)

# ============================================================
# 🔴 ANTI-CHURN: Position Management
# ============================================================
MIN_HOLD_MINUTES = int(os.getenv("MIN_HOLD_MINUTES", "30"))  # NEW: Minimum hold time before closing
REENTRY_COOLDOWN_MINUTES = int(os.getenv("REENTRY_COOLDOWN_MINUTES", "60"))  # NEW: Wait after closing before reopening same symbol

# Multi-Symbol Snapshot Configuration
SNAPSHOT_TOP_N = int(os.getenv("SNAPSHOT_TOP_N", "12"))
SNAPSHOT_MODE = os.getenv("SNAPSHOT_MODE", "TOP_N")  # TOP_N | ROTATE | ALL
ROTATE_PER_TICK = int(os.getenv("ROTATE_PER_TICK", "5"))
ALLOW_SYMBOL_NOT_IN_SNAPSHOT = os.getenv("ALLOW_SYMBOL_NOT_IN_SNAPSHOT", "true").lower() == "true"

# ============================================================
# 🔴 ANTI-CHURN: Trade Sizing - Increased minimums
# ============================================================
MIN_NOTIONAL_USD = float(os.getenv("MIN_NOTIONAL_USD", "25.0"))  # Increased from 10 to 25
MIN_STOP_LOSS_PCT = float(os.getenv("MIN_STOP_LOSS_PCT", "1.5"))  # NEW: Minimum 1.5% SL distance
AUTO_CAP_LEVERAGE = os.getenv("AUTO_CAP_LEVERAGE", "true").lower() == "true"
ORDER_SLIPPAGE = float(os.getenv("ORDER_SLIPPAGE", "0.01"))  # 1% default slippage for market orders

# Multi-Symbol Controls
ALLOW_SYMBOL_NOT_IN_SNAPSHOT = os.getenv("ALLOW_SYMBOL_NOT_IN_SNAPSHOT", "true").lower() in ("1", "true", "yes", "y", "on")

# Anti-Loop Operational (Intent-based Deduplication)
PLACE_ORDER_DEDUP_SECONDS = int(os.getenv("PLACE_ORDER_DEDUP_SECONDS", "300"))  # 5 min (was 60)
TRIGGER_DEDUP_SECONDS = int(os.getenv("TRIGGER_DEDUP_SECONDS", "300"))  # 5 min (was 120)
MAX_OPEN_ORDERS_PER_SYMBOL = int(os.getenv("MAX_OPEN_ORDERS_PER_SYMBOL", "3"))  # Reduced from 6
MAX_POSITION_ADDS_PER_HOUR = int(os.getenv("MAX_POSITION_ADDS_PER_HOUR", "3"))  # Reduced from 12
STATE_INCLUDE_OPEN_ORDERS = os.getenv("STATE_INCLUDE_OPEN_ORDERS", "true").lower() == "true"
STATE_INCLUDE_RECENT_ACTIONS = os.getenv("STATE_INCLUDE_RECENT_ACTIONS", "true").lower() == "true"

# Hyperliquid Configuration
HYPERLIQUID_WALLET_ADDRESS = os.getenv("HYPERLIQUID_WALLET_ADDRESS") or os.getenv("HYPERLIQUID_ACCOUNT_ADDRESS", "")
HYPERLIQUID_PRIVATE_KEY = os.getenv("HYPERLIQUID_PRIVATE_KEY", "")
HYPERLIQUID_NETWORK = os.getenv("HYPERLIQUID_NETWORK", "mainnet")

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ENABLE_TELEGRAM = os.getenv("ENABLE_TELEGRAM", "false").lower() == "true"

# Testing Configuration
FORCE_TEST_ORDER = os.getenv("FORCE_TEST_ORDER", "false").lower() == "true"
TEST_ORDER_SIDE = os.getenv("TEST_ORDER_SIDE", "BUY").upper()
TEST_ORDER_SIZE = float(os.getenv("TEST_ORDER_SIZE", "0.001"))
# TEST_ORDER_SYMBOL will be set to first symbol in SYMBOL list if not specified
TEST_ORDER_SYMBOL = os.getenv("TEST_ORDER_SYMBOL", "")

# Rotation Configuration (disabled by default)
ENABLE_ROTATION = os.getenv("ENABLE_ROTATION", "false").lower() == "true"
ROTATE_MIN_DELTA_SCORE = int(os.getenv("ROTATE_MIN_DELTA_SCORE", "12"))
ROTATE_CONFIRM_TICKS = int(os.getenv("ROTATE_CONFIRM_TICKS", "3"))


def print_config():
    """Print configuration (without secrets)"""
    print(f"[ENV] SYMBOL={SYMBOL}")
    print(f"[ENV] LOOP_INTERVAL_SECONDS={LOOP_INTERVAL_SECONDS}")
    print(f"[ENV] LIVE_TRADING={LIVE_TRADING}")
    print(f"[ENV] AI_ENABLED={AI_ENABLED}")
    print(f"[ENV] AI_MODEL={AI_MODEL}")
    print(f"[ENV] HYPERLIQUID_NETWORK={HYPERLIQUID_NETWORK}")
    print(f"[ENV] ENABLE_TELEGRAM={ENABLE_TELEGRAM}")
    print(f"[ENV] FORCE_TEST_ORDER={FORCE_TEST_ORDER}")
    
    # Anti-churn settings
    print(f"[ENV] 🔴 ANTI-CHURN SETTINGS:")
    print(f"[ENV]   LLM_MIN_SECONDS={LLM_MIN_SECONDS}")
    print(f"[ENV]   AI_CALL_INTERVAL_SECONDS={AI_CALL_INTERVAL_SECONDS}")
    print(f"[ENV]   MIN_NOTIONAL_USD={MIN_NOTIONAL_USD}")
    print(f"[ENV]   MIN_HOLD_MINUTES={MIN_HOLD_MINUTES}")
    print(f"[ENV]   REENTRY_COOLDOWN_MINUTES={REENTRY_COOLDOWN_MINUTES}")
    print(f"[ENV]   MIN_STOP_LOSS_PCT={MIN_STOP_LOSS_PCT}")
    
    if FORCE_TEST_ORDER:
        print(f"[ENV] TEST_ORDER_SIDE={TEST_ORDER_SIDE}")
        print(f"[ENV] TEST_ORDER_SIZE={TEST_ORDER_SIZE}")
        if TEST_ORDER_SYMBOL:
            print(f"[ENV] TEST_ORDER_SYMBOL={TEST_ORDER_SYMBOL}")
    
    # Validate critical configs
    if HYPERLIQUID_WALLET_ADDRESS:
        print(f"[ENV] HYPERLIQUID_WALLET_ADDRESS=***{HYPERLIQUID_WALLET_ADDRESS[-6:]}")
    else:
        print("[ENV] HYPERLIQUID_WALLET_ADDRESS=NOT_SET")
    
    if HYPERLIQUID_PRIVATE_KEY:
        print("[ENV] HYPERLIQUID_PRIVATE_KEY=***SET")
    else:
        print("[ENV] HYPERLIQUID_PRIVATE_KEY=NOT_SET")
    
    if OPENAI_API_KEY:
        print("[ENV] OPENAI_API_KEY=***SET")
    else:
        print("[ENV] OPENAI_API_KEY=NOT_SET")
