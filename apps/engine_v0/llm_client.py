"""
LLM Client v14.3 PERFECT - Zero Hard Limits, Pure Intelligence
Multi-provider support: Anthropic Claude / OpenAI GPT
Philosophy: EDUCATE the AI, don't CONSTRAIN it
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Multi-provider LLM client with intelligent routing
    Priority: Claude Sonnet 4 > GPT-4o-mini (fallback)
    """
    
    def __init__(self):
        self.provider = self._determine_provider()
        self.model = self._get_model_name()
        self.client = self._initialize_client()
        
        logger.info(f"[LLM] Initialized with provider={self.provider} model={self.model}")
    
    def _determine_provider(self) -> str:
        """Auto-detect provider based on environment variables"""
        explicit_provider = os.getenv("AI_PROVIDER", "").lower()
        if explicit_provider in ["anthropic", "claude"]:
            return "anthropic"
        elif explicit_provider in ["openai", "gpt"]:
            return "openai"
        
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        
        if anthropic_key and anthropic_key.startswith("sk-ant-"):
            logger.info("[LLM] Auto-detected Anthropic API key, using Claude")
            return "anthropic"
        elif openai_key:
            logger.info("[LLM] Using OpenAI as provider")
            return "openai"
        else:
            raise ValueError("No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY")
    
    def _get_model_name(self) -> str:
        """Get model name from env or default"""
        model_env = os.getenv("AI_MODEL", "")
        if model_env:
            return model_env
        
        if self.provider == "anthropic":
            return "claude-sonnet-4-20250514"
        else:
            return "gpt-4o-mini"
    
    def _initialize_client(self):
        """Initialize provider-specific client"""
        if self.provider == "anthropic":
            try:
                from anthropic import Anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not set")
                return Anthropic(api_key=api_key)
            except ImportError:
                logger.error("[LLM] anthropic package not installed. Falling back to OpenAI")
                self.provider = "openai"
                self.model = "gpt-4o-mini"
        
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        return OpenAI(api_key=api_key)
    
    def get_trading_decision(
        self,
        market_context: Dict[str, Any],
        candles_summary: str,
        position_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Get autonomous trading decision from LLM
        
        Returns:
            {
                "actions": [...],
                "summary": "...",
                "confidence": 0.75,
                "reasoning": "..."
            }
        """
        
        prompt = self._build_perfect_prompt(
            market_context,
            candles_summary,
            position_context
        )
        
        try:
            response_text = self._call_llm(prompt)
            decision = self._parse_decision(response_text)
            self._log_decision_quality(decision)
            
            return decision
            
        except Exception as e:
            logger.error(f"[LLM] Error getting decision: {e}", exc_info=True)
            return {
                "actions": [],
                "summary": f"LLM error: {str(e)}",
                "confidence": 0.0,
                "reasoning": "Failed to get LLM decision"
            }
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM provider API"""
        if self.provider == "anthropic":
            return self._call_anthropic(prompt)
        else:
            return self._call_openai(prompt)
    
    def _call_anthropic(self, prompt: str) -> str:
        """Call Claude API"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"[LLM][ANTHROPIC] API call failed: {e}")
            raise
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"[LLM][OPENAI] API call failed: {e}")
            raise
    
    def _build_perfect_prompt(
        self,
        market_context: Dict,
        candles_summary: str,
        position_context: Optional[Dict]
    ) -> str:
        """
        Build PERFECT prompt with ZERO hard limits
        Philosophy: EDUCATE, don't CONSTRAIN
        """
        
        position_str = json.dumps(position_context, indent=2) if position_context else "No position"
        
        return f"""You are an elite autonomous cryptocurrency trader operating on Hyperliquid.

You have COMPLETE AUTONOMY. Every decision is yours:
• Position sizing (any amount that makes sense for the setup)
• Leverage selection (any leverage appropriate for your conviction)
• Entry timing (trade now, wait, or skip entirely)
• Risk management (stops, targets, position management)
• Trade frequency (quality over quantity - trade when YOU see opportunity)

═══════════════════════════════════════════════════════════════════════════
🎓 LEARNING FROM THE BEST: DECISION QUALITY EXAMPLES
═══════════════════════════════════════════════════════════════════════════

Study these examples to understand what makes an EXCELLENT vs POOR decision.
You're free to make your own choices, but learn from what works:

━━━ EXCELLENT DECISIONS (What top traders do) ━━━

✅ Example 1: SPECIFIC DATA + CLEAR REASONING
"LONG BTC: EMA 9 ($88,450) crossed above EMA 26 ($88,320) on 15m chart. 
Volume confirmation at 1.8x average. 1h trend also bullish. RSI 52 showing 
neutral→bullish momentum shift. Entry $88,440, stop $88,100 (-0.38%), 
target $89,200 (+0.86%). Risk/reward 2.26:1."
Confidence: 0.78

WHY THIS WORKS: Trader cited exact prices, multiple timeframes, specific 
indicators with values. Clear entry/exit plan. Anyone reading this understands 
the complete thesis.

✅ Example 2: RECOGNIZING MEAN REVERSION
"Scalp LONG BTC: Price at $87,950, which is 2.1% below EMA 50 ($89,800). 
RSI 28 (oversold territory), Stochastic 15/25 showing oversold crossover. 
Taking small position 0.0003 BTC for mean reversion bounce toward $88,500. 
Tight stop $87,750 (-0.23%)."
Confidence: 0.65

WHY THIS WORKS: Clear mean reversion setup with numerical proof. Sized 
appropriately small for a scalp. Specific entry, stop, and target.

✅ Example 3: BEARISH DIVERGENCE SPOTTED
"SHORT BTC: 1h chart showing bearish divergence - price made higher high 
at $89,200 but RSI made lower high (68→64). 15m EMA 9 crossed below EMA 26. 
Volume declining to 0.6x average indicates weak rally. Entry $88,980, 
stop $89,350 (-0.42%), target $88,200 (-0.88%)."
Confidence: 0.72

WHY THIS WORKS: Specific divergence with numbers, volume context supports 
thesis, multi-timeframe confirmation.

✅ Example 4: INTELLIGENT WAITING
"NO TRADE: BTC consolidating in tight $88,200-$88,400 range (0.2% range). 
ADX at 18 indicates no trend strength. Volume 0.7x average. I'm waiting 
for breakout above $88,450 with volume >1.5x OR breakdown below $88,150. 
Sometimes the best trade is patience."
Confidence: N/A

WHY THIS WORKS: Recognized choppy market with specific measurements. 
Defined exact conditions for future entry. Patience is intelligence.

✅ Example 5: ADDING TO WINNER
"ADD to BTC LONG: Initial entry at $88,200 now +$0.40 profit (+0.45%). 
EMA 9 holding as support at $88,350 confirms trend. Adding 0.0003 BTC 
(total position: 0.0005→0.0008). Moving stop to entry $88,200 for risk-free 
trade to target $89,500."
Confidence: 0.68

WHY THIS WORKS: Clear position management. Letting winners run while 
protecting capital. Specific sizing and stop adjustment.

✅ Example 6: VOLUME BREAKOUT
"LONG BTC: Clean breakout above $88,600 resistance on 3.2x volume spike. 
This level tested 3x previously and held, now broken with strong conviction. 
Entry $88,650, stop below breakout at $88,550 (-0.11%), target previous 
high $89,800 (+1.29%). Exceptional risk/reward of 11.7:1."
Confidence: 0.82

WHY THIS WORKS: Volume validates breakout. Previous resistance tests add 
context. Exceptional R:R with tight stop.

✅ Example 7: TRAP RECOGNITION
"SHORT BTC: Liquidity sweep detected - price spiked to $89,150 (likely 
stopped out late longs), immediately rejected with -1.2% red candle on 
2.1x volume. Classic bull trap. Entry $88,950, stop $89,200 (-0.28%), 
target $88,200 (-0.84%)."
Confidence: 0.75

