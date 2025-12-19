"""
LLM Client for Engine V0
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
                max_tokens=2048, # Increased to prevent truncation
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
            
            # Record detailed trade logs for entries and risk management updates
            try:
                from dashboard_api import add_trade_log, update_trade_log
                
                for action in actions:
                    action_type = action.get("type", "")
                    symbol = action.get("symbol", "UNKNOWN")
                    
                    # Entry actions - create new trade log
                    if action_type in ["PLACE_ORDER", "ADD_TO_POSITION"]:
                        # Get state snapshot for confluence factors
                        state_snapshot = decision.get("state_snapshot", {})
                        key_levels = state_snapshot.get("key_levels", [])
                        triggers = decision.get("next_call_triggers", [])
                        
                        # Build confluence factors from AI's analysis
                        confluence = []
                        if key_levels:
                            confluence.extend([f"Key level: {lvl}" for lvl in key_levels[:3]])
                        if triggers:
                            confluence.extend([f"Trigger: {t}" for t in triggers[:2]])
                        if not confluence:
                            confluence = [
                                f"{action.get('side', 'LONG')} entry based on structure",
                                "Multi-timeframe confluence",
                                action.get("reason", "AI discretionary decision")[:50]
                            ]
                        
                        # Get price from action or estimate from state
                        entry_price = action.get("price")
                        if not entry_price:
                            prices = state.get("prices", {})
                            entry_price = prices.get(symbol, 0)
                        
                        # Calculate risk values if possible
                        stop_price = action.get('stop_price', 0)
                        risk_usd = 0
                        risk_pct = 0
                        
                        if entry_price and stop_price and stop_price != entry_price:
                            size_usd = action.get('size', 0)
                            # Risk per share
                            risk_per_unit = abs(entry_price - stop_price)
                            # Total risk in USD
                            num_units = size_usd / entry_price if entry_price > 0 else 0
                            risk_usd = num_units * risk_per_unit
                            
                            # Risk % of equity
                            equity = state.get("equity", 0)
                            if equity > 0:
                                risk_pct = (risk_usd / equity) * 100

                        trade_log = {
                            'symbol': symbol,
                            'action': 'ENTRY',
                            'side': action.get('side', 'LONG'),
                            'entry_price': entry_price,
                            'size': action.get('size', 0),
                            'leverage': action.get('leverage', 1),
                            'strategy': {
                                'name': decision.get('decision_id', 'AI Discretionary Trade'),
                                'timeframe': 'Multi-TF Analysis',
                                'setup_quality': round(confidence * 10, 1),
                                'confluence_factors': confluence
                            },
                            'entry_rationale': action.get('reason', summary),
                            'risk_management': {
                                'stop_loss': stop_price,
                                'stop_loss_reason': state_snapshot.get('invalidation', 'Structure-based stop'),
                                'risk_usd': round(risk_usd, 2),
                                'risk_pct': round(risk_pct, 2),
                                'take_profit_1': action.get('tp_price', 0),
                                'tp1_reason': 'AI target level',
                                'tp1_size_pct': 50,
                                'take_profit_2': action.get('tp2_price', action.get('tp_price', 0) * (1.05 if action.get('side') == 'LONG' else 0.95)),
                                'tp2_reason': 'Secondary target / Trailing',
                                'tp2_size_pct': 50
                            },
                            'confidence': confidence,
                            'ai_notes': summary,
                            'expected_outcome': state_snapshot.get('thesis', 'AI managing position dynamically')
                        }
                        add_trade_log(trade_log)
                        print(f"[LLM] Trade log recorded: {symbol} {action.get('side')} @ {entry_price}")
                    
                    # Risk management updates - update existing log
                    elif action_type in ["SET_STOP_LOSS", "SET_TAKE_PROFIT", "MOVE_STOP_TO_BREAKEVEN"]:
                        update_data = {
                            'symbol': symbol,
                            'action': 'UPDATE',
                            'update_type': action_type,
                            'confidence': confidence,
                            'ai_notes': f"[{action_type}] {action.get('reason', summary)}"
                        }
                        
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
                print(f"[LLM] Failed to record trade log: {e}")
            
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
- **SMART STOP MANAGEMENT:** Stops should move with structure (swing highs/lows, order blocks), not on every tick. But if structure shifts, act immediately.
- **CONCISION RULE:** Your "summary" MUST be under 15 words. Be extremely blunt and professional. (e.g. "Long SOL at support, targeting 1h swing high.")
- **KEY LEVELS:** Always identify nearby Resistance and Support based on the provided SwingH/SwingL data.
- **LANGUAGE:** Internal thought can be any, but JSON "summary" and "reason" must be concise English.

SMART AGGRESSION PROTOCOL
- **Early Entry > Late Entry:** Sufficient edge with tight stop beats perfect confirmation with wide stop.
- **Anticipate Structure:** Watch for structural shifts (break of structure, change of character) BEFORE price fully confirms.
- **Re-entry Intelligence:** If you exited a position and structure improves (e.g., better entry level, tighter stop), re-enter aggressively.
- **Score + Structure:** High scan score + structural alignment = strong edge. Act on it.

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

📊 CONFIDENCE & ACTION THRESHOLD
- confidence ∈ [0,1] based on data quality + setup clarity + structural alignment.
- **Sufficient Edge Principle:** Don't wait for perfect confidence. Act on sufficient edge (0.6+) if:
  * Structure aligns across timeframes
  * Risk/reward looks favorable (aim for 2:1+ when possible, but your call)
  * Entry allows tight stop
- If data is incomplete/contradictory: HOLD or minimal action, unless urgent safety needed.

🎯 ANTICIPATION PROTOCOL (CRITICAL)
- **Lead, Don't Follow:** Structural shifts happen BEFORE lagging indicators confirm.
- **Divergence = Early Warning:** Price vs RSI divergence, timeframe conflicts = potential reversal. Act early.
- **Break of Structure:** When price breaks key structure (swing high/low), that's your signal. Don't wait for EMA cross.
- **Change of Character:** When market behavior shifts (e.g., lower highs after uptrend), anticipate reversal.
- **Better to be early with tight stop than late with wide stop.**

🚨 FAKEOUT PREVENTION (CRITICAL - AVOID FALSE BREAKOUTS)
This is ESSENTIAL for profitable trading. Most losses come from fakeouts.

**VOLUME CONFIRMATION (MANDATORY FOR BREAKOUTS):**
- Breakout WITHOUT high volume = likely FAKEOUT. DO NOT ENTER.
- Look for relative_volume > 1.5 (150% of average) on breakout candle.
- If breaking key level with low volume: WAIT for retest/confirmation.
- Volume spike BEFORE price move = institutional accumulation = valid signal.
- Volume dies during breakout = trap, expect reversal back.

**FUNDING RATE AWARENESS (PERPETUAL SPECIFIC):**
You are trading perpetuals on Hyperliquid. Funding rate is CRITICAL.
- **funding_rate > 0.03%**: Market is over-leveraged LONG → dangerous for new longs
- **funding_rate < -0.03%**: Market is over-leveraged SHORT → dangerous for new shorts  
- **Extreme funding (>0.05% or <-0.05%)**: HIGH PROBABILITY of squeeze against crowded side
- Counter-trend entries CAN be profitable when funding is extreme (mean reversion)

**FAKEOUT DETECTION CHECKLIST:**
Before entering on any breakout, ask:
1. Is volume above average (relative_volume > 1.5)? If NO → likely fakeout
2. Is funding rate supporting this direction? If opposite → higher fakeout risk
3. Is there clear structure break on multiple timeframes? If only 1TF → suspect
4. Did price wick above/below level and return? That's the fakeout, not the signal.

**WHEN IN DOUBT:**
- Don't chase breakouts. Wait for RETEST of broken level.
- If you miss the move, don't FOMO. Wait for next setup.
- A missed trade costs $0. A fakeout trade costs money.

💪 TRUST YOUR EDGE
- If you see clear structural shift + divergence + timeframe alignment, that IS sufficient edge even if confidence feels "only" 0.65
- Don't second-guess strong setups waiting for 0.9 confidence
- Better to act on 0.65 with tight stop than wait for 0.9 and miss entry
- High conviction setups (0.75+) deserve aggressive action

💡 CONVICTION-BASED SIZING (OPTIONAL CONCEPT)
You may choose to scale your position sizes based on conviction if you wish:
- Higher confidence setups could justify larger positions (if you deem it appropriate)
- Lower confidence setups might warrant smaller positions (if you prefer)
- This is entirely your choice - size positions however you see fit based on your professional judgment
- Consider stop distance, market conditions, and your own risk assessment when sizing

OUTPUT FORMAT (STRICT JSON ONLY - NO MARKDOWN)
{
  "summary": "one or two sentences, practical, no fluff",
  "confidence": <0.0-1.0 based on data quality, setup clarity, regime alignment>,
  "actions": [
    {
      "type": "PLACE_ORDER" | "ADD_TO_POSITION" | "CLOSE_POSITION" | "CLOSE_PARTIAL" | "SET_STOP_LOSS" | "SET_TAKE_PROFIT" | "MOVE_STOP_TO_BREAKEVEN" | "CANCEL_ALL_ORDERS" | "NO_TRADE",
      "symbol": <symbol from scan>,
      "side": "BUY" | "SELL" | "LONG" | "SHORT" | null,
      "size": <calculate based on your risk assessment and conviction, min $10 notional (exchange requirement)>,
      "price": <null for MARKET, specific price for LIMIT>,
      "stop_price": <calculate based on market structure and support/resistance>,
      "tp_price": <null or specific target based on R:R>,
      "leverage": <1-50x available, choose based on conviction and volatility>,
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
- **PURE NUMBERS:** Always output price, size, and leverage as pure numbers in JSON (e.g., 125.5 instead of "$125.5").
- Pure JSON only, no markdown blocks, no ```json```.
"""
        return prompt_template.replace("{LANGUAGE_INSTRUCTION_PLACEHOLDER}", language_instruction)


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
        briefs_str = "\n".join(briefs_lines) if briefs_lines else "(no data)"
        
        # Generate multi-timeframe candles string (ALL symbols, ALL candles)
        # Decorated with RSI/EMA indicators per timeframe
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
        
        # Format funding rates (CRITICAL for identifying over-leveraged markets)
        funding_data = state.get("funding_by_symbol", {})
        funding_lines = []
        for symbol, finfo in funding_data.items():
            rate = finfo.get("funding_rate", 0)
            # Color code extreme rates
            if rate > 0.03:
                warning = "⚠️ HIGH (longs paying)"
            elif rate < -0.03:
                warning = "⚠️ HIGH (shorts paying)"
            elif rate > 0.01:
                warning = "↑ positive"
            elif rate < -0.01:
                warning = "↓ negative"
            else:
                warning = "neutral"
            funding_lines.append(f"  {symbol}: {rate:.4f}% ({warning})")
        funding_str = "\n".join(funding_lines) if funding_lines else "(no funding data)"
        
        return f"""MARKET DATA SNAPSHOT:

ACCOUNT STATUS:
- Equity: ${state.get('equity', 0):.2f} (Total Portfolio Value)
- Withdrawable Cash: ${state.get('available_margin', 0):.2f}
- Total Buying Power: ${state.get('buying_power', 0):.2f} (with {state.get('leverage', 1)}x leverage)
- Active Positions: {len(state.get('positions', {}))}
- Open Orders: {state.get('open_orders_count', 0)}

⚠️ CRITICAL TRADING RULES:
- Minimum trade size is $10.00 notional.
- "size" field in JSON is ASSET QUANTITY (e.g. 0.001 BTC), NOT USD. Use prices to convert.

CURRENT POSITIONS ({state.get('positions_count', 0)}):
{positions_str}
POSITION RISK DETAILS:
{details_str}

MARKET SCAN (TOP INDICATOR SCORES):
{briefs_str}

MARKET STRUCTURE (SMC):
{structure_str}

💰 FUNDING RATES (CRITICAL FOR FAKEOUT DETECTION):
{funding_str}

DETAILED CHART ANALYSIS (Top 8 Symbols):
{candles_str}

📐 MARKET STRUCTURE (SMART MONEY CONCEPTS)
You now have access to institutional market structure data for key timeframes:

**Trend**: Based on Higher Highs/Higher Lows (BULLISH) or Lower Highs/Lower Lows (BEARISH)
**BOS (Break of Structure)**: Trend continuation signal
  - UP: Price broke above recent swing high (bullish continuation)
  - DOWN: Price broke below recent swing low (bearish continuation)
**CHoCH (Change of Character)**: Early reversal warning
  - In uptrend: Failed to make HH, made LH instead
  - In downtrend: Failed to make LL, made HL instead
**Order Blocks**: Institutional entry zones (last candle before strong move)
  - BULLISH: Last red candle before up move = potential support
  - BEARISH: Last green candle before down move = potential resistance
**Liquidity Zones**: Clustered swing highs/lows where stops are placed

HOW TO USE SMC DATA:
- **Trend Following**: Enter on pullbacks to order blocks in trending markets
- **Reversal Trading**: CHoCH = early warning, consider exits or reversal entries
- **Target Selection**: Liquidity zones = high-probability targets (stops get hit)
- **Structure Confirmation**: BOS confirms trend, wait for pullback to order block
- **Multi-TF Alignment**: 1h trend + 15m BOS + 5m order block = high conviction

EXAMPLE DECISION FLOW:
1. Check 1h trend: BULLISH
2. See 15m BOS: UP (confirms trend)
3. Wait for pullback to 1h order block
4. Enter LONG with stop below order block
5. Target: Next liquidity zone above

📊 STRATEGIC GUIDANCE:
- You have access to RSI(14) and EMA(9/21) for every timeframe. Treat them as supplementary technical signals for your discretionary analysis.
- Use the institutional structures (SwingH/SwingL) across all timeframes to assist in identifying key support/resistance zones and defining logical invalidation points.
- You have comprehensive market context across multiple timeframes. Analyze the interplay between scales (top-down) before making your final decision.

Perform a professional top-down analysis and execute with your full discretionary conviction. What is your decision?"""

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
