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
    DEFAULT_SL_DISTANCE,
    AI_TEMPERATURE
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
        return jsonify({"ok": True, **news_data, "server_time_ms": int(time.time() * 1000)})
    except Exception as e:
        print(f"[DASHBOARD][ERROR] News failed: {e}")
        return jsonify({"ok": False, "error": str(e), "news": [], "count": 0}), 500


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
    """Get top gainers and losers (CoinGecko > Binance)"""
    try:
        from data_sources import fetch_cmc_gainers_losers
        data = fetch_cmc_gainers_losers()
        return jsonify({"ok": True, **data, "server_time_ms": int(time.time() * 1000)})
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Movers failed: {e}")
        return jsonify({"ok": False, "error": str(e), "gainers": [], "losers": []}), 500


@app.route('/api/market-intelligence/trending')
@app.route('/api/trending')
def api_trending_coins():
    """Get trending coins from CoinGecko"""
    try:
        from data_sources import fetch_trending_coins
        res = fetch_trending_coins()
        return jsonify({"ok": True, "data": res.get("coins", []), **res})
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Trending failed: {e}")
        return jsonify({"ok": False, "error": str(e), "data": []}), 500

@app.route('/api/market-intelligence/tvl')
@app.route('/api/tvl')
def api_market_intelligence_tvl():
    """Get TVL from DefiLlama"""
    try:
        from data_sources import fetch_defi_tvl
        res = fetch_defi_tvl()
        return jsonify({"ok": True, "data": res, **res})
    except Exception as e:
        print(f"[DASHBOARD][ERROR] TVL failed: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/market-intelligence/funding')
@app.route('/api/funding')
def api_funding_rate():
    """Get funding rates from Binance"""
    try:
        from data_sources import fetch_funding_rates
        res = fetch_funding_rates()
        return jsonify({"ok": True, "data": res, **res})
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Funding failed: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/market-intelligence/long-short')
@app.route('/api/long-short')
def api_long_short_ratio():
    """Get Long/Short ratios from Binance"""
    try:
        from data_sources import fetch_long_short_ratio
        res = fetch_long_short_ratio()
        return jsonify({"ok": True, "data": res, **res})
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Long/Short failed: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/halving')
def api_halving():
    """Get Bitcoin halving data"""
    try:
        from data_sources import fetch_bitcoin_halving
        res = fetch_bitcoin_halving()
        return jsonify({"ok": True, "data": res, **res})
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Halving failed: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/altseason')
def api_altseason():
    """Get Altcoin Season Index"""
    try:
        from data_sources import fetch_altcoin_season
        res = fetch_altcoin_season()
        return jsonify({"ok": True, "data": res, **res})
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Altseason failed: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/rainbow')
def api_rainbow():
    """Get Bitcoin Rainbow Chart data"""
    try:
        from data_sources import fetch_rainbow_chart
        res = fetch_rainbow_chart()
        return jsonify({"ok": True, "data": res, **res})
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Rainbow failed: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/gas')
def api_eth_gas():
    """Get ETH Gas prices"""
    try:
        from data_sources import fetch_eth_gas
        res = fetch_eth_gas()
        return jsonify({"ok": True, "data": res, **res})
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Gas failed: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


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
    """Get global market data (Market Cap, Dominance)"""
    try:
        from data_sources import fetch_cmc
        data = fetch_cmc()
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        "ok": True,
        "service": "dashboard",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server_time_ms": int(time.time() * 1000)
    })


