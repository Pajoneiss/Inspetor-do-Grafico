"use client";

import { useEffect, useState } from "react";

interface CMCGlobalData {
    market_cap: number;
    volume_24h: number;
    btc_dominance: number;
    eth_dominance: number;
    market_cap_change_24h: number;
}

export default function CMCMarketOverview() {
    const [data, setData] = useState<CMCGlobalData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch("/api/cmc/global");
                const json = await res.json();
                if (json.ok) {
                    setData(json.data);
                }
            } catch (error) {
                console.error("Failed to fetch CMC global data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 60000); // Update every minute
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="glass-card glass-card-hover rounded-2xl p-6 animate-pulse">
                <div className="h-6 bg-white/10 rounded w-1/3 mb-4"></div>
                <div className="space-y-3">
                    <div className="h-12 bg-white/10 rounded"></div>
                    <div className="h-12 bg-white/10 rounded"></div>
                </div>
            </div>
        );
    }

    if (!data) {
        return null;
    }

    const formatLargeNumber = (num: number) => {
        if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
        if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
        if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
        return `$${num.toFixed(2)}`;
    };

    const isPositive = data.market_cap_change_24h >= 0;

    return (
        <div className="glass-card glass-card-hover rounded-2xl p-6 animate-slide-up">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider">
                    Global Market
                </h3>
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse-glow"></div>
                    <span className="text-xs text-white/40">Live</span>
                </div>
            </div>

            {/* Market Cap */}
            <div className="mb-6">
                <div className="text-xs text-white/50 mb-1">Total Market Cap</div>
                <div className="flex items-baseline gap-3">
                    <span className="data-value data-value-lg text-white">
                        {formatLargeNumber(data.market_cap)}
                    </span>
                    <span
                        className={`text-sm font-mono ${isPositive ? "text-profit" : "text-loss"
                            }`}
                    >
                        {isPositive ? "+" : ""}
                        {data.market_cap_change_24h.toFixed(2)}%
                    </span>
                </div>
            </div>

            {/* Volume */}
            <div className="mb-6">
                <div className="text-xs text-white/50 mb-1">24h Volume</div>
                <span className="data-value data-value-md text-white/90">
                    {formatLargeNumber(data.volume_24h)}
                </span>
            </div>

            {/* Dominance */}
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <div className="text-xs text-white/50 mb-2">BTC Dominance</div>
                    <div className="relative">
                        <div className="data-value data-value-sm text-white mb-1">
                            {data.btc_dominance.toFixed(1)}%
                        </div>
                        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                            <div
                                className="h-full gradient-info rounded-full transition-all duration-500"
                                style={{ width: `${data.btc_dominance}%` }}
                            ></div>
                        </div>
                    </div>
                </div>
                <div>
                    <div className="text-xs text-white/50 mb-2">ETH Dominance</div>
                    <div className="relative">
                        <div className="data-value data-value-sm text-white mb-1">
                            {data.eth_dominance.toFixed(1)}%
                        </div>
                        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                            <div
                                className="h-full gradient-primary rounded-full transition-all duration-500"
                                style={{ width: `${data.eth_dominance}%` }}
                            ></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
