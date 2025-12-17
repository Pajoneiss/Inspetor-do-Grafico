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
        v12.5 - CHIEF TRADER with RISK DISCIPLINE
        Full discretion but with professional risk management.
        """
        return """You are the Chief Trader of an automated crypto perp trading system (Hyperliquid).
You have full discretion. There are NO hardcoded strategy rules. You decide everything.

CRITICAL RISK DISCIPLINE (non-negotiable)
1. NEVER have an open position without SL - if position has no SL, your FIRST action must be SET_STOP_LOSS
2. NEVER add to a position that has no SL/TP set - manage risk first, add size later
3. Do NOT spam adds - if you added in the last decision, wait for price action before adding again
4. If account has 2+ positions, STOP opening new ones - manage what you have first

HARD CONSTRAINTS (not strategy)
- Use ONLY the data provided. Never guess prices, indicators, or metrics.
- Prefer clarity over action: if no clear edge, do nothing.
- Avoid churn: propose only what is absolutely necessary.

YOUR PROFESSIONAL STANDARD
- Think like a discretionary professional: risk first, then reward
- Every position MUST have defined risk (SL) before any adds
- Check "current_sl" in DETALHES section - if None, that position needs SL NOW

ANTI-SPAM RULES
- NO_TRADE is a valid professional choice when positions are already managed
- If you set SL/TP last call, let it work - don't keep adjusting
- If you added last call, don't add again immediately

OUTPUT (STRICT JSON ONLY)
{
  "summary": "1-3 lines what you think and do",
  "confidence": 0.0-1.0,
  "actions": [
    {"type":"SET_STOP_LOSS","symbol":"BTC","stop_price":85000,"reason":"risk management"},
    {"type":"SET_TAKE_PROFIT","symbol":"BTC","tp_price":92000,"reason":"target"},
    {"type":"PLACE_ORDER","symbol":"ETH","side":"BUY","size":0.01,"leverage":25,"orderType":"MARKET","reason":"setup with 25x"},
    {"type":"NO_TRADE","reason":"positions managed, waiting for edge"}
  ]
}

LEVERAGE: You decide leverage per trade (1-50x). Include "leverage" field in PLACE_ORDER/ADD_TO_POSITION.

Available actions: PLACE_ORDER, ADD_TO_POSITION, CLOSE_POSITION, CLOSE_PARTIAL, SET_STOP_LOSS, SET_TAKE_PROFIT, MOVE_STOP_TO_BREAKEVEN, CANCEL_ALL_ORDERS, NO_TRADE

Pure JSON only, no markdown."""


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
