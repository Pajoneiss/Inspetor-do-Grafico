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
from config import CMC_API_KEY, CRYPTOPANIC_API_KEY, FMP_API_KEY, API_TIMEOUT_SECONDS

# Cache storage
_cache: Dict[str, Dict[str, Any]] = {}

# TTL settings (seconds)
TTL_NEWS = 300      # 5 minutes (Real-time)
TTL_NEWS_DELAYED = 86400 # 24 hours (CryptoPanic)
TTL_MACRO = 60      # 1 minute
TTL_MARKET = 60     # 1 minute
TTL_FEAR = 300      # 5 minutes
TTL_CALENDAR = 86400 # 24 hours (FMP)


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
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
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



def fetch_cryptocompare() -> List[Dict[str, str]]:
    """
    Fetch real-time crypto news from CryptoCompare (Truly Free)
    Returns: [{"title": ..., "url": ..., "source": ...}, ...]
    """
    cache_key = "cryptocompare_news"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    headlines = []
    try:
        import httpx
        # No key strictly required for this endpoint on some tiers, but good practice
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for post in data.get("Data", [])[:20]:
                    headlines.append({
                        "title": post.get("title", "")[:120],
                        "url": post.get("url", ""),
                        "source": post.get("source_info", {}).get("name", "CryptoCompare"),
                        "published_at": datetime.fromtimestamp(post.get("published_on", 0)).isoformat(),
                        "kind": "news"
                    })
    except Exception as e:
        print(f"[NEWS][WARN] CryptoCompare failed: {e}")
    
    if headlines:
        _set_cache(cache_key, headlines, TTL_NEWS)
    return headlines


def fetch_cryptopanic() -> List[Dict[str, str]]:
    """
    Fetch crypto news headlines. 
    Primary: CryptoCompare (Real-time). 
    Secondary: CryptoPanic (Delayed 24h on free tier).
    """
    cache_key = "cryptopanic_trending"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    headlines = []
    # Try CryptoPanic API if key available
    try:
        import httpx
        if CRYPTOPANIC_API_KEY:
            url = f"https://cryptopanic.com/api/free/v1/posts/?auth_token={CRYPTOPANIC_API_KEY}&filter=rising&public=true"
            with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    for post in data.get("results", [])[:15]:
                        headlines.append({
                            "title": post.get("title", "")[:120],
                            "url": post.get("url", ""),
                            "source": post.get("source", {}).get("title", "CryptoPanic"),
                            "published_at": post.get("published_at", ""),
                            "kind": "trending"
                        })
    except Exception as e:
        print(f"[NEWS][WARN] CryptoPanic fallback failed: {e}")
    
    if not headlines:
        headlines = [
            {"title": "📈 Mercado crypto operando normalmente", "source": "Bot", "kind": "trending"},
            {"title": "💹 Acompanhe Fear & Greed no resumo", "source": "Bot", "kind": "trending"}
        ]
    
    if headlines:
        _set_cache(cache_key, headlines, TTL_NEWS_DELAYED)
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
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
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
        with httpx.Client(timeout=API_TIMEOUT_SECONDS, headers=headers) as client:
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
                # Also get fear & greed
                fear_data = fetch_fear_greed()
                result["fear_greed"] = fear_data.get("value")
                
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
        with httpx.Client(timeout=API_TIMEOUT_SECONDS, headers=headers) as client:
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
    Fetch top gainers and losers. 
    Falls back to CoinGecko trending/movers if CMC key is missing or fails.
    """
    if not CMC_API_KEY:
        return fetch_binance_movers()
    
    cache_key = "cmc_gainers_losers"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    try:
        import httpx
        headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
        with httpx.Client(timeout=API_TIMEOUT_SECONDS, headers=headers) as client:
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
        print(f"[CMC][WARN] Gainers/Losers fetch failed: {e}, falling back to Binance")
        return fetch_binance_movers()

def fetch_binance_movers() -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch top gainers and losers from Binance Futures (Highly Reliable)
    """
    try:
        import httpx
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                # Sort by priceChangePercent
                sorted_data = sorted(data, key=lambda x: float(x.get("priceChangePercent", 0)), reverse=True)
                
                gainers = []
                for c in sorted_data[:5]:
                    symbol = c.get("symbol", "").replace("USDT", "")
                    if symbol in ["USDC", "FDUSD", "TUSD", "USDP"]: continue
                    gainers.append({
                        "name": symbol,
                        "symbol": symbol,
                        "price": float(c.get("lastPrice", 0)),
                        "percent_change_24h": float(c.get("priceChangePercent", 0))
                    })
                
                losers = []
                for c in reversed(sorted_data):
                    symbol = c.get("symbol", "").replace("USDT", "")
                    if symbol in ["USDC", "FDUSD", "TUSD", "USDP"]: continue
                    losers.append({
                        "name": symbol,
                        "symbol": symbol,
                        "price": float(c.get("lastPrice", 0)),
                        "percent_change_24h": float(c.get("priceChangePercent", 0))
                    })
                    if len(losers) >= 5: break
                
                return {"gainers": gainers, "losers": losers}
    except Exception as e:
        print(f"[BINANCE_MOVERS][WARN] Failed: {e}")
    
    return fetch_coingecko_movers()


