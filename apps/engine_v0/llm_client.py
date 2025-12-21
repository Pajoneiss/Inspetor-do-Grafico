"""
LLM Client v15.0 CLAUDE ONLY - No OpenAI Fallback
Claude is the brain, OpenAI is NOT used for trading decisions
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class LLMClient:
    """Claude-only LLM client - no OpenAI fallback for trading"""
    
    def __init__(self):
        self.provider = "anthropic"  # ALWAYS Claude
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
        """Get Claude model name"""
        model = os.getenv("AI_MODEL", "")
        if model:
            return model
        return "claude-sonnet-4-20250514"  # Default Claude model
    
    def _initialize_claude(self):
        """Initialize Claude client - CLAUDE ONLY, NO FALLBACK"""
        import anthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set! Claude is REQUIRED for trading.")
        
        if not api_key.startswith("sk-ant-"):
            print(f"[LLM] ⚠️  WARNING: ANTHROPIC_API_KEY doesn't start with 'sk-ant-'")
        
        # Simple initialization - just API key
        return anthropic.Anthropic(api_key=api_key)
    
    def is_ready(self) -> bool:
        """Check if Claude is ready to trade"""
        return self.client is not None
    
    def decide(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Main decision method - called by engine"""
        market_context = state.get("market_context", {})
        candles_summary = state.get("candles_summary", "")
        position_context = state.get("position_context")
        
        return self.get_trading_decision(market_context, candles_summary, position_context)
    
    def get_trading_decision(
        self,
        market_context: Dict[str, Any],
        candles_summary: str,
        position_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Get trading decision from LLM"""
        
        if not self.client:
            return {
                "actions": [],
                "summary": "LLM not available",
                "confidence": 0.0,
                "reasoning": "LLM client failed to initialize"
            }
        
        prompt = self._build_prompt(market_context, candles_summary, position_context)
        
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
        """Call LLM API"""
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
    
    def _build_prompt(self, market_context: Dict, candles_summary: str, position_context: Optional[Dict]) -> str:
        """Build v14.3 prompt - ZERO HARD LIMITS"""
        
        position_str = json.dumps(position_context, indent=2) if position_context else "No position"
        
        return f"""You are an elite autonomous cryptocurrency trader on Hyperliquid.

You have COMPLETE AUTONOMY over ALL decisions:
• Position sizing (any amount appropriate for the setup)
• Leverage (any leverage fitting your conviction)
• Entry timing (trade now, wait, or skip)
• Risk management (stops, targets, position management)
• Trade frequency (quality over quantity)

═══════════════════════════════════════════════════════════════════════════
🎓 LEARNING FROM THE BEST: DECISION QUALITY EXAMPLES
═══════════════════════════════════════════════════════════════════════════

Study these to understand EXCELLENT vs POOR decisions:

━━━ EXCELLENT DECISIONS ━━━

✅ "LONG BTC: EMA 9 ($88,450) crossed EMA 26 ($88,320) on 15m chart. Volume 1.8x average confirms. 1h trend bullish. RSI 52 (neutral→bullish). Entry $88,440, stop $88,100 (-0.38%), target $89,200 (+0.86%). R:R 2.26:1."
Confidence: 0.78

WHY WORKS: Specific prices, multiple timeframes, clear R:R

✅ "Scalp LONG BTC: Price $87,950 is 2.1% below EMA 50 ($89,800). RSI 28 (oversold), Stochastic 15/25 crossover. Small position 0.0003 BTC for bounce to $88,500. Stop $87,750 (-0.23%)."
Confidence: 0.65

WHY WORKS: Numerical proof of mean reversion, appropriate sizing

✅ "NO TRADE: BTC consolidating in $88,200-$88,400 (0.2% range). ADX 18 (no trend). Volume 0.7x avg. Waiting for breakout >$88,450 with volume >1.5x OR breakdown <$88,150."
Confidence: N/A

WHY WORKS: Recognizes choppy conditions, specific breakout levels

━━━ POOR DECISIONS ━━━

❌ "Entering LONG on bullish momentum and strong signals."
Confidence: 0.65

WHY FAILS: No data, "bullish momentum" meaningless

❌ "Considering SHORT. Market appears bearish."
Confidence: 0.60

WHY FAILS: Indecisive ("considering"), vague ("appears")

═══════════════════════════════════════════════════════════════════════════
💡 WHAT MAKES EXCELLENT DECISIONS
═══════════════════════════════════════════════════════════════════════════

Top traders typically:

📊 CITE SPECIFIC DATA: "RSI 52, rising from 45" not "bullish momentum"
💭 SHOW REASONING: Explain WHY taking this trade
🎯 DEFINE LEVELS: "$88,100 stop" not "tight stop"
⏰ USE MULTI-TIMEFRAME: 5m + 15m + 1h confirmation
🎲 CALIBRATE CONFIDENCE: 0.30-0.45 (uncertain), 0.50-0.65 (decent), 0.70-0.85 (strong), 0.90+ (exceptional)
🧘 PRACTICE PATIENCE: Not trading unclear conditions is intelligence

═══════════════════════════════════════════════════════════════════════════
📊 CURRENT MARKET CONTEXT
═══════════════════════════════════════════════════════════════════════════

{json.dumps(market_context, indent=2)}

MULTI-TIMEFRAME CANDLES:
{candles_summary}

CURRENT POSITION:
{position_str}

═══════════════════════════════════════════════════════════════════════════
🎯 YOUR DECISION (JSON ONLY)
═══════════════════════════════════════════════════════════════════════════

Respond with valid JSON:

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
  "summary": "LONG BTC: EMA 9 ($88,450) crossed EMA 26 ($88,320), RSI 52, volume 1.8x. Entry $88,440, stop $88,100, target $89,200.",
  "confidence": 0.78,
  "reasoning": "15m EMA cross + 1h uptrend. Volume validates. Stop below structure. R:R 2.26:1."
}}

