# Chapter 04: Mathematical Tools
## The Geometry and Statistics of Profit

> *"Mathematics is the language in which God has written the universe."* — Galileo Galilei

While Price Action and SMC deal with subjective structure, Mathematical Tools deal with cold statistics. They filter our decisions. The Graph Inspector uses these to measure the market's "temperature" and "geometry".

---

## 1. Fibonacci: The Golden Ruler
Leonardo Fibonacci discovered a sequence (1, 1, 2, 3, 5, 8...) describing proportions found in nature. The financial market respects these proportions scarily well.

### Retracement (Where to Enter)
After an impulse, price tends to retrace.
*   **0.382:** Shallow correction. Strong trend.
*   **0.50:** Halfway. Psychological.
*   **0.618 (Golden Ratio):** The most famous support point.
*   **0.786:** The "Last Frontier" and part of OTE. If crossed, trend likely reversed.

*   **Bot Tip:** Inspector doesn't buy 0.618 blindly. It waits for price to hit 0.618 **AND** show a reversal candle **OR** hit an Order Block. Confluence creates profit.

### Extension (Where to Exit)
*   **Target 1 (1.0):** Projected move (AB = CD). Safe partial.
*   **Target 2 (1.618):** Classic euphoria target. Great for final exit.

---

## 2. RSI (Relative Strength Index)
Measures speed of price change.

*   **Overbought (>70):** Price rose too fast. "Expensive".
*   **Oversold (<30):** Price fell too fast. "Cheap".

### The Secret: Divergences
Basic reading breaks in strong trends. The real gold is **Divergence**:
*   **Bearish Divergence:** Price makes Higher High, RSI makes Lower High. Buyers losing power. Reversal imminent.
*   **Bullish Divergence:** Price makes Lower Low, RSI makes Higher Low. Sellers losing power.

---

## 3. Stochastic RSI
A faster RSI. Great for exact timing. Inspector uses K/D crossover in extreme zones as a final "trigger pull".

---

## 4. ADX (Average Directional Index)
Most traders lose money trying to trade trends in sideways markets. ADX prevents this.
*   **ADX < 20:** Ranging market. Trend indicators will fail. Use "buy low, sell high" range strategies.
*   **ADX > 25:** Strong trend starting.
*   **ADX > 50:** Very strong/exhaustion.

The Bot checks ADX. If low, it knows breakouts often fail (traps). If high, it trades with the flow.

---

## 5. VWAP (Volume Weighted Average Price)
The "Institutional Average". Unlike simple moving averages, VWAP weighs Volume.
*   VWAP acts as strong dynamic support/resistance intraday. Funds love to defend positions at average daily VWAP.
*   **Standard Deviation:** Bot calculates bands. If price deviates too far (2 SD), statistically it "must" return to the mean. Mean Reversion.

---

## Chapter Summary
Indicators don't predict the future. They show the processed past.
*   **Fibonacci** gives us "WHERE" (Map).
*   **SMC/Price Action** gives us "WHEN" (Trigger).
*   **RSI/ADX/VWAP** gives us "HOW" (Context).

The Graph Inspector combines these three layers for a robust probabilistic decision.
