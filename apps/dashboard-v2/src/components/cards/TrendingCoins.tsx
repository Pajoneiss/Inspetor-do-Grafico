"use client";

import { useEffect, useState } from "react";

interface TrendingCoin {
    name: string;
    symbol: string;
    price: number;
    volume_24h: number;
    percent_change_24h: number;
    market_cap: number;
}

export default function TrendingCoins() {
    const [coins, setCoins] = useState<TrendingCoin[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch("/api/cmc/trending");
                const json = await res.json();
                if (json.ok) {
                    setCoins(json.data);
                }
            } catch (error) {
                console.error("Failed to fetch trending coins:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 120000); // Update every 2 minutes
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="glass-card glass-card-hover p-10 animate-pulse">
                <div className="h-6 bg-white/10 rounded w-1/3 mb-4"></div>
                <div className="space-y-2">
                    {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-12 bg-white/10"></div>
                    ))}
                </div>
            </div>
        );
    }

    const formatPrice = (price: number) => {
        if (price >= 1) return `$${price.toFixed(2)}`;
        if (price >= 0.01) return `$${price.toFixed(4)}`;
        return `$${price.toFixed(6)}`;
    };

    const formatVolume = (vol: number) => {
        if (vol >= 1e9) return `$${(vol / 1e9).toFixed(2)}B`;
        if (vol >= 1e6) return `$${(vol / 1e6).toFixed(2)}M`;
        return `$${(vol / 1e3).toFixed(2)}K`;
    };

    return (
        <div className="glass-card glass-card-hover p-10 animate-slide-up">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider">
                    🔥 Trending Coins
                </h3>
                <span className="text-xs text-white/40">Top 10</span>
            </div>

            {/* Coins List */}
            {coins.length === 0 ? (
                <div className="text-center py-8 text-white/40">
                    <div className="text-4xl mb-2">📊</div>
                    <div className="text-sm">No trending data available</div>
                    <div className="text-xs mt-1">API may be rate limited or unavailable</div>
                </div>
            ) : (
                <div className="space-y-3">
                    {coins.slice(0, 10).map((coin, index) => {
                        const isPositive = coin.percent_change_24h >= 0;
                        return (
                            <div
                                key={coin.symbol}
                                className="flex items-center justify-between p-4 bg-white/5 hover:bg-white/10 transition-all duration-200 group"
                            >
                                {/* Left: Rank + Name */}
                                <div className="flex items-center gap-3 flex-1">
                                    <div className="w-6 h-6 bg-gradient-info flex items-center justify-center text-xs font-bold text-white">
                                        {index + 1}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="font-semibold text-white text-sm truncate">
                                            {coin.symbol}
                                        </div>
                                        <div className="text-xs text-white/40 truncate">{coin.name}</div>
                                    </div>
                                </div>

                                {/* Right: Price + Change */}
                                <div className="text-right">
                                    <div className="data-value data-value-sm text-white/90">
                                        {formatPrice(coin.price)}
                                    </div>
                                    <div
                                        className={`text-xs font-mono ${isPositive ? "text-profit" : "text-loss"
                                            }`}
                                    >
                                        {isPositive ? "+" : ""}
                                        {coin.percent_change_24h.toFixed(2)}%
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