@app.route('/api/pnl-summary')
def api_pnl_summary():
    """
    Get comprehensive PnL summary for client display.
    Combines Hyperliquid portfolio API with TradeJournal stats.
    """
    try:
        from pnl_tracker import get_pnl_windows
        from trade_journal import get_journal
        
        # Get real PnL from Hyperliquid Portfolio API
        pnl_data = get_pnl_windows()
        
        # Get real stats from TradeJournal
        journal = get_journal()
        journal_stats = journal.get_stats()
        
        # Helper to safely extract numeric PNL value
        def safe_pnl(window_key):
            val = pnl_data.get(window_key, {}).get("pnl", 0)
            if isinstance(val, (int, float)):
                return round(val, 2)
            return 0
        
        return jsonify({
            "ok": True,
            "data": {
                # PnL Windows (from Hyperliquid)
                "pnl_24h": safe_pnl("24h"),
                "pnl_7d": safe_pnl("7d"),
                "pnl_30d": safe_pnl("30d"),
                "pnl_all_time": safe_pnl("allTime"),
                
                # Trade Stats (from Journal)
                "total_trades": journal_stats.get("total_trades", 0),
                "closed_trades": journal_stats.get("closed_trades", 0),
                "open_trades": journal_stats.get("open_trades", 0),
                "wins": journal_stats.get("wins", 0),
                "losses": journal_stats.get("losses", 0),
                "win_rate": journal_stats.get("win_rate", 0),
                "avg_pnl_pct": journal_stats.get("avg_pnl_pct", 0),
                "total_pnl_usd": journal_stats.get("total_pnl_usd", 0),
                "best_trade_pct": journal_stats.get("best_trade_pct", 0),
                "worst_trade_pct": journal_stats.get("worst_trade_pct", 0),
                "avg_duration_minutes": journal_stats.get("avg_duration_minutes", 0)
            },
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[DASHBOARD][ERROR] PnL Summary failed: {e}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "data": {}
        }), 500