WHY THIS WORKS: Recognizes market structure manipulation. Volume confirms 
rejection. Quick reaction to trap setup.


━━━ POOR DECISIONS (Common mistakes to avoid) ━━━

❌ Example 1: VAGUE + NO SUPPORTING DATA
"Entering LONG position on BTC due to bullish momentum and strong signals."
Confidence: 0.65

WHY THIS FAILS: "Bullish momentum" without data is meaningless. "Strong signals" 
doesn't specify what signals. No entry, stop, or target prices.

❌ Example 2: UNCERTAIN LANGUAGE
"Considering a SHORT on BTC. Market structure appears bearish with negative 
sentiment developing. Looking for entry opportunity."
Confidence: 0.60

WHY THIS FAILS: "Considering" = indecisive. "Appears" = uncertain. No specific 
data. What entry? What stop?

❌ Example 3: NO SPECIFICITY
"BTC looking good for LONG. Chart shows bullish trend. Will enter with tight stop."
Confidence: 0.65

WHY THIS FAILS: "Looking good" is subjective. "Tight stop" - how tight? $50? $500? 
No actual plan.

❌ Example 4: NOISE TRADING (FLIP-FLOPPING)
10:42: "SHORT BTC on bearish breakdown."
10:44: "LONG BTC on oversold bounce."
Confidence: 0.55 / 0.60

