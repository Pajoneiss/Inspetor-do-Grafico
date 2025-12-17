"""
Dashboard API for Inspetor do Gráfico
Provides real-time data for the web dashboard
"""
import os
import json
import time
import threading
from datetime import datetime, timezone
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

# Shared state file path
STATE_FILE = os.path.join(os.path.dirname(__file__), "dashboard_state.json")

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
    "account": {
        "equity": 0,
        "balance": 0,
        "buying_power": 0,
        "positions_count": 0
    },
    "positions": [],
    "ai_actions": [],
    "market": {
        "fear_greed": 50,
        "btc_dominance": 0,
        "top_symbols": []
    },
    "engine_status": "offline"
}

# Lock for thread-safe updates
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
        action["timestamp"] = datetime.utcnow().isoformat()
        _dashboard_state["ai_actions"].insert(0, action)
        _dashboard_state["ai_actions"] = _dashboard_state["ai_actions"][:50]


@app.route('/')
def serve_dashboard():
    """Serve main dashboard page"""
    return send_from_directory('dashboard', 'index.html')


@app.route('/api/status')
def api_status():
    """Get current account status"""
    with _state_lock:
        return jsonify({
            "ok": True,
            "data": {
                "equity": _dashboard_state["account"]["equity"],
                "balance": _dashboard_state["account"]["balance"],
                "buying_power": _dashboard_state["account"]["buying_power"],
                "positions_count": _dashboard_state["account"]["positions_count"],
                "engine_status": _dashboard_state["engine_status"],
                "last_update": _dashboard_state["last_update"],
                "last_update_ms": _dashboard_state.get("last_update_ms", 0),
                "server_time_ms": int(time.time() * 1000)
            }
        })


@app.route('/api/positions')
def api_positions():
    """Get all open positions"""
    with _state_lock:
        return jsonify({
            "ok": True,
            "data": _dashboard_state["positions"]
        })


@app.route('/api/actions')
def api_actions():
    """Get recent AI actions"""
    limit = request.args.get('limit', 20, type=int)
    with _state_lock:
        return jsonify({
            "ok": True,
            "data": _dashboard_state["ai_actions"][:limit]
        })


@app.route('/api/market')
def api_market():
    """Get market overview"""
    with _state_lock:
        return jsonify({
            "ok": True,
            "data": _dashboard_state["market"]
        })


@app.route('/api/health')
def api_health():
    """Health check endpoint"""
    return jsonify({
        "ok": True,
        "service": "dashboard",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server_time_ms": int(time.time() * 1000)
    })


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


def run_dashboard_server(port: int = 8080, host: str = "0.0.0.0"):
    """Run dashboard server in background thread"""
    def _run():
        print(f"[DASHBOARD] Starting on http://{host}:{port}")
        app.run(host=host, port=port, debug=False, use_reloader=False)
    
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread


# Load saved state on import
try:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            saved_state = json.load(f)
            _dashboard_state.update(saved_state)
            print(f"[DASHBOARD] Loaded saved state")
except Exception as e:
    print(f"[DASHBOARD] Could not load saved state: {e}")
