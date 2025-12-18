'use client';

import { useState, useEffect } from 'react';

interface FearGreedData {
    value: number;
    classification: string;
    timestamp: string;
}

export function MarketSentimentCard({ loading = false }: { loading?: boolean }) {
    const [data, setData] = useState<FearGreedData | null>(null);
    const [fetching, setFetching] = useState(true);

    useEffect(() => {
        const fetchFearGreed = async () => {
            try {
                // Use Alternative.me API for Fear & Greed Index
                const res = await fetch('https://api.alternative.me/fng/?limit=1');
                if (res.ok) {
                    const json = await res.json();
                    if (json.data && json.data[0]) {
                        setData({
                            value: parseInt(json.data[0].value),
                            classification: json.data[0].value_classification,
                            timestamp: json.data[0].timestamp
                        });
                    }
                }
            } catch (err) {
                // Use fallback mock data
                setData({
                    value: 45,
                    classification: 'Fear',
                    timestamp: new Date().toISOString()
                });
            }
            setFetching(false);
        };

        fetchFearGreed();
        const interval = setInterval(fetchFearGreed, 60000); // Update every minute
        return () => clearInterval(interval);
    }, []);

    if (loading || fetching) {
        return (
            <div className="card">
                <div className="skeleton h-6 w-32 mb-4" />
                <div className="skeleton h-20 w-full" />
            </div>
        );
    }

    const value = data?.value || 50;
    const classification = data?.classification || 'Neutral';

    // Determine color based on value
    const getColor = (val: number) => {
        if (val <= 20) return 'var(--accent-red)';
        if (val <= 40) return '#FF8C42';
        if (val <= 60) return 'var(--accent-yellow)';
        if (val <= 80) return '#A8E063';
        return 'var(--accent-green)';
    };

    const color = getColor(value);

    // Calculate gradient position
    const gradientStyle = {
        background: `linear-gradient(90deg, 
            #FF4444 0%, 
            #FF8C42 25%, 
            #FFD93D 50%, 
            #A8E063 75%, 
            #7CFF6B 100%)`,
        height: '8px',
        position: 'relative' as const
    };

    return (
        <div className="card">
            <div className="card-header">
                <span className="card-title">Market Sentiment</span>
                <span className="text-xs text-[var(--text-muted)]">Fear & Greed Index</span>
            </div>

            {/* Main Value Display */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <div className="text-4xl font-bold" style={{ color }}>
                        {value}
                    </div>
                    <div className="text-sm font-medium mt-1" style={{ color }}>
                        {classification}
                    </div>
                </div>

                {/* Gauge Indicator */}
                <div className="w-16 h-16 relative">
                    <svg viewBox="0 0 36 36" className="w-full h-full">
                        {/* Background arc */}
                        <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke="var(--bg-tertiary)"
                            strokeWidth="3"
                            strokeLinecap="round"
                        />
                        {/* Foreground arc */}
                        <path
                            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            fill="none"
                            stroke={color}
                            strokeWidth="3"
                            strokeLinecap="round"
                            strokeDasharray={`${value}, 100`}
                            style={{
                                filter: `drop-shadow(0 0 4px ${color})`
                            }}
                        />
                    </svg>
                </div>
            </div>

            {/* Gradient Bar */}
            <div style={gradientStyle}>
                <div
                    className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 shadow-lg"
                    style={{
                        left: `${value}%`,
                        borderColor: color,
                        transform: 'translate(-50%, -50%)',
                        boxShadow: `0 0 8px ${color}`
                    }}
                />
            </div>

            {/* Labels */}
            <div className="flex justify-between mt-2 text-xs text-[var(--text-muted)]">
                <span>Extreme Fear</span>
                <span>Neutral</span>
                <span>Extreme Greed</span>
            </div>
        </div>
    );
}
