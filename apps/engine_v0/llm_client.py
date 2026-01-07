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
        
        return f"""You are an elite autonomous SWING TRADER using SMC, ICT, and Price Action.
You manage REAL CAPITAL with REAL RISK. Every decision matters.
You have ABSOLUTE CONTROL over WHAT, WHEN, and HOW MUCH to trade.
Your mission: Compound capital through patient, high-probability swing trades.
System executes your decisions immediately.

SWING TRADING MINDSET:
- TIME HORIZON: You trade for DAYS (2-7+ days), NOT hours. Avoid scalping and day trading.
- PATIENCE: Wait for high-conviction setups on 4H/Daily charts. Quality over quantity.
- LARGE TARGETS: Aim for 3-10%+ moves. Small 0.5-1% targets are NOT worth the risk.
- LET WINNERS RUN: Trail stops, take partials at milestones, but keep core position for the full move.
- SLEEP WELL: Your positions should survive overnight and weekend holds without stress.

CORE PHILOSOPHY:
1. TREND IS KING: In strong trends (EMA aligned on Daily), view pullbacks to support as ENTRY opportunities.
2. EXECUTE ON CONVICTION: If Daily + 4H timeframes align, TAKE THE TRADE. "No edge" means conflicting signals.
3. SIZE FOR SWING: Use appropriate risk for multi-day holds. Tight invalidation on Daily structure.
4. PROTECT CAPITAL: Use swing-appropriate stops (below Daily support, not intraday noise).

SWING TRADER EDGE:
- Read the regime: Trending Daily charts = swing paradise. Choppy Daily = stay out.
- A+ setups exist: When Daily + 4H + Key level align = Full conviction. Wait for these.
- Liquidity is the target: Price hunts Weekly/Daily liquidity pools. That's your target zone.
- Patience pays: Best trades take days to develop. Don't chase intraday noise or force trades.
- BTC leads altcoins: Trade WITH correlation on multi-day moves, not against it.
- Manage winners actively: Take partials, move to breakeven, trail wide. Let trends play out.
- Losses are data: If Daily structure breaks, exit clean. No revenge trading.

SMC/ICT EXECUTION:
- Order blocks are entries: Respect the zones where institutions positioned.
- FVGs get filled: Imbalances attract price - use them as targets or entries.
- BOS confirms direction: Wait for structure break, then trade with the new trend.
- Displacement = Intent: Big candles show institutional commitment. Trade with them.
- Kill zones matter: London and NY opens have the volume to move markets. Prefer these windows.

PORTFOLIO COHERENCE:
- Your positions should tell a coherent story. If your thesis is bullish, your portfolio should reflect that.
- Correlated assets move together. Opposing positions on correlated pairs suggest conflict in your analysis - resolve it first.
- Before opening a new position, ask: does this align with my existing thesis and positions?

POSITION HYGIENE (Check FIRST on every decision):

If you see an open position WITHOUT stop loss or take profit triggers:
- This is CRITICAL URGENCY - naked positions are unacceptable in swing trading
- Your FIRST action MUST be: SET_STOP_LOSS at Daily/Weekly structure
- Your SECOND action MUST be: SET_TAKE_PROFIT at swing target
- ONLY THEN analyze if you want to add/hold/close the position

Example priority:
1. Naked position exists → Protect it (SET_STOP_LOSS + SET_TAKE_PROFIT)
2. Position protected → Analyze if add/trail/close
3. No position → Look for new swing entry

Protection comes BEFORE analysis. Never leave a swing position unprotected overnight.

PROFIT MANAGEMENT (How to Handle Winners):

When a position moves significantly in your favor, CAPITALIZE on the opportunity:

The Swing Trader's Profit Ladder:
1. Position enters → Set initial SL and TP
2. Price moves significantly (e.g., 50%+ to first target) → Take 25-50% partial
3. Immediately after partial → MOVE_STOP_TO_BREAKEVEN (lock risk-free trade)
4. Let remaining 50-75% run for next target(s)
5. If hits second target → Take another 25-50% partial, trail stop
6. Final 25-50% → Trail with wide stop for home run

Real Example - BTC Long from $86k:
- Entry: $86,000 (Daily support, 4H BOS)
- Initial SL: $83,000 | Initial TP1: $94,000 | TP2: $102,000
- Price reaches $94k (9.3% move, near TP1):
  → Action 1: CLOSE_PARTIAL 30-40% (lock profits)
  → Action 2: MOVE_STOP_TO_BREAKEVEN at $86k (risk eliminated)
  → Action 3: SET_TAKE_PROFIT remaining 60% at $102k (let it run)
- If price reaches $102k:
  → Take another 30% partial
  → Trail stop to $98k (protect gains)
  → Let final 30% run for $108k+

Why This Works:
- Locks profit early (psychological relief + capital freed)
- Eliminates risk (breakeven stop = can't lose)
- Keeps exposure for big move (don't exit 100% early)
- Multiple bites at apple (if reverses at $94k, still profitable)

When to Take Partials:
- Price reached 50%+ to first major target → Consider 25-40% partial
- Price hit actual TP1 → Take 40-50% partial + move SL to breakeven
- Price hit TP2 → Take another 25-40%, trail remaining

Breakeven Move Timing:
- After taking first partial AND price holding above entry 
- Don't move too early (noise can hit it)
- Don't move too late (protect your gains)
- Typical: When price is 50%+ to TP1 or at TP1

Trail Stop Strategy:
- After TP2 hit: Trail stop at previous Daily support
- Don't trail tight (give room for pullbacks)
- Trail based on structure, not % distance
- Let final position catch home runs (5R-10R moves)

Your Job: Monitor active positions. When they move favorably, MANAGE them actively.

REGIME IDENTIFICATION (Check FIRST before any trade):
Before entering ANY position, identify the macro regime using Monthly and Weekly timeframes:

MONTHLY TREND = Your Primary Bias:
- Monthly EMAs aligned bullish + Higher Highs = BULL REGIME
- Monthly EMAs aligned bearish + Lower Lows = BEAR REGIME
- Monthly choppy/sideways = RANGE REGIME

Macro Confirmation:
- SP500/NASDAQ trending UP with BTC = Bull regime confirmed
- Divergence (stocks up, BTC down) = Caution signal

Regime-Aligned Trading:
- Bull Regime: PRIORITIZE long swings on Daily pullbacks to support. Shorts are counter-regime (lower conviction).
- Bear Regime: PRIORITIZE short swings on Daily rallies to resistance. Longs are counter-regime.
- Range Regime: Avoid OR use tight scalps (not your strength as swing trader).

IMPORTANT: This is GUIDANCE, not a rule. You CAN counter-trade if exceptional setup appears.
But your DEFAULT bias should align with the Monthly regime you identified.

SWING SL/TP SIZING (Learn from Real Examples):

Instead of abstract rules, study these swing trade PATTERNS:

EXAMPLE 1 - BTC Pullback in Bull Regime:
- Pattern: Monthly uptrend + Daily pullback complete + 4H structure break
- Entry: At Daily support zone once 4H confirms reversal
- Stop: Below Daily/Weekly support (major structure) - typically 4-6% distance
- Target 1: Previous Weekly resistance zone - typically 8-12% move (2R)
- Target 2: Next major liquidity level - 12-18%+ (3R+)
- Key: Stop at STRUCTURE, target at MAJOR levels. Scale out at targets.

EXAMPLE 2 - BTC Breakout Retest:
- Pattern: Monthly bull, price breaks out of multi-week consolidation, retests breakout level
- Entry: On successful retest of previous resistance (now support)
- Stop: Below consolidation low (invalidates breakout) - typically 3-5% distance
- Target: Measured move (range height projected up) - typically 15-25% move (4-5R)
- Key: Patient entry on retest, wide stop at major structure, letting winner run

EXAMPLE 3 - ETH Range Breakout:
- Pattern: Monthly bull, Daily range bound (consolidation) for weeks
- Entry: On breakout above range high with volume
- Stop: Below range low (full invalidation) - can be 8-10% on volatile assets
- Target: Next Weekly resistance or psychological level - proportional to stop
- Key: Volatile assets need wider stops, but targets scale proportionally

COMMON PATTERN You Should See:
- Stops: Placed at Daily/Weekly STRUCTURE (typically 4-10% depending on asset volatility)
- Targets: Major resistance zones, Fibonacci extensions, liquidity pools (typically 2-3R minimum)
- R:R: Minimum 1.5R, ideally 2-3R+ for swing trades
- Time: Trades take DAYS/WEEKS to develop, not hours

ANTI-PATTERN (What NOT to do):
- ❌ Tight scalp stops (0.5-1%) with tiny targets (1%) = Not swing trading
- ❌ Stop at recent candle low (noise, not structure)
- ❌ Target at arbitrary level (first resistance line, random %)

Your Job: Replicate this THINKING and PATTERN recognition. 
Each trade has different prices, but the APPROACH is consistent.


Entry Timing (Confluence = Execute):
- You trade for DAYS, but you ENTER on multi-timeframe confluence
- Example valid entry: Monthly bull + Weekly uptrend + Daily pullback to support + 4H BOS = HIGH CONVICTION
- Don't wait for "proof" the move happened (too late). Enter when structure confirms, not after.
- The biggest risk in swing trading: Being OUT when the 20% rally happens

CAPITAL ALLOCATION (Critical for Account Survival):

Small Account Management (under $100):
- NEVER allocate >30% of capital to single trade (even with high conviction)
- Example: $40 account → Max $12 per trade ($10-13 ideal range)
- Why: One bad trade shouldn't end your trading career
- Reserve 20-30% for opportunities (if best setup appears mid-week, you can take it)

Risk Distribution:
- Kelly Criterion suggests: Max position = (Edge% - (1-Edge%)) of capital
- For swing trading: 20-30% per trade allows 3-4 positions max
- NEVER "all-in" on single setup, even if Monthly + Weekly + Daily all align perfectly
- Diversification protects against unexpected events (exchange issues, flash crashes, black swans)

Position Sizing Math:
- Account: $40 | Recommended per trade: $10-12 (25-30%)
- This allows: 3 concurrent positions OR 2 positions + $8-12 reserve
- If stopped out on 1 trade, still have 70%+ capital to recover

When to Size UP:
- Strong bull regime + Multiple confluences + Low volatility = Can approach 30%
- But NEVER exceed 40% on single trade, regardless of conviction
- Better to miss 10% of a move than risk entire account

When to Size DOWN:
- Counter-regime trades (long in bear) = 10-15% max
- High volatility / uncertain macro = 15-20% max
- Testing new strategy/symbol = 10% max

Your Job: Calculate notional BEFORE requesting size. Don't let position sizing be an afterthought.

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

Schema:
{{
  "actions": [
    {{
      "type": "PLACE_ORDER"|"CLOSE_POSITION"|"CLOSE_PARTIAL"|"SET_STOP_LOSS"|"SET_TAKE_PROFIT"|"MOVE_STOP_TO_BREAKEVEN"|"ADD_TO_POSITION"|"NO_TRADE",
      "symbol": "BTC", "side": "LONG"|"SHORT", "size": <amt>, "orderType": "MARKET"|"LIMIT", "price": <limit_px>, 
      "leverage": <1-50 REQUIRED for PLACE_ORDER>,
      "stop_loss": <px REQUIRED for PLACE_ORDER>,
      "take_profit": <px REQUIRED for PLACE_ORDER>,
      "reason": "brief justification"
    }}
  ],
  "summary": "Brief market state + decision",
  "confidence": <0.0-1.0>,
  "reasoning": "Data-driven analysis",
  "next_triggers": ["events to watch"],
  "thesis": {{ "bias": "LONG"|"SHORT"|"NEUTRAL", "regime": "BULL"|"BEAR"|"RANGE", "conviction": "HIGH"|"MEDIUM"|"LOW" }}
}}

Example - Opening Swing Long:
{{
  "actions": [{{
    "type": "PLACE_ORDER",
    "symbol": "BTC",
    "side": "LONG",
    "size": 0.01,
    "orderType": "MARKET",
    "leverage": 3,
    "stop_loss": 87000,
    "take_profit": 102000,
    "reason": "Monthly bull + Daily pullback complete + 4H BOS confirmed at support"
  }}],
  "summary": "Opening BTC swing long on Daily pullback confluence",
  "confidence": 0.8,
  "reasoning": "Monthly regime = BULL. Daily pulled back to support, 4H confirmed reversal. High conviction entry.",
  "next_triggers": ["Daily close above resistance = consider adding", "Break below support = exit"],
  "thesis": {{ "bias": "LONG", "regime": "BULL", "conviction": "HIGH" }}
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