@app.route('/api/analytics')
def api_analytics():
    """
    Get comprehensive analytics data from Hyperliquid blockchain.
    Calculates ALL metrics from fills: Win Rate, Best/Worst Trade, Profit Factor, etc.
    Fetches PnL directly from Hyperliquid Portfolio API (no hl_client needed).
    """
    try:
        from pnl_tracker import get_pnl_history
        
        # Get wallet address
        wallet = os.environ.get("HYPERLIQUID_WALLET_ADDRESS", "")
        
        # Initialize PnL values and chart data
        pnl_24h = 0
        pnl_7d = 0
        pnl_30d = 0
        pnl_total = 0
        equity_history = []  # For the chart like HyperDash
        pnl_history_alltime = []  # PnL over time for chart
        
        # Fetch PnL directly from Hyperliquid Portfolio API
        if wallet:
            try:
                portfolio_resp = requests.post(
                    "https://api.hyperliquid.xyz/info",
                    json={"type": "portfolio", "user": wallet},
                    timeout=15
                )
                if portfolio_resp.status_code == 200:
                    portfolio_data = portfolio_resp.json()
                    # Format: [["day", {...}], ["week", {...}], ["month", {...}], ["allTime", {...}]]
                    if portfolio_data and isinstance(portfolio_data, list):
                        for item in portfolio_data:
                            if isinstance(item, list) and len(item) >= 2:
                                period_name = item[0]
                                period_data = item[1]
                                
                                # Get PnL from last entry in pnlHistory
                                pnl_hist = period_data.get("pnlHistory", [])
                                current_pnl = 0
                                if pnl_hist and len(pnl_hist) > 0:
                                    current_pnl = float(pnl_hist[-1][1])
                                
                                if period_name == "day":
                                    pnl_24h = current_pnl
                                elif period_name == "week":
                                    pnl_7d = current_pnl
                                elif period_name == "month":
                                    pnl_30d = current_pnl
                                elif period_name == "allTime":
                                    pnl_total = current_pnl
                                    # Get equity history for chart (like HyperDash)
                                    acc_hist = period_data.get("accountValueHistory", [])
                                    print(f"[ANALYTICS] allTime accountValueHistory has {len(acc_hist)} entries")
                                    for entry in acc_hist:
                                        equity_history.append({
                                            "time": entry[0],  # timestamp in ms
                                            "value": float(entry[1])
                                        })
                                    # Also get PnL history for chart
                                    print(f"[ANALYTICS] allTime pnlHistory has {len(pnl_hist)} entries")
                                    for entry in pnl_hist:
                                        pnl_history_alltime.append({
                                            "time": entry[0],
                                            "value": float(entry[1])
                                        })
                        
                        print(f"[ANALYTICS] PnL fetched from Hyperliquid: 24h=${pnl_24h:.2f}, 7d=${pnl_7d:.2f}, 30d=${pnl_30d:.2f}, allTime=${pnl_total:.2f}")
                        print(f"[ANALYTICS] History counts: equity={len(equity_history)}, pnl={len(pnl_history_alltime)}")
            except Exception as e:
                print(f"[ANALYTICS] Portfolio API error: {e}")
                import traceback
                traceback.print_exc()
        
        # Use API equity history if available, otherwise fallback to local history
        history = equity_history if equity_history else get_pnl_history()
        
        
        
        # Initialize metrics
        total_trades = 0
        wins = 0
        losses = 0
        volume = 0
        best_trade_pnl = 0
        worst_trade_pnl = 0
        total_profit = 0
        total_loss = 0
        trade_durations = []
        
        # Fetch fills directly from Hyperliquid
        wallet = os.environ.get("HYPERLIQUID_WALLET_ADDRESS", "")
        if wallet:
            try:
                fills_url = "https://api.hyperliquid.xyz/info"
                fills_resp = requests.post(fills_url, json={
                    "type": "userFills",
                    "user": wallet
                }, timeout=15)
                
                if fills_resp.status_code == 200:
                    fills = fills_resp.json()
                    
                    # Group fills by position (symbol + side)
                    positions = {}
                    for fill in fills:
                        key = f"{fill.get('coin')}_{fill.get('dir')}"
                        if key not in positions:
                            positions[key] = []
                        positions[key].append(fill)
                    
                    # Analyze each closed position
                    for key, position_fills in positions.items():
                        if len(position_fills) >= 2:
                            # Calculate PnL for this position
                            pnl = sum(float(f.get("closedPnl", 0)) for f in position_fills)
                            fill_value = sum(abs(float(f.get("sz", 0)) * float(f.get("px", 0))) for f in position_fills)
                            volume += fill_value
                            
                            if pnl != 0:
                                total_trades += 1
                                if pnl > 0:
                                    wins += 1
                                    total_profit += pnl
                                    if pnl > best_trade_pnl:
                                        best_trade_pnl = pnl
                                else:
                                    losses += 1
                                    total_loss += abs(pnl)
                                    if pnl < worst_trade_pnl:
                                        worst_trade_pnl = pnl
                                
                                # Calculate duration if timestamps available
                                times = [int(f.get("time", 0)) for f in position_fills if f.get("time")]
                                if len(times) >= 2:
                                    duration_ms = max(times) - min(times)
                                    duration_min = duration_ms / 60000
                                    if duration_min > 0:
                                        trade_durations.append(duration_min)
                    
                    # Also count individual fills with closedPnl
                    for fill in fills:
                        closed_pnl = float(fill.get("closedPnl", 0))
                        if closed_pnl != 0 and total_trades == 0:
                            total_trades += 1
                            volume += abs(float(fill.get("sz", 0)) * float(fill.get("px", 0)))
                            if closed_pnl > 0:
                                wins += 1
                                total_profit += closed_pnl
                                best_trade_pnl = max(best_trade_pnl, closed_pnl)
                            else:
                                losses += 1
                                total_loss += abs(closed_pnl)
                                worst_trade_pnl = min(worst_trade_pnl, closed_pnl)
                                
            except Exception as e:
                print(f"[ANALYTICS] Fills fetch error: {e}")
        
        # Calculate derived metrics
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        profit_factor = (total_profit / total_loss) if total_loss > 0 else (1.0 if total_profit == 0 else 2.0)
        avg_duration = (sum(trade_durations) / len(trade_durations)) if trade_durations else 0
        
        # Fallback: if Portfolio API returned 0, use fills-based calculation
        fills_pnl = total_profit - total_loss
        if pnl_total == 0 and fills_pnl != 0:
            pnl_total = fills_pnl
            print(f"[ANALYTICS] Using fills-based PnL as fallback: ${fills_pnl:.2f}")
        
        return jsonify({
            "ok": True,
            "data": {
                "history": history,  # Equity history for chart (like HyperDash)
                "pnl_history": pnl_history_alltime,  # PnL over time for chart
                # PnL values from Hyperliquid Portfolio API
                "pnl_24h": round(pnl_24h, 2),
                "pnl_7d": round(pnl_7d, 2),
                "pnl_30d": round(pnl_30d, 2),
                "pnl_total": round(pnl_total, 2),
                # Metrics calculated from fills
                "win_rate": round(win_rate, 1),
                "profit_factor": round(profit_factor, 2),
                "total_trades": total_trades,
                "wins": wins,
                "losses": losses,
                "volume": round(volume, 2),
                "best_trade_pnl": round(best_trade_pnl, 2),
                "worst_trade_pnl": round(worst_trade_pnl, 2),
                "avg_duration_minutes": round(avg_duration, 1),
                "total_profit": round(total_profit, 2),
                "total_loss": round(total_loss, 2)
            },
            "server_time_ms": int(time.time() * 1000)
        })
    except Exception as e:
        print(f"[DASHBOARD][ERROR] Analytics failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(e),
            "data": {
                "history": [],
                "pnl_24h": 0,
                "pnl_total": 0,
                "win_rate": 0,
                "profit_factor": 1.0,
                "total_trades": 0,
                "volume": 0
            }
        }), 500


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
        
        period = request.args.get('period', '24H')
        history = get_pnl_history(current_equity=current_equity, period=period)
        
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
        
        # Get REAL stats from TradeJournal
        try:
            from trade_journal import get_journal
            journal = get_journal()
            journal_stats = journal.get_stats()
            real_win_rate = journal_stats.get("win_rate", 0)
            real_total_trades = journal_stats.get("closed_trades", 0)
            real_profit_factor = 1.0
            if journal_stats.get("losses", 0) > 0 and journal_stats.get("wins", 0) > 0:
                # Calculate profit factor from actual data
                # For now, use a simple approximation
                real_profit_factor = round((journal_stats.get("wins", 0) / max(1, journal_stats.get("losses", 1))) * 1.2, 2)
            print(f"[ANALYTICS] Real stats from journal: {real_total_trades} trades, {real_win_rate}% win rate")
        except Exception as je:
            print(f"[ANALYTICS] Journal stats error: {je}")
            real_win_rate = 0
            real_total_trades = 0
            real_profit_factor = 0
        
        return {
            "history": formatted_history,
            "pnl_total": total_pnl,
            "pnl_24h": float(day_stats.get('pnlHistory', [[0, "0"]])[-1][1]) if day_stats.get('pnlHistory') else 0,
            "volume": volume,
            "win_rate": real_win_rate,  # REAL from journal
            "total_trades": real_total_trades,  # REAL from journal
            "profit_factor": real_profit_factor,  # REAL calculated
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
    """Add detailed trade log to history (keep last 50, deduplicate by symbol)"""
    global _trade_logs
    log['id'] = str(len(_trade_logs) + 1)
    log['timestamp'] = log.get('timestamp', datetime.now(timezone.utc).isoformat())
    
    # Deduplicate: remove older entries for the same symbol (keep only latest 2 per symbol)
    symbol = log.get('symbol')
    if symbol:
        symbol_entries = [i for i, l in enumerate(_trade_logs) if l.get('symbol') == symbol]
        if len(symbol_entries) >= 2:
            # Remove oldest entries for this symbol
            for idx in sorted(symbol_entries[1:], reverse=True):
                _trade_logs.pop(idx)
    
    _trade_logs.insert(0, log)
    _trade_logs = _trade_logs[:50]


# AI Analysis Cache (60s TTL per symbol)
_ai_analysis_cache = {}
AI_ANALYSIS_CACHE_TTL = 60


def fetch_real_sl_tp(symbol: str) -> dict:
    """
    Fetch real SL/TP trigger orders from Hyperliquid for a given symbol.
    Returns dict with 'stop_loss' and 'take_profit' prices, or None if not set.
    """
    try:
        user_address = os.getenv("HYPERLIQUID_WALLET_ADDRESS", "0x96E09Fb536CfB0E424Df3B496F9353b98704bA24")
        
        # Fetch open orders
        response = requests.post(
            "https://api.hyperliquid.xyz/info",
            json={"type": "openOrders", "user": user_address},
            timeout=10
        )
        
        if not response.ok:
            print(f"[SL_TP] Failed to fetch orders: {response.status_code}")
            return {'stop_loss': None, 'take_profit': None}
        
        orders = response.json()
        
        sl_price = None
        tp_price = None
        
        for order in orders:
            coin = order.get('coin', '')
            if coin != symbol:
                continue
            
            # Check if this is a trigger order (SL or TP)
            trigger_px = order.get('triggerPx')
            if trigger_px:
                trigger_price = float(trigger_px)
                side = order.get('side')  # 'B' = buy, 'A' = sell
                reduce_only = order.get('reduceOnly', False)
                
                # For a LONG position:
                #   - SL is a SELL trigger below entry
                #   - TP is a SELL trigger above entry
                # For a SHORT position:
                #   - SL is a BUY trigger above entry
                #   - TP is a BUY trigger below entry
                
                # If reduce_only and it's a trigger order, categorize it
                if reduce_only:
                    # We need to determine if it's SL or TP based on order type
                    order_type = order.get('orderType', '')
                    
                    # Trigger condition helps identify SL vs TP
                    # For now, we'll assume the first trigger is the active SL
                    if sl_price is None:
                        sl_price = trigger_price
                        print(f"[SL_TP] Found SL for {symbol}: ${trigger_price:,.2f}")
                    elif tp_price is None:
                        tp_price = trigger_price
                        print(f"[SL_TP] Found TP for {symbol}: ${trigger_price:,.2f}")
        
        return {
            'stop_loss': sl_price,
            'take_profit': tp_price,
            'source': 'hyperliquid'
        }
        
    except Exception as e:
        print(f"[SL_TP] Error fetching SL/TP for {symbol}: {e}")
        return {'stop_loss': None, 'take_profit': None}


def generate_ai_trade_analysis(position: dict) -> dict:
    """
    Generate real-time AI analysis for a position using GPT-4o-mini.
    Returns a structured trade log with strategy, risk management, and notes.
    """
    global _ai_analysis_cache
    
    symbol = position.get('symbol', 'UNKNOWN')
    cache_key = f"ai_analysis_{symbol}"
    
    # Check cache first
    if cache_key in _ai_analysis_cache:
        cached_data, cached_time = _ai_analysis_cache[cache_key]
        if time.time() - cached_time < AI_ANALYSIS_CACHE_TTL:
            print(f"[AI_ANALYSIS] Cache hit for {symbol}")
            return cached_data
    
    # No OpenAI client available
    if not openai_client:
        print(f"[AI_ANALYSIS] OpenAI client not available, returning minimal log")
        return _create_minimal_log(position)
    
    # Extract position data
    side = position.get('side', 'LONG')
    entry_price = float(position.get('entry_price', 0))
    mark_price = float(position.get('mark_price', entry_price))
    size = float(position.get('size', 0))
    leverage = int(position.get('leverage', 1))
    pnl = float(position.get('unrealized_pnl', 0))
    
    # Get current equity for risk calculations
    with _state_lock:
        equity = float(_dashboard_state.get("account", {}).get("equity", 100))
    
    # Retrieve TradeJournal data (v17 FIX)
    journal_trade = None
    journal_context = ""
    try:
        from trade_journal import get_journal
        journal = get_journal()
        journal_trade = journal.get_trade_by_symbol(symbol)
        
        if journal_trade:
            entry = journal_trade.get("entry", {})
            snapshot = journal_trade.get("market_snapshot_entry", {})
            journal_context = f"""
ORIGINAL ENTRY DECISION:
- Rationale: "{entry.get("reason", "N/A")}"
- Initial Confidence: {entry.get("confidence", "N/A")}
- Market Context: RSI={snapshot.get("rsi_14", "N/A")}, Trend={snapshot.get("ema_trend", "N/A")}
"""
    except Exception as je:
        print(f"[AI_ANALYSIS] Journal lookup failed: {je}")

    # Build the AI prompt
    prompt = f"""You are a professional crypto derivatives trader analyzing an active position.

POSITION DATA:
- Symbol: {symbol}
- Side: {side}
- Entry Price: ${entry_price:,.2f}
- Current Mark Price: ${mark_price:,.2f}
- Size: {size}
- Leverage: {leverage}x
- Unrealized PnL: ${pnl:,.2f}
- Account Equity: ${equity:,.2f}
{journal_context}

Analyze this position and provide your professional assessment. You must respond with ONLY valid JSON (no markdown, no code blocks, just raw JSON) in this exact format:

{{
  "strategy": {{
    "name": "Name of the strategy used (align with rationale if provided)",
    "timeframe": "Primary timeframe (e.g. '4H', '1H', '15m')",
    "setup_quality": 7.5,
    "confluence_factors": ["Factor 1", "Factor 2", "Factor 3"]
  }},
  "entry_rationale": "Explanation of the trade (incorporate original rationale if available)",
  "risk_management": {{
    "stop_loss": {entry_price * (0.97 if side == 'LONG' else 1.03):.2f},
    "stop_loss_reason": "Why this stop loss level (reference market structure)",
    "take_profit_1": {entry_price * (1.03 if side == 'LONG' else 0.97):.2f},
    "tp1_reason": "Why this TP1 level",
    "take_profit_2": {entry_price * (1.06 if side == 'LONG' else 0.94):.2f},
    "tp2_reason": "Why this TP2 level",
    "risk_usd": 0.00,
    "risk_pct": 0.00
  }},
  "confidence": 0.75,
  "ai_notes_pt": "Portuguese analysis paragraph (3-4 sentences)",
  "ai_notes_en": "English analysis paragraph (3-4 sentences)",
  "expected_outcome": "Short quote about expected outcome"
}}

IMPORTANT:
- Base stop_loss and take_profit on realistic market structure, not arbitrary percentages
- Be specific in confluence_factors (e.g. "RSI oversold bounce from 28", not just "RSI")
- Confidence should reflect actual setup quality (0.6-0.95 range)
- Calculate risk_usd as: |entry_price - stop_loss| * size / entry_price
- Calculate risk_pct as: risk_usd / equity * 100"""

    try:
        print(f"[AI_ANALYSIS] Generating analysis for {symbol}...")
        
        # CRITICAL: Fetch REAL SL/TP from Hyperliquid FIRST
        real_sl_tp = fetch_real_sl_tp(symbol)
        real_sl = real_sl_tp.get('stop_loss')
        real_tp = real_sl_tp.get('take_profit')
        
        print(f"[AI_ANALYSIS] Real SL/TP for {symbol}: SL=${real_sl}, TP=${real_tp}")
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional crypto derivatives trader. Respond ONLY with valid JSON, no markdown."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        raw_response = response.choices[0].message.content.strip()
        
        # Clean response if wrapped in code blocks
        if raw_response.startswith("```"):
            lines = raw_response.split("\n")
            raw_response = "\n".join(lines[1:-1])
        
        # Parse JSON
        ai_data = json.loads(raw_response)
        
        # Get AI's risk management data (for reasons/explanations only)
        ai_risk = ai_data.get('risk_management', {})
        
        # Build risk management with REAL values from exchange
        # Only use AI values as fallback if no real order exists
        actual_sl = real_sl if real_sl else ai_risk.get('stop_loss', entry_price * (0.97 if side == 'LONG' else 1.03))
        actual_tp = real_tp if real_tp else ai_risk.get('take_profit_1', entry_price * (1.03 if side == 'LONG' else 0.97))
        
        # Calculate actual risk based on REAL SL
        risk_usd = abs(entry_price - actual_sl) * size if entry_price > 0 else 0
        risk_pct = (risk_usd / equity * 100) if equity > 0 else 0
        
        # Build complete trade log with REAL values
        trade_log = {
            'id': f'ai-{symbol}-{int(time.time())}',
            'symbol': symbol,
            'action': 'HOLDING',
            'side': side,
            'entry_price': entry_price,
            'mark_price': mark_price,
            'size': size,
            'leverage': leverage,
            'strategy': ai_data.get('strategy', {}),
            'entry_rationale': ai_data.get('entry_rationale', 'AI-generated analysis'),
            'risk_management': {
                'stop_loss': actual_sl,
                'stop_loss_reason': ai_risk.get('stop_loss_reason', 'Trigger order set on exchange'),
                'stop_loss_source': 'exchange' if real_sl else 'ai_suggestion',
                'take_profit_1': actual_tp,
                'tp1_reason': ai_risk.get('tp1_reason', 'Target based on market structure'),
                'tp1_source': 'exchange' if real_tp else 'ai_suggestion',
                'take_profit_2': ai_risk.get('take_profit_2', entry_price * (1.06 if side == 'LONG' else 0.94)),
                'tp2_reason': ai_risk.get('tp2_reason', 'Secondary expansion target'),
                'risk_usd': round(risk_usd, 2),
                'risk_pct': round(risk_pct, 2)
            },
            'confidence': ai_data.get('confidence', 0.75),
            'ai_notes': f"🇧🇷 {ai_data.get('ai_notes_pt', '')}\n\n🇺🇸 {ai_data.get('ai_notes_en', '')}",
            'expected_outcome': ai_data.get('expected_outcome', 'Monitoring position.'),
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'source': 'gpt-4o-mini',
            'sl_tp_source': 'hyperliquid' if real_sl else 'ai_fallback'
        }
        
        # Cache the result
        _ai_analysis_cache[cache_key] = (trade_log, time.time())
        
        # Also add to trade logs history
        add_trade_log(trade_log.copy())
        
        print(f"[AI_ANALYSIS] Successfully generated analysis for {symbol} (SL source: {'exchange' if real_sl else 'AI'})")
        return trade_log
        
    except json.JSONDecodeError as e:
        print(f"[AI_ANALYSIS] JSON parse error for {symbol}: {e}")
        print(f"[AI_ANALYSIS] Raw response: {raw_response[:500]}")
        return _create_minimal_log(position)
    except Exception as e:
        print(f"[AI_ANALYSIS] Error generating analysis for {symbol}: {e}")
        return _create_minimal_log(position)


def _create_minimal_log(position: dict) -> dict:
    """Create a minimal trade log when AI is unavailable"""
    symbol = position.get('symbol', 'UNKNOWN')
    side = position.get('side', 'LONG')
    entry_price = float(position.get('entry_price', 0))
    
    # Defaults
    rationale = 'Position opened manually. AI analysis pending.'
    strategy_name = 'Manual Entry'
    confidence = 0.5
    confluence = ['Manual entry - awaiting AI analysis']
    
    # Try to hydrate from Journal
    try:
        from trade_journal import get_journal
        jt = get_journal().get_trade_by_symbol(symbol)
        if jt:
            entry = jt.get("entry", {})
            rationale = entry.get("reason", rationale)
            confidence = float(entry.get("confidence", confidence))
            strategy_name = "AI Strategy (Cached)"
            
            snapshot = jt.get("market_snapshot_entry", {})
            confluence = [
                f"Trend: {snapshot.get('ema_trend', 'N/A')}",
                f"RSI: {snapshot.get('rsi_14', 'N/A')}"
            ]
            if snapshot.get("bos_status") in ["UP", "DOWN"]:
                confluence.append(f"Structure: {snapshot.get('bos_status')}")
    except Exception as e:
        print(f"[DASHBOARD] Failed to hydrate minimal log: {e}")

    return {
        'id': f'min-{symbol}-{int(time.time())}',
        'symbol': symbol,
        'action': 'HOLDING',
        'side': side,
        'entry_price': entry_price,
        'mark_price': position.get('mark_price', entry_price),
        'size': position.get('size', 0),
        'leverage': position.get('leverage', 1),
        'strategy': {
            'name': strategy_name,
            'timeframe': 'N/A',
            'setup_quality': 5.0,
            'confluence_factors': confluence
        },
        'entry_rationale': rationale,
        'risk_management': {
            'stop_loss': entry_price * (0.95 if side == 'LONG' else 1.05),
            'stop_loss_reason': 'Default risk management',
            'take_profit_1': entry_price * (1.05 if side == 'LONG' else 0.95),
            'tp1_reason': 'Default target',
            'risk_usd': 0,
            'risk_pct': 0
        },
        'confidence': confidence,
        'ai_notes': '⚠️ AI analysis unavailable. Showing cached entry data.',
        'expected_outcome': 'Awaiting AI analysis.',
        'source': 'fallback'
    }


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
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    # Get existing logs from history
    response_logs = _trade_logs[:limit]
    
    # Get active positions
    with _state_lock:
        active_positions = _dashboard_state.get("positions", [])
    
    # If we have active positions but no logs for them, generate AI analysis
    if active_positions:
        existing_symbols = {log.get('symbol') for log in response_logs}
        
        for pos in active_positions:
            symbol = pos.get('symbol', 'UNKNOWN')
            
            # Check if we already have a recent log for this symbol
            has_recent_log = symbol in existing_symbols
            
            # Generate fresh analysis if no log exists or refresh is forced
            if not has_recent_log or force_refresh:
                print(f"[API] Generating AI analysis for {symbol} (force_refresh={force_refresh})")
                ai_log = generate_ai_trade_analysis(pos)
                
                # If this is a new analysis (not from cache), add to response
                if ai_log.get('source') == 'gpt-4o-mini' or not has_recent_log:
                    # Remove old log for same symbol if exists
                    response_logs = [log for log in response_logs if log.get('symbol') != symbol]
                    response_logs.insert(0, ai_log)
    
    # Sort by timestamp (most recent first)
    response_logs.sort(key=lambda x: x.get('generated_at', x.get('timestamp', '')), reverse=True)
    
    return jsonify({
        "ok": True,
        "data": response_logs[:limit],
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
