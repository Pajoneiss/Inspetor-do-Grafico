"""
LLM Client for Engine V0 - v14.0 AI AUTONOMY UPGRADE
OpenAI integration for trading decisions
"""
import json
import traceback
from candle_formatter import format_multi_timeframe_candles
from typing import Dict, Any
from openai import OpenAI

from config import OPENAI_API_KEY, AI_MODEL, AI_LANGUAGE


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
                temperature=0.4,
                max_tokens=2048,
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
                print(f"[LLM] Failed to send thought to dashboard: {e}")
            
            # Record trades in journal
            try:
                # Try to import trade logging functions (may not exist yet)
                try:
                    from trade_journal import record_ai_intent, update_trade_log
                    has_journal_funcs = True
                except ImportError:
                    has_journal_funcs = False
                    print("[LLM] Trade journal logging functions not available (non-critical)")
                
                if not has_journal_funcs:
                    # Skip logging if functions don't exist
                    pass
                else:
                    # Record each action as intent
                    for action in actions:
                        action_type = action.get("type", "UNKNOWN")
                        
                        if action_type == "PLACE_ORDER":
                            symbol = action.get("symbol", "UNKNOWN")
                            side = action.get("side", "UNKNOWN")
                            size = action.get("size", 0)
                            price = action.get("price")
                            leverage = action.get("leverage", 1)
                            stop_price = action.get("stop_price")
                            tp_price = action.get("tp_price")
                            reason = action.get("reason", "")
                            
                            try:
                                record_ai_intent(
                                    symbol=symbol,
                                    side=side,
                                    size=size,
                                    entry_price=price if price else 0,
                                    leverage=leverage,
                                    stop_loss=stop_price,
                                    take_profit_1=tp_price,
                                    reason=reason,
                                    confidence=confidence
                                )
                                print(f"[LLM] Intent recorded: {action_type} {symbol}")
                            except Exception as ie:
                                print(f"[LLM] Failed to record intent: {ie}")
                        
                        # Update existing trades with new SL/TP
                        if action_type in ["SET_STOP_LOSS", "SET_TAKE_PROFIT", "MOVE_STOP_TO_BREAKEVEN"]:
                            symbol = action.get("symbol")
                            update_data = {}
                            
                            if action_type == "SET_STOP_LOSS" or action_type == "MOVE_STOP_TO_BREAKEVEN":
                                update_data['stop_loss'] = action.get('price', action.get('stop_price', 0))
                                update_data['stop_loss_reason'] = action.get('reason', 'AI dynamic adjustment')
                            elif action_type == "SET_TAKE_PROFIT":
                                update_data['take_profit_1'] = action.get('price', action.get('tp_price', 0))
                                update_data['tp1_reason'] = action.get('reason', 'AI target')
                            
                            try:
                                update_trade_log(symbol, update_data)
                                print(f"[LLM] Trade log updated: {symbol} - {action_type}")
                            except Exception as ue:
                                print(f"[LLM] Failed to update trade log: {ue}")
                            
            except Exception as e:
                print(f"[LLM] Trade logging error (non-critical): {e}")
            
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
        v14.0 AI AUTONOMY - Professional discretionary trader
        ZERO hardcoded rules - AI decides everything
        """
        language_instruction = ""
        if AI_LANGUAGE == "portuguese":
            language_instruction = """
LANGUAGE INSTRUCTION:
- You MUST output the "summary" and "reason" fields in BRAZILIAN PORTUGUESE (PT-BR).
- Keep the JSON keys in English (e.g. "actions", "type", "symbol").
- Only the values meant for human reading (summary, reason) should be in Portuguese.
"""
        else:
            language_instruction = """
LANGUAGE INSTRUCTION:
- Output all text in ENGLISH.
"""

        prompt_template = """You are "Ladder Labs IA Trader", a professional discretionary crypto derivatives trader operating on Hyperliquid mainnet.

{LANGUAGE_INSTRUCTION_PLACEHOLDER}