def fetch_hl_prices() -> Dict[str, float]:
    """Fetch live BTC and ETH prices from Hyperliquid"""
    try:
        import httpx
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
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
    NOW WITH CHANGE %
    """
    cache_key = "macro"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    result = {
        "usd_brl": "N/A",
        "dxy": "N/A",
        "sp500": "N/A",
        "sp500_change": 0,  # NEW
        "nasdaq": "N/A",
        "nasdaq_change": 0,  # NEW
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
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            for key, symbol in symbols.items():
                try:
                    # Stooq provides free delayed quotes
                    url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlc"
                    resp = client.get(url)
                    if resp.status_code == 200:
                        # Format: Symbol,Date,Time,Open,High,Low,Close
                        content = resp.text.strip().split("\n")
                        
                        # Find the data line
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
                                close = float(data_parts[6])
                                open_price = float(data_parts[3]) if data_parts[3] != "N/D" else close
                                
                                result[key] = close
                                
                                # Calculate % change from open (NEW)
                                if key in ["sp500", "nasdaq"] and open_price > 0:
                                    change_pct = ((close - open_price) / open_price) * 100
                                    result[f"{key}_change"] = round(change_pct, 2)
                                
                            except ValueError:
                                pass
                except Exception:
                    pass
        
        # Add BTC/ETH as well for dashboard fallback
        crypto = fetch_hl_prices()
        result["btc"] = crypto["btc"]
        result["eth"] = crypto["eth"]
        
        _set_cache(cache_key, result, TTL_MACRO)
        print(f"[MACRO] Fetched: BTC={result['btc']} SP500={result['sp500']} ({result['sp500_change']:+.2f}%) NASDAQ={result['nasdaq']} ({result['nasdaq_change']:+.2f}%)")
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


def fetch_fmp_economic_calendar(days_ahead: int = 7) -> List[Dict[str, Any]]:
    """
    Fetch economic events from Financial Modeling Prep (Truly Free tier)
    """
    cache_key = "fmp_calendar"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    events = []
    if not FMP_API_KEY:
        print("[CALENDAR][WARN] FMP_API_KEY not configured")
        return []

    try:
        import httpx
        from datetime import datetime, timedelta
        
        today = datetime.now()
        end_date = today + timedelta(days=days_ahead)
        
        from_date = today.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        url = f"https://financialmodelingprep.com/api/v3/economic_calendar?from={from_date}&to={to_date}&apikey={FMP_API_KEY}"
        
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for item in data:
                    # Filter for relevance (US events or High impact)
                    # Use case-insensitive check for impact
                    impact = str(item.get("impact", "Low")).lower()
                    country = str(item.get("country", "")).upper()
                    
                    if country == "US" or impact == "high":
                        events.append({
                            "date": item.get("date", "").split(" ")[0],
                            "time": item.get("date", "").split(" ")[1] if " " in item.get("date", "") else "TBD",
                            "event": item.get("event", ""),
                            "country": country,
                            "importance": impact.upper(),
                            "actual": item.get("actual"),
                            "estimate": item.get("estimate"),
                            "previous": item.get("previous"),
                            "impact": impact
                        })
                # Sort by date
                events.sort(key=lambda x: x["date"])
                _set_cache(cache_key, events, ttl=TTL_CALENDAR) # 24h
    except Exception as e:
        print(f"[CALENDAR][WARN] FMP failed: {e}")
    
    return events


def fetch_investing_economic_calendar(days_ahead: int = 7) -> List[Dict[str, Any]]:
    """
    Fetch economic calendar from Investing.com (free, no API key needed)
    """
    cache_key = f"economic_calendar_{days_ahead}d"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    events = []
    try:
        import httpx
        from datetime import datetime, timedelta
        
        # Investing.com economic calendar URL (public data)
        url = "https://www.investing.com/economic-calendar/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        with httpx.Client(timeout=API_TIMEOUT_SECONDS, headers=headers, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                # Simple parsing - look for high impact events
                # This is a basic implementation, could be improved with BeautifulSoup
                content = resp.text
                
                # For now, return a placeholder message
                events.append({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time": "TBD",
                    "event": "Economic Calendar - Free API Integration",
                    "country": "US",
                    "importance": "INFO",
                    "actual": None,
                    "estimate": None,
                    "previous": None,
                    "impact": "info"
                })
                
                _set_cache(cache_key, events, ttl=TTL_CALENDAR)
    except Exception as e:
        print(f"[CALENDAR][WARN] Investing.com failed: {e}")
    
    return events


def fetch_economic_calendar(days_ahead: int = 7) -> List[Dict[str, Any]]:
    """
    Fetch upcoming high-impact economic events.
    Prioritizes FMP (Financial Modeling Prep) if API key is present.
    """
    if FMP_API_KEY:
        events = fetch_fmp_economic_calendar(days_ahead)
        if events:
            return events

    # Fallback to Investing.com scraper/parser
    events = fetch_investing_economic_calendar(days_ahead)
    if events:
        return events
        
    # Final Fallback message
    return [
        {
            "date": "TBD",
            "time": "TBD",
            "event": "Economic Calendar - Awaiting Data Sync",
            "country": "US",
            "importance": "INFO",
            "actual": None,
            "estimate": None,
            "previous": None,
            "impact": "low"
        }
    ]


def format_economic_calendar(events: List[Dict[str, Any]], max_events: int = 5) -> str:
    """Format economic calendar for Telegram/Dashboard display"""
    if not events or (len(events) == 1 and "Unavailable" in events[0]["event"]):
        return "(Calendário econômico indisponível)"
    
    lines = []
    for event in events[:max_events]:
        date_str = event.get("date", "TBD")
        time_str = event.get("time", "TBD")
        name = event.get("event", "Unknown")
        estimate = event.get("estimate")
        previous = event.get("previous")
        
        # Format importance stars
        stars = "🔴🔴🔴" if event.get("importance") == "HIGH" else "🟡🟡"
        
        # Format date (convert YYYY-MM-DD to DD/MM)
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_display = date_obj.strftime("%d/%m")
        except:
            date_display = date_str
        
        line = f"{stars} {date_display} {time_str} - {name}"
        
        # Add forecast if available
        if estimate or previous:
            details = []
            if estimate:
                details.append(f"Prev: {estimate}")
            if previous:
                details.append(f"Ant: {previous}")
            line += f"\n       {' | '.join(details)}"
        
        lines.append(line)
    
    return "\n".join(lines) if lines else "(sem eventos próximos)"


def fetch_coingecko_movers() -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch trending/movers from CoinGecko (free alternative)
    """
    try:
        import httpx
        # v15.1: Use markets endpoint for real gainers/losers if trending is not enough
        # But markets with sorting is better for gainers/losers
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=price_change_percentage_24h_desc&per_page=50&page=1&sparkline=false"
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                # Gainers are first 5, Losers are last 5 of the top 50 (or sorted)
                # Let's just get top 50 and pick
                sorted_data = sorted(data, key=lambda x: x.get("price_change_percentage_24h") or 0, reverse=True)
                
                gainers = []
                for c in sorted_data[:5]:
                    gainers.append({
                        "name": c.get("name", ""),
                        "symbol": (c.get("symbol", "")).upper(),
                        "price": c.get("current_price", 0),
                        "percent_change_24h": c.get("price_change_percentage_24h", 0)
                    })
                
                losers = []
                for c in sorted_data[-5:]:
                    losers.append({
                        "name": c.get("name", ""),
                        "symbol": (c.get("symbol", "")).upper(),
                        "price": c.get("current_price", 0),
                        "percent_change_24h": c.get("price_change_percentage_24h", 0)
                    })
                return {"gainers": gainers, "losers": losers}
    except Exception as e:
        print(f"[MOVERS][WARN] CoinGecko failed: {e}")
    
    return {"gainers": [], "losers": []}