Remember:
• YOU decide everything (size, leverage, timing, stops, targets)
• Cite specific data when you have it
• Use any confidence value reflecting your true conviction
• Not trading is valid when conditions unclear
• Quality > quantity

Trade with intelligence. You're in complete control.

Your decision:"""
    
    def _parse_decision(self, response: str) -> Dict[str, Any]:
        """Parse JSON response"""
        try:
            cleaned = response.strip()
            
            # Remove markdown fences if present
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.startswith("```"):
                        in_block = not in_block
                        continue
                    if in_block or not line.startswith("```"):
                        json_lines.append(line)
                cleaned = "\n".join(json_lines).strip()
            
            decision = json.loads(cleaned)
            
            # Ensure required fields
            decision.setdefault("actions", [])
            decision.setdefault("summary", "No summary")
            decision.setdefault("confidence", 0.5)
            decision.setdefault("reasoning", "No reasoning")
            
            return decision
            
        except json.JSONDecodeError as e:
            logger.error(f"[LLM] JSON parse error: {e}")
            return {
                "actions": [],
                "summary": "Parse error",
                "confidence": 0.0,
                "reasoning": f"JSON error: {str(e)}"
            }
    
    def _log_quality(self, decision: Dict):
        """Log decision quality (informational)"""
        summary = decision.get("summary", "")
        confidence = decision.get("confidence") or 0.0  # Handle None
        
        has_numbers = any(c.isdigit() for c in summary)
        has_dollar = "$" in summary
        
        score = 5.0
        if has_numbers: score += 1.5
        if has_dollar: score += 1.0
        if confidence < 0.55 or confidence > 0.70: score += 1.0
        
        quality = "GOOD ✅" if score >= 8.0 else "MEDIOCRE 🟡" if score >= 6.0 else "BASIC ⚪"
        
        logger.info(f"[LLM] Quality: {quality} ({score:.1f}/10)")
        logger.info(f"[LLM]   Data: {'✓' if has_numbers else '○'}")
        logger.info(f"[LLM]   Prices: {'✓' if has_dollar else '○'}")
        logger.info(f"[LLM]   Confidence: {confidence:.2f}")


# Singleton
_instance = None

def get_llm_client():
    """Get singleton instance"""
    global _instance
    if _instance is None:
        _instance = LLMClient()
    return _instance
