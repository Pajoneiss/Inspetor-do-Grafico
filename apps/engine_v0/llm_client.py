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
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a trading AI. Respond ONLY with valid JSON in the exact format specified. No markdown, no explanations, just pure JSON."
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
    
    def _build_prompt(self, state: Dict[str, Any]) -> str:
        """Build prompt for AI"""
        positions_str = ""
        if state.get("positions"):
            positions_str = "\n".join([
                f"  - {p['symbol']}: {p['side']} {p['size']} @ ${p['entry_price']:.2f} (PnL: ${p['unrealized_pnl']:.2f})"
                for p in state["positions"]
            ])
        else:
            positions_str = "  (none)"
        
        return f"""Analyze this market state and decide on trading actions.

Current State:
- Time: {state.get('time', 'unknown')}
- Symbol: {state.get('symbol', 'BTC')}
- Price: ${state.get('price', 0):.2f}
- Account Equity: ${state.get('equity', 0):.2f}
- Open Positions: {state.get('positions_count', 0)}
{positions_str}
- Open Orders: {state.get('open_orders_count', 0)}
- Live Trading: {state.get('live_trading', False)}

Available Actions:
1. PLACE_ORDER - Open new position
2. CLOSE_POSITION - Close position (partial or full)
3. MOVE_STOP_TO_BREAKEVEN - Move stop loss to entry price
4. SET_STOP_LOSS - Set/update stop loss
5. SET_TAKE_PROFIT - Set/update take profit
6. CANCEL_ALL - Cancel all open orders for symbol

Respond with ONLY this JSON format (no markdown, no code blocks):
{{
  "summary": "brief analysis and decision rationale",
  "confidence": 0.75,
  "actions": [
    {{"type":"PLACE_ORDER","symbol":"BTC","side":"BUY","size":0.001,"orderType":"MARKET"}},
    {{"type":"CLOSE_POSITION","symbol":"BTC","pct":0.3,"orderType":"MARKET"}},
    {{"type":"MOVE_STOP_TO_BREAKEVEN","symbol":"BTC"}},
    {{"type":"SET_STOP_LOSS","symbol":"BTC","stop_price":65000}},
    {{"type":"SET_TAKE_PROFIT","symbol":"BTC","tp_price":72000}},
    {{"type":"CANCEL_ALL","symbol":"BTC"}}
  ]
}}

Rules:
- confidence: 0.0 to 1.0
- actions: can be empty array [] if no action recommended
- PLACE_ORDER: side "BUY" or "SELL", orderType "MARKET" only, size 0.001-0.01
- CLOSE_POSITION: pct 0.0-1.0 (0.3 = 30%, 1.0 = 100%)
- MOVE_STOP_TO_BREAKEVEN: moves stop to entry price (protects profit)
- SET_STOP_LOSS: stop_price below entry for LONG, above for SHORT
- SET_TAKE_PROFIT: tp_price above entry for LONG, below for SHORT
- CANCEL_ALL: cancels all pending orders for symbol
- Max 5 actions per decision

Respond with pure JSON only:"""
    
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
