"""
Market Data Fetcher for Macro Indicators
Fetches USD/BRL, SP500, NASDAQ, BTC dominance, market cap
"""
import requests
from typing import Dict, Any
import os


class MarketDataFetcher:
    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.alternative_base = "https://api.alternative.me"
        
    def get_macro_data(self) -> Dict[str, Any]:
        """Fetch all macro market data"""
        try:
            # BTC data from CoinGecko (includes dominance, market cap)
            btc_data = self._get_btc_data()
            
            # Fear & Greed Index
            fear_greed = self._get_fear_greed()
            
            # USD/BRL from CoinGecko (using USDT/BRL as proxy)
            usd_brl = self._get_usd_brl()
            
            # SP500 & NASDAQ (using crypto proxies or cached values)
            indices = self._get_stock_indices()
            
            return {
                "usd_brl": usd_brl,
                "sp500": indices.get("sp500", 0),
                "nasdaq": indices.get("nasdaq", 0),
                "btc_dominance": btc_data.get("dominance", 0),
                "total_mcap": btc_data.get("total_mcap", "$0"),
                "fear_greed": fear_greed,
                "btc_24h": btc_data.get("btc_24h", 0),
                "last_updated": btc_data.get("timestamp", "")
            }
        except Exception as e:
            print(f"[MACRO] Error fetching data: {e}")
            return self._get_fallback_data()
    
    def _get_btc_data(self) -> Dict[str, Any]:
        """Get BTC dominance and market cap from CoinGecko"""
        try:
            url = f"{self.coingecko_base}/global"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()["data"]
                total_mcap = data.get("total_market_cap", {}).get("usd", 0)
                btc_dom = data.get("market_cap_percentage", {}).get("btc", 0)
                
                # Format market cap
                if total_mcap >= 1e12:
                    mcap_str = f"${total_mcap/1e12:.2f}T"
                else:
                    mcap_str = f"${total_mcap/1e9:.2f}B"
                
                # Get BTC 24h change
                btc_url = f"{self.coingecko_base}/coins/bitcoin"
                btc_resp = requests.get(btc_url, timeout=10)
                btc_24h = 0
                if btc_resp.status_code == 200:
                    btc_24h = btc_resp.json()["market_data"]["price_change_percentage_24h"]
                
                return {
                    "dominance": round(btc_dom, 1),
                    "total_mcap": mcap_str,
                    "btc_24h": round(btc_24h, 2),
                    "timestamp": data.get("updated_at", 0)
                }
        except Exception as e:
            print(f"[MACRO] BTC data error: {e}")
        
        return {}
    
    def _get_fear_greed(self) -> int:
        """Get Fear & Greed Index from alternative.me"""
        try:
            url = f"{self.alternative_base}/fng/"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return int(resp.json()["data"][0]["value"])
        except:
            pass
        return 50  # Neutral fallback
    
    def _get_usd_brl(self) -> float:
        """Get USD/BRL exchange rate"""
        try:
            # Use USDT/BRL from CoinGecko as USD/BRL proxy
            url = f"{self.coingecko_base}/simple/price?ids=tether&vs_currencies=brl"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return round(resp.json()["tether"]["brl"], 2)
        except:
            pass
        return 5.50  # Fallback ~R$5.50
    
    def _get_stock_indices(self) -> Dict[str, float]:
        """Get SP500 & NASDAQ (using cached or estimated values)"""
        # Note: Real-time stock data requires paid APIs
        # Using reasonable estimates as placeholders
        return {
            "sp500": 4800,  # ~$4800 (update manually or use paid API)
            "nasdaq": 16000  # ~16000 (update manually or use paid API)
        }
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Fallback data when API fails"""
        return {
            "usd_brl": 5.50,
            "sp500": 4800,
            "nasdaq": 16000,
            "btc_dominance": 57.0,
            "total_mcap": "$3.0T",
            "fear_greed": 50,
            "btc_24h": 0,
            "last_updated": ""
        }


# Singleton instance
_fetcher = None

def get_market_data() -> Dict[str, Any]:
    """Get cached or fresh market data"""
    global _fetcher
    if _fetcher is None:
        _fetcher = MarketDataFetcher()
    return _fetcher.get_macro_data()


def generate_daily_summary() -> str:
    """Generate human-readable daily market summary"""
    data = get_market_data()
    
    # Fear & Greed emoji
    fg = data.get("fear_greed", 50)
    if fg < 25:
        fg_emoji = "😱 Extreme Fear"
    elif fg < 45:
        fg_emoji = "😨 Fear"
    elif fg < 55:
        fg_emoji = "😐 Neutral"
    elif fg < 75:
        fg_emoji = "😄 Greed"
    else:
        fg_emoji = "🤑 Extreme Greed"
    
    # BTC 24h emoji
    btc_24h = data.get("btc_24h", 0)
    btc_emoji = "📈" if btc_24h > 0 else "📉" if btc_24h < 0 else "➖"
    
    # Build summary
    summary = f"{fg_emoji} ({fg}/100)\n"
    summary += f"{btc_emoji} BTC 24h: {btc_24h:+.2f}%\n"
    summary += f"💰 Market Cap: {data.get('total_mcap', 'N/A')}\n"
    summary += f"📊 BTC Dominance: {data.get('btc_dominance', 0):.1f}%"
    
    return summary