def fetch_coingecko_trending() -> List[Dict[str, Any]]:
    """
    Fetch trending coins from CoinGecko (100% Free, No API Key)
    Returns: [{"name": ..., "symbol": ..., "market_cap_rank": ...}, ...]
    """
    cache_key = "coingecko_trending"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    try:
        import httpx
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get("https://api.coingecko.com/api/v3/search/trending")
            if resp.status_code == 200:
                data = resp.json()
                trending = []
                for item in data.get("coins", [])[:7]:  # Top 7
                    coin = item.get("item", {})
                    trending.append({
                        "name": coin.get("name", ""),
                        "symbol": coin.get("symbol", "").upper(),
                        "market_cap_rank": coin.get("market_cap_rank", 0),
                        "price_btc": coin.get("price_btc", 0)
                    })
                _set_cache(cache_key, trending, TTL_MARKET)
                return trending
    except Exception as e:
        print(f"[TRENDING][WARN] CoinGecko trending failed: {e}")
    
    return []


def fetch_defillama_tvl() -> Dict[str, Any]:
    """
    Fetch Total Value Locked from DefiLlama (100% Free, No API Key)
    Returns: {"total_tvl": float, "chains": [...]}
    """
    cache_key = "defillama_tvl"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    try:
        import httpx
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get("https://api.llama.fi/v2/chains")
            if resp.status_code == 200:
                chains = resp.json()
                total_tvl = sum(chain.get("tvl", 0) for chain in chains)
                result = {
                    "total_tvl": total_tvl,
                    "top_chains": sorted(chains, key=lambda x: x.get("tvl", 0), reverse=True)[:5]
                }
                _set_cache(cache_key, result, TTL_MARKET)
                return result
    except Exception as e:
        print(f"[TVL][WARN] DefiLlama failed: {e}")
    
    return {"total_tvl": 0, "top_chains": []}


