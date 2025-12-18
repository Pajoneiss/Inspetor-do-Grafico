'use client';

import { useEffect, useState } from 'react';

interface Candle {
    time: number;
    open: number;
    high: number;
    low: number;
    close: number;
}

interface CandlestickChartProps {
    symbol: string;
    entryPrice: number;
    markPrice: number;
    side: 'LONG' | 'SHORT';
    roe: number;
}

export default function CandlestickChart({ symbol, entryPrice, markPrice, side, roe }: CandlestickChartProps) {
    const [candles, setCandles] = useState<Candle[]>([]);

    useEffect(() => {
        // Generate realistic candles based on entry and current price
        const generateCandles = () => {
            const numCandles = 24; // 24 candles for cleaner visualization
            const newCandles: Candle[] = [];

            const priceRange = Math.abs(markPrice - entryPrice);
            const volatility = Math.max(priceRange * 0.15, markPrice * 0.005); // Min 0.5% volatility

            let currentPrice = entryPrice;

            for (let i = 0; i < numCandles; i++) {
                const progress = i / (numCandles - 1);

                // Trend towards mark price with some noise
                const targetPrice = entryPrice + (markPrice - entryPrice) * progress;
                const trendInfluence = 0.3;
                currentPrice = currentPrice * (1 - trendInfluence) + targetPrice * trendInfluence;

                // Generate OHLC with realistic relationships
                const candleVolatility = volatility * (0.5 + Math.random() * 0.5);
                const open = currentPrice + (Math.random() - 0.5) * candleVolatility;
                const close = currentPrice + (Math.random() - 0.5) * candleVolatility;

                const bodyRange = Math.abs(close - open);
                const wickRange = bodyRange * (1 + Math.random() * 2); // Wicks can be up to 3x body

                const high = Math.max(open, close) + wickRange * Math.random();
                const low = Math.min(open, close) - wickRange * Math.random();

                newCandles.push({
                    time: Date.now() - (numCandles - i) * 3600000, // Hourly candles
                    open,
                    high,
                    low,
                    close
                });

                currentPrice = close;
            }

            // Ensure last candle close is near current mark price
            const lastCandle = newCandles[newCandles.length - 1];
            const adjustment = markPrice - lastCandle.close;
            lastCandle.close = markPrice;
            lastCandle.high = Math.max(lastCandle.high, markPrice);
            lastCandle.low = Math.min(lastCandle.low, markPrice);

            return newCandles;
        };

        setCandles(generateCandles());

        // Update last candle periodically
        const interval = setInterval(() => {
            setCandles(prev => {
                if (prev.length === 0) return prev;
                const updated = [...prev];
                const last = { ...updated[updated.length - 1] };

                // Small variation around mark price
                const variation = markPrice * (Math.random() - 0.5) * 0.003; // ±0.3%
                last.close = markPrice + variation;
                last.high = Math.max(last.high, last.close);
                last.low = Math.min(last.low, last.close);

                updated[updated.length - 1] = last;
                return updated;
            });
        }, 10000);

        return () => clearInterval(interval);
    }, [entryPrice, markPrice]);

    if (candles.length === 0) return null;

    // Calculate bounds
    const allPrices = candles.flatMap(c => [c.high, c.low, entryPrice]);
    const maxPrice = Math.max(...allPrices);
    const minPrice = Math.min(...allPrices);
    const priceRange = maxPrice - minPrice || 1;

    // Add 5% padding
    const paddedMax = maxPrice + priceRange * 0.05;
    const paddedMin = minPrice - priceRange * 0.05;
    const paddedRange = paddedMax - paddedMin;

    const priceToY = (price: number) => ((paddedMax - price) / paddedRange) * 100;
    const entryY = priceToY(entryPrice);

    const isProfit = roe >= 0;
    const entryColor = side === 'LONG' ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)';

    return (
        <div className="relative w-full h-32 bg-[var(--bg-secondary)] p-2 overflow-hidden group">
            {/* Legend */}
            <div className="absolute top-2 left-2 flex items-center gap-3 text-xs z-10">
                <div className="flex items-center gap-1">
                    <div className="w-2 h-2" style={{ backgroundColor: entryColor, opacity: 0.6 }}></div>
                    <span className="text-[var(--text-muted)]">Entry ${entryPrice.toFixed(2)}</span>
                </div>
                <div className={`flex items-center gap-1 ${isProfit ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'}`}>
                    <span className="font-bold">{isProfit ? '+' : ''}{roe.toFixed(2)}%</span>
                </div>
            </div>

            {/* Chart */}
            <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                {/* Entry price line */}
                <line
                    x1="0"
                    y1={entryY}
                    x2="100"
                    y2={entryY}
                    stroke={entryColor}
                    strokeWidth="0.3"
                    strokeDasharray="1,1"
                    opacity="0.5"
                />

                {/* Candles */}
                {candles.map((candle, i) => {
                    const x = (i / (candles.length - 1)) * 100;
                    const candleWidth = Math.max(100 / candles.length * 0.7, 0.5);

                    const openY = priceToY(candle.open);
                    const closeY = priceToY(candle.close);
                    const highY = priceToY(candle.high);
                    const lowY = priceToY(candle.low);

                    const isBullish = candle.close >= candle.open;
                    const bodyTop = Math.min(openY, closeY);
                    const bodyHeight = Math.abs(closeY - openY) || 0.2;

                    const color = isBullish ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)';

                    return (
                        <g key={i}>
                            {/* Wick */}
                            <line
                                x1={x}
                                y1={highY}
                                x2={x}
                                y2={lowY}
                                stroke={color}
                                strokeWidth="0.2"
                                opacity="0.8"
                            />

                            {/* Body */}
                            <rect
                                x={x - candleWidth / 2}
                                y={bodyTop}
                                width={candleWidth}
                                height={bodyHeight}
                                fill={isBullish ? color : 'transparent'}
                                stroke={color}
                                strokeWidth="0.2"
                                opacity={isBullish ? 0.9 : 0.8}
                            />
                        </g>
                    );
                })}

                {/* Current price marker */}
                <circle
                    cx="95"
                    cy={priceToY(markPrice)}
                    r="1"
                    fill={isProfit ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)'}
                    className="animate-pulse"
                />
            </svg>

            {/* Hover overlay with details */}
            <div className="absolute inset-0 bg-[var(--bg-primary)] bg-opacity-95 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-1 text-xs">
                <div className="text-[var(--text-muted)] text-center mb-1">{symbol} • 24H Chart</div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                    <span className="text-[var(--text-muted)] text-right">Entry:</span>
                    <span className="font-bold" style={{ color: entryColor }}>${entryPrice.toFixed(4)}</span>

                    <span className="text-[var(--text-muted)] text-right">Current:</span>
                    <span className="font-bold" style={{ color: isProfit ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)' }}>
                        ${markPrice.toFixed(4)}
                    </span>

                    <span className="text-[var(--text-muted)] text-right">Change:</span>
                    <span className="font-bold" style={{ color: isProfit ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)' }}>
                        {isProfit ? '+' : ''}{((markPrice - entryPrice) / entryPrice * 100).toFixed(2)}%
                    </span>

                    <span className="text-[var(--text-muted)] text-right">ROE:</span>
                    <span className="font-bold" style={{ color: isProfit ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)' }}>
                        {isProfit ? '+' : ''}{roe.toFixed(2)}%
                    </span>
                </div>
            </div>
        </div>
    );
}
