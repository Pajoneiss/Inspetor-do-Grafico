# Chapter 02: Advanced Price Action
## Reading the Pure Language of the Market

> *"Price is the only thing that pays."*

Price Action is the art of reading the market without indicators polluting the screen. It's understanding the story Candlesticks are telling in real-time.

**The Graph Inspector** is, at its core, a Price Action bot. It looks at *Highs*, *Lows*, *Opens*, and *Closes* before looking at any moving average.

---

## 1. Candlesticks: The Real-Time Battle
Each candle summarizes a battle between Buyers (Bulls) and Sellers (Bears).

### Reversal Patterns (Detected by Bot)

#### The Hammer (Pinbar)
*   **Visual:** Small body at top, long lower wick (at least 2x body size).
*   **Story:** Sellers pushed price down hard, but buyers rejected the drop and pushed it back up before close.
*   **Meaning:** Strong bullish signal, especially at support.

#### Engulfing
*   **Visual:** A small candle (e.g., red) is completely "swallowed" by the next candle (e.g., giant green).
*   **Meaning:** Immediate trend reversal. Bullish Engulfing at a bottom is a favorite Inspector signal.

#### Doji
*   **Visual:** Open and close are nearly equal. Looks like a cross.
*   **Meaning:** Indecision. Often precedes a big move.

#### Morning Star
*   **Visual:** 3 Candles. (1) Strong Red -> (2) Small indecision -> (3) Strong Green closing inside the first red.
*   **Meaning:** Reversal confirmed.

---

## 2. Classic Chart Patterns
Human behavior repeats, forming shapes that anticipate moves.

### Continuation Patterns
*   **Flag:** A strong pole followed by a small sideways channel against the trend. Breakout follows the pole direction.

### Reversal Patterns
*   **Head and Shoulders (H&S):** High, Higher High (Head), Lower High (Shoulder). Shows buying force failed to make a new high. Drop imminent.
*   **Double Bottom (W) / Top (M):** Price hits the same level twice and rejects.

---

## 3. Pivot Points & Support/Resistance
The market has memory.

### Pivot Points (Auto-Calculated by Bot)
Mathematical levels based on previous day.
*   **Central Pivot (P):** Balance point. Above is Bullish, below is Bearish.
*   **Supports (S1, S2, S3):** Where buyers appear.
*   **Resistances (R1, R2, R3):** Where sellers appear.

### How the Inspector Applies Price Action
Unlike humans who might "imagine" a pattern, the Bot uses rigid geometry rules.
1.  Calculates body/wick size in exact pixels/cents.
2.  A Hammer is only a Hammer if the wick is mathematically > 2x body.
3.  Combines with location. A Hammer at S1 Pivot is a **High Probability** signal.

This is the power of automation: **Surgical Precision without Emotional Bias.**