def fetch_binance_funding_rate() -> Dict[str, Any]:
    """
    Fetch BTC funding rate from Binance Futures (100% Free, No API Key)
    Returns: {"symbol": "BTCUSDT", "funding_rate": float, "next_funding_time": int}
    """
    cache_key = "binance_funding"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    try:
        import httpx
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get("https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1")
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    result = {
                        "symbol": data[0].get("symbol", "BTCUSDT"),
                        "funding_rate": float(data[0].get("fundingRate", 0)) * 100,  # Convert to percentage
                        "funding_time": data[0].get("fundingTime", 0)
                    }
                    _set_cache(cache_key, result, TTL_MARKET)
                    return result
    except Exception as e:
        print(f"[FUNDING][WARN] Binance funding rate failed: {e}")
    
    return {"symbol": "BTCUSDT", "funding_rate": 0, "funding_time": 0}


def fetch_binance_long_short_ratio() -> Dict[str, Any]:
    """
    Fetch BTC Long/Short ratio from Binance (100% Free, No API Key)
    Returns: {"symbol": "BTCUSDT", "long_short_ratio": float, "long_account": float, "short_account": float}
    """
    cache_key = "binance_long_short"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    try:
        import httpx
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get("https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol=BTCUSDT&period=1d&limit=1")
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    result = {
                        "symbol": data[0].get("symbol", "BTCUSDT"),
                        "long_short_ratio": float(data[0].get("longShortRatio", 0)),
                        "long_account": float(data[0].get("longAccount", 0)) * 100,  # Convert to percentage
                        "short_account": float(data[0].get("shortAccount", 0)) * 100,  # Convert to percentage
                        "timestamp": data[0].get("timestamp", 0)
                    }
                    _set_cache(cache_key, result, TTL_MARKET)
                    return result
    except Exception as e:
        print(f"[LONG_SHORT][WARN] Binance long/short ratio failed: {e}")
    
    return {"symbol": "BTCUSDT", "long_short_ratio": 0, "long_account": 0, "short_account": 0, "timestamp": 0}


# Aliases for backward compatibility
def get_fear_greed() -> Dict[str, Any]:
    """Alias for fetch_fear_greed"""
    return fetch_fear_greed()


def get_cryptopanic_news() -> Dict[str, Any]:
    """Dual feed: CryptoCompare (Real-time) + CryptoPanic (Trending)"""
    try:
        realtime = fetch_cryptocompare()
        trending = fetch_cryptopanic()
        return {
            "realtime": realtime,
            "trending": trending
        }
    except Exception as e:
        return {"error": str(e), "realtime": [], "trending": []}


