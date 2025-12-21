"""
LLM Client v16.0 - PROFESSIONAL AUTONOMOUS TRADER
Claude-only with complete market intelligence and full autonomy
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def _format_candles_multi_tf(candles_by_symbol: Dict) -> str:
    """Format multi-timeframe candles for prompt"""
    if not candles_by_symbol:
        return "(no candle data)"
    
    lines = []
    for symbol, timeframes in candles_by_symbol.items():
        lines.append(f"\n{symbol}:")
        for tf, candles in timeframes.items():
            if candles and len(candles) >= 3:
                last_3 = candles[-3:]
                changes = []
                for c in last_3:
                    o = c.get('o', c.get('open', 0))
                    close = c.get('c', c.get('close', 0))
                    if o and close:
                        pct = ((close - o) / o) * 100
                        changes.append(f"{pct:+.2f}%")
                last_close = last_3[-1].get('c', last_3[-1].get('close', 0))
                lines.append(f"  {tf}: ${last_close:.2f} [{' '.join(changes)}]")
    
    return "\n".join(lines) if lines else "(no candle data)"


def _format_funding(funding_by_symbol: Dict) -> str:
    """Format funding rate data"""
    if not funding_by_symbol:
        return "(no funding data)"
    
    lines = []
    for symbol, data in funding_by_symbol.items():
        rate = data.get("funding_rate", 0) if isinstance(data, dict) else 0
        oi = data.get("open_interest", 0) if isinstance(data, dict) else 0
        rate_pct = rate * 100 if rate < 1 else rate
        oi_str = f"${oi/1e6:.1f}M" if oi > 1e6 else f"${oi/1e3:.0f}K" if oi > 1e3 else f"${oi:.0f}"
        lines.append(f"  {symbol}: rate={rate_pct:+.4f}% | OI={oi_str}")
    
    return "\n".join(lines) if lines else "(no funding data)"


def _format_orderbook(orderbook_by_symbol: Dict) -> str:
    """Format orderbook imbalance data"""
    if not orderbook_by_symbol:
        return "(no orderbook data)"
    
    lines = []
    for symbol, book in orderbook_by_symbol.items():
        if not book:
            continue
        bids = book.get("bids", [])
        asks = book.get("asks", [])
        bid_vol = sum(float(b.get("sz", b.get("size", 0))) for b in bids[:5]) if bids else 0
        ask_vol = sum(float(a.get("sz", a.get("size", 0))) for a in asks[:5]) if asks else 0
        total = bid_vol + ask_vol
        if total > 0:
            bid_pct = (bid_vol / total) * 100
            imbalance = "BID HEAVY" if bid_pct > 60 else "ASK HEAVY" if bid_pct < 40 else "BALANCED"
            lines.append(f"  {symbol}: {imbalance} (bids {bid_pct:.0f}%)")
    
    return "\n".join(lines) if lines else "(no orderbook data)"


def _format_indicators(indicators_by_symbol: Dict, prices: Dict) -> str:
    """Format technical indicators"""
    if not indicators_by_symbol:
        return "(no indicator data)"
    
    lines = []
    for symbol, ind in indicators_by_symbol.items():
        if not ind:
            continue
        price = prices.get(symbol, 0)
        ema9 = ind.get("ema_9", 0)
        ema21 = ind.get("ema_21", 0)
        ema50 = ind.get("ema_50", 0)
        rsi = ind.get("rsi_14", 50)
        macd = ind.get("macd_hist", 0)
        atr_pct = ind.get("atr_pct", 0)
        
        # EMA alignment
        if ema9 > ema21 > ema50:
            ema_status = "BULLISH ALIGNED"
        elif ema9 < ema21 < ema50:
            ema_status = "BEARISH ALIGNED"
        else:
            ema_status = "MIXED"
        
        lines.append(f"  {symbol} @ ${price:.2f}:")
        lines.append(f"    EMA: 9=${ema9:.2f} | 21=${ema21:.2f} | 50=${ema50:.2f} [{ema_status}]")
        lines.append(f"    RSI: {rsi:.1f} | MACD: {macd:+.2f} | ATR: {atr_pct:.2f}%")
    
    return "\n".join(lines) if lines else "(no indicator data)"


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


def _get_session() -> str:
    """Get current trading session"""
    hour = datetime.utcnow().hour
    if 0 <= hour < 8:
        return "ASIA (00:00-08:00 UTC) - Lower volume, range-bound tendency"
    elif 8 <= hour < 14:
        return "LONDON (08:00-14:00 UTC) - High volatility, trend initiation"
    elif 14 <= hour < 21:
        return "NEW YORK (14:00-21:00 UTC) - Highest volume, trend continuation/reversal"
    else:
        return "LATE NY/ASIA TRANSITION (21:00-00:00 UTC) - Decreasing volume"


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
            max_tokens=3000,
            temperature=0.7,
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
        
        # Symbol briefs
        briefs_lines = []
        for sym, brief in sorted(symbol_briefs.items(), key=lambda x: x[1].get("score", 0), reverse=True):
            reason = brief.get("reason", "")
            briefs_lines.append(f"  {sym}: ${brief.get('price', 0)} | {brief.get('trend', '?')} | score={brief.get('score', 0):.0f} {f'[{reason}]' if reason else ''}")
        briefs_str = "\n".join(briefs_lines) if briefs_lines else "(no scan data)"
        
        # News summary
        news_str = "\n".join([f"  - {n.get('title', n) if isinstance(n, dict) else n}" for n in news[:3]]) if news else "(no news)"
        
        return f"""You are an elite professional cryptocurrency trader operating on Hyperliquid perpetuals.

