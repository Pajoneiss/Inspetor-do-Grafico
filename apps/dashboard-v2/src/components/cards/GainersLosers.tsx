"use client";

import { useEffect, useState } from "react";

interface Coin {
    name: string;
    symbol: string;
    price: number;
    percent_change_24h: number;
}

interface GainersLosersData {
    gainers: Coin[];
    losers: Coin[];
}

export default function GainersLosers() {
    const [data, setData] = useState<GainersLosersData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch("/api/cmc/gainers-losers");
                const json = await res.json();
                if (json.ok) {
                    setData(json.data);
                }
            } catch (error) {
                console.error("Failed to fetch gainers/losers:", error);
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
            <div className="glass-card glass-card-hover rounded-2xl p-6 animate-pulse">
                <div className="h-6 bg-white/10 rounded w-1/3 mb-4"></div>
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                        {[...Array(3)].map((_, i) => (
                            <div key={i} className="h-16 bg-white/10 rounded"></div>
                        ))}
                    </div>
                    <div className="space-y-2">
                        {[...Array(3)].map((_, i) => (
                            <div key={i} className="h-16 bg-white/10 rounded"></div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    if (!data) {
        return null;
    }

    const formatPrice = (price: number) => {
        if (price >= 1) return `$${price.toFixed(2)}`;
        if (price >= 0.01) return `$${price.toFixed(4)}`;
        return `$${price.toFixed(6)}`;
    };

    return (
        <div className="glass-card glass-card-hover rounded-2xl p-6 animate-slide-up">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider">
                    Top Movers 24h
                </h3>
            </div>

            {/* Split View */}
            <div className="grid grid-cols-2 gap-6">
                {/* Gainers */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-2 h-2 rounded-full bg-profit animate-pulse-glow"></div>
                        <span className="text-xs font-semibold text-profit uppercase tracking-wide">
                            Top Gainers
                        </span>
                    </div>
                    <div className="space-y-2">
                        {data.gainers.slice(0, 5).map((coin) => (
                            <div
                                key={coin.symbol}
                                className="p-3 rounded-xl bg-gradient-to-r from-profit/10 to-transparent hover:from-profit/20 transition-all duration-200"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex-1 min-w-0">
                                        <div className="font-semibold text-white text-sm truncate">
                                            {coin.symbol}
                                        </div>
                                        <div className="text-xs text-white/40 truncate">
                                            {formatPrice(coin.price)}
                                        </div>
                                    </div>
                                    <div className="data-value data-value-sm text-profit">
                                        +{coin.percent_change_24h.toFixed(1)}%
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Losers */}
                <div>
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-2 h-2 rounded-full bg-loss animate-pulse-glow"></div>
                        <span className="text-xs font-semibold text-loss uppercase tracking-wide">
                            Top Losers
                        </span>
                    </div>
                    <div className="space-y-2">
                        {data.losers.slice(0, 5).map((coin) => (
                            <div
                                key={coin.symbol}
                                className="p-3 rounded-xl bg-gradient-to-r from-loss/10 to-transparent hover:from-loss/20 transition-all duration-200"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex-1 min-w-0">
                                        <div className="font-semibold text-white text-sm truncate">
                                            {coin.symbol}
                                        </div>
                                        <div className="text-xs text-white/40 truncate">
                                            {formatPrice(coin.price)}
                                        </div>
                                    </div>
                                    <div className="data-value data-value-sm text-loss">
                                        {coin.percent_change_24h.toFixed(1)}%
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
