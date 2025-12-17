"""
Dashboard API - Flask server for Engine V0 Dashboard
"""
import os
import json
import time
import re
import threading
from datetime import datetime, timezone
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

# State file for persistence
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
    return send_from_directory(os.path.join(DASHBOARD_NEXT_PATH, '_next'), subpath)


@app.route('/ai/')
def serve_ai_page():
    """Serve AI page"""
    if os.path.exists(os.path.join(DASHBOARD_NEXT_PATH, 'ai', 'index.html')):
        return send_from_directory(os.path.join(DASHBOARD_NEXT_PATH, 'ai'), 'index.html')
    return "Not found", 404


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
    # Fallback to old dashboard
    old_file = os.path.join(DASHBOARD_OLD_PATH, filename)
    if os.path.exists(old_file):
        return send_from_directory(DASHBOARD_OLD_PATH, filename)
    # 404
    return "Not found", 404


@app.route('/api/status')
def api_status():
    """Get current bot status"""
    with _state_lock:
        return jsonify({
            "ok": True,
            "data": {
                "equity": _dashboard_state["account"]["equity"],
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
    """Get open positions"""
    with _state_lock:
        return jsonify({
            "ok": True,
            "data": _dashboard_state["positions"]
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


@app.route('/api/ai/thoughts')
def api_ai_thoughts():
    """Get AI thoughts feed"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify({
        "ok": True,
        "data": _ai_thoughts[:limit],
        "server_time_ms": int(time.time() * 1000)
    })


@app.route('/api/ai/ask', methods=['POST'])
def api_ai_ask():
    """Answer questions about the bot (READ-ONLY, blocks commands)"""
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
    
    # Simple Q&A responses
    with _state_lock:
        state = _dashboard_state.copy()
    
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['equity', 'balance', 'saldo', 'quanto']):
        equity = state.get('account', {}).get('equity', 0)
        buying_power = state.get('account', {}).get('buying_power', 0)
        answer = f"Your current equity is ${equity:.2f} with buying power of ${buying_power:.2f}."
    elif any(word in question_lower for word in ['position', 'posição', 'posicao']):
        positions = state.get('positions', [])
        if positions:
            symbols = ", ".join([p.get('symbol', '?') for p in positions])
            answer = f"You have {len(positions)} open positions: {symbols}"
        else:
            answer = "You have no open positions."
    elif any(word in question_lower for word in ['status', 'running', 'funcionando']):
        status = state.get('engine_status', 'unknown')
        update = state.get('last_update', 'N/A')
        answer = f"Engine is {status}. Last update: {update}."
    else:
        answer = "I can answer questions about your equity, positions, and bot status. For trading commands, please use Telegram."
    
    return jsonify({
        "ok": True,
        "answer": answer,
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
    print(f"[DASHBOARD] Failed to load saved state: {e}")
