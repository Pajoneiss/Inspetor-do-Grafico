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
        
        Args:
            state: Current market state with:
                - time: Current timestamp
                - equity: Account equity
                - positions_count: Number of open positions
                - price: Current price of symbol
                - symbol: Trading symbol
                - live_trading: Whether live trading is enabled
        
        Returns:
            dict: {
                "summary": "string",
                "confidence": 0.0-1.0,
                "actions": [{"type":"PLACE_ORDER","symbol":"BTC","side":"BUY","size":0.001,"orderType":"MARKET"}]
            }
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
                max_tokens=500
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
- Having open positions does NOT automatically prevent new trades. If you see a new edge and execution is feasible with current account state, you may open another position or hedge.
- If you choose HOLD, it must be because: (a) no actionable edge with the given data, or (b) best action is to wait for a specific trigger.
- If position is open, consider proactive management: tighten/loosen stop based on structure, move to breakeven when justified, partial take at levels, cancel stale orders, adjust TP to realistic levels, hedge if regime flips.

ORDER/EXECUTION HYGIENE
- Prefer actions that are idempotent and stable across 10s ticks:
  - Avoid constantly moving orders every tick unless the price meaningfully moved or a candle closed / regime changed.
  - If modifying SL/TP, only do so with a specific rationale (structure break, new swing low/high, VWAP reclaim/loss, etc.).
- If you recommend placing or editing orders, be explicit: price/level, side, type (market/limit), and why that level.

USE OF SCAN SCORES
- Scan scores are signals, not truth. If you don't know what "BTC:90" means (momentum? trend? confidence?), treat it as a hint only.
- If scan definition is missing, request it once via "next_call_triggers" and do not overfit decisions to the score.

CONSISTENT CONFIDENCE
- confidence ∈ [0,1]. Base it on:
  - Data completeness (more complete => higher)
  - Setup clarity (clear invalidation & target => higher)
  - Regime alignment (HTF aligns with entry TF => higher)
- If confidence < 0.60, prefer HOLD or minimal management unless there is an urgent safety action.

OUTPUT FORMAT (STRICT JSON ONLY - NO MARKDOWN)
{
  "summary": "one or two sentences, practical, no fluff",
  "confidence": 0.0,
  "actions": [
    {
      "type": "PLACE_ORDER" | "ADD_TO_POSITION" | "CLOSE_POSITION" | "CLOSE_PARTIAL" | "SET_STOP_LOSS" | "SET_TAKE_PROFIT" | "MOVE_STOP_TO_BREAKEVEN" | "CANCEL_ALL_ORDERS" | "NO_TRADE",
      "symbol": "BTC" | "ETH" | "...",
      "side": "BUY" | "SELL" | "LONG" | "SHORT" | null,
      "size": 0.01,
      "price": null,
      "stop_price": null,
      "tp_price": null,
      "leverage": 25,
      "reason": "short, specific justification tied to provided data"
    }
  ],
  "next_call_triggers": [
    "bullet triggers that would change decision (e.g., candle close above/below X, EMA cross, break of swing low/high, funding spike, order filled, price hits level)"
  ],
  "data_needed": [
    "ONLY if missing info blocks a higher-quality decision: e.g., 'meaning of scan score', 'latest 1h candle close', 'current open orders per symbol', 'VWAP timeframe', 'recent swing levels'"
  ]
}

IMPORTANT
- Keep actions minimal: 0 to 3 actions per call.
- If you output NO_TRADE, still provide meaningful next_call_triggers (so the engine can call you at the right moments).
- Pure JSON only, no markdown blocks, no ```json```.
- LEVERAGE: You decide leverage per trade (1-50x). Include "leverage" field in PLACE_ORDER/ADD_TO_POSITION actions."""


    def _build_prompt(self, state: Dict[str, Any]) -> str:

        """Build prompt for AI"""
        # Format positions
        positions_str = ""
        if state.get("positions"):
            if isinstance(state["positions"], dict):
                # positions_by_symbol format
                for symbol, pos in state["positions"].items():
                    positions_str += f"  - {symbol}: {pos['side']} {pos['size']} @ ${pos['entry_price']:.2f} (PnL: ${pos['unrealized_pnl']:.2f})\n"
            else:
                # list format
                for p in state["positions"]:
                    positions_str += f"  - {p['symbol']}: {p['side']} {p['size']} @ ${p['entry_price']:.2f} (PnL: ${p['unrealized_pnl']:.2f})\n"
        
        if not positions_str:
            positions_str = "  (none)\n"
        
        # Format prices
        prices_str = ""
        if state.get("prices"):
            for symbol, price in list(state["prices"].items())[:10]:  # Show top 10
                prices_str += f"  - {symbol}: ${price:.2f}\n"
        elif state.get("price") and state.get("symbol"):
            prices_str = f"  - {state['symbol']}: ${state['price']:.2f}\n"
        
        # Format snapshot symbols
        snapshot_symbols = state.get("snapshot_symbols", state.get("symbols", []))
        if isinstance(snapshot_symbols, list) and len(snapshot_symbols) > 0:
            symbols_str = ", ".join(snapshot_symbols[:15])
            if len(snapshot_symbols) > 15:
                symbols_str += f" (+{len(snapshot_symbols) - 15} more)"
        else:
            symbols_str = state.get("symbol", "BTC")
        
        # v11.0: Format symbol briefs for multi-symbol scan with reasons
        symbol_briefs = state.get("symbol_briefs", {})
        briefs_lines = []
        # Sort by score descending
        sorted_briefs = sorted(symbol_briefs.items(), key=lambda x: x[1].get("score", 0), reverse=True)
        for symbol, brief in sorted_briefs[:11]:  # Show all 11
            reason = brief.get('reason', '') 
            reason_str = f" [{reason}]" if reason else ""
            briefs_lines.append(
                f"  {symbol}: ${brief.get('price', 0)} | {brief.get('trend', '?')} | RSI={brief.get('rsi', 50):.0f} | score={brief.get('score', 0):.0f}{reason_str}"
            )
        briefs_str = "\n".join(briefs_lines) if briefs_lines else "(sem dados)"

        # Position details for context
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
- Buying Power: ${state.get('buying_power', state.get('equity', 0) * 40):.2f}
- Leverage: {state.get('leverage', 40)}x

POSIÇÕES ({state.get('positions_count', 0)}):
{positions_str}
DETALHES:
{details_str}

SCAN DE MERCADO:
{briefs_str}

O que você decide fazer?"""

    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON response from AI"""
        try:
            # Try direct parse
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_str = content[start:end].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # Try to extract JSON from any code block
            if "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                json_str = content[start:end].strip()
                # Remove language identifier if present
                if json_str.startswith("json"):
                    json_str = json_str[4:].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # Try to find JSON object in content
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
            
            # Failed to parse
            print(f"[LLM][ERROR] invalid_json: {content[:200]}")
            return {
                "summary": "invalid_json",
                "confidence": 0.0,
                "actions": []
            }
