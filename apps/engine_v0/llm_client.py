"""
LLM Client v16.0 - PROFESSIONAL AUTONOMOUS TRADER
Claude-only with complete market intelligence and full autonomy
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from config import (
    AI_MODEL, 
    AI_TEMPERATURE, 
    AI_MAX_TOKENS
)

logger = logging.getLogger(__name__)


def _format_candles_multi_tf(candles_by_symbol: Dict) -> str:
    """Format multi-timeframe candles for prompt"""
    if not candles_by_symbol:
        return "(no candle data)"
    
    lines = []
    for symbol, timeframes in candles_by_symbol.items():
        parts = []
        for tf, candles in timeframes.items():
            if candles and len(candles) >= 3:
                # Dense format: 1h:90000[+1.2%]
                try:
                    c = candles[-1]
                    close = float(c.get('c', c.get('close', 0)) or 0)
                    op = float(c.get('o', c.get('open', 0)) or 0)
                    pct = ((close - op) / op) * 100 if op else 0
                    parts.append(f"{tf}:${close:.0f}[{pct:+.1f}%]")
                except: continue
        if parts:
            lines.append(f"{symbol}: " + " | ".join(parts))
    
    return "\n".join(lines) if lines else "(no data)"


def _format_funding(funding_by_symbol: Dict) -> str:
    """Format funding rate data"""
    if not funding_by_symbol:
        return "(no funding data)"
    
    lines = []
    for symbol, data in funding_by_symbol.items():
        rate = data.get("funding_rate", 0) if isinstance(data, dict) else 0
        oi = data.get("open_interest", 0) if isinstance(data, dict) else 0
        rate_pct = rate * 100 if rate < 1 else rate
        oi_str = f"${oi/1e6:.1f}M" if oi > 1e6 else f"${oi/1e3:.0f}K"
        lines.append(f"{symbol}: rate={rate_pct:+.4f}% OI={oi_str}")
    
    return " | ".join(lines) if lines else "(no funding)"


def _format_orderbook(orderbook_by_symbol: Dict) -> str:
    """Format orderbook imbalance data"""
    if not orderbook_by_symbol:
        return "(no orderbook data)"
    
    lines = []
    for symbol, book in orderbook_by_symbol.items():
        if not book: continue
        try:
            bids = book.get("bids", []) or []
            asks = book.get("asks", []) or []
            
            # Simplified calc
            bid_vol = sum(float(b[1]) if isinstance(b, list) else float(b.get("sz", 0)) for b in bids[:5])
            ask_vol = sum(float(a[1]) if isinstance(a, list) else float(a.get("sz", 0)) for a in asks[:5])
            
            total = bid_vol + ask_vol
            if total > 0:
                bid_pct = (bid_vol / total) * 100
                imb = "BID+" if bid_pct > 60 else "ASK+" if bid_pct < 40 else "BAL"
                lines.append(f"{symbol}:{imb}({bid_pct:.0f}%)")
        except: continue
    
    return " | ".join(lines) if lines else "(no ob)"


def _format_indicators(indicators_by_symbol: Dict, prices: Dict) -> str:
    """Format technical indicators"""
    if not indicators_by_symbol:
        return "(no indicator data)"
    
    lines = []
    for symbol, ind in indicators_by_symbol.items():
        if not ind: continue
        price = prices.get(symbol, 0)
        ema9, ema21, ema50 = ind.get("ema_9", 0), ind.get("ema_21", 0), ind.get("ema_50", 0)
        rsi, macd, atr = ind.get("rsi_14", 50), ind.get("macd_hist", 0), ind.get("atr_pct", 0)
        
        status = "BULL" if ema9>ema21>ema50 else "BEAR" if ema9<ema21<ema50 else "FLAT"
        lines.append(f"{symbol}(${price:.0f}): EMA[{status}] 9={ema9:.0f} 21={ema21:.0f} 50={ema50:.0f} | RSI={rsi:.1f} MACD={macd:.2f} ATR={atr:.2f}%")
    
    return "\n".join(lines) if lines else "(no indicators)"


def _format_positions(positions: Dict, position_details: Dict) -> str:
    """Format open positions with context"""
    if not positions:
        return "(no open positions)"
    
    lines = []
    for symbol, pos in positions.items():
        side = pos.get("side", "?")
        size = pos.get("size", 0)
        entry = pos.get("entry_price", 0)
        pnl = pos.get("unrealized_pnl", 0)
        
        details = position_details.get(symbol, {})
        pnl_pct = details.get("pnl_pct", 0)
        sl = details.get("current_sl")
        tp = details.get("current_tp")
        
        sl_str = f"SL=${sl:.2f}" if sl else "SL=NONE"
        tp_str = f"TP=${tp:.2f}" if tp else "TP=NONE"
        
        lines.append(
            f"  {symbol}: {side} {abs(size)} @ ${entry:.2f} | "
            f"PnL: ${pnl:.2f} ({pnl_pct:+.2f}%) | {sl_str} | {tp_str}"
        )
    
    return "\n".join(lines) if lines else "(no open positions)"


def _format_recent_trades(recent_fills: list) -> str:
    """Format recent trades for AI to learn from"""
    if not recent_fills:
        return "(no recent trades)"
    
    lines = []
    wins = 0
    losses = 0
    
    for fill in recent_fills[:10]:  # Last 10 trades
        symbol = fill.get("coin", fill.get("symbol", "?"))
        side = fill.get("side", "?")
        px = float(fill.get("px", 0))
        sz = float(fill.get("sz", 0))
        pnl = float(fill.get("closedPnl", fill.get("realizedPnl", 0)))
        
        if pnl > 0:
            wins += 1
            result = f"✅ +${pnl:.2f}"
        elif pnl < 0:
            losses += 1
            result = f"❌ -${abs(pnl):.2f}"
        else:
            result = "⚪ $0"
        
        lines.append(f"  {symbol} {side} @ ${px:.2f} ({sz}) → {result}")
    
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0
    
    summary = f"Win Rate: {win_rate:.0f}% ({wins}W / {losses}L)"
    
    return f"{summary}\n" + "\n".join(lines) if lines else "(no recent trades)"


def _get_session() -> str:
    """Get current trading session"""
    h = datetime.now(timezone.utc).hour
    if 0 <= h < 8: return "ASIA"
    elif 8 <= h < 14: return "LONDON"
    elif 14 <= h < 21: return "NY"
    return "LATE NY"


class LLMClient:
    """Claude-only professional crypto trader with full autonomy"""
    
    def __init__(self):
        self.provider = "anthropic"
        self.model = self._get_model_name()
        self.client = None
        
        print(f"[LLM] 🧠 Initializing Claude AI trader...")
        print(f"[LLM]   Provider: {self.provider}")
        print(f"[LLM]   Model: {self.model}")
        
        try:
            self.client = self._initialize_claude()
            print(f"[LLM] ✅ Claude initialized successfully!")
            logger.info(f"[LLM] ✅ Initialized with provider={self.provider} model={self.model}")
        except Exception as e:
            print(f"[LLM] ❌ CRITICAL: Claude failed to initialize: {e}")
            print(f"[LLM] ⚠️  Bot will NOT trade until Claude is working!")
            logger.error(f"[LLM] ❌ Failed to initialize: {e}")
            self.client = None
    
    def _get_model_name(self) -> str:
        model = os.getenv("AI_MODEL", "")
        return model if model else "claude-sonnet-4-20250514"
    
    def _initialize_claude(self):
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set!")
        return anthropic.Anthropic(api_key=api_key)
    
    def is_ready(self) -> bool:
        return self.client is not None
    
    def decide(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Main decision method - extracts ALL available data from state"""
        if not self.client:
            return {
                "actions": [],
                "summary": "LLM not available",
                "confidence": 0.0,
                "reasoning": "Claude client failed to initialize"
            }
        
        prompt = self._build_prompt(state)
        print(f"[LLM] Prompt length: {len(prompt)} chars")
        
        try:
            response_text = self._call_llm(prompt)
            decision = self._parse_decision(response_text)
            self._log_quality(decision)
            return decision
        except Exception as e:
            error_str = str(e)
            if "credit balance" in error_str.lower() or "overloaded" in error_str.lower():
                print(f"[LLM] ⚠️  API LIMITATION: {error_str} -> Using NEUTRAL fallback")
                return {
                    "actions": [],
                    "summary": "AI in Neutral/Sleep Mode (API Credit Limit / Overload)",
                    "confidence": 0.0,
                    "reasoning": "External AI provider unavailable. Holding current positions.",
                    "thesis": {"bias": "NEUTRAL", "key_levels": [], "invalidation": "API recovery"}
                }
            
            logger.error(f"[LLM] Error: {e}", exc_info=True)
            return {
                "actions": [],
                "summary": f"Error: {str(e)}",
                "confidence": 0.0,
                "reasoning": "LLM call failed"
            }
    
    def _call_llm(self, prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=AI_MAX_TOKENS,
            temperature=AI_TEMPERATURE,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    def _build_prompt(self, state: Dict[str, Any]) -> str:
        """Build comprehensive professional trader prompt with ALL data"""
        
        # Extract ALL available data from state
        equity = state.get("equity", 0)
        buying_power = state.get("buying_power", 0)
        positions = state.get("positions", {})
        position_details = state.get("position_details", {})
        prices = state.get("prices", {})
        
        # Market data
        candles = state.get("candles_by_symbol", {})
        indicators = state.get("indicators_by_symbol", {})
        funding = state.get("funding_by_symbol", {})
        orderbook = state.get("orderbook_by_symbol", {})
        symbol_briefs = state.get("symbol_briefs", {})
        
        # External data
        market_data = state.get("market_data", {})
        fear_greed = market_data.get("fear_greed", {}).get("value", 50)
        fg_class = market_data.get("fear_greed", {}).get("classification", "Neutral")
        btc_dom = market_data.get("market", {}).get("btc_dominance", 0)
        news = market_data.get("news", [])
        
        # Format all sections
        candles_str = _format_candles_multi_tf(candles)
        funding_str = _format_funding(funding)
        orderbook_str = _format_orderbook(orderbook)
        indicators_str = _format_indicators(indicators, prices)
        positions_str = _format_positions(positions, position_details)
        session_str = _get_session()
        
        # Trade history for learning
        recent_fills = state.get("recent_fills", [])
        trades_str = _format_recent_trades(recent_fills)
        
        # Symbol briefs
        briefs_lines = []
        for sym, brief in sorted(symbol_briefs.items(), key=lambda x: x[1].get("score", 0), reverse=True):
            reason = brief.get("reason", "")
            briefs_lines.append(f"  {sym}: ${brief.get('price', 0)} | {brief.get('trend', '?')} | score={brief.get('score', 0):.0f} {f'[{reason}]' if reason else ''}")
        briefs_str = "\n".join(briefs_lines) if briefs_lines else "(no scan data)"
        
        # News summary
        news_str = "\n".join([f"  - {n.get('title', n) if isinstance(n, dict) else n}" for n in news[:3]]) if news else "(no news)"
        
        return f"""You are an elite autonomous crypto trader using SMC, ICT, and Price Action.
You have ABSOLUTE CONTROL. You decide WHAT, WHEN, HOW MUCH to trade.
System executes your decisions immediately.

CORE PHILOSOPHY:
1. TREND IS KING: In strong trends (EMA aligned), view momentum cooling (MACD pullback) as an ENTRY opportunity, not a reversal warning.
2. DO NOT HESITATE: If multiple timeframes align, EXECUTE. "No edge" means conflicting signals, not "waiting for perfection".
3. AGGRESSIVE IN TREND: When price is respecting EMAs, add to winners or enter on touches.
4. PROTECT CAPITAL: Use tight invalidation, but let winners run.

# ACCOUNT
Equity: ${equity:.2f} | BP: ${buying_power:.2f} | Session: {session_str}

# MARKET
Sentiment: {fear_greed}({fg_class}) | BTC.D: {btc_dom}%
News: {news_str}

# SCAN
{briefs_str}

# INDICATORS
{indicators_str}

# FUNDING & ORDERBOOK
{funding_str}
{orderbook_str}

# CANDLES
{candles_str}

# POSITIONS
{positions_str}

# HISTORY
{trades_str}

# DECISION
Analyze data. Return JSON ONLY.
{{
  "actions": [
    {{
      "type": "PLACE_ORDER"|"CLOSE_POSITION"|"CLOSE_PARTIAL"|"SET_STOP_LOSS"|"SET_TAKE_PROFIT"|"MOVE_STOP_TO_BREAKEVEN"|"ADD_TO_POSITION"|"NO_TRADE",
      "symbol": "BTC", "side": "LONG"|"SHORT", "size": <amt>, "orderType": "MARKET"|"LIMIT", "price": <limit_px>, 
      "leverage": <int>, "stop_loss": <px>, "take_profit": <px>, "reason": "brief justification"
    }}
  ],
  "summary": "Brief explanation",
  "confidence": <0.0-1.0>,
  "reasoning": "Data-driven analysis",
  "next_triggers": ["events to watch"],
  "thesis": {{ "bias": "LONG"|"SHORT"|"NEUTRAL", "key_levels": ["px"], "invalidation": "condition" }}
}}"""

    def _parse_decision(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from Claude"""
        try:
            cleaned = response.strip()
            
            # Remove markdown fences
            if "```" in cleaned:
                lines = cleaned.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_block = not in_block
                        continue
                    if in_block or not line.strip().startswith("```"):
                        json_lines.append(line)
                cleaned = "\n".join(json_lines).strip()
            
            # Find JSON object
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start >= 0 and end > start:
                cleaned = cleaned[start:end]
            
            decision = json.loads(cleaned)
            
            # Ensure required fields
            decision.setdefault("actions", [])
            decision.setdefault("summary", "No summary")
            decision.setdefault("confidence", 0.5)
            decision.setdefault("reasoning", "No reasoning")
            
            return decision
            
        except json.JSONDecodeError as e:
            logger.error(f"[LLM] JSON parse error: {e}")
            logger.error(f"[LLM] Response was: {response[:500]}...")
            return {
                "actions": [],
                "summary": "JSON parse error",
                "confidence": 0.0,
                "reasoning": f"Failed to parse: {str(e)}"
            }
    
    def _log_quality(self, decision: Dict):
        """Log decision quality metrics"""
        summary = decision.get("summary", "")
        confidence = decision.get("confidence") or 0.0
        actions = decision.get("actions", [])
        
        has_numbers = any(c.isdigit() for c in summary)
        has_dollar = "$" in summary
        has_actions = len(actions) > 0
        has_thesis = "thesis" in decision
        
        score = 5.0
        if has_numbers: score += 1.5
        if has_dollar: score += 1.0
        if has_thesis: score += 1.0
        if 0.4 < confidence < 0.9: score += 0.5
        
        quality = "EXCELLENT ✅" if score >= 8.5 else "GOOD 🟢" if score >= 7.0 else "FAIR 🟡" if score >= 5.5 else "WEAK 🔴"
        
        action_summary = f"{len(actions)} action(s)" if actions else "HOLD"
        print(f"[LLM] Decision: {quality} | Confidence: {confidence:.2f} | {action_summary}")
        logger.info(f"[LLM] Quality: {quality} ({score:.1f}/10)")


# Singleton
_instance = None

def get_llm_client():
    global _instance
    if _instance is None:
        _instance = LLMClient()
    return _instance