═══════════════════════════════════════════════════════════════════════════════
🎯 YOUR COMPLETE AUTONOMY
═══════════════════════════════════════════════════════════════════════════════

You have ABSOLUTE CONTROL over ALL trading decisions. There are NO restrictions.
You decide:
• WHAT to trade (any symbol in the scan)
• WHEN to trade (now, wait for confirmation, or skip)
• HOW MUCH to trade (position sizing based on your conviction)
• LEVERAGE (any amount you deem appropriate for the setup)
• STOP LOSS & TAKE PROFIT (based on market structure, not arbitrary percentages)
• HOLD DURATION (scalp seconds, swing hours/days - you decide)
• MULTIPLE POSITIONS (if you see opportunities, take them)
• POSITION MANAGEMENT (add, reduce, close partial, move stops, hedge)

You are the trader. The system executes YOUR decisions. Period.

═══════════════════════════════════════════════════════════════════════════════
🧠 PROFESSIONAL TRADING INTELLIGENCE
═══════════════════════════════════════════════════════════════════════════════

As a professional trader, you understand:

📊 SMART MONEY CONCEPTS (SMC/ICT):
- Order Blocks: Institutional accumulation/distribution zones where price often reacts
- Liquidity: Resting orders above swing highs (buy stops) and below swing lows (sell stops)
- Break of Structure (BOS): Continuation signal when HH/HL or LL/LH breaks
- Change of Character (CHoCH): Reversal signal when structure shifts
- Fair Value Gaps (FVG): Imbalanced price zones that often get filled
- Inducement: False breakouts designed to trap retail traders

💰 FUNDING RATE (Perpetual Mechanics):
- Positive funding = longs pay shorts = market over-leveraged long
- Negative funding = shorts pay longs = market over-leveraged short
- Extreme funding often precedes squeezes against the crowded side
- Use funding to gauge sentiment and potential mean reversion

📈 OPEN INTEREST (OI):
- OI rising + price rising = new longs, strong bullish
- OI falling + price rising = shorts closing, weaker bullish
- OI rising + price falling = new shorts, strong bearish
- OI falling + price falling = longs closing, weaker bearish
- OI + Breakout = confirmation of institutional participation

