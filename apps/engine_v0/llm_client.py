"""
LLM Client for Engine V0
OpenAI integration for trading decisions
"""
import json
import traceback
from typing import Dict, Any
from openai import OpenAI

from config import OPENAI_API_KEY, AI_MODEL


class LLMClient:
    """OpenAI client for trading decisions"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.api_key = OPENAI_API_KEY
        self.model = AI_MODEL
        
        if not self.api_key:
            print("[LLM][WARN] OPENAI_API_KEY not set")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
            print(f"[LLM] Initialized with model: {self.model}")
    
    def decide(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get trading decision from AI
        """
        print("[LLM] called")
        
        if not self.client:
            print("[LLM][ERROR] OpenAI client not initialized")
            return {
                "summary": "no_api_key",
                "confidence": 0.0,
                "actions": []
            }
        
        try:
            # Build prompt
            prompt = self._build_prompt(state)
            
            # Call OpenAI with STRICT system prompt
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=600  # Increased for more actions
            )

            # Extract response
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            decision = self._parse_json_response(content)
            
            # TAG ALL ACTIONS WITH SOURCE=LLM
            actions = decision.get("actions", [])
            for action in actions:
                action["source"] = "LLM"
            
            # Log decision
            actions_count = len(actions)
            summary = decision.get("summary", "")
            confidence = decision.get("confidence", 0.0)
            
            print(f'[LLM] decision actions={actions_count} summary="{summary}" conf={confidence:.2f}')
            
            # Send to dashboard API for AI Thoughts feed
            try:
                from dashboard_api import add_ai_thought
                symbols = list(set([a.get("symbol", "ALL") for a in actions if a.get("symbol")]))
                if not symbols:
                    symbols = ["ALL"]
                thought = {
                    "symbols": symbols,
                    "summary": summary,
                    "confidence": confidence,
                    "actions": [
                        {
                            "type": a.get("type", "UNKNOWN"),
                            "symbol": a.get("symbol", "ALL"),
                            "status": "executed" if a.get("type") != "NO_TRADE" else "skipped",
                            "reason": a.get("reason", "")
                        }
                        for a in actions
                    ]
                }
                add_ai_thought(thought)
            except Exception as e:
                print(f"[LLM] Failed to add thought to dashboard: {e}")
            
            return decision
            
        except Exception as e:
            print(f"[LLM][ERROR] {e}")
            traceback.print_exc()
            return {
                "summary": "error",
                "confidence": 0.0,
                "actions": []
            }
    
    def _get_system_prompt(self) -> str:
        """
        Professional discretionary trader prompt - NO hardcoded rules
        AI decides everything based on data provided
        """
        return """You are "Ladder Labs IA Trader", a professional discretionary crypto derivatives trader operating on Hyperliquid mainnet.

MISSION
- Maximize long-run risk-adjusted returns using the information provided by the engine (prices, positions, orders, indicators, scan scores, timeframes, funding, etc.).
- You have full authority to decide: open/close, add/reduce, hedge, move SL/TP, partial take, do nothing.
- Do NOT follow artificial constraints unless explicitly provided by the engine. (No hardcoded limits, no fixed caps. You decide like a pro.)

CRITICAL REALISM RULES (ANTI-FANTASY)
- Never claim "strong momentum", "bullish trend", "bearish" etc. unless you can point to explicit inputs that justify it (e.g., EMA relation, VWAP, structure, higher highs, breakout level, scan signal meaning).
- If the data needed to confirm an edge is missing, say so and default to the best action you can with current data (often HOLD), plus specify exactly what would change your decision in "next_call_triggers".
- Never fabricate fills, PnL, positions, order status, liquidation price, margin mode, leverage, or exchange behavior. Only use what is in the state.

DECISION STYLE (PRO TRADER)
- Always think in three layers:
  (1) Market regime / context (trend, range, volatility, key levels) across available timeframes.
  (2) Edge & setup quality (why this trade, why now, what invalidates).
  (3) Execution & management (entries, stops, take-profits, adds, partials, hedges, order hygiene).
- Your default is NOT "positions managed". Your default is: "Is there a better action right now than doing nothing?" If yes, do it. If no, hold with a clear reason.

WHEN POSITIONS EXIST
- **FULL POWER:** Having open positions does NOT prevent new trades. If you see edges on multiple symbols, open them. Manage your buying power like a professional.
- If you choose HOLD, it must be because: (a) no actionable edge with the given data, or (b) best action is to wait for a specific trigger.
- If position is open, consider proactive management: tighten/loosen stop based on structure, move to breakeven when justified, partial take at levels, adjust TP to realistic levels.

ANTI-CHURN INTELLIGENCE
- Avoid re-entering the same coin immediately unless the setup has MEANINGFULLY improved.
- Avoid "score chasing" - a high scan score alone is NOT enough if nothing changed since last exit.

ORDER/EXECUTION HYGIENE
- Prefer actions that are idempotent and stable across 10s ticks.
- If you recommend placing or editing orders, be explicit: price/level, side, type (market/limit), and why that level.

CONSISTENT CONFIDENCE
- confidence ∈ [0,1]. Base it on data quality and setup clarity.
- If confidence < 0.60, prefer HOLD unless there is an urgent safety action.

OUTPUT FORMAT (STRICT JSON ONLY - NO MARKDOWN)
{
  "summary": "one or two sentences, practical, no fluff",
  "confidence": <0.0-1.0 based on data quality, setup clarity, regime alignment>,
  "actions": [
    {
      "type": "PLACE_ORDER" | "ADD_TO_POSITION" | "CLOSE_POSITION" | "CLOSE_PARTIAL" | "SET_STOP_LOSS" | "SET_TAKE_PROFIT" | "MOVE_STOP_TO_BREAKEVEN" | "CANCEL_ALL_ORDERS" | "NO_TRADE",
      "symbol": <symbol from scan>,
      "side": "BUY" | "SELL" | "LONG" | "SHORT" | null,
      "size": <calculate based on risk/equity, suggest $10-50 notional>,
      "price": <null for MARKET, specific price for LIMIT>,
      "stop_price": <entry +/- (2-5% for volatile, 1-3% for BTC)>,
      "tp_price": <null or specific target based on R:R>,
      "leverage": <1-50x based on conviction and volatility>,
      "reason": "short, specific justification"
    }
  ],
  "next_call_triggers": ["triggers that would change decision"]
}

IMPORTANT
- **FULL AUTONOMY:** You are not limited to one trade. You can open multiple positions if the account has buying power.
- **ACTION LIMIT:** You can output up to 5 actions per tick if needed for complex management.
- Pure JSON only, no markdown blocks, no ```json```.
"""

    def _build_prompt(self, state: Dict[str, Any]) -> str:
        """Build prompt for AI"""
        # Format positions
        positions_str = ""
        if state.get("positions"):
            for symbol, pos in state["positions"].items():
                positions_str += f"  - {symbol}: {pos['side']} {pos['size']} @ ${pos['entry_price']:.2f} (PnL: ${pos['unrealized_pnl']:.2f})\n"
        
        if not positions_str:
            positions_str = "  (none)\n"
        
        # v11.0: Format symbol briefs for multi-symbol scan
        symbol_briefs = state.get("symbol_briefs", {})
        briefs_lines = []
        sorted_briefs = sorted(symbol_briefs.items(), key=lambda x: x[1].get("score", 0), reverse=True)
        for symbol, brief in sorted_briefs[:11]:
            reason = brief.get('reason', '') 
            reason_str = f" [{reason}]" if reason else ""
            briefs_lines.append(
                f"  {symbol}: ${brief.get('price', 0)} | {brief.get('trend', '?')} | score={brief.get('score', 0):.1f}{reason_str}"
            )
        briefs_str = "\n".join(briefs_lines) if briefs_lines else "(sem dados)"

        # Position details
        pos_details = state.get("position_details", {})
        details_lines = []
        for sym, data in pos_details.items():
            sl_str = f"SL=${data['current_sl']:.2f}" if data.get('current_sl') else "SL=None"
            tp_str = f"TP=${data['current_tp']:.2f}" if data.get('current_tp') else "TP=None"
            details_lines.append(f"  {sym}: PnL={data['pnl_pct']:.2f}% | entry=${data['entry_price']:.2f} | {sl_str} | {tp_str}")
        details_str = "\n".join(details_lines) if details_lines else "(sem posições)"
        
        return f"""DADOS DE MERCADO:

CONTA:
- Equity: ${state.get('equity', 0):.2f}
- Buying Power: ${state.get('buying_power', 0):.2f}

POSIÇÕES ({state.get('positions_count', 0)}):
{positions_str}
DETALHES:
{details_str}

SCAN DE MERCADO (TOP SIGNALS):
{briefs_str}

O que você decide fazer? Pense como um gestor de fundo de hedge."""

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON response from AI"""
        try:
            # Try direct parse
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(content[start:end])
                except:
                    pass
            
            print(f"[LLM][ERROR] invalid_json: {content[:100]}")
            return {"summary": "invalid_json", "confidence": 0.0, "actions": []}
