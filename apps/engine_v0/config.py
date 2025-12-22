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

# AI Configuration - Claude is the default trader
AI_MODEL = os.getenv("AI_MODEL", "claude-sonnet-4-20250514")  # Claude as default
AI_LANGUAGE = os.getenv("AI_LANGUAGE", "english").lower() # 'english' or 'portuguese'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # Kept for dashboard chat only

# External APIs - keys from Railway environment
CMC_API_KEY = os.getenv("CMC_API_KEY", "")  # CoinMarketCap API key from env
CRYPTOPANIC_API_KEY = os.getenv("CRYPTOPANIC_API_KEY", "")

# ============================================================
# 🎯 AI TIMING - Balanced for cost vs reactivity
# ============================================================
AI_CALL_INTERVAL_SECONDS = int(os.getenv("AI_CALL_INTERVAL_SECONDS", "1800"))  # 30 min default (saves ~65% API costs)
LLM_MIN_SECONDS = int(os.getenv("LLM_MIN_SECONDS", "1800"))  # 30 min minimum between AI calls
LLM_STATE_CHANGE_THRESHOLD = float(os.getenv("LLM_STATE_CHANGE_THRESHOLD", "0.5"))  # 0.5% change triggers AI
PRICE_CHANGE_THRESHOLD = float(os.getenv("PRICE_CHANGE_THRESHOLD", "0.5"))  # 0.5% price move triggers AI
VOLATILITY_TRIGGER_PCT = float(os.getenv("VOLATILITY_TRIGGER_PCT", "2.0"))  # Call AI immediately if BTC moves >2%
MAX_ACTIONS_PER_TICK = int(os.getenv("MAX_ACTIONS_PER_TICK", "10"))  # AI can take up to 10 actions per decision
ACTION_DEDUP_SECONDS = int(os.getenv("ACTION_DEDUP_SECONDS", "60"))  # 1 min dedup

# Multi-Symbol Snapshot Configuration
SNAPSHOT_TOP_N = int(os.getenv("SNAPSHOT_TOP_N", "12"))
SNAPSHOT_MODE = os.getenv("SNAPSHOT_MODE", "TOP_N")  # TOP_N | ROTATE | ALL
ROTATE_PER_TICK = int(os.getenv("ROTATE_PER_TICK", "5"))
ALLOW_SYMBOL_NOT_IN_SNAPSHOT = os.getenv("ALLOW_SYMBOL_NOT_IN_SNAPSHOT", "true").lower() == "true"

# ============================================================
# 💰 TRADE SIZING - AI decides sizing, these are just minimums
# ============================================================
MIN_NOTIONAL_USD = float(os.getenv("MIN_NOTIONAL_USD", "15.0"))  # $15 minimum (exchange is $10)
MIN_STOP_LOSS_PCT = float(os.getenv("MIN_STOP_LOSS_PCT", "1.0"))  # Minimum 1% SL distance - INFO for AI, not enforced
AUTO_CAP_LEVERAGE = os.getenv("AUTO_CAP_LEVERAGE", "true").lower() == "true"
ORDER_SLIPPAGE = float(os.getenv("ORDER_SLIPPAGE", "0.01"))  # 1% default slippage for market orders

# Multi-Symbol Controls
ALLOW_SYMBOL_NOT_IN_SNAPSHOT = os.getenv("ALLOW_SYMBOL_NOT_IN_SNAPSHOT", "true").lower() in ("1", "true", "yes", "y", "on")

# Anti-Loop Operational (Intent-based Deduplication)
PLACE_ORDER_DEDUP_SECONDS = int(os.getenv("PLACE_ORDER_DEDUP_SECONDS", "300"))  # 5 min dedup for same order
TRIGGER_DEDUP_SECONDS = int(os.getenv("TRIGGER_DEDUP_SECONDS", "120"))  # 2 min for triggers
MAX_OPEN_ORDERS_PER_SYMBOL = int(os.getenv("MAX_OPEN_ORDERS_PER_SYMBOL", "6"))  # Circuit breaker
MAX_POSITION_ADDS_PER_SYMBOL_PER_HOUR = int(os.getenv("MAX_POSITION_ADDS_PER_SYMBOL_PER_HOUR", "5"))  # Max 5 adds per hour
STATE_INCLUDE_OPEN_ORDERS = os.getenv("STATE_INCLUDE_OPEN_ORDERS", "true").lower() == "true"
STATE_INCLUDE_RECENT_ACTIONS = os.getenv("STATE_INCLUDE_RECENT_ACTIONS", "true").lower() == "true"

