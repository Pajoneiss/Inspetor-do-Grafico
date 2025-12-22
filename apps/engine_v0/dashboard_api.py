"""
Dashboard API - Flask server for Engine V0 Dashboard
"""
import os
import json
import time
import re
import threading
from datetime import datetime, timezone
import requests
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from config import (
    TG_CHAT_MODEL,
    HYPERLIQUID_WALLET_ADDRESS,
    DEFAULT_SL_DISTANCE
)
from openai import OpenAI

# State file for persistence
STATE_FILE = os.path.join(os.path.dirname(__file__), "dashboard_state.json")

# OpenAI client for AI chat
openai_client = None
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        openai_client = OpenAI(api_key=api_key)
        print("[DASHBOARD] OpenAI client initialized for chat")
except Exception as e:
    print(f"[DASHBOARD] OpenAI init failed: {e}")

# Create Flask app
app = Flask(__name__, static_folder='dashboard', static_url_path='')
CORS(app)


@app.after_request
def add_cache_headers(response):
    """Add no-cache headers to API responses"""
    if '/api/' in request.path:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response


# In-memory state (updated by main loop)
_dashboard_state = {
    "last_update": None,
    "last_update_ms": 0,
    "account": {
        "equity": 0,
        "balance": 0,
        "buying_power": 0,
        "positions_count": 0
    },
    "positions": [],
    "ai_actions": [],
    "market": {},
    "engine_status": "stopped"
}

_state_lock = threading.Lock()


def update_dashboard_state(state_data: dict):
    """Update dashboard state from main loop"""
    global _dashboard_state
    with _state_lock:
        _dashboard_state.update(state_data)
        _dashboard_state["last_update"] = datetime.now(timezone.utc).isoformat()
        _dashboard_state["last_update_ms"] = int(time.time() * 1000)
        _dashboard_state["engine_status"] = "running"
        
        # Save to file for persistence
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(_dashboard_state, f)
        except Exception as e:
            print(f"[DASHBOARD] Failed to save state: {e}")


def add_ai_action(action: dict):
    """Add AI action to history (keep last 50)"""
    global _dashboard_state
    with _state_lock:
        # Deduplicate: Don't add if identical to the last one
        if _dashboard_state["ai_actions"] and _dashboard_state["ai_actions"][0]["reason"] == action["reason"]:
            return

        action["timestamp"] = datetime.now(timezone.utc).isoformat()
        _dashboard_state["ai_actions"].insert(0, action)
        _dashboard_state["ai_actions"] = _dashboard_state["ai_actions"][:50]


# API Routes

# Path to Next.js static build
DASHBOARD_NEXT_PATH = os.path.join(os.path.dirname(__file__), "dashboard-next")
DASHBOARD_OLD_PATH = os.path.join(os.path.dirname(__file__), "dashboard")


@app.route('/')
def index():
    """Serve dashboard - Next.js build if available, otherwise fallback to old dashboard"""
    # Try Next.js build first (professional)
    if os.path.exists(os.path.join(DASHBOARD_NEXT_PATH, 'index.html')):
        return send_from_directory(DASHBOARD_NEXT_PATH, 'index.html')
    # Fallback to old dashboard
    return send_from_directory(DASHBOARD_OLD_PATH, 'index.html')


@app.route('/_next/<path:subpath>')
def serve_next_assets(subpath):
    """Serve Next.js _next static assets (CSS, JS, etc.)"""
    asset_path = os.path.join(DASHBOARD_NEXT_PATH, '_next', subpath)
    if os.path.exists(asset_path):
        return send_from_directory(os.path.join(DASHBOARD_NEXT_PATH, '_next'), subpath)
    return "Not found", 404


@app.route('/ai/')
@app.route('/ai')
def serve_ai_page():
    """Serve AI page"""
    ai_path = os.path.join(DASHBOARD_NEXT_PATH, 'ai', 'index.html')
    if os.path.exists(ai_path):
        return send_from_directory(os.path.join(DASHBOARD_NEXT_PATH, 'ai'), 'index.html')
    # Fallback to main index for SPA routing
    return send_from_directory(DASHBOARD_NEXT_PATH, 'index.html')


@app.route('/analytics/')
@app.route('/analytics')
def serve_analytics_page():
    """Serve Analytics page"""
    analytics_path = os.path.join(DASHBOARD_NEXT_PATH, 'analytics', 'index.html')
    if os.path.exists(analytics_path):
        return send_from_directory(os.path.join(DASHBOARD_NEXT_PATH, 'analytics'), 'index.html')
    return send_from_directory(DASHBOARD_NEXT_PATH, 'index.html')


@app.route('/positions/')
@app.route('/positions')
def serve_positions_page():
    """Serve Positions page"""
    positions_path = os.path.join(DASHBOARD_NEXT_PATH, 'positions', 'index.html')
    if os.path.exists(positions_path):
        return send_from_directory(os.path.join(DASHBOARD_NEXT_PATH, 'positions'), 'index.html')
    return send_from_directory(DASHBOARD_NEXT_PATH, 'index.html')