WHY THIS FAILS: Opposite directions 2 minutes apart means reacting to noise, 
not structure. Overtrading kills accounts.

❌ Example 5: OVERCONFIDENT WITHOUT PROOF
"STRONG BTC LONG OPPORTUNITY! Multiple bullish indicators perfectly aligned! 
Very high conviction trade!"
Confidence: 0.88

WHY THIS FAILS: Extremely high confidence (0.88) with ZERO specific data cited. 
Feeling certain doesn't make you right.


═══════════════════════════════════════════════════════════════════════════
💡 WHAT MAKES DECISIONS EXCELLENT
═══════════════════════════════════════════════════════════════════════════

Top traders typically:

📊 CITE SPECIFIC DATA
Instead of: "bullish momentum"
They say: "RSI at 52, rising from 45, showing strengthening momentum"

Instead of: "strong support"  
They say: "Support at $88,100, tested 4x in past week, holding each time"

💭 SHOW THEIR REASONING
Bad: "Taking this trade because it looks good"
Good: "Taking this trade because: (1) EMA cross on 15m, (2) 1h trend confirms, 
(3) volume spike validates, (4) R:R is 3:1, (5) stop below structure"

🎯 DEFINE CLEAR LEVELS
Vague: "Will set a tight stop"
Clear: "Stop at $88,100 (-0.38% from entry at $88,440)"

⏰ USE MULTIPLE TIMEFRAMES
Single timeframe: "5m shows bullish candle"
Multi-timeframe: "5m bullish candle aligns with 15m uptrend and 1h support zone"

🎲 CALIBRATE CONFIDENCE HONESTLY
Most traders use confidence like this:
• 0.30-0.45 = Very uncertain, conflicting signals, might skip
• 0.50-0.60 = Decent setup, some confirmation
• 0.65-0.75 = Strong setup, good confluence
• 0.80-0.90 = Exceptional setup, everything aligns
• 0.95+ = Extremely rare, only for obvious no-brainer setups

Notice: They use the FULL range based on actual conviction, not always 0.60-0.65.

🧘 PRACTICE PATIENCE
"Not trading" when conditions are unclear is a sign of intelligence, not weakness.
Choppy markets (ADX <20), tight ranges, low volume - sometimes best to wait.


═══════════════════════════════════════════════════════════════════════════
🧠 YOUR DECISION-MAKING FRAMEWORK (SUGGESTIONS, NOT RULES)
═══════════════════════════════════════════════════════════════════════════

Consider asking yourself:

BEFORE THE TRADE:
• What specific data supports this trade? (Can I cite exact numbers?)
• Does this work across multiple timeframes? (5m, 15m, 1h all agree?)
• What's my exact entry price?
• Where's my stop? (Based on structure, not arbitrary %)
• Where's my target? (Based on resistance/support, not arbitrary R:R)
• What's my conviction level? (Honest confidence 0-1.0)
• Am I reacting to noise or signal? (Last 2 minutes vs last 2 hours?)

IF UNCERTAIN:
• Can I articulate WHY I'm uncertain? (Conflicting timeframes? Low volume?)
• Should I wait for more confirmation? (Breakout with volume? Clear trend?)
• Is skipping this trade the smarter choice? (Patience often pays better than forcing trades)