# ================== NEW FEATURES - Free APIs ==================

def fetch_bitcoin_halving() -> Dict[str, Any]:
    """
    Fetch Bitcoin halving countdown data
    API: Blockchain.com (free, no key)
    """
    cache_key = "btc_halving"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    result = {
        "current_block": 0,
        "halving_block": 1050000,
        "blocks_remaining": 0,
        "days_remaining": 0,
        "percent_complete": 0,
        "error": None
    }
    
    try:
        import httpx
        url = "https://blockchain.info/q/getblockcount"
        
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                current_block = int(resp.text.strip())
                next_halving_block = 1050000
                blocks_remaining = next_halving_block - current_block
                days_remaining = (blocks_remaining * 10) / (60 * 24)
                
                # Estimated date
                from datetime import datetime, timedelta
                est_date = datetime.now() + timedelta(days=days_remaining)
                
                result = {
                    "current_block": current_block,
                    "halving_block": next_halving_block,
                    "blocks_remaining": max(0, blocks_remaining),
                    "days_remaining": max(0, round(days_remaining)),
                    "days_until_halving": max(0, round(days_remaining)),
                    "halving_date": est_date.strftime("%b %Y"),
                    "next_halving_date": est_date.strftime("%b %Y"),
                    "percent_complete": round((current_block % 210000) / 210000 * 100, 1),
                    "error": None
                }
                _set_cache(cache_key, result, TTL_MARKET * 10)
    except Exception as e:
        print(f"[HALVING][WARN] Failed: {e}")
        result["error"] = str(e)
    
    return result


def fetch_defi_tvl() -> Dict[str, Any]:
    """Fetch DeFi TVL from DefiLlama (free, no key)"""
    cache_key = "defi_tvl"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    result = {"total_tvl": 0, "total_tvl_formatted": "$0", "chains": {}, "error": None}
    
    try:
        import httpx
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get("https://api.llama.fi/v2/chains")
            if resp.status_code == 200:
                data = resp.json()
                total_tvl = sum(c.get("tvl", 0) for c in data)
                top_chains = sorted(data, key=lambda x: x.get("tvl", 0), reverse=True)[:5]
                chains = {c["name"]: round(c.get("tvl", 0) / 1e9, 2) for c in top_chains}
                
                result = {
                    "total_tvl": total_tvl,
                    "total_tvl_formatted": f"${total_tvl / 1e9:.2f}B",
                    "chains": chains,
                    "error": None
                }
                _set_cache(cache_key, result, TTL_MARKET * 5)
    except Exception as e:
        print(f"[TVL][WARN] Failed: {e}")
        result["error"] = str(e)
    
    return result


def fetch_funding_rates() -> Dict[str, Any]:
    """Fetch funding rates from Binance (free, no key)"""
    cache_key = "funding_rates"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    result = {"rates": {}, "average": 0, "sentiment": "neutral", "error": None}
    
    try:
        import httpx
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"]
        
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get("https://fapi.binance.com/fapi/v1/premiumIndex")
            if resp.status_code == 200:
                data = resp.json()
                rates = {}
                rates_list = []
                total_rate, count = 0, 0
                
                for item in data:
                    symbol = item.get("symbol", "")
                    if symbol in symbols:
                        rate = float(item.get("lastFundingRate", 0))
                        # Format for frontend: symbol and rate as string/float
                        rates_list.append({
                            "symbol": symbol.replace("USDT", ""),
                            "lastFundingRate": str(rate)
                        })
                        rates[symbol.replace("USDT", "")] = round(rate * 100, 4)
                        total_rate += (rate * 100)
                        count += 1
                
                # Sort by funding rate descending (highest to lowest) to show interesting ones
                rates_list.sort(key=lambda x: float(x["lastFundingRate"]), reverse=True)

                avg_rate = total_rate / count if count > 0 else 0
                sentiment = "bullish" if avg_rate > 0.05 else "bearish" if avg_rate < -0.05 else "neutral"
                
                result = {"rates": rates, "funding_rates": rates_list, "average": round(avg_rate, 4), "sentiment": sentiment, "error": None}
                _set_cache(cache_key, result, TTL_MARKET * 5)
    except Exception as e:
        print(f"[FUNDING][WARN] Failed: {e}")
        result["error"] = str(e)
    
    return result