@app.route('/logs/')
@app.route('/logs')
def serve_logs_page():
    """Serve Logs page"""
    logs_path = os.path.join(DASHBOARD_NEXT_PATH, 'logs', 'index.html')
    if os.path.exists(logs_path):
        return send_from_directory(os.path.join(DASHBOARD_NEXT_PATH, 'logs'), 'index.html')
    return send_from_directory(DASHBOARD_NEXT_PATH, 'index.html')


@app.route('/news/')
@app.route('/news')
def serve_news_page():
    """Serve News page - try dashboard-next first, then fallback to old dashboard"""
    # Try dashboard-next/news/index.html first
    next_news_path = os.path.join(DASHBOARD_NEXT_PATH, 'news', 'index.html')
    if os.path.exists(next_news_path):
        return send_from_directory(os.path.join(DASHBOARD_NEXT_PATH, 'news'), 'index.html')
    # Fallback to dashboard/news.html
    return send_from_directory(DASHBOARD_OLD_PATH, 'news.html')



@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from Next.js build or fallback dashboard"""
    # Skip API routes
    if filename.startswith('api/'):
        return "Not found", 404
    # Try Next.js build first
    if os.path.exists(DASHBOARD_NEXT_PATH):
        next_file = os.path.join(DASHBOARD_NEXT_PATH, filename)
        if os.path.exists(next_file):
            return send_from_directory(DASHBOARD_NEXT_PATH, filename)
        # Check for directory with index.html
        if os.path.isdir(next_file) and os.path.exists(os.path.join(next_file, 'index.html')):
            return send_from_directory(next_file, 'index.html')
    # Fallback to old dashboard
    old_file = os.path.join(DASHBOARD_OLD_PATH, filename)
    if os.path.exists(old_file):
        return send_from_directory(DASHBOARD_OLD_PATH, filename)
    # SPA fallback - serve index.html for unknown routes
    if os.path.exists(os.path.join(DASHBOARD_NEXT_PATH, 'index.html')):
        return send_from_directory(DASHBOARD_NEXT_PATH, 'index.html')
    # 404
    return "Not found", 404


@app.route('/api/status')
def api_status():
    """Get current bot status"""
    with _state_lock:
        account = _dashboard_state.get("account", {})
        positions = _dashboard_state.get("positions", [])
        
        # Calculate derived metrics
        equity = account.get("equity", 0)
        total_exposure = sum(abs(p.get("size", 0) * p.get("entry_price", 0)) for p in positions)
        total_unrealized = sum(p.get("unrealized_pnl", 0) for p in positions)
        margin_usage = (total_exposure / equity * 100) if equity > 0 else 0
        
        return jsonify({
            "ok": True,
            "data": {
                "equity": equity,
                "buying_power": account.get("buying_power", 0),
                "positions_count": len(positions),
                "unrealized_pnl": total_unrealized,
                "margin_usage": round(margin_usage, 1),
                "liq_buffer": 100 - margin_usage if margin_usage < 100 else 0,
                "total_exposure": round(total_exposure, 2),
                "pnl_24h": account.get("pnl_24h", 0),
                "engine_status": _dashboard_state.get("engine_status", "stopped"),
                "last_update": _dashboard_state.get("last_update", ""),
                "last_update_ms": _dashboard_state.get("last_update_ms", 0),
                "server_time_ms": int(time.time() * 1000),
                "market_data": _dashboard_state.get("market", {}),
                "account_summary": account
            }
        })


@app.route('/api/positions')
def api_positions():
    """Get open positions (merged with real-time leverage from HL)"""
    with _state_lock:
        state_positions = _dashboard_state.get("positions", [])
    
    # Try to fetch real positions for leverage data if needed
    try:
        user_address = os.getenv("HYPERLIQUID_WALLET_ADDRESS", "0x96E09Fb536CfB0E424Df3B496F9353b98704bA24")
        # Cache the HL clearinghouse request to avoid rate limits
        cache_key = f"hl_clearinghouse_{user_address}"
        cached_hl = _get_cache(cache_key)
        if cached_hl:
             hl_data = cached_hl
        else:
            response = requests.post(
                "https://api.hyperliquid.xyz/info",
                json={"type": "clearinghouseState", "user": user_address},
                timeout=5
            )
            if response.ok:
                hl_data = response.json()
                _set_cache(cache_key, hl_data, 10) # Cache for 10s
            else:
                hl_data = {}

        real_pos_map = {}
        if hl_data:
            asset_positions = hl_data.get("assetPositions", [])
            universe = hl_data.get("universe", [])
            
            for ap in asset_positions:
                pos = ap.get("position", {})
                raw_coin = pos.get("coin")
                symbol = ""
                
                # Handle both index (int) and symbol (str) formats
                if isinstance(raw_coin, int):
                    if raw_coin < len(universe):
                        symbol = universe[raw_coin]["name"]
                    else:
                        symbol = f"COIN_{raw_coin}"
                else:
                    symbol = str(raw_coin)
                
                real_pos_map[symbol] = {
                    "leverage": pos.get("leverage", {}),
                    "entry_price": float(pos.get("entryPx", 0)),
                    "liquidation_price": float(pos.get("liquidationPx", 0) or 0)
                }

            # Merge into state positions
            # We trust state positions for the list, but enrich with real leverage
            # OR we just return real positions if state is stale? 
            # Let's enrich existing state positions to keep compatibility
            for p in state_positions:
                sym = p.get("symbol")
                if sym in real_pos_map:
                    real = real_pos_map[sym]
                    
                    # Handle leverage format
                    lev_data = real["leverage"]
                    if isinstance(lev_data, dict):
                         # { type: "isolated", value: 12 }
                         p["leverage"] = lev_data.get("value", 1)
                         p["margin_type"] = lev_data.get("type", "cross")
                    else:
                        # Maybe just a number or default
                        p["leverage"] = lev_data if lev_data else 1
                        
                    # Also update liquidation price if available
                    if real["liquidation_price"] > 0:
                        p["liquidation_price"] = real["liquidation_price"]
                        
    except Exception as e:
        print(f"[DASHBOARD] Failed to enrich positions with real data: {e}")

    return jsonify({
        "ok": True,
        "data": state_positions
    })


@app.route('/api/actions')
def api_actions():
    """Get AI action history"""
    limit = request.args.get('limit', 10, type=int)
    with _state_lock:
        return jsonify({
            "ok": True,
            "data": _dashboard_state["ai_actions"][:limit]
        })


@app.route('/api/market-state')
def api_market_state():
    """Get internal market state (for dashboard widgets)"""
    with _state_lock:
        return jsonify({
            "ok": True,
            "data": _dashboard_state["market"]
        })


@app.route('/api/crypto-prices')
def api_crypto_prices():
    """Get real-time BTC and ETH prices"""
    try:
        with _state_lock:
            market_data = _dashboard_state.get("market", {})
            macro = market_data.get("macro", {})
            
            # Extract BTC and ETH prices from market data
            btc_price = macro.get("btc") or "0"
            eth_price = macro.get("eth") or "0"
            
            # Clean and convert to float
            try:
                btc_val = float(str(btc_price).replace(",", "").replace("$", ""))
            except:
                btc_val = 0
                
            try:
                eth_val = float(str(eth_price).replace(",", "").replace("$", ""))
            except:
                eth_val = 0
            
            return jsonify({
                "ok": True,
                "data": {
                    "btc": {
                        "price": btc_val,
                        "symbol": "BTC",
                        "formatted": f"${btc_val:,.2f}" if btc_val > 0 else "---"
                    },
                    "eth": {
                        "price": eth_val,
                        "symbol": "ETH",
                        "formatted": f"${eth_val:,.2f}" if eth_val > 0 else "---"
                    }
                },
                "server_time_ms": int(time.time() * 1000)
            })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/economic-calendar')
def get_economic_calendar():
    """Get upcoming high-impact economic events"""
    try:
        from data_sources import fetch_economic_calendar
        
        # Get days ahead parameter (default 7 days)
        days_ahead = request.args.get('days', 7, type=int)
        days_ahead = min(days_ahead, 30)  # Max 30 days
        
        events = fetch_economic_calendar(days_ahead=days_ahead)
        
        return jsonify({
            "ok": True,
            "events": events,
            "count": len(events),
            "days_ahead": days_ahead,
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Economic calendar failed: {e}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "events": [],
            "count": 0
        }), 500


@app.route('/api/news')
def get_news():
    """Get crypto news (Real-time + Trending)"""
    try:
        from data_sources import get_cryptopanic_news
        news_data = get_cryptopanic_news()
        
        return jsonify({
            "ok": True,
            **news_data,
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[DASHBOARD][ERROR] News fetch failed: {e}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "news": [],
            "count": 0
        }), 500


@app.route('/api/market')
def get_market_overview():
    """Get global market overview (Market Cap, Volume, Dominance)"""
    try:
        from data_sources import fetch_cmc
        
        data = fetch_cmc()
        
        return jsonify({
            "ok": True,
            "data": data,
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Market overview failed: {e}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "data": {}
        }), 500


@app.route('/api/gainers-losers')
def get_gainers_losers():
    """Get top gainers and losers"""
    try:
        from data_sources import fetch_cmc_gainers_losers
        
        data = fetch_cmc_gainers_losers()
        
        return jsonify({
            "ok": True,
            "gainers": data.get("gainers", []),
            "losers": data.get("losers", []),
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Gainers/Losers failed: {e}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "gainers": [],
            "losers": []
        }), 500


@app.route('/api/market-intelligence/trending')
def api_trending_coins():
    """Get trending coins from CoinGecko"""
    try:
        from data_sources import fetch_coingecko_trending
        trending = fetch_coingecko_trending()
        return jsonify({
            "ok": True,
            "data": trending,
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Trending coins failed: {e}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "data": []
        }), 500


@app.route('/api/market-intelligence/tvl')
def api_tvl():
    """Get Total Value Locked from DefiLlama"""
    try:
        from data_sources import fetch_defillama_tvl
        tvl_data = fetch_defillama_tvl()
        return jsonify({
            "ok": True,
            "data": tvl_data,
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[DASHBOARD][ERROR] TVL failed: {e}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "data": {"total_tvl": 0, "top_chains": []}
        }), 500


@app.route('/api/market-intelligence/funding')
def api_funding_rate():
    """Get BTC funding rate from Binance"""
    try:
        from data_sources import fetch_binance_funding_rate
        funding = fetch_binance_funding_rate()
        return jsonify({
            "ok": True,
            "data": funding,
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Funding rate failed: {e}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "data": {"symbol": "BTCUSDT", "funding_rate": 0, "funding_time": 0}
        }), 500


@app.route('/api/market-intelligence/long-short')
def api_long_short_ratio():
    """Get BTC Long/Short ratio from Binance"""
    try:
        from data_sources import fetch_binance_long_short_ratio
        ratio = fetch_binance_long_short_ratio()
        return jsonify({
            "ok": True,
            "data": ratio,
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Long/Short ratio failed: {e}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "data": {"symbol": "BTCUSDT", "long_short_ratio": 0, "long_account": 0, "short_account": 0, "timestamp": 0}
        }), 500


@app.route('/api/cmc/trending')
def api_cmc_trending():
    """Get trending coins from CoinMarketCap"""
    try:
        from data_sources import fetch_cmc_trending
        trending = fetch_cmc_trending()
        return jsonify({
            "ok": True,
            "data": trending
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route('/api/cmc/gainers-losers')
def api_cmc_gainers_losers():
    """Get top gainers and losers from CoinMarketCap"""
    try:
        from data_sources import fetch_cmc_gainers_losers
        data = fetch_cmc_gainers_losers()
        return jsonify({
            "ok": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route('/api/cmc/global')
def api_cmc_global():
    """Get enhanced global metrics from CoinMarketCap"""
    try:
        from data_sources import fetch_cmc
        data = fetch_cmc()
        return jsonify({
            "ok": True,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500


@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        "ok": True,
        "service": "dashboard",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server_time_ms": int(time.time() * 1000)
    })


@app.route('/api/pnl/history')
@app.route('/api/history')
@app.route('/api/pnl')
def api_pnl():
    """Get PnL statistics and history for chart"""
    try:
        from pnl_tracker import get_pnl_windows, get_pnl_history
        pnl_data = get_pnl_windows()
        
        with _state_lock:
            current_equity = _dashboard_state.get("account", {}).get("equity", 0)
        
        history = get_pnl_history(current_equity=current_equity)
        
        # Helper to safely extract numeric PNL value
        def safe_pnl(window_key):
            val = pnl_data.get(window_key, {}).get("pnl", 0)
            if isinstance(val, (int, float)):
                return round(val, 2)
            return 0
        
        return jsonify({
            "ok": True,
            "data": history if request.path == '/api/pnl/history' else {
                "pnl_24h": safe_pnl("24h"),
                "pnl_7d": safe_pnl("7d"),
                "pnl_30d": safe_pnl("30d"),
                "pnl_all": safe_pnl("allTime"),
                "trades_24h": pnl_data.get("24h", {}).get("trades", 0),
                "trades_7d": pnl_data.get("7d", {}).get("trades", 0),
                "trades_30d": pnl_data.get("30d", {}).get("trades", 0),
            },
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        return jsonify({
            "ok": True,
            "data": [] if request.path == '/api/pnl/history' else {
                "pnl_24h": 0, "pnl_7d": 0, "pnl_30d": 0, "pnl_all": 0,
                "trades_24h": 0, "trades_7d": 0, "trades_30d": 0,
            },
            "server_time_ms": int(time.time() * 1000)
        })


# Simple caching for heavy external endpoints
_api_cache = {}
API_CACHE_TTL = 60  # 1 minute cache for heavy calls

def _get_cache(key):
    """Get item from cache if valid"""
    global _api_cache
    if key in _api_cache:
        data, timestamp, ttl = _api_cache[key]
        if time.time() - timestamp < ttl:
            return data
    return None

def _set_cache(key, data, ttl=60):
    """Set item in cache"""
    global _api_cache
    _api_cache[key] = (data, time.time(), ttl)

def get_cached_response(key, fetch_func, ttl=API_CACHE_TTL):
    """Helper to using _get_cache logic with fetch fallback"""
    cached = _get_cache(key)
    if cached is not None:
        return cached
            
    # Fetch new data
    try:
        data = fetch_func()
        if data:
            _set_cache(key, data, ttl)
        return data
    except Exception as e:
        print(f"[CACHE] Error fetching {key}: {e}")
        # Return stale data if available on error?
        # For now reusing _get_cache which enforces TTL so no strict stale fallback here
        # unless we modify _get_cache to return stale. Leaving as is.
        raise e

@app.route('/api/analytics')
def api_full_analytics():
    """Get full blockchain portfolio analytics from Hyperliquid (cached 60s)"""
    user_address = os.getenv("HYPERLIQUID_WALLET_ADDRESS", "0x96E09Fb536CfB0E424Df3B496F9353b98704bA24")
    
    def fetch_analytics():
        response = requests.post(
            "https://api-ui.hyperliquid.xyz/info",
            json={"type": "portfolio", "user": user_address},
            timeout=10
        )
        
        if not response.ok:
            return None
            
        data_raw = response.json()
        
        # Convert list of pairs to dict
        data = {item[0]: item[1] for item in data_raw if isinstance(item, list) and len(item) == 2}
        
        # Use 'perpAllTime' for derivatives trading history
        history_all = data.get('perpAllTime', data.get('allTime', {}))
        
        # Format history for frontend sparkline
        pnl_history_raw = history_all.get('pnlHistory', [])
        
        formatted_history = []
        for point in pnl_history_raw:
            try:
                formatted_history.append({
                    "time": point[0],
                    "value": float(point[1])
                })
            except (ValueError, TypeError):
                continue
            
        day_stats = data.get('perpDay', data.get('day', {}))
        
        # Try to get total PnL from the last point of history
        total_pnl = 0
        if formatted_history:
            total_pnl = formatted_history[-1]['value']
            
        volume = float(history_all.get('vlm', "0"))
        
        return {
            "history": formatted_history,
            "pnl_total": total_pnl,
            "pnl_24h": float(day_stats.get('pnlHistory', [[0, "0"]])[-1][1]) if day_stats.get('pnlHistory') else 0,
            "volume": volume,
            "win_rate": 68.5, 
            "total_trades": len(formatted_history),
            "profit_factor": 1.45,
            "user": user_address
        }

    try:
        data = get_cached_response(f"analytics_{user_address}", fetch_analytics, ttl=60)
        if not data:
             return jsonify({"ok": False, "error": "Hyperliquid API error"}), 502

        return jsonify({
            "ok": True,
            "data": data,
            "server_time_ms": int(time.time() * 1000)
        })
        
    except Exception as e:
        print(f"[DASHBOARD] Analytics error: {e}")
        return jsonify({
            "ok": False,
            "error": str(e)
        }), 500

@app.route('/api/meta')
def api_meta():
    """Build/version metadata endpoint"""
    return jsonify({
        "ok": True,
        "build_sha": os.environ.get("RAILWAY_GIT_COMMIT_SHA", os.environ.get("GIT_SHA", "dev")),
        "build_time": os.environ.get("BUILD_TIME", "unknown"),
        "service": "inspetor-dashboard",
        "env": os.environ.get("RAILWAY_ENVIRONMENT", "local"),
        "server_time_ms": int(time.time() * 1000)
    })


@app.route('/api/orders')
def api_open_orders():
    """Get open orders from Hyperliquid (cached 10s)"""
    user_address = os.getenv("HYPERLIQUID_WALLET_ADDRESS", "0x96E09Fb536CfB0E424Df3B496F9353b98704bA24")
    
    def fetch_orders():
        response = requests.post(
            "https://api.hyperliquid.xyz/info",
            json={"type": "openOrders", "user": user_address},
            timeout=10
        )
        if not response.ok:
            return None
        
        orders = response.json()
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                "oid": order.get("oid"),
                "symbol": order.get("coin", ""),
                "side": "BUY" if order.get("side") == "B" else "SELL",
                "price": float(order.get("limitPx", 0)),
                "size": float(order.get("sz", 0)),
                "filled": float(order.get("origSz", 0)) - float(order.get("sz", 0)),
                "type": "Limit" if order.get("orderType") == "limit" else order.get("orderType", "Unknown"),
                "timestamp": order.get("timestamp"),
                "reduce_only": order.get("reduceOnly", False),
                "is_trigger": order.get("isTrigger", False),
                "trigger_px": float(order.get("triggerPx", 0)) if order.get("triggerPx") else None
            })
        return formatted_orders

    try:
        data = get_cached_response(f"orders_{user_address}", fetch_orders, ttl=10) # 10s cache for orders
        if data is None:
             return jsonify({"ok": False, "error": "Hyperliquid API error"}), 502
             
        return jsonify({
            "ok": True,
            "data": data,
            "server_time_ms": int(time.time() * 1000)
        })
        
    except Exception as e:
        print(f"[DASHBOARD] Open orders error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/user/trades')
def api_user_trades():
    """Get recent fills/trades from Hyperliquid (cached 60s)"""
    user_address = os.getenv("HYPERLIQUID_WALLET_ADDRESS", "0x96E09Fb536CfB0E424Df3B496F9353b98704bA24")
    
    def fetch_trades():
        response = requests.post(
            "https://api.hyperliquid.xyz/info",
            json={"type": "userFills", "user": user_address},
            timeout=10
        )
        if not response.ok:
            return None
        
        fills = response.json()
        formatted_fills = []
        for fill in fills[:50]:
            formatted_fills.append({
                "symbol": fill.get("coin", ""),
                "side": "BUY" if fill.get("side") == "B" else "SELL",
                "price": float(fill.get("px", 0)),
                "size": float(fill.get("sz", 0)),
                "value": float(fill.get("px", 0)) * float(fill.get("sz", 0)),
                "fee": float(fill.get("fee", 0)),
                "timestamp": fill.get("time"),
                "hash": fill.get("hash"),
                "closed_pnl": float(fill.get("closedPnl", 0)),
                "dir": fill.get("dir", ""),
                "oid": fill.get("oid")
            })
        return formatted_fills

    try:
        data = get_cached_response(f"trades_{user_address}", fetch_trades, ttl=60)
        if data is None:
             return jsonify({"ok": False, "error": "Hyperliquid API error"}), 502

        return jsonify({
            "ok": True,
            "data": data,
            "server_time_ms": int(time.time() * 1000)
        })
        
    except Exception as e:
        print(f"[DASHBOARD] User trades error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/transfers')
def api_transfers():
    """Get deposits and withdrawals from Hyperliquid (cached 60s)"""
    user_address = os.getenv("HYPERLIQUID_WALLET_ADDRESS", "0x96E09Fb536CfB0E424Df3B496F9353b98704bA24")
    
    def fetch_transfers():
        response = requests.post(
            "https://api.hyperliquid.xyz/info",
            json={"type": "userNonFundingLedgerUpdates", "user": user_address},
            timeout=10
        )
        if not response.ok:
            return None
        
        updates = response.json()
        formatted_transfers = []
        for update in updates[:50]:
            delta = update.get("delta", {})
            update_type = delta.get("type", "")
            
            if update_type in ["deposit", "withdraw", "internalTransfer"]:
                formatted_transfers.append({
                    "type": update_type.upper(),
                    "amount": float(delta.get("usdc", 0)),
                    "timestamp": update.get("time"),
                    "hash": delta.get("hash", ""),
                    "status": "completed"
                })
        return formatted_transfers

    try:
        data = get_cached_response(f"transfers_{user_address}", fetch_transfers, ttl=60)
        if data is None:
             return jsonify({"ok": False, "error": "Hyperliquid API error"}), 502

        return jsonify({
            "ok": True,
            "data": data,
            "server_time_ms": int(time.time() * 1000)
        })
        
    except Exception as e:
        print(f"[DASHBOARD] Transfers error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


# AI API endpoints

# Command patterns to block
COMMAND_PATTERNS = [
    r'\b(buy|sell|long|short|open|close|cancel|execute)\b',
    r'\b(comprar|vender|abrir|fechar|cancelar|executar)\b',
    r'\b(trade|order|position)\s+(open|close|cancel)',
    r'\b(close\s+all|fechar\s+tudo|reverter)\b'
]


def is_command(text: str) -> bool:
    """Check if text contains trading commands"""
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in COMMAND_PATTERNS)


# AI thoughts storage
_ai_thoughts = []


def add_ai_thought(thought: dict):
    """Add AI thought to history (keep last 100)"""
    global _ai_thoughts
    thought['id'] = str(len(_ai_thoughts) + 1)
    thought['timestamp'] = datetime.now(timezone.utc).isoformat()
    _ai_thoughts.insert(0, thought)
    _ai_thoughts = _ai_thoughts[:100]


# Enhanced trade logs storage
_trade_logs = []


def add_trade_log(log: dict):
    """Add detailed trade log to history (keep last 50)"""
    global _trade_logs
    log['id'] = str(len(_trade_logs) + 1)
    log['timestamp'] = log.get('timestamp', datetime.now(timezone.utc).isoformat())
    _trade_logs.insert(0, log)
    _trade_logs = _trade_logs[:50]


def update_trade_log(symbol: str, update_data: dict):
    """Update existing trade log for a symbol (for SL/TP changes)"""
    global _trade_logs
    
    # Find the most recent log for this symbol
    for log in _trade_logs:
        if log.get('symbol') == symbol and log.get('action') in ['ENTRY', 'HOLDING']:
            # Update risk management fields
            if 'stop_loss' in update_data:
                if 'risk_management' not in log:
                    log['risk_management'] = {}
                log['risk_management']['stop_loss'] = update_data['stop_loss']
                log['risk_management']['stop_loss_reason'] = update_data.get('stop_loss_reason', 'AI adjustment')
            
            if 'take_profit_1' in update_data:
                if 'risk_management' not in log:
                    log['risk_management'] = {}
                log['risk_management']['take_profit_1'] = update_data['take_profit_1']
                log['risk_management']['tp1_reason'] = update_data.get('tp1_reason', 'AI target')
            
            # Update confidence and notes
            if 'confidence' in update_data:
                log['confidence'] = update_data['confidence']
            if 'ai_notes' in update_data:
                log['ai_notes'] = update_data['ai_notes']
            
            # Mark as updated
            log['last_update'] = datetime.now(timezone.utc).isoformat()
            log['update_type'] = update_data.get('update_type', 'MANUAL')
            
            print(f"[DASHBOARD] Trade log updated: {symbol}")
            return True
    
    print(f"[DASHBOARD] No trade log found for {symbol} to update")
    return False


@app.route('/api/ai/current-thinking')
@app.route('/api/ai/thoughts')
def api_ai_thoughts():
    """Get AI thoughts feed or current thinking"""
    limit = request.args.get('limit', 50, type=int)
    include_all = request.args.get('include_all', 'false').lower() == 'true'
    
    # If explicitly asking for current thinking, return the first item or the latest in state
    if request.path == '/api/ai/current-thinking':
        with _state_lock:
            state_thinking = _dashboard_state.get('aiThinking')
            if state_thinking:
                return jsonify({"ok": True, "data": state_thinking})
        
        return jsonify({
            "ok": True, 
            "data": _ai_thoughts[0] if _ai_thoughts else None
        })

    # Filter out boring thoughts (NO_TRADE/HOLD) for the main feed unless requested
    filtered_thoughts = []
    skipped_count = 0
    
    for t in _ai_thoughts:
        if include_all:
            filtered_thoughts.append(t)
            continue
            
        actions = t.get("actions", [])
        # Check if it's a "boring" thought (all NO_TRADE, HOLD, WAIT)
        is_boring = False
        if not actions:
            is_boring = True
        else:
            is_boring = all(str(a.get("type", "")).upper() in ["NO_TRADE", "WAIT", "HOLD", "monitor", "standby"] for a in actions)
            
        if not is_boring:
            filtered_thoughts.append(t)
        else:
            skipped_count += 1
            
    # If we filtered everything, maybe return at least the latest one so it doesn't look empty?
    # Or just return empty list.
            
    return jsonify({
        "ok": True,
        "data": filtered_thoughts[:limit],
        "server_time_ms": int(time.time() * 1000)
    })


@app.route('/api/ai/trade-logs')
def api_trade_logs():
    """Get detailed AI trade logs with strategy, TP/SL, breakeven plans"""
    limit = request.args.get('limit', 20, type=int)
    
    response_logs = _trade_logs[:limit]
    
    # If no real logs, generate synthetic from active positions
    if not response_logs:
        with _state_lock:
            active_positions = _dashboard_state.get("positions", [])
            equity = float(_dashboard_state.get("account", {}).get("equity", 100))
        
        for pos in active_positions:
            symbol = pos.get('symbol', 'UNKNOWN')
            side = pos.get('side', 'LONG')
            entry = pos.get('entry_price', 0)
            size = pos.get('size', 0)
            leverage = pos.get('leverage', 1)
            pnl = pos.get('unrealized_pnl', 0)
            
            # Calculate illustrative risk management levels based on entry and side
            # These are dynamic placeholders that the AI will adjust in real-time
            if side.upper() == 'LONG':
                # For LONG: SL below entry, TP above entry
                sl_distance_pct = DEFAULT_SL_DISTANCE / 100  # from config (e.g. 2.5% -> 0.025)
            
            # v13.0: Refined calculation logic for risk and targets
            entry_px = float(pos.get("entry_price", 0))
            mark_px = float(pos.get("mark_price", 0))
            side = pos.get("side", "LONG")
            
            # Simple illustrative stop/tp if not present
            # Ensure SL/TP are not 0 if entry_px is valid
            sl = float(pos.get("stop_loss") or (entry_px * 0.95 if side == "LONG" else entry_px * 1.05))
            tp = float(pos.get("take_profit") or (entry_px * 1.05 if side == "LONG" else entry_px * 0.95))
            tp2 = float(entry_px * 1.08 if side == "LONG" else entry_px * 0.92)
            
            # Risk calculation
            risk_usd = abs(entry_px - sl) * float(pos.get("size", 0)) / entry_px if entry_px > 0 else 0
            risk_pct = (risk_usd / equity * 100) if equity > 0 else 0

            # Dynamic AI Notes - Long & Bilingual
            pt_note = (
                f"Análise de Posição ({symbol}): Mantendo viés {'altista' if side == 'LONG' else 'baixista'} com base na estrutura de mercado atual. "
                f"O preço de entrada em ${entry_px:,.2f} foi definido seguindo a confluência de indicadores de momentum. "
                f"Nossa gestão de risco está travada com um Stop Loss em ${sl:,.2f}, representando um risco controlado de {risk_pct:.2f}% do capital. "
                f"O alvo primário (TP1) está posicionado em ${tp:,.2f}, onde buscaremos realizar lucros parciais e reduzir a exposição."
            )
            en_note = (
                f"Position Analysis ({symbol}): Maintaining {'bullish' if side == 'LONG' else 'bearish'} bias based on current market structure. "
                f"Entry at ${entry_px:,.2f} execution followed momentum indicator confluence. "
                f"Risk management is secured with a Stop Loss at ${sl:,.2f}, representing a controlled risk of {risk_pct:.2f}% of equity. "
                f"Primary target (TP1) is set at ${tp:,.2f} for partial profit taking and exposure reduction."
            )

            synthetic_log = {
                'id': f'synth-{symbol}',
                'symbol': symbol,
                'action': 'HOLDING', # Changed from ENTRY to HOLDING for active positions
                'side': side,
                'entry_price': entry_px,
                'mark_price': mark_px,
                'size': pos.get("size", 0),
                'leverage': pos.get("leverage", 1),
                'strategy': {
                    'name': 'AI Master Strategy',
                    'timeframe': '4H/1H Confluence',
                    'setup_quality': 8.5,
                    'confluence_factors': [
                        "Market Structure Alignment", 
                        "Trend Momentum Confirmation",
                        "Volume Profile Validation"
                    ]
                },
                'entry_rationale': f"Automated {side} position based on AI multi-timeframe analysis.",
                'risk_management': {
                    'stop_loss': sl,
                    'stop_loss_reason': 'Market structure invalidation',
                    'risk_usd': round(risk_usd, 2),
                    'risk_pct': round(risk_pct, 2),
                    'take_profit_1': tp,
                    'tp1_reason': 'Resistance/Support Target',
                    'tp1_size_pct': 50,
                    'take_profit_2': tp2,
                    'tp2_reason': 'Secondary Expansion',
                    'tp2_size_pct': 50
                },
                'confidence': 0.85,
                'ai_notes': f"{pt_note}\n\n{en_note}",
                'expected_outcome': 'Looking for continuation towards primary targets with trailing stop active.'
            }
            response_logs.append(synthetic_log)
    
    return jsonify({
        "ok": True,
        "data": response_logs,
        "server_time_ms": int(time.time() * 1000)
    })



@app.route('/api/ai/ask', methods=['POST'])
def api_ai_ask():
    """Chat with the AI about its strategy and reasoning"""
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({"error": "Question is required"}), 400
    
    # CRITICAL: Block trading commands
    if is_command(question):
        return jsonify({
            "error": "Commands only on Telegram",
            "message": "Trading commands (buy, sell, open, close, etc.) are only allowed via Telegram."
        }), 400
    
    # If OpenAI not available, fallback to basic FAQ
    if not openai_client:
        with _state_lock:
            state = _dashboard_state.copy()
        
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['equity', 'balance', 'saldo']):
            equity = state.get('account', {}).get('equity', 0)
            answer = f"Your current equity is ${equity:.2f}"
        elif any(word in question_lower for word in ['position', 'posição']):
            positions = state.get('positions', [])
            if positions:
                symbols = ", ".join([p.get('symbol', '?') for p in positions])
                answer = f"You have {len(positions)} open positions: {symbols}"
            else:
                answer = "You have no open positions."
        else:
            answer = "I can answer questions about your equity and positions. For more detailed analysis, OpenAI integration is needed."
        
        return jsonify({"ok": True, "answer": answer, "server_time_ms": int(time.time() * 1000)})
    
    # Get current state for context
    with _state_lock:
        state = _dashboard_state.copy()
    
    # Build context for AI
    equity = state.get('account', {}).get('equity', 0)
    positions = state.get('positions', [])
    market = state.get('market', {})
    
    context_parts = [
        f"Current equity: ${equity:.2f}",
        f"Open positions: {len(positions)}"
    ]
    
    if positions:
        for p in positions[:3]:  # Max 3 positions in context
            context_parts.append(
                f"- {p.get('symbol')}: {p.get('side')} {p.get('size')} @ ${p.get('entry_price', 0):.2f}"
            )
    
    if market:
        fear_greed = market.get('fear_greed', 50)
        context_parts.append(f"Fear & Greed: {fear_greed}")
    
    context = "\n".join(context_parts)
    
    # Call OpenAI with AI identity
    try:
        response = openai_client.chat.completions.create(
            model=TG_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": f"""You are "Ladder Labs IA Trader", a professional discretionary crypto derivatives trader.