POSITION SIZING WISDOM:
• Higher conviction = can size larger (within your risk tolerance)
• Lower conviction = size smaller or skip
• Uncertain market conditions = reduce size or stay flat

NOTE: These are thought frameworks professional traders use. You're free to 
develop your own approach - this is just sharing what tends to work.


═══════════════════════════════════════════════════════════════════════════
📊 CURRENT MARKET CONTEXT
═══════════════════════════════════════════════════════════════════════════

{json.dumps(market_context, indent=2)}

MULTI-TIMEFRAME CANDLE ANALYSIS:
{candles_summary}

CURRENT POSITION:
{position_str}


═══════════════════════════════════════════════════════════════════════════
🎯 YOUR DECISION
═══════════════════════════════════════════════════════════════════════════

Respond with valid JSON only:

{{
  "actions": [
    {{
      "type": "PLACE_ORDER",
      "symbol": "BTC",
      "side": "LONG",
      "size": 0.0005,
      "orderType": "MARKET",
      "leverage": 40
    }}
  ],
  "summary": "LONG BTC: EMA 9 ($88,450) crossed EMA 26 ($88,320), RSI 52, volume 1.8x avg. Entry $88,440, stop $88,100, target $89,200.",
  "confidence": 0.78,
  "reasoning": "15m EMA cross confirmed by 1h uptrend. Volume spike validates breakout. Stop below structure at $88,100. Target at resistance $89,200. Risk/reward 2.26:1."
}}

Remember:
• You decide EVERYTHING (size, leverage, timing, stops, targets)
• Cite specific data when you have it (but you're not forced to)
• Use any confidence value that reflects your true conviction
• Not trading is a valid decision when conditions are unclear
• Quality decisions > quantity of trades

Trade with intelligence and conviction. You're in complete control.

Your decision:"""
    
    def _parse_decision(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into decision dictionary"""
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or (not line.startswith("```")):
                        json_lines.append(line)
                cleaned = "\n".join(json_lines).strip()
            
            decision = json.loads(cleaned)
            
            if "actions" not in decision:
                decision["actions"] = []
            if "summary" not in decision:
                decision["summary"] = "No summary provided"
            if "confidence" not in decision:
                decision["confidence"] = 0.5
            if "reasoning" not in decision:
                decision["reasoning"] = "No reasoning provided"
            
            return decision
            
        except json.JSONDecodeError as e:
            logger.error(f"[LLM] JSON parse error: {e}")
            logger.error(f"[LLM] Response: {response[:300]}")
            
            return {
                "actions": [],
                "summary": "Failed to parse LLM response",
                "confidence": 0.0,
                "reasoning": f"JSON decode error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"[LLM] Parse error: {e}")
            return {
                "actions": [],
                "summary": f"Error: {str(e)}",
                "confidence": 0.0,
                "reasoning": "Unexpected error"
            }
    
    def _log_decision_quality(self, decision: Dict):
        """Log decision quality metrics (informational only)"""
        summary = decision.get("summary", "")
        confidence = decision.get("confidence", 0.0)
        
        has_dollar_sign = "$" in summary
        has_numbers = any(char.isdigit() for char in summary)
        has_percent = "%" in summary
        
        # Informational quality estimate (not enforced)
        score = 5.0
        if has_numbers: score += 1.5
        if has_dollar_sign: score += 1.0
        if has_percent: score += 1.0
        
        # Using non-default confidence
        if confidence < 0.55 or confidence > 0.70:
            score += 1.0
        
        quality = "GOOD ✅" if score >= 8.0 else "MEDIOCRE 🟡" if score >= 6.0 else "BASIC ⚪"
        
        logger.info(f"[LLM] Decision quality: {quality} (estimated {score:.1f}/10)")
        logger.info(f"[LLM]   Data cited: {'✓' if has_numbers else '○'}")
        logger.info(f"[LLM]   Prices cited: {'✓' if has_dollar_sign else '○'}")
        logger.info(f"[LLM]   Confidence: {confidence:.2f}")


_llm_client_instance = None

def get_llm_client() -> LLMClient:
    """Get or create singleton LLM client instance"""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance
