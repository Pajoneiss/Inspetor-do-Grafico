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
        // Generate realistic price history based on current state
        const generateHistory = () => {
            const points = 30;
            const history: number[] = [];
            const priceRange = Math.abs(markPrice - entryPrice);
            const volatility = priceRange * 0.3;

            // Start from entry, move towards current mark
            for (let i = 0; i < points; i++) {
                const progress = i / (points - 1);
                // Interpolate between entry and mark with some noise
                const basePrice = entryPrice + (markPrice - entryPrice) * progress;
                const noise = (Math.random() - 0.5) * volatility;
                history.push(basePrice + noise);
            }

            // Ensure last point is current mark price
            history[points - 1] = markPrice;

            return history;
        };

        setPriceHistory(generateHistory());

        // Update every 10 seconds with slight variation
        const interval = setInterval(() => {
            setPriceHistory(prev => {
                const newHistory = [...prev.slice(1)];
                const lastPrice = prev[prev.length - 1];
                const variation = lastPrice * (Math.random() - 0.5) * 0.002; // 0.2% variation
                newHistory.push(markPrice + variation);
                return newHistory;
            });
        }, 10000);

        return () => clearInterval(interval);
    }, [entryPrice, markPrice]);

    if (priceHistory.length === 0) return null;

    const maxPrice = Math.max(...priceHistory, entryPrice);
    const minPrice = Math.min(...priceHistory, entryPrice);
    const priceRange = maxPrice - minPrice || 1;

    // Calculate positions
    const entryY = ((maxPrice - entryPrice) / priceRange) * 100;

    // Generate SVG path
    const points = priceHistory.map((price, index) => {
        const x = (index / (priceHistory.length - 1)) * 100;
        const y = ((maxPrice - price) / priceRange) * 100;
        return `${x},${y}`;
    }).join(' ');

    const isProfit = roe >= 0;
    const lineColor = isProfit ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)';
    const entryColor = side === 'LONG' ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)';

    return (
        <div className="relative w-full h-24 bg-[var(--bg-secondary)] rounded-lg p-2 overflow-hidden group">
            {/* Chart */}
            <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                {/* Area fill */}
                <defs>
                    <linearGradient id={`gradient-${symbol}`} x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style={{ stopColor: lineColor, stopOpacity: 0.3 }} />
                        <stop offset="100%" style={{ stopColor: lineColor, stopOpacity: 0 }} />
                    </linearGradient>
                </defs>

                {/* Area under line */}
                <polygon
                    points={`0,100 ${points} 100,100`}
                    fill={`url(#gradient-${symbol})`}
                />

                {/* Entry price line */}
                <line
                    x1="0"
                    y1={entryY}
                    x2="100"
                    y2={entryY}
                    stroke={entryColor}
                    strokeWidth="0.5"
                    strokeDasharray="2,2"
                    opacity="0.5"
                />

                {/* Price line */}
                <polyline
                    points={points}
                    fill="none"
                    stroke={lineColor}
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />

                {/* Entry marker */}
                <circle
                    cx="15"
                    cy={entryY}
                    r="1.5"
                    fill={entryColor}
                    opacity="0.8"
                />

                {/* Current price marker */}
                <circle
                    cx="95"
                    cy={((maxPrice - markPrice) / priceRange) * 100}
                    r="2"
                    fill={lineColor}
                    className="animate-pulse"
                />
            </svg>

            {/* Overlay labels on hover */}
            <div className="absolute inset-0 bg-[var(--bg-primary)] bg-opacity-95 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-1 text-xs">
                <div className="flex items-center gap-2">
                    <span className="text-[var(--text-muted)]">Entry:</span>
                    <span className="font-bold" style={{ color: entryColor }}>${entryPrice.toFixed(4)}</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-[var(--text-muted)]">Current:</span>
                    <span className="font-bold" style={{ color: lineColor }}>${markPrice.toFixed(4)}</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-[var(--text-muted)]">ROE:</span>
                    <span className="font-bold" style={{ color: lineColor }}>
                        {roe >= 0 ? '+' : ''}{roe.toFixed(2)}%
                    </span>
                </div>
            </div>
        </div>
    );
}