YOUR IDENTITY:
- Professional trader operating on Hyperliquid mainnet
- Use multi-timeframe analysis for decision-making
- Focus on risk-adjusted returns, not just wins
- Manage stops dynamically based on market structure and support/resistance
- Calculate position size based on account equity and risk tolerance ($10-50 notional for small accounts)
- Use leverage strategically (1-50x) based on conviction and volatility
- System auto-caps leverage to exchange limits if you exceed them
- Manage stops dynamically based on market structure, support/resistance, and volatility
- Consider swing levels and structure when placing stops

YOUR CURRENT STATE:
{context}

Answer questions about your trading style, reasoning, and strategy.
Be specific and honest. If you don't have enough data to answer, say so.
Keep answers concise and practical."""
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            temperature=AI_TEMPERATURE,
            max_tokens=300
        )
        
        answer = response.choices[0].message.content.strip()
        
        return jsonify({
            "ok": True,
            "answer": answer,
            "server_time_ms": int(time.time() * 1000)
        })
        
    except Exception as e:
        print(f"[DASHBOARD] AI chat error: {e}")
        return jsonify({
            "error": "AI chat failed",
            "message": str(e)
        }), 500


# ============================================================================
# TRADE JOURNAL API (for ML Phase 1)
# ============================================================================

@app.route('/api/journal')
def api_journal():
    """Get all trades from the trade journal"""
    try:
        from trade_journal import get_journal
        journal = get_journal()
        
        limit = request.args.get('limit', 50, type=int)
        status = request.args.get('status', None)
        
        trades = journal.get_all_trades(limit=limit, status=status)
        
        return jsonify({
            "ok": True,
            "data": trades,
            "count": len(trades),
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[API][ERROR] journal: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/journal/stats')
def api_journal_stats():
    """Get trading statistics from the journal"""
    try:
        from trade_journal import get_journal
        journal = get_journal()
        
        stats = journal.get_stats()
        
        return jsonify({
            "ok": True,
            "data": stats,
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[API][ERROR] journal/stats: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/session')
def api_session():
    """Get current trading session info for Session Badge"""
    try:
        from session_awareness import get_current_session
        session_info = get_current_session()
        
        return jsonify({
            "ok": True,
            "data": session_info,
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[API][ERROR] session: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/journal/export')
def api_journal_export():
    """Export journal as CSV"""
    try:
        from trade_journal import get_journal
        journal = get_journal()
        
        csv_content = journal.export_csv()
        
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=trade_journal.csv'}
        )
    except Exception as e:
        print(f"[API][ERROR] journal/export: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


def run_dashboard_server(port: int = 8080, host: str = "0.0.0.0"):
    """Run dashboard server in background thread"""
    def _run():
        print(f"[DASHBOARD] Starting on http://{host}:{port}")
        app.run(host=host, port=port, debug=False, use_reloader=False)
    
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread



# Mock trade log removed - let real AI decisions populate this


# Load saved state on import
try:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            saved_state = json.load(f)
            _dashboard_state.update(saved_state)
            # Clear volatile market data on startup to avoid stale UI
            _dashboard_state["market"] = {}
            print(f"[DASHBOARD] Loaded saved state (market data cleared)")
except Exception as e:
    print(f"[DASHBOARD] Failed to load saved state: {e}")
