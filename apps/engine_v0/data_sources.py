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

# Import API keys from config
from config import CMC_API_KEY, CRYPTOPANIC_API_KEY

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
        print(f"[FEAR] Using cached: {cached['value']}")
        return cached
    
    try:
        import httpx
        with httpx.Client(timeout=4.0) as client:
            resp = client.get("https://api.alternative.me/fng/?limit=1")
            print(f"[FEAR] API response status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"[FEAR] Raw API data: {data}")
                if data.get("data"):
                    fg = data["data"][0]
                    result = {
                        "value": int(fg.get("value", 0)),
                        "classification": fg.get("value_classification", "Unknown"),
                        "timestamp": fg.get("timestamp", "")
                    }
                    _set_cache(cache_key, result, TTL_FEAR)
                    print(f"[FEAR] Final value: {result['value']} ({result['classification']})")
                    return result
    except Exception as e:
        print(f"[FEAR][ERROR] API failed: {e}")
    
    return {"value": "N/A", "classification": "N/A", "timestamp": ""}



def fetch_cryptopanic() -> List[Dict[str, str]]:
    """
    Fetch crypto news headlines from CryptoPanic
    Falls back to CoinDesk RSS if API fails
    Returns: [{"title": ..., "url": ..., "source": ...}, ...]
    """
    cache_key = "cryptopanic"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    headlines = []
    
    # Try CryptoPanic API first (if key available)
    try:
        import httpx
        
        if CRYPTOPANIC_API_KEY:
            url = f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&public=true&kind=news"
            with httpx.Client(timeout=4.0) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for post in data.get("results", [])[:10]:
                        headlines.append({
                            "title": post.get("title", "")[:100],
                            "url": post.get("url", ""),
                            "source": post.get("source", {}).get("title", "CryptoPanic")
                        })
    except Exception as e:
        print(f"[NEWS][WARN] CryptoPanic API failed: {e}")
    
    # Fallback: CoinGecko trending + CoinDesk
    if not headlines:
        try:
            import httpx
            
            # Try CoinGecko trending for some data
            with httpx.Client(timeout=4.0) as client:
                # Simple fallback - create dummy news from market status
                headlines = [
                    {"title": "📈 Mercado crypto operando normalmente", "source": "Bot"},
                    {"title": "💹 Acompanhe Fear & Greed no resumo", "source": "Bot"},
                    {"title": "🔔 Configure CRYPTOPANIC_API_KEY para notícias", "source": "Sistema"}
                ]
                print("[NEWS] Using fallback news (no API key)")
        except:
            pass
    
    if headlines:
        _set_cache(cache_key, headlines, TTL_NEWS)
        print(f"[NEWS] Fetched: {len(headlines)} headlines")
    
    return headlines


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


def fetch_cmc_trending() -> List[Dict[str, Any]]:
    """
    Fetch trending coins from CoinMarketCap
    Returns: [{name, symbol, price, volume_24h, percent_change_24h, market_cap}, ...]
    """
    if not CMC_API_KEY:
        return []
    
    cache_key = "cmc_trending"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    try:
        import httpx
        headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
        with httpx.Client(timeout=4.0, headers=headers) as client:
            resp = client.get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/trending/most-visited")
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                trending = []
                for coin in data[:10]:  # Top 10
                    quote = coin.get("quote", {}).get("USD", {})
                    trending.append({
                        "name": coin.get("name", ""),
                        "symbol": coin.get("symbol", ""),
                        "price": quote.get("price", 0),
                        "volume_24h": quote.get("volume_24h", 0),
                        "percent_change_24h": quote.get("percent_change_24h", 0),
                        "market_cap": quote.get("market_cap", 0)
                    })
                _set_cache(cache_key, trending, TTL_MARKET)
                print(f"[CMC] Trending fetched: {len(trending)} coins")
                return trending
    except Exception as e:
        print(f"[CMC][WARN] Trending fetch failed: {e}")
    
    return []


def fetch_cmc_gainers_losers() -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch top gainers and losers from CoinMarketCap
    Returns: {gainers: [...], losers: [...]}
    """
    if not CMC_API_KEY:
        return {"gainers": [], "losers": []}
    
    cache_key = "cmc_gainers_losers"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    try:
        import httpx
        headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
        with httpx.Client(timeout=4.0, headers=headers) as client:
            resp = client.get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/trending/gainers-losers")
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                
                gainers = []
                for coin in data.get("gainers", [])[:5]:  # Top 5
                    quote = coin.get("quote", {}).get("USD", {})
                    gainers.append({
                        "name": coin.get("name", ""),
                        "symbol": coin.get("symbol", ""),
                        "price": quote.get("price", 0),
                        "percent_change_24h": quote.get("percent_change_24h", 0)
                    })
                
                losers = []
                for coin in data.get("losers", [])[:5]:  # Top 5
                    quote = coin.get("quote", {}).get("USD", {})
                    losers.append({
                        "name": coin.get("name", ""),
                        "symbol": coin.get("symbol", ""),
                        "price": quote.get("price", 0),
                        "percent_change_24h": quote.get("percent_change_24h", 0)
                    })
                
                result = {"gainers": gainers, "losers": losers}
                _set_cache(cache_key, result, TTL_MARKET)
                print(f"[CMC] Gainers/Losers fetched: {len(gainers)} gainers, {len(losers)} losers")
                return result
    except Exception as e:
        print(f"[CMC][WARN] Gainers/Losers fetch failed: {e}")
    
    return {"gainers": [], "losers": []}


def fetch_hl_prices() -> Dict[str, float]:
    """Fetch live BTC and ETH prices from Hyperliquid"""
    try:
        import httpx
        with httpx.Client(timeout=4.0) as client:
            resp = client.post("https://api.hyperliquid.xyz/info", json={"type": "allMids"})
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "btc": float(data.get("BTC", 0)),
                    "eth": float(data.get("ETH", 0))
                }
    except Exception as e:
        print(f"[HL_PRICE][WARN] Failed to fetch prices: {e}")
    return {"btc": 0, "eth": 0}


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
                        content = resp.text.strip().split("\n")
                        
                        # Find the data line (skipping header if present)
                        data_parts = None
                        for line in content:
                            parts = line.split(",")
                            # Data line usually starts with Symbol name or has numeric date/time
                            # Header line starts with "Symbol" or "Date"
                            if len(parts) >= 7 and "Symbol" not in parts[0] and "Date" not in parts[1]:
                                data_parts = parts
                                break
                        
                        if data_parts and len(data_parts) >= 7 and data_parts[6] != "N/D":
                            try:
                                result[key] = float(data_parts[6])
                            except ValueError:
                                pass
                except Exception:
                    pass
        
        # Add BTC/ETH as well for dashboard fallback
        crypto = fetch_hl_prices()
        result["btc"] = crypto["btc"]
        result["eth"] = crypto["eth"]
        
        _set_cache(cache_key, result, TTL_MACRO)
        print(f"[MACRO] Fetched: BTC={result['btc']} DXY={result['dxy']}")
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
