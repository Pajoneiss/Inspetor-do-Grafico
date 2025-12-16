"""
Data Sources Module for Telegram Summary
Fetches external data with caching and fallbacks.
Never crashes the bot - always returns partial data.
"""
import os
import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

# API Keys (optional)
CRYPTOPANIC_API_KEY = os.environ.get("CRYPTOPANIC_API_KEY", "")
CMC_API_KEY = os.environ.get("CMC_API_KEY", "")

# Cache storage
_cache: Dict[str, Dict[str, Any]] = {}

# TTL settings (seconds)
TTL_NEWS = 300      # 5 minutes
TTL_MACRO = 60      # 1 minute
TTL_MARKET = 60     # 1 minute
TTL_FEAR = 300      # 5 minutes


def _get_cache(key: str) -> Optional[Any]:
    """Get cached value if not expired"""
    if key in _cache:
        entry = _cache[key]
        if time.time() < entry.get("expires", 0):
            return entry.get("data")
    return None


def _set_cache(key: str, data: Any, ttl: int):
    """Set cache with TTL"""
    _cache[key] = {
        "data": data,
        "expires": time.time() + ttl
    }


def fetch_fear_greed() -> Dict[str, Any]:
    """
    Fetch Fear & Greed Index from Alternative.me
    Returns: {"value": 0-100, "classification": "Fear/Greed", "timestamp": ...}
    """
    cache_key = "fear_greed"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    try:
        import httpx
        with httpx.Client(timeout=4.0) as client:
            resp = client.get("https://api.alternative.me/fng/?limit=1")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("data"):
                    fg = data["data"][0]
                    result = {
                        "value": int(fg.get("value", 0)),
                        "classification": fg.get("value_classification", "Unknown"),
                        "timestamp": fg.get("timestamp", "")
                    }
                    _set_cache(cache_key, result, TTL_FEAR)
                    print(f"[NEWS] Fear&Greed fetched: {result['value']} ({result['classification']})")
                    return result
    except Exception as e:
        print(f"[NEWS][WARN] Fear&Greed failed: {e}")
    
    return {"value": "N/A", "classification": "N/A", "timestamp": ""}


def fetch_cryptopanic() -> List[Dict[str, str]]:
    """
    Fetch crypto news headlines from CryptoPanic
    Returns: [{"title": ..., "url": ..., "source": ...}, ...]
    """
    cache_key = "cryptopanic"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    try:
        import httpx
        
        # Use API if key available
        if CRYPTOPANIC_API_KEY:
            url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&public=true&kind=news"
        else:
            # Fallback to public RSS-like endpoint
            url = "https://cryptopanic.com/api/free/v1/posts/?public=true&kind=news"
        
        with httpx.Client(timeout=4.0) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                headlines = []
                for post in data.get("results", [])[:10]:
                    headlines.append({
                        "title": post.get("title", "")[:100],
                        "url": post.get("url", ""),
                        "source": post.get("source", {}).get("title", "Unknown")
                    })
                _set_cache(cache_key, headlines, TTL_NEWS)
                print(f"[NEWS] CryptoPanic fetched: {len(headlines)} headlines")
                return headlines
    except Exception as e:
        print(f"[NEWS][WARN] CryptoPanic failed: {e}")
    
    return []


def fetch_coingecko_global() -> Dict[str, Any]:
    """
    Fetch global market data from CoinGecko (free, no key needed)
    Returns: {"market_cap": ..., "volume": ..., "btc_dominance": ..., "eth_dominance": ...}
    """
    cache_key = "coingecko_global"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    try:
        import httpx
        with httpx.Client(timeout=4.0) as client:
            resp = client.get("https://api.coingecko.com/api/v3/global")
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                result = {
                    "market_cap": data.get("total_market_cap", {}).get("usd", 0),
                    "volume_24h": data.get("total_volume", {}).get("usd", 0),
                    "btc_dominance": data.get("market_cap_percentage", {}).get("btc", 0),
                    "eth_dominance": data.get("market_cap_percentage", {}).get("eth", 0),
                    "market_cap_change_24h": data.get("market_cap_change_percentage_24h_usd", 0)
                }
                _set_cache(cache_key, result, TTL_MARKET)
                print(f"[MARKET] CoinGecko global fetched: BTC dom={result['btc_dominance']:.1f}%")
                return result
    except Exception as e:
        print(f"[MARKET][WARN] CoinGecko failed: {e}")
    
    return {
        "market_cap": "N/A",
        "volume_24h": "N/A",
        "btc_dominance": "N/A",
        "eth_dominance": "N/A",
        "market_cap_change_24h": "N/A"
    }


