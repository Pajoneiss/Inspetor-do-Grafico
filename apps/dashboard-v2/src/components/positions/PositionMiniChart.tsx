'use client';

import { useEffect, useState } from 'react';

interface MiniChartProps {
    symbol: string;
    entryPrice: number;
    markPrice: number;
    side: 'LONG' | 'SHORT';
    roe: number;
}

export default function PositionMiniChart({ symbol, entryPrice, markPrice, side, roe }: MiniChartProps) {
    const [priceHistory, setPriceHistory] = useState<number[]>([]);

    useEffect(() => {
        const generateHistory = () => {
            const points = 40;
            const history: number[] = [];
            const priceRange = Math.abs(markPrice - entryPrice);
            const volatility = Math.max(priceRange * 0.2, markPrice * 0.003);

            for (let i = 0; i < points; i++) {
                const progress = i / (points - 1);
                const basePrice = entryPrice + (markPrice - entryPrice) * progress;
                const noise = (Math.random() - 0.5) * volatility;
                history.push(basePrice + noise);
            }

            history[points - 1] = markPrice;
            return history;
        };

        setPriceHistory(generateHistory());

        const interval = setInterval(() => {
            setPriceHistory(prev => {
                if (prev.length === 0) return prev;
                const newHistory = [...prev.slice(1)];
                const variation = markPrice * (Math.random() - 0.5) * 0.002;
                newHistory.push(markPrice + variation);
                return newHistory;
            });
        }, 8000);

        return () => clearInterval(interval);
    }, [entryPrice, markPrice]);

    if (priceHistory.length === 0) return null;

    const maxPrice = Math.max(...priceHistory, entryPrice);
    const minPrice = Math.min(...priceHistory, entryPrice);
    const priceRange = maxPrice - minPrice || 1;

    const paddedMax = maxPrice + priceRange * 0.1;
    const paddedMin = minPrice - priceRange * 0.1;
    const paddedRange = paddedMax - paddedMin;

    const priceToY = (price: number) => ((paddedMax - price) / paddedRange) * 100;
    const entryY = priceToY(entryPrice);

    const points = priceHistory.map((price, index) => {
        const x = (index / (priceHistory.length - 1)) * 100;
        const y = priceToY(price);
        return `${x},${y}`;
    }).join(' ');

    const isProfit = roe >= 0;
    const lineColor = isProfit ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)';
    const fillOpacity = Math.min(Math.abs(roe) / 100, 0.3);

    return (
        <div className="relative w-full h-16 bg-gradient-to-br from-[var(--bg-secondary)] to-[var(--bg-primary)] rounded-lg overflow-hidden">
            <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                <defs>
                    <linearGradient id={`grad-${symbol}`} x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style={{ stopColor: lineColor, stopOpacity: fillOpacity }} />
                        <stop offset="100%" style={{ stopColor: lineColor, stopOpacity: 0 }} />
                    </linearGradient>
                </defs>

                {/* Area fill */}
                <polygon
                    points={`0,100 ${points} 100,100`}
                    fill={`url(#grad-${symbol})`}
                />

                {/* Entry line */}
                <line
                    x1="0"
                    y1={entryY}
                    x2="100"
                    y2={entryY}
                    stroke="rgba(255,255,255,0.2)"
                    strokeWidth="0.5"
                    strokeDasharray="2,2"
                />

                {/* Price line */}
                <polyline
                    points={points}
                    fill="none"
                    stroke={lineColor}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{
                        filter: `drop-shadow(0 0 4px ${lineColor})`
                    }}
                />

                {/* Current marker */}
                <circle
                    cx="98"
                    cy={priceToY(markPrice)}
                    r="2"
                    fill={lineColor}
                    className="animate-pulse"
                    style={{
                        filter: `drop-shadow(0 0 3px ${lineColor})`
                    }}
                />
            </svg>
        </div>
    );
}