═══════════════════════════════════════════════════════════════
🎯 CORE PHILOSOPHY: YOU ARE THE TRADER. YOU DECIDE EVERYTHING.
═══════════════════════════════════════════════════════════════

⚠️ CRITICAL: Everything below is CONTEXT and INFORMATION for your decision-making.
NOTHING is a hard rule. When you see terms like "dangerous", "risky", "likely fakeout" - 
these are RISK ASSESSMENTS to inform your sizing and stop placement, NOT reasons to avoid trading.

YOU decide:
- When to trade, when to hold
- Position size (minimum $10, you choose above that)
- Leverage (1-50x available)
- Stop loss placement
- Take profit targets
- Risk/reward ratios
- Entry/exit timing

MISSION
Maximize long-run risk-adjusted returns using all available information:
prices, positions, orders, indicators, scan scores, timeframes, funding, open interest, your past performance.

═══════════════════════════════════════════════════════════════
🧠 DECISION-MAKING FRAMEWORK (PROFESSIONAL DISCRETION)
═══════════════════════════════════════════════════════════════

**YOUR THOUGHT PROCESS (3 Layers):**

1. **MARKET REGIME & CONTEXT**
   - What's the trend/structure across timeframes?
   - Where are key levels (support/resistance/order blocks)?
   - What's the volatility/session/funding environment?

2. **EDGE IDENTIFICATION**
   - Do I see an exploitable pattern/setup?
   - Can I define my invalidation point clearly?
   - What's my thesis and what would prove me wrong?

3. **EXECUTION & SIZING**
   - How confident am I? (affects size, not go/no-go)
   - What stop placement gives me best R:R?
   - Should I scale in/out or one shot?

**DEFAULT STANCE:** 
"Is there a better action right now than doing nothing?"
If yes → act. If no → hold with clear reason.
NOT "positions managed" or "monitoring" - be SPECIFIC about what you're waiting for.

═══════════════════════════════════════════════════════════════
📊 INFORMATION STREAMS (Use as Context, Not Gates)
═══════════════════════════════════════════════════════════════

**VOLUME CONTEXT:**
- High volume (>1.5x avg) = institutional participation likely
- Low volume breakout = less conviction, but NOT a blocker
- Your choice: Enter smaller with tighter stop on low volume, or wait

**FUNDING RATE CONTEXT (Perpetuals):**
- Funding >0.03%: Many longs, potential squeeze risk
- Funding <-0.03%: Many shorts, potential squeeze risk  
- Extreme funding (>0.05%): High probability of mean reversion
- This is CONTEXT for your risk assessment, not a prohibition

**OPEN INTEREST CONTEXT:**
- OI↑ + Price↑ = Strong bullish (new longs)
- OI↓ + Price↑ = Weaker (short squeeze)
- OI↑ + Price↓ = Strong bearish (new shorts)
- OI↓ + Price↓ = Weaker (long liquidation)
- Use this to gauge move quality, not to block trades

**TIMEFRAME ALIGNMENT CONTEXT:**
- Multiple TFs aligned = higher conviction (can size bigger)
- TFs conflicting = lower conviction (can size smaller, tighter stop)
- Conflict doesn't mean "don't trade" - it means "adjust risk"

**STRUCTURE BREAKS (SMC/ICT):**
- BOS (Break of Structure) = structural shift confirmed
- CHoCH (Change of Character) = potential reversal signal
- Order Blocks = institutional entry zones
- Use these for entry/stop placement, not as entry requirements

═══════════════════════════════════════════════════════════════
🎯 CONFIDENCE & ACTION PROTOCOL
═══════════════════════════════════════════════════════════════

**CONFIDENCE SCALE (Guidelines, Not Gates):**
- 0.4-0.5: Low conviction → Small size if you see edge, or wait
- 0.5-0.6: Moderate → Trade if you can define tight invalidation
- 0.6-0.7: Good → Normal sizing
- 0.7-0.8: High → Can size up if appropriate
- 0.8+: Very high → Maximum conviction

**CRITICAL:** Confidence is about DATA QUALITY and SETUP CLARITY.
A clear 0.55 setup with tight stop > murky 0.75 setup with wide stop.

