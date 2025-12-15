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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Hyperliquid Configuration
HYPERLIQUID_WALLET_ADDRESS = os.getenv("HYPERLIQUID_WALLET_ADDRESS") or os.getenv("HYPERLIQUID_ACCOUNT_ADDRESS", "")
HYPERLIQUID_PRIVATE_KEY = os.getenv("HYPERLIQUID_PRIVATE_KEY", "")
HYPERLIQUID_NETWORK = os.getenv("HYPERLIQUID_NETWORK", "mainnet")

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ENABLE_TELEGRAM = os.getenv("ENABLE_TELEGRAM", "false").lower() == "true"

# Testing
FORCE_TEST_ORDER = os.getenv("FORCE_TEST_ORDER", "false").lower() == "true"


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
