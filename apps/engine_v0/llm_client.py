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
- If position is open, consider proactive management: adjust stops only when market structure has SIGNIFICANTLY changed (new swing high/low, break of key level), move to breakeven when justified, partial take at levels, adjust TP to realistic levels.
- **ANTI-OVERTRADING:** Avoid adjusting stops on every tick. Stops should remain stable unless there's a clear structural reason to move them.

ANTI-CHURN INTELLIGENCE
- Avoid re-entering the same coin immediately unless the setup has MEANINGFULLY improved.
- Avoid "score chasing" - a high scan score alone is NOT enough if nothing changed since last exit.

ORDER/EXECUTION HYGIENE
- Prefer actions that are idempotent and stable across 10s ticks.
- If you recommend placing or editing orders, be explicit: price/level, side, type (market/limit), and why that level.

🧼 STATE INTEGRITY (ANTI-BUG)
- If you detect state inconsistency (position/orders don't match reported state), prioritize safety: NO_TRADE or minimal actions to stabilize (cancel clearly invalid orders, adjust protection), always explaining why.

🧯 MISSING DATA PROTOCOL
- If critical data is missing, explicitly state "INSUFFICIENT DATA" and return NO_TRADE (or only urgent safety actions), specifying exactly what data is needed.

📈 SWING vs SCALP FLEXIBILITY
- You can close quickly (scalp) or let it run (swing) based on how the context evolves.
- If you decide to "let it become a swing", explain why (thesis + context) and what triggers would make you reduce/exit.
- Adjust stops based on market structure (SMC-style): swing highs/lows, order blocks, liquidity zones, not arbitrary percentages.

📊 CONSISTENT CONFIDENCE (NO FIXED THRESHOLD)
- confidence ∈ [0,1] based on data quality + setup clarity.
- If confidence is low or data is incomplete/contradictory: prefer HOLD, unless there's an urgent safety action (e.g., liquidation risk / missing stop).

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
      "stop_price": <calculate based on market structure and support/resistance>,
      "tp_price": <null or specific target based on R:R>,
      "leverage": <1-50x based on conviction and volatility>,
      "reason": "short, specific justification"
    }
  ],
  "next_call_triggers": ["triggers that would change decision"],
  
  // OPTIONAL BUT RECOMMENDED
  "decision_id": "symbol_thesis_v1",
  "state_snapshot": {
    "thesis": "short",
    "key_levels": ["..."],
    "invalidation": "...",
    "what_changed": "..."
  }
}

🧠 DISCIPLINE (NO HARD LIMITS)
- Prefer the minimum actions necessary to express your decision.
- Avoid "churn" (entering/exiting/adjusting without relevant new information).
- Only do multiple chained actions when there's a clear, verifiable reason (material structure change, necessary execution, or risk management).

🧾 SELF-CHECK (MANDATORY BEFORE ACTING)
Before any action, answer mentally:
1) What changed in the data to make me act now?
2) If I were flat, would I make the same decision?
3) What event/level invalidates my thesis?
4) Is there a better action than doing nothing?

🧩 SCENARIO THINKING (AVOID SINGLE-STORY BIAS)
- Consider at least 2 scenarios (bull/bear or continuation/reversal) with clear triggers that confirm/invalidate each.
- State which scenario is currently more probable based on data, and what would flip your view.

⏱️ DATA FRESHNESS (ANTI-STALE DATA)
- Always consider timestamp/freshness of data provided
- Distinguish closed candle vs forming candle (if available)
- If latency, gaps, or inconsistency detected: declare uncertainty and adjust stance
- Never act on stale data without acknowledging the risk

🗂️ STATE SNAPSHOT (CONSISTENCY)
- Maintain mental state per symbol: current thesis, key levels, invalidation, what changed
- Include in JSON output (optional but recommended):
  "state_snapshot": {
    "thesis": "short description",
    "key_levels": ["level1", "level2"],
    "invalidation": "what proves me wrong",
    "what_changed": "why I'm acting now"
  }

🧬 DECISION_ID (THESIS TRACKING)
- Generate short ID per symbol thesis (e.g., "BTC_breakout_v1")
- Reuse same ID if thesis unchanged
- Change ID if thesis changes
- Include in JSON output: "decision_id": "symbol_thesis_version"

🧲 NEXT_CALL_TRIGGERS (MANDATORY)
- Always include 1–3 objective conditions that would make you change your decision on the next tick (e.g., losing level X, breaking level Y, setup invalidation, regime change).

🧱 NO VAGUENESS IN REASONS
- Do NOT use generic justifications ("looks strong", "seems bullish", "good momentum") without pointing to the specific data/level/indicator that supports it.
- Every reason must reference concrete inputs from the state.

IMPORTANT
- **FULL AUTONOMY:** You are not limited to one trade. You can open multiple positions if the account has buying power.
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
        """
        Parse JSON response from AI with robust repair for truncation
        """
        if not content:
            return {"summary": "empty_response", "confidence": 0.0, "actions": []}
            
        try:
            # 1. Clean markdown if present
            clean_content = content.replace("```json", "").replace("```", "").strip()
            
            # 2. Try direct parse
            try:
                return json.loads(clean_content)
            except json.JSONDecodeError:
                pass
                
            # 3. Robust Extraction and Repair
            # Find first { and last }
            start = clean_content.find("{")
            if start < 0:
                print(f"[LLM][ERROR] No JSON object found in response")
                return {"summary": "no_json_found", "confidence": 0.0, "actions": []}
                
            json_str = clean_content[start:]
            
            # Try to fix truncated JSON
            # Count braces and brackets
            open_braces = json_str.count("{")
            close_braces = json_str.count("}")
            open_brackets = json_str.count("[")
            close_brackets = json_str.count("]")
            
            # If truncated in the middle of a string or array
            temp_str = json_str
            
            # Fix unclosed quotes in the last line if any
            lines = temp_str.split('\n')
            if lines:
                last_line = lines[-1]
                if last_line.count('"') % 2 != 0:
                    lines[-1] = last_line + '"'
                temp_str = '\n'.join(lines)
            
            # Add missing closing symbols
            while open_brackets > close_brackets:
                temp_str += "]"
                close_brackets += 1
            while open_braces > close_braces:
                temp_str += "}"
                close_braces += 1
                
            # Try parsing the repaired string
            try:
                return json.loads(temp_str)
            except json.JSONDecodeError as e:
                # If still failing, try to find the last valid object boundary
                # This is a last resort "best effort"
                last_comma = temp_str.rfind(",")
                if last_comma > 0:
                    retry_str = temp_str[:last_comma].strip()
                    # Re-balance after truncation
                    o_br = retry_str.count("{")
                    c_br = retry_str.count("}")
                    o_bk = retry_str.count("[")
                    c_bk = retry_str.count("]")
                    while o_bk > c_bk:
                        retry_str += "]"
                        c_bk += 1
                    while o_br > c_br:
                        retry_str += "}"
                        c_br += 1
                    try:
                        return json.loads(retry_str)
                    except:
                        pass
            
            print(f"[LLM][ERROR] Failed to repair JSON: {content[:100]}...")
            return {"summary": "invalid_json", "confidence": 0.0, "actions": []}
        except Exception as e:
            print(f"[LLM][ERROR] Json parser exception: {e}")
            return {"summary": "parser_error", "confidence": 0.0, "actions": []}