📕 ORDERBOOK ANALYSIS:
- Bid heavy = buying pressure, potential support
- Ask heavy = selling pressure, potential resistance
- Large orders appearing/disappearing = smart money activity
- Thin orderbook = potential for fast moves

⏰ SESSION DYNAMICS:
- Asia: Range-bound, accumulation phase
- London: Volatility spike, trend initiation
- New York: Highest volume, trend continuation or reversal
- Session overlaps: Maximum volatility opportunities

🔥 ANTI-FAKEOUT AWARENESS:
- True breakouts have volume confirmation
- True breakouts have OI expansion
- Fakeouts wick and return
- Patience prevents trapped entries

═══════════════════════════════════════════════════════════════════════════════
📊 CURRENT ACCOUNT STATUS
═══════════════════════════════════════════════════════════════════════════════

💵 Equity: ${equity:.2f}
💰 Buying Power: ${buying_power:.2f}
⏰ Session: {session_str}

═══════════════════════════════════════════════════════════════════════════════
📈 MARKET SENTIMENT
═══════════════════════════════════════════════════════════════════════════════

😱 Fear & Greed Index: {fear_greed} ({fg_class})
₿ BTC Dominance: {btc_dom:.1f}%

📰 Recent News:
{news_str}

═══════════════════════════════════════════════════════════════════════════════
🔍 SYMBOL SCAN (by opportunity score)
═══════════════════════════════════════════════════════════════════════════════

{briefs_str}

═══════════════════════════════════════════════════════════════════════════════
📊 TECHNICAL INDICATORS
═══════════════════════════════════════════════════════════════════════════════

{indicators_str}

═══════════════════════════════════════════════════════════════════════════════
💰 FUNDING & OPEN INTEREST
═══════════════════════════════════════════════════════════════════════════════

{funding_str}

═══════════════════════════════════════════════════════════════════════════════
📕 ORDERBOOK IMBALANCE
═══════════════════════════════════════════════════════════════════════════════

{orderbook_str}

═══════════════════════════════════════════════════════════════════════════════
🕯️ MULTI-TIMEFRAME CANDLES
═══════════════════════════════════════════════════════════════════════════════

{candles_str}

═══════════════════════════════════════════════════════════════════════════════
📍 OPEN POSITIONS
═══════════════════════════════════════════════════════════════════════════════

{positions_str}

═══════════════════════════════════════════════════════════════════════════════
🎯 YOUR DECISION
═══════════════════════════════════════════════════════════════════════════════

Analyze the data above and make your trading decision. You have complete autonomy.

Return ONLY valid JSON (no markdown):

{{
  "actions": [
    {{
      "type": "PLACE_ORDER" | "CLOSE_POSITION" | "CLOSE_PARTIAL" | "SET_STOP_LOSS" | "SET_TAKE_PROFIT" | "MOVE_STOP_TO_BREAKEVEN" | "ADD_TO_POSITION" | "NO_TRADE",
      "symbol": "BTC",
      "side": "LONG" | "SHORT",
      "size": <your calculated size in asset units>,
      "orderType": "MARKET" | "LIMIT",
      "price": <null for market, or your limit price>,
      "leverage": <your chosen leverage>,
      "stop_loss": <your stop price>,
      "take_profit": <your target price>,
      "reason": "specific justification citing data"
    }}
  ],
  "summary": "Clear, specific description of what you're doing and why",
  "confidence": <0.0-1.0 based on setup quality>,
  "reasoning": "Detailed analysis citing specific data points",
  "next_triggers": ["what would make you act differently next tick"],
  "thesis": {{
    "bias": "LONG" | "SHORT" | "NEUTRAL",
    "key_levels": ["important price levels"],
    "invalidation": "what proves your thesis wrong"
  }}
}}

Remember: You are a professional. Cite specific data. No vague language. Act with conviction when the edge is there. Wait patiently when it's not. You decide everything."""

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