# ============================================================
# 🤖 AI AUTONOMY - NO HARD LIMITS on trading decisions
# ============================================================
# The AI is a professional trader. We don't limit:
# - Hold time (market structure can change in seconds)
# - Reentry cooldown (AI may need to flip direction instantly)
# - Position sizing (AI decides based on conviction)
# We only enforce: min notional ($50), min SL (1.5%), dedup (5min same order)

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

# Vision Configuration (multi-timeframe analysis)
VISION_CANDLES_INTERVALS = os.getenv("VISION_CANDLES_INTERVALS", "1m,5m,15m,1h,4h,1d,1w")
VISION_CANDLES_LIMIT = int(os.getenv("VISION_CANDLES_LIMIT", "60"))
VISION_ORDERBOOK_DEPTH = int(os.getenv("VISION_ORDERBOOK_DEPTH", "5"))
VISION_RECENT_FILLS_LIMIT = int(os.getenv("VISION_RECENT_FILLS_LIMIT", "10"))

# Symbol Configuration
SYMBOL_ALLOWLIST = [s.strip() for s in os.getenv("SYMBOL_ALLOWLIST", "").split(",") if s.strip()]

# AI Provider (for future multi-provider support)
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")


def print_config():
    """Print configuration (without secrets)"""
    print(f"[ENV] SYMBOL={SYMBOL}")
    print(f"[ENV] LOOP_INTERVAL_SECONDS={LOOP_INTERVAL_SECONDS}")
    print(f"[ENV] LIVE_TRADING={LIVE_TRADING}")
    print(f"[ENV] AI_ENABLED={AI_ENABLED}")
    print(f"[ENV] AI_MODEL={AI_MODEL} ({AI_PROVIDER})")
    print(f"[ENV] HYPERLIQUID_NETWORK={HYPERLIQUID_NETWORK}")
    print(f"[ENV] ENABLE_TELEGRAM={ENABLE_TELEGRAM}")
    
    # AI settings
    print(f"[ENV] 🎯 AI TUNING:")
    print(f"[ENV]   LLM_MIN_SECONDS={LLM_MIN_SECONDS}s")
    print(f"[ENV]   AI_TEMPERATURE={AI_TEMPERATURE}")
    print(f"[ENV]   PRICE_CHANGE_THRESHOLD={PRICE_CHANGE_THRESHOLD}%")
    print(f"[ENV]   LLM_STATE_CHANGE_THRESHOLD={LLM_STATE_CHANGE_THRESHOLD}%")
    
    # Risk settings
    print(f"[ENV] 💰 RISK & SIZING:")
    print(f"[ENV]   DEFAULT_LEVERAGE={DEFAULT_LEVERAGE}x")
    print(f"[ENV]   MIN_NOTIONAL_USD=${MIN_NOTIONAL_USD}")
    print(f"[ENV]   MARGIN_BUFFER={MARGIN_BUFFER_FACTOR*100}%")
    
    # Operational
    print(f"[ENV] ⚙️ OPERATIONAL:")
    print(f"[ENV]   API_CONCURRENCY={MAX_API_CONCURRENCY}")
    print(f"[ENV]   API_TIMEOUT={API_TIMEOUT_SECONDS}s")
    
    # Validate critical configs
    if HYPERLIQUID_WALLET_ADDRESS:
        print(f"[ENV] HYPERLIQUID_WALLET_ADDRESS=***{HYPERLIQUID_WALLET_ADDRESS[-6:]}")
    if HYPERLIQUID_PRIVATE_KEY:
        print("[ENV] HYPERLIQUID_PRIVATE_KEY=***SET")
    if OPENAI_API_KEY:
        print("[ENV] OPENAI_API_KEY=***SET")
