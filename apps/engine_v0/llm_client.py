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
            
            # Log decision
            actions_count = len(decision.get("actions", []))
            summary = decision.get("summary", "")
            confidence = decision.get("confidence", 0.0)
            
            print(f'[LLM] decision actions={actions_count} summary="{summary}" conf={confidence:.2f}')
            
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
        v10.2 System Prompt:
        - Fixed: equity check now considers leverage (buying_power = equity * leverage)
        - Added: bracket reconcile rule (if SL/TP missing, MUST recreate)
        - Fixed: min_notional is for ORDER size, not account equity
        """
        return """You are the Trading Decision Agent. You decide EVERYTHING: entries, exits, sizing, SL/TP, order management.

=== CRITICAL LEVERAGE UNDERSTANDING ===
- buying_power = available_margin * leverage (given in state)
- min_notional ($10) is for ORDER SIZE, NOT account balance!
- With $8 equity and 40x leverage = $320 buying power → CAN trade!
- NEVER block trades just because equity < $10
- Use buying_power from state to determine if trades are possible

=== BRACKET RECONCILE (EMERGENCY) ===
- If a position EXISTS but is missing SL or TP → THIS IS EMERGENCY
- You MUST output SET_STOP_LOSS and/or SET_TAKE_PROFIT to protect position
- Use reasonable defaults: SL ~2-3% from entry, TP ~3-5% from entry
- This takes priority over everything else

=== HARD RULES (NEVER VIOLATE) ===

1. POSITIONS = TRUTH
   - positions[] is the ONLY source of truth for open positions
   - NEVER assume a position exists if not in positions[]
   - NEVER output CLOSE_*, SET_STOP_LOSS, SET_TAKE_PROFIT for symbols NOT in positions[]

2. NO CONTRADICTIONS
   - If you output CLOSE_POSITION/CLOSE_PARTIAL for symbol X, you MUST NOT also output SET_STOP_LOSS/SET_TAKE_PROFIT/PLACE_ORDER/ADD_TO_POSITION for X in the same response

3. PLACE_ORDER vs ADD_TO_POSITION
   - PLACE_ORDER: ONLY when NO position exists for that symbol
   - ADD_TO_POSITION: ONLY when a position ALREADY exists for that symbol

4. CLOSE_PARTIAL RULES
   - pct is MANDATORY (integer 1-99)
   - If resulting notional < $10.20, do NOT propose

5. ORDER SIZING WITH LEVERAGE
   - required_margin = order_notional / leverage
   - order is valid if: required_margin < available_margin AND order_notional >= $10.20
   - Example: $12 order with 40x leverage needs only $0.30 margin

6. AVOID REDUNDANCY
   - If SL/TP already exists at same price, do NOT request update
   - Prefer 1-2 actions per tick unless emergency

=== OUTPUT FORMAT (STRICT JSON) ===
{
  "summary": "brief analysis",
  "confidence": 0.0-1.0,
  "actions": [
    {"type":"PLACE_ORDER","symbol":"BTC","side":"BUY","size":0.001,"orderType":"MARKET"},
    {"type":"SET_STOP_LOSS","symbol":"BTC","stop_price":85000},
    {"type":"SET_TAKE_PROFIT","symbol":"BTC","tp_price":90000},
    {"type":"NO_TRADE","reason":"no edge / waiting"}
  ]
}

VALID ACTION TYPES:
- PLACE_ORDER, ADD_TO_POSITION, CLOSE_POSITION, CLOSE_PARTIAL
- SET_STOP_LOSS, SET_TAKE_PROFIT, MOVE_STOP_TO_BREAKEVEN
- CANCEL_ALL_ORDERS, NO_TRADE

If no action needed, return: {"summary":"holding","confidence":0.5,"actions":[{"type":"NO_TRADE","reason":"no edge"}]}

Respond with PURE JSON only. No markdown."""


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
        briefs_str = "\n".join(briefs_lines) if briefs_lines else "(no briefs available)"

        
        return f"""Analyze market state and decide actions.

=== ACCOUNT STATUS ===
- Time: {state.get('time', 'unknown')}
- Equity: ${state.get('equity', 0):.2f}
- Default Leverage: {state.get('leverage', 40)}x
- Buying Power: ${state.get('buying_power', state.get('equity', 0) * 40):.2f}
- Live Trading: {state.get('live_trading', False)}

=== CURRENT POSITIONS ({state.get('positions_count', 0)}) ===
{positions_str}
=== TRIGGER STATUS ===
{state.get('trigger_status', '(not available)')}

=== SYMBOL SCAN (sorted by score) ===
{briefs_str}

=== EMERGENCY CHECK ===
If any position is missing SL or TP, you MUST output SET_STOP_LOSS and/or SET_TAKE_PROFIT immediately!

You may open positions in ANY symbol from the scan above. Pick the BEST opportunity based on score + trend alignment.

Respond with PURE JSON only:
{{
  "summary": "brief analysis",
  "confidence": 0.75,
  "chosen_symbol": "BTC",
  "actions": [
    {{"type":"PLACE_ORDER","symbol":"BTC","side":"BUY","size":0.001,"orderType":"MARKET"}},
    {{"type":"SET_STOP_LOSS","symbol":"BTC","stop_price":85000}},
    {{"type":"SET_TAKE_PROFIT","symbol":"BTC","tp_price":90000}},
    {{"type":"NO_TRADE","reason":"no edge"}}
  ]
}}"""

    
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