def fetch_cmc() -> Dict[str, Any]:
    """
    Fetch market data from CoinMarketCap (requires API key)
    Falls back to CoinGecko if no key.
    """
    if not CMC_API_KEY:
        return fetch_coingecko_global()
    
    cache_key = "cmc_global"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    try:
        import httpx
        headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
        with httpx.Client(timeout=4.0, headers=headers) as client:
            resp = client.get("https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest")
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                result = {
                    "market_cap": data.get("quote", {}).get("USD", {}).get("total_market_cap", 0),
                    "volume_24h": data.get("quote", {}).get("USD", {}).get("total_volume_24h", 0),
                    "btc_dominance": data.get("btc_dominance", 0),
                    "eth_dominance": data.get("eth_dominance", 0),
                    "market_cap_change_24h": data.get("quote", {}).get("USD", {}).get("total_market_cap_yesterday_percentage_change", 0)
                }
                _set_cache(cache_key, result, TTL_MARKET)
                print(f"[MARKET] CMC global fetched: BTC dom={result['btc_dominance']:.1f}%")
                return result
    except Exception as e:
        print(f"[MARKET][WARN] CMC failed: {e}, falling back to CoinGecko")
    
    return fetch_coingecko_global()


def fetch_macro() -> Dict[str, Any]:
    """
    Fetch macro indicators: USD/BRL, DXY, S&P500, Nasdaq
    Uses public stooq.com CSV endpoint (free, no key)
    """
    cache_key = "macro"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    result = {
        "usd_brl": "N/A",
        "dxy": "N/A",
        "sp500": "N/A",
        "nasdaq": "N/A",
        "timestamp": datetime.now().isoformat()
    }
    
    # Stooq symbols
    symbols = {
        "usd_brl": "usdbrl",
        "dxy": "dx-y.ny",
        "sp500": "^spx",
        "nasdaq": "^ndq"
    }
    
    try:
        import httpx
        with httpx.Client(timeout=4.0) as client:
            for key, symbol in symbols.items():
                try:
                    # Stooq provides free delayed quotes
                    url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlc"
                    resp = client.get(url)
                    if resp.status_code == 200:
                        # Format: Symbol,Date,Time,Open,High,Low,Close
                        parts = resp.text.strip().split(",")
                        if len(parts) >= 7 and parts[6] != "N/D":
                            result[key] = float(parts[6])
                except Exception:
                    pass
        
        _set_cache(cache_key, result, TTL_MACRO)
        print(f"[MACRO] Fetched: USD/BRL={result['usd_brl']} DXY={result['dxy']}")
    except Exception as e:
        print(f"[MACRO][WARN] Macro fetch failed: {e}")
    
    return result


def get_all_external_data() -> Dict[str, Any]:
    """
    Get all external data sources for Telegram summary.
    Never throws - always returns partial data.
    """
    return {
        "fear_greed": fetch_fear_greed(),
        "news": fetch_cryptopanic(),
        "market": fetch_cmc(),
        "macro": fetch_macro()
    }


def format_external_data_for_telegram(data: Dict[str, Any]) -> str:
    """Format external data as Telegram message section"""
    lines = []
    
    # Fear & Greed
    fg = data.get("fear_greed", {})
    if fg.get("value") != "N/A":
        lines.append(f"😨 *Fear & Greed:* {fg.get('value')} ({fg.get('classification', '?')})")
    
    # Macro
    macro = data.get("macro", {})
    macro_parts = []
    if macro.get("usd_brl") != "N/A":
        macro_parts.append(f"USD/BRL: {macro['usd_brl']:.2f}" if isinstance(macro['usd_brl'], float) else f"USD/BRL: {macro['usd_brl']}")
    if macro.get("dxy") != "N/A":
        macro_parts.append(f"DXY: {macro['dxy']:.1f}" if isinstance(macro['dxy'], float) else f"DXY: {macro['dxy']}")
    if macro.get("sp500") != "N/A":
        macro_parts.append(f"S&P: {macro['sp500']:.0f}" if isinstance(macro['sp500'], float) else f"S&P: {macro['sp500']}")
    if macro_parts:
        lines.append(f"📈 *Macro:* {' | '.join(macro_parts)}")
    
    # Market
    mkt = data.get("market", {})
    if mkt.get("btc_dominance") != "N/A":
        btc_d = mkt['btc_dominance']
        btc_str = f"{btc_d:.1f}%" if isinstance(btc_d, float) else str(btc_d)
        lines.append(f"🌍 *BTC Dom:* {btc_str}")
    
    # News (top 3)
    news = data.get("news", [])
    if news:
        lines.append("\n📰 *Top News:*")
        for n in news[:3]:
            title = n.get("title", "")[:60]
            lines.append(f"  • {title}...")
    
    return "\n".join(lines) if lines else "(dados externos indisponíveis)"


# Aliases for backward compatibility
def get_fear_greed() -> Dict[str, Any]:
    """Alias for fetch_fear_greed"""
    return fetch_fear_greed()


def get_cryptopanic_news() -> Dict[str, Any]:
    """Alias for fetch_cryptopanic with error handling"""
    try:
        headlines = fetch_cryptopanic()
        return {"headlines": headlines}
    except Exception as e:
        return {"error": str(e)}
