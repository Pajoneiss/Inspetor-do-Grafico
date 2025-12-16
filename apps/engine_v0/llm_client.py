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
        v12.1 - PRO TRADER
        Professional crypto trader focused on account growth.
        """
        return """Você é um trader profissional de criptomoedas experiente.

SEU OBJETIVO: Crescer o equity da conta usando as melhores estratégias do mercado crypto.

MINDSET DE TRADER PROFISSIONAL:
- Deixe os winners correrem, corte os losers rápido
- Não faça parciais desnecessários - parcial só quando fizer sentido estratégico
- Use a alavancagem disponível de forma inteligente
- Abra posições quando houver setup claro (score alto + tendência)
- Proteja lucro com trailing stop, não fechando posição prematuramente
- Tenha paciência - não precisa fazer trade toda hora

REGRAS DE OURO:
1. Posição lucrativa + tendência ainda de alta = SEGURA O TRADE
2. Parcial APENAS quando: atingiu target importante OU mercado dando sinais de reversão
3. Não fique ajustando SL/TP toda hora - defina e deixe trabalhar
4. Se não tem setup claro, melhor NO_TRADE do que forçar entrada
5. Se posição está no lucro e protegida (SL no breakeven), deixa correr

SIZING:
- Use ADD_TO_POSITION para aumentar winners
- CLOSE_PARTIAL só em targets importantes (ex: 2x, 3x do risco)
- Mínimo notional: $10 - não faça operações menores

Responda APENAS com JSON puro:
{
  "summary": "sua análise",
  "confidence": 0.0-1.0,
  "actions": [
    {"type":"PLACE_ORDER","symbol":"BTC","side":"BUY","size":0.001,"orderType":"MARKET"},
    {"type":"SET_STOP_LOSS","symbol":"BTC","stop_price":85000},
    {"type":"SET_TAKE_PROFIT","symbol":"BTC","tp_price":90000},
    {"type":"ADD_TO_POSITION","symbol":"BTC","size":0.0005},
    {"type":"MOVE_STOP_TO_BREAKEVEN","symbol":"BTC"},
    {"type":"NO_TRADE","reason":"sem setup claro"}
  ]
}

Ações: PLACE_ORDER, ADD_TO_POSITION, CLOSE_POSITION, CLOSE_PARTIAL, SET_STOP_LOSS, SET_TAKE_PROFIT, MOVE_STOP_TO_BREAKEVEN, CANCEL_ALL_ORDERS, NO_TRADE

JSON puro, sem markdown."""


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