def fetch_long_short_ratio() -> Dict[str, Any]:
    """Fetch Long/Short ratio from Binance (free, no key)"""
    cache_key = "long_short_ratio"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    result = {"ratios": {}, "global_ratio": [], "btc_ratio": 1.0, "sentiment": "neutral", "error": None}
    
    try:
        import httpx
        ratios = {}
        global_ratio_list = []
        
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            for symbol in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
                url = f"https://fapi.binance.com/futures/data/globalLongShortAccountRatio?symbol={symbol}&period=1h&limit=1"
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    if data:
                        item = data[0]
                        ratio = float(item.get("longShortRatio", 1.0))
                        clean_symbol = symbol.replace("USDT", "")
                        ratios[clean_symbol] = round(ratio, 2)
                        
                        global_ratio_list.append({
                            "symbol": clean_symbol,
                            "longShortRatio": str(ratio),
                            "longAccount": item.get("longAccount", "0.5"),
                            "shortAccount": item.get("shortAccount", "0.5")
                        })
        
        btc_ratio = ratios.get("BTC", 1.0)
        if btc_ratio > 1.5:
            sentiment = "very_long"
        elif btc_ratio > 1.1:
            sentiment = "long"
        elif btc_ratio < 0.67:
            sentiment = "very_short"
        elif btc_ratio < 0.9:
            sentiment = "short"
        else:
            sentiment = "neutral"
        
        result = {"ratios": ratios, "global_ratio": global_ratio_list, "btc_ratio": btc_ratio, "sentiment": sentiment, "error": None}
        _set_cache(cache_key, result, TTL_MARKET * 5)
    except Exception as e:
        print(f"[L/S][WARN] Failed: {e}")
        result["error"] = str(e)
    
    return result


def fetch_trending_coins() -> Dict[str, Any]:
    """Fetch trending coins from CoinGecko (free, no key)"""
    cache_key = "trending_coins"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    result = {"coins": [], "error": None}
    
    try:
        import httpx
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get("https://api.coingecko.com/api/v3/search/trending")
            if resp.status_code == 200:
                data = resp.json()
                coins = []
                for item in data.get("coins", [])[:7]:
                    coin = item.get("item", {})
                    coins.append({
                        "name": coin.get("name", ""),
                        "symbol": coin.get("symbol", "").upper(),
                        "rank": coin.get("market_cap_rank", 0),
                        "score": coin.get("score", 0),
                        "thumb": coin.get("thumb", ""),
                        "small": coin.get("small", "")
                    })
                result = {"coins": coins, "error": None}
                _set_cache(cache_key, result, TTL_NEWS)
    except Exception as e:
        print(f"[TRENDING][WARN] Failed: {e}")
        result["error"] = str(e)
    
    return result


def fetch_altcoin_season() -> Dict[str, Any]:
    """
    Fetch Altcoin Season Index
    Scrapes blockchaincenter.net because they have no public JSON API
    """
    cache_key = "altcoin_season"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    result = {"index": 0, "status": "neutral", "error": None}
    
    try:
        import httpx
        import re
        url = "https://www.blockchaincenter.net/en/altcoin-season-index/"
        # User-agent is required for scraping
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        
        with httpx.Client(timeout=API_TIMEOUT_SECONDS, headers=headers, verify=False) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                html = resp.text
                # Look for the current index in the HTML
                # <div class="number">67</div>
                match = re.search(r'<div class="number">(\d+)</div>', html)
                if match:
                    val = int(match.group(1))
                    result = {
                        "index": val,
                        "blockchaincenter": {
                            "season_index": val,
                            "formatted_season_index": str(val)
                        },
                        "status": "altcoin" if val >= 75 else "bitcoin" if val <= 25 else "neutral",
                        "error": None
                    }
                    _set_cache(cache_key, result, TTL_MARKET * 10)
    except Exception as e:
        print(f"[ALTSEASON][WARN] Scraping failed: {e}")
        # Default/Mock if all fails
        result = {
            "index": 45,
            "blockchaincenter": {
                "season_index": 45,
                "formatted_season_index": "45"
            },
            "status": "neutral",
            "error": str(e)
        }
    
    return result