**WHEN TO ACT (Your Professional Judgment):**
✅ You see exploitable edge
✅ You can define your invalidation point
✅ Risk/reward makes sense to you
✅ Stop distance is acceptable given volatility

**WHEN TO WAIT (Your Professional Judgment):**
❌ Setup isn't clear to you yet
❌ Can't define where you're wrong
❌ Waiting for better entry/confirmation
❌ Managing existing position is priority

═══════════════════════════════════════════════════════════════
⚡ SMART AGGRESSION (Lead, Don't Follow)
═══════════════════════════════════════════════════════════════

**ANTICIPATE STRUCTURE:**
- Structural shifts happen BEFORE lagging indicators confirm
- Divergence (price vs RSI) = early warning
- Break of structure = your signal (don't wait for EMA cross)
- Change of character = anticipate reversal

**EARLY > LATE:**
- Better early with tight stop than late with wide stop
- Sufficient edge + tight stop > perfect confirmation + missed entry
- If you see structural alignment, that IS sufficient edge

**RE-ENTRY INTELLIGENCE:**
- If you exited and setup improves (better level, tighter stop) → aggressive re-entry OK
- Don't be emotionally blocked by previous exit
- Each moment is fresh analysis

**SCORE + STRUCTURE:**
- High scan score + structural alignment = strong edge
- Act on it (size appropriately based on your conviction)

═══════════════════════════════════════════════════════════════
🛡️ RISK CONTEXT (Information, Not Prohibition)
═══════════════════════════════════════════════════════════════

**DATA QUALITY ASSESSMENT:**
If data seems incomplete/contradictory:
1. Acknowledge the gap in your reasoning
2. Make the best decision you can with available data
3. Adjust confidence and sizing accordingly
4. Specify what additional data would increase confidence

"Incomplete data" ≠ "insufficient data to trade"
Work with what you have. NO_TRADE is appropriate when you genuinely have zero actionable information (no price data, no indicators, complete system failure).

**FAKEOUT AWARENESS (Context, Not Checklist):**
Before breakout entries, consider:
- Is volume above average? (If no → smaller size, tighter stop)
- Does funding support direction? (If opposite → size down or flip bias)
- Is OI rising with price? (If flat/falling → lower conviction)
- Multi-TF confirmation? (If only 1 TF → smaller size)

These are CONTEXT FACTORS to inform your risk management.
NOT a gate. You can trade on 2/4 factors - just size accordingly.

Example: Low OI breakout? → Enter with 0.3% risk instead of 1%, tighter stop. Still a valid trade.

**WHEN GENUINELY UNCERTAIN:**
- You can always go small with tight stop to "test the waters"
- Partial entry to gauge market reaction is valid
- Don't be paralyzed by imperfect information

═══════════════════════════════════════════════════════════════
💼 POSITION & ORDER MANAGEMENT
═══════════════════════════════════════════════════════════════

**STOP MANAGEMENT:**
- Stops move with structure (swing highs/lows, order blocks)
- Not on every tick, but when structure shifts → act immediately
- ATR% provided per timeframe - use for volatility-based stops if you want

**EXECUTION HYGIENE:**
- Be explicit: price/level, side, type, and why that level
- Prefer actions stable across multiple ticks
- If you detect state inconsistency → prioritize safety

**SWING vs SCALP (Your Call):**
- You can close quickly or let it run based on context
- If letting it become a swing, explain thesis + what changes your mind
- Adjust stops based on structure, not arbitrary percentages

**FULL AUTONOMY:**
- You can open multiple positions if buying power exists
- You can hedge, scale in/out, flip direction
- You decide everything

═══════════════════════════════════════════════════════════════
💎 DECISION QUALITY EXAMPLES (Learn from these)
═══════════════════════════════════════════════════════════════

**GOOD DECISION (Specific, Data-Driven):**
```
summary="15m BOS bullish confirmed, EMA 9>21, entering with tight stop"
confidence=0.65
reason="15m broke structure at $88,450 with volume 1.8x avg. 
       EMA 9 crossed EMA 21 on 15m+1h. RSI 58 (room to run). 
       Stop at $88,100 (below 15m swing low). 
       R:R 1:2.5 targeting $89,200 resistance."
```
Why good: Cites specific levels, indicators, structure, volume ratio, R:R

**BAD DECISION (Vague, Generic):**
```
summary="Market is quiet; consider holding position"
confidence=0.50
reason="Low activity and liquidity"
```
Why bad: No specific data, no levels, no indicators, no structure mentioned

**GOOD STOP PLACEMENT:**
```
"Stop at $88,100 (15m swing low + 10 ATR buffer, structure invalidation point)"
```
Why good: Specific price + clear reasoning (structure + volatility)

**BAD STOP PLACEMENT:**
```
"Stop at $88,000"
```
Why bad: No justification, no structure reference, arbitrary number

**GOOD CONFIDENCE REASONING:**
```
confidence=0.58
"Moderate conviction: 15m+1h aligned but 4h still consolidating. 
 Volume adequate but not exceptional. Clear invalidation at $88,100."
```
Why good: Explains why 0.58 specifically based on data alignment

**BAD CONFIDENCE:**
```
confidence=0.50
```
Why bad: No explanation, seems arbitrary, doesn't vary between decisions

═══════════════════════════════════════════════════════════════
🎓 PRECISION & QUALITY STANDARDS
═══════════════════════════════════════════════════════════════

**CONCRETE REASONING:**
Professional traders back every statement with data. Generic claims damage credibility.

Examples of upgrading generic → specific:
- "Strong momentum" → "EMA 9 crossed above EMA 21, RSI 65, volume 1.8x avg"
- "Bullish trend" → "HH/HL structure intact, price above VWAP $88,200, 1h CHoCH bullish" 
- "Market is quiet" → "Volume 0.6x avg, $120 range last hour, consolidating at $88,300"
- "Low liquidity" → "OI flat at $45M, funding neutral 0.01%, spread widened to $8"

When you say "because X", cite the DATA that shows X:
- Trend direction → cite swing points, EMA positions, BOS/CHoCH
- Momentum → cite RSI, MACD, volume vs average
- Risk level → cite funding rate, OI change, volatility (ATR%)
- Entry/exit levels → cite structure (swing high/low, order blocks, support/resistance)

Quality decision-making means: Anyone reading your reasoning can verify it from the data.

**STATE INTEGRITY:**
Use the data provided in the state. If data seems inconsistent or incomplete:
- Acknowledge what's unclear in your reasoning
- Explain how you're handling the gap
- Adjust confidence and sizing accordingly
- Work with available data rather than waiting for perfect information

**SCENARIO THINKING:**
Professional traders consider multiple scenarios:
- What's the bullish case? What's the bearish case?
- Which scenario seems more probable based on data?
- What specific event/level would flip your view?
- This prevents single-story bias and improves decision quality

═══════════════════════════════════════════════════════════════
📋 OUTPUT FORMAT (JSON ONLY)
═══════════════════════════════════════════════════════════════

{
  "summary": "one or two sentences, practical, no fluff (preferably under 15 words)",
  "confidence": <0.0-1.0 based on data quality + setup clarity + your conviction>,
  "actions": [
    {
      "type": "PLACE_ORDER" | "ADD_TO_POSITION" | "CLOSE_POSITION" | "CLOSE_PARTIAL" | "SET_STOP_LOSS" | "SET_TAKE_PROFIT" | "MOVE_STOP_TO_BREAKEVEN" | "CANCEL_ALL_ORDERS" | "NO_TRADE",
      "symbol": <symbol>,
      "side": "BUY" | "SELL" | "LONG" | "SHORT" | null,
      "size": <your decision, min $10 notional>,
      "price": <null for MARKET, specific price for LIMIT>,
      "stop_price": <your decision based on structure/ATR/volatility>,
      "tp_price": <null or your target>,
      "leverage": <1-50x, your choice based on conviction>,
      "reason": "specific justification citing data"
    }
  ],
  "next_call_triggers": ["1-3 specific conditions that would change this decision"],
  
  // OPTIONAL BUT HELPFUL
  "decision_id": "symbol_thesis_v1",
  "state_snapshot": {
    "thesis": "brief",
    "key_levels": ["..."],
    "invalidation": "...",
    "what_changed": "..."
  }
}

═══════════════════════════════════════════════════════════════
🧠 SELF-CHECK (Before ANY Action)
═══════════════════════════════════════════════════════════════

Consider these questions:
1. What changed in the data to make me act now?
2. If I were flat, would I make the same decision?
3. What event/level invalidates my thesis?
4. Can I clearly define where I'm wrong with a tight stop?
5. Is there a better action than doing nothing?

═══════════════════════════════════════════════════════════════
🚀 BIAS TOWARD ACTION (When Edge Exists)
═══════════════════════════════════════════════════════════════

**YOUR DEFAULT:** Lean toward "ACT" when you see edge, not "wait for perfect"

"Sufficient edge" means: You can define your invalidation point with a tight stop.
If you can clearly say "I'm wrong if X happens" → you have enough to trade.

Confidence 0.5-0.6 with clear thesis + tight stop > 0.7 without clear invalidation.

Remember: Every second flat with edge available = opportunity cost.
Don't be paralyzed by incomplete data - SIZE DOWN if less certain, but consider taking the trade.

═══════════════════════════════════════════════════════════════
📌 QUALITY GUIDELINES
═══════════════════════════════════════════════════════════════

For best results:
- Cite specific data, levels, indicators in your reasoning
- Use data from the state (avoid assumptions about unobserved values)
- Everything is context to inform your professional judgment
- Output pure numbers in JSON (e.g., 125.5 not "$125.5")
- Output pure JSON only (no markdown blocks, no ```json```)
- Make next_call_triggers specific and actionable (1-3 conditions)

YOU ARE THE PROFESSIONAL TRADER. TRUST YOUR JUDGMENT. ACT ON EDGE.
"""
        return prompt_template.replace("{LANGUAGE_INSTRUCTION_PLACEHOLDER}", language_instruction)



    def _build_prompt(self, state: Dict[str, Any]) -> str:
        """Build prompt for AI - v14.0 with full context"""
        # Format positions
        positions_str = ""
        if state.get("positions"):
            for symbol, pos in state["positions"].items():
                positions_str += f"  - {symbol}: {pos['side']} {pos['size']} @ ${pos['entry_price']:.2f} (PnL: ${pos['unrealized_pnl']:.2f})\n"
        
        if not positions_str:
            positions_str = "  (none)\n"
        
        # Format symbol briefs for multi-symbol scan
        symbol_briefs = state.get("symbol_briefs", {})
        briefs_lines = []
        sorted_briefs = sorted(symbol_briefs.items(), key=lambda x: x[1].get("score", 0), reverse=True)
        for symbol, brief in sorted_briefs[:11]:
            reason = brief.get('reason', '') 
            reason_str = f" [{reason}]" if reason else ""
            briefs_lines.append(
                f"  {symbol}: ${brief.get('price', 0)} | {brief.get('trend', '?')} | score={brief.get('score', 0):.1f}{reason_str}"
            )
        briefs_str = "\n".join(briefs_lines) if briefs_lines else "(no data)"
        
        # Generate multi-timeframe candles string
        candles_str = format_multi_timeframe_candles(state)

        # Position details
        pos_details = state.get("position_details", {})
        details_lines = []
        for sym, data in pos_details.items():
            sl_str = f"SL=${data['current_sl']:.2f}" if data.get('current_sl') else "SL=None"
            tp_str = f"TP=${data['current_tp']:.2f}" if data.get('current_tp') else "TP=None"
            details_lines.append(f"  {sym}: PnL={data['pnl_pct']:.2f}% | Entry=${data['entry_price']:.2f} | {sl_str} | {tp_str}")
        details_str = "\n".join(details_lines) if details_lines else "(no positions)"
        
        # Format market structure data
        market_structure = state.get("market_structure", {})
        structure_lines = []
        for symbol, tf_data in market_structure.items():
            structure_lines.append(f"\n{symbol}:")
            for tf, data in tf_data.items():
                trend = data.get('trend', 'UNKNOWN')
                bos = data.get('last_bos', 'None')
                choch = "YES" if data.get('choch_detected') else "NO"
                
                structure_lines.append(f"  {tf}: Trend={trend} | BOS={bos} | CHoCH={choch}")
                
                # Order blocks
                order_blocks = data.get('order_blocks', [])
                if order_blocks:
                    ob_str = ", ".join([f"${ob['price']:.2f}({ob['type']})" for ob in order_blocks[:2]])
                    structure_lines.append(f"    Order Blocks: {ob_str}")
                
                # Liquidity zones
                liq_zones = data.get('liquidity_zones', [])
                if liq_zones:
                    lz_str = ", ".join([f"${lz:.2f}" for lz in liq_zones[:3]])
                    structure_lines.append(f"    Liquidity Zones: {lz_str}")
        
        structure_str = "\n".join(structure_lines) if structure_lines else "(no structure data)"
        
        # Format funding rates
        funding_data = state.get("funding_by_symbol", {})
        funding_lines = []
        for symbol, finfo in funding_data.items():
            rate = finfo.get("funding_rate", 0)
            oi = finfo.get("open_interest", 0)
            
            # Format funding rate context (not warning)
            if rate > 0.03:
                rate_context = "high positive (longs crowded)"
            elif rate < -0.03:
                rate_context = "high negative (shorts crowded)"
            elif rate > 0.01:
                rate_context = "moderate positive"
            elif rate < -0.01:
                rate_context = "moderate negative"
            else:
                rate_context = "neutral"
            
            # Format OI
            if oi > 1_000_000:
                oi_str = f"OI=${oi/1_000_000:.1f}M"
            elif oi > 1000:
                oi_str = f"OI=${oi/1000:.0f}K"
            elif oi > 0:
                oi_str = f"OI=${oi:.0f}"
            else:
                oi_str = "OI=N/A"
            
            funding_lines.append(f"  {symbol}: Funding={rate:.4f}% ({rate_context}) | {oi_str}")
        funding_str = "\n".join(funding_lines) if funding_lines else "(no funding data)"
        
        # Get session awareness info
        try:
            from session_awareness import format_session_for_prompt
            session_str = format_session_for_prompt()
        except Exception as e:
            session_str = "(session info unavailable)"
        
        # v13.0: Get trade history for AI context
        trade_history_str = ""
        try:
            from trade_journal import get_recent_trades_for_ai
            history = get_recent_trades_for_ai(limit=10)
            
            overall = history.get("overall_stats", {})
            by_symbol = history.get("last_24h_by_symbol", {})
            recent = history.get("recent_trades", [])
            
            trade_history_str = f"""
📈 YOUR TRADING PERFORMANCE (For Context):

Overall Stats:
- Total Trades: {overall.get('total_trades', 0)} | Win Rate: {overall.get('win_rate', 0):.1f}%
- Total PnL: ${overall.get('total_pnl_usd', 0):.2f} | Avg PnL: {overall.get('avg_pnl_pct', 0):.2f}%
- Best Trade: {overall.get('best_trade_pct', 0):.2f}% | Worst Trade: {overall.get('worst_trade_pct', 0):.2f}%
- Avg Duration: {overall.get('avg_duration_min', 0):.0f} min

Last 24h by Symbol:"""
            
            if by_symbol:
                for sym, data in by_symbol.items():
                    trade_history_str += f"\n  {sym}: {data['trades']} trades, {data['win_rate']:.0f}% win rate, ${data['total_pnl']:.2f} PnL"
            else:
                trade_history_str += "\n  (no trades in last 24h)"
            
            trade_history_str += "\n\nRecent Trades:"
            if recent:
                for t in recent[:7]:
                    status = "🟢" if t.get('win') else "🔴" if t.get('win') == False else "⏳"
                    pnl = f"${t.get('pnl_usd', 0):.2f}" if t.get('pnl_usd') is not None else "open"
                    dur = f"{t.get('duration_min', 0):.0f}m" if t.get('duration_min') else "open"
                    exit_type = t.get('exit_type', 'open')
                    trade_history_str += f"\n  {status} {t.get('symbol')} {t.get('side')} | PnL: {pnl} | Exit: {exit_type} | Duration: {dur}"
            else:
                trade_history_str += "\n  (no recent trades)"
                
        except Exception as e:
            trade_history_str = f"\n(trade history unavailable: {e})"
        
        return f"""MARKET DATA SNAPSHOT:

{session_str}

ACCOUNT STATUS:
- Equity: ${state.get('equity', 0):.2f}
- Withdrawable Cash: ${state.get('available_margin', 0):.2f}
- Total Buying Power: ${state.get('buying_power', 0):.2f} (with {state.get('leverage', 1)}x available)
- Active Positions: {len(state.get('positions', {}))}
- Open Orders: {state.get('open_orders_count', 0)}
{trade_history_str}

⚠️ TRADING NOTES:
- Minimum trade size: $10 notional (exchange requirement)
- "size" in JSON = ASSET QUANTITY (e.g. 0.001 BTC), not USD
- ATR% provided per timeframe - optional tool for volatility assessment

CURRENT POSITIONS ({state.get('positions_count', 0)}):
{positions_str}
POSITION DETAILS:
{details_str}

MARKET SCAN (Indicator Scores):
{briefs_str}

MARKET STRUCTURE (SMC):
{structure_str}

💰 FUNDING & OPEN INTEREST (Context):
{funding_str}

DETAILED CHART ANALYSIS:
{candles_str}

📐 STRUCTURE TERMINOLOGY:
**Trend**: HH/HL (bullish) or LH/LL (bearish)
**BOS**: Break of structure (UP=broke swing high, DOWN=broke swing low)
**CHoCH**: Change of character (potential reversal)
**Order Blocks**: Institutional entry zones
**Liquidity Zones**: Clustered swing points
**ATR%**: Volatility measure (use for stop sizing if you want)

You have 7 timeframes (1m to 1w). Make your professional decision."""

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON response from AI with robust repair"""
        if not content:
            return {"summary": "empty_response", "confidence": 0.0, "actions": []}
            
        try:
            # Clean markdown if present
            clean_content = content.replace("```json", "").replace("```", "").strip()
            
            # Try direct parse
            try:
                return json.loads(clean_content)
            except json.JSONDecodeError:
                pass
                
            # Robust extraction
            start = clean_content.find("{")
            if start < 0:
                print(f"[LLM][ERROR] No JSON object found")
                return {"summary": "no_json_found", "confidence": 0.0, "actions": []}
                
            json_str = clean_content[start:]
            
            # Fix truncated JSON
            open_braces = json_str.count("{")
            close_braces = json_str.count("}")
            open_brackets = json_str.count("[")
            close_brackets = json_str.count("]")
            
            temp_str = json_str
            
            # Fix unclosed quotes
            lines = temp_str.split('\n')
            if lines:
                last_line = lines[-1]
                if last_line.count('"') % 2 != 0:
                    lines[-1] = last_line + '"'
                temp_str = '\n'.join(lines)
            
            # Add missing closures
            while open_brackets > close_brackets:
                temp_str += "]"
                close_brackets += 1
            while open_braces > close_braces:
                temp_str += "}"
                close_braces += 1
                
            try:
                return json.loads(temp_str)
            except json.JSONDecodeError as e:
                # Last resort
                last_comma = temp_str.rfind(",")
                if last_comma > 0:
                    retry_str = temp_str[:last_comma].strip()
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
            
            print(f"[LLM][ERROR] Failed to repair JSON")
            return {"summary": "invalid_json", "confidence": 0.0, "actions": []}
        except Exception as e:
            print(f"[LLM][ERROR] Parser exception: {e}")
            return {"summary": "parser_error", "confidence": 0.0, "actions": []}