def fetch_eth_gas() -> Dict[str, Any]:
    """Fetch ETH gas prices from Owlracle (free, no key)"""
    cache_key = "eth_gas"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    result = {"slow": 0, "standard": 0, "fast": 0, "instant": 0, "error": None}
    
    try:
        import httpx
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get("https://api.owlracle.info/v4/eth/gas")
            if resp.status_code == 200:
                data = resp.json()
                speeds = data.get("speeds", [])
                if len(speeds) >= 4:
                    result = {
                        "slow": round(speeds[0].get("gasPrice", 0), 1),
                        "standard": round(speeds[1].get("gasPrice", 0), 1),
                        "fast": round(speeds[2].get("gasPrice", 0), 1),
                        "instant": round(speeds[3].get("gasPrice", 0), 1),
                        "error": None
                    }
                    _set_cache(cache_key, result, TTL_MARKET)
    except Exception as e:
        print(f"[GAS][WARN] Owlracle failed: {e}, trying fallback")
        try:
            # Fallback to Etherscan free (often works without key for basic status)
            with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
                resp = client.get("https://api.etherscan.io/api?module=proxy&action=eth_gasPrice")
                if resp.status_code == 200:
                    data = resp.json()
                    wei = int(data.get("result", "0x0"), 16)
                    gwei = wei / 1e9
                    result = {
                        "slow": round(gwei * 0.9, 1),
                        "standard": round(gwei, 1),
                        "fast": round(gwei * 1.1, 1),
                        "instant": round(gwei * 1.3, 1),
                        "error": None
                    }
                    _set_cache(cache_key, result, TTL_MARKET)
        except Exception as e2:
             print(f"[GAS][WARN] Fallback failed: {e2}")
             result["error"] = str(e)
    
    return result


def fetch_rainbow_chart() -> Dict[str, Any]:
    """
    Fetch Bitcoin Rainbow Chart data
    Uses logarithmic regression bands like blockchaincenter.net
    """
    cache_key = "rainbow_chart"
    cached = _get_cache(cache_key)
    if cached:
        return cached
    
    result = {
        "btc_price": 0,
        "band": "neutral",
        "band_index": 4,
        "band_name": "HODL",
        "bands": [],
        "error": None
    }
    
    try:
        import httpx
        import math
        
        # Get current BTC price
        with httpx.Client(timeout=API_TIMEOUT_SECONDS) as client:
            resp = client.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
            if resp.status_code == 200:
                data = resp.json()
                btc_price = data.get("bitcoin", {}).get("usd", 0)
                
                # Rainbow bands based on log regression (approximation)
                # Days since Bitcoin genesis (Jan 3, 2009)
                from datetime import datetime
                genesis = datetime(2009, 1, 3)
                days = (datetime.now() - genesis).days
                
                # Logarithmic regression base price (Approximation)
                # Formula: Price = 10 ^ (4.65 * log10(days) - 12.35)
                log_price = 10 ** (4.65 * math.log10(days) - 12.35)
                
                # Band multipliers (from "Fire Sale" to "Maximum Bubble")
                band_info = [
                    (0.4, "fire_sale", "🔥 Fire Sale"),
                    (0.5, "buy", "💚 BUY!"),
                    (0.65, "accumulate", "🟢 Accumulate"),
                    (0.85, "still_cheap", "🟡 Still Cheap"),
                    (1.1, "hodl", "🟠 HODL"),
                    (1.4, "bubble", "🟠 Is this a bubble?"),
                    (1.8, "fomo", "🔴 FOMO intensifies"),
                    (2.4, "sell", "🔴 Sell. Seriously, SELL!"),
                    (999, "max_bubble", "💀 Maximum Bubble")
                ]
                
                # Determine which band current price falls into
                price_ratio = btc_price / log_price if log_price > 0 else 1
                
                band = "neutral"
                band_index = 4
                band_name = "HODL"
                
                for i, (mult, b, name) in enumerate(band_info):
                    if price_ratio < mult:
                        band = b
                        band_index = i
                        band_name = name
                        break
                
                # Calculate band prices for current date
                bands = []
                for mult, b, name in band_info[:-1]:  # Skip max_bubble
                    bands.append({
                        "name": name,
                        "band": b,
                        "price": round(log_price * mult, 0)
                    })
                
                result = {
                    "btc_price": btc_price,
                    "fair_value": round(log_price, 0),
                    "log_price": round(log_price, 0),
                    "band": band,
                    "band_index": band_index,
                    "band_name": band_name,
                    "bands": bands,
                    "error": None
                }
                _set_cache(cache_key, result, TTL_MARKET * 5)
                
    except Exception as e:
        print(f"[RAINBOW][WARN] Failed: {e}")
        result["error"] = str(e)
    
    return result
