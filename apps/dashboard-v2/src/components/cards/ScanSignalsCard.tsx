'use client';

import { Radar, TrendingUp, TrendingDown } from 'lucide-react';

interface ScanSignal {
    symbol: string;
    score: number;
    bias: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
    reason: string;
}

interface ScanSignalsProps {
    topSignals: ScanSignal[];
    bottomSignals: ScanSignal[];
    totalScanned?: number;
    loading?: boolean;
}

export function ScanSignalsCard({
    topSignals,
    bottomSignals,
    totalScanned = 11,
    loading = false
}: ScanSignalsProps) {
    if (loading) {
        return (
            <div className="card">
                <div className="skeleton h-6 w-32 mb-4" />
                <div className="space-y-2">
                    {[1, 2, 3, 4, 5].map(i => (
                        <div key={i} className="skeleton h-10 w-full" />
                    ))}
                </div>
            </div>
        );
    }

    const getBiasIcon = (bias: string) => {
        if (bias === 'BULLISH') return <TrendingUp className="w-3 h-3 text-[var(--profit)]" />;
        if (bias === 'BEARISH') return <TrendingDown className="w-3 h-3 text-[var(--loss)]" />;
        return null;
    };

    const getScoreColor = (score: number) => {
        if (score >= 80) return 'text-[var(--profit)]';
        if (score >= 60) return 'text-[var(--accent-cyan)]';
        if (score >= 40) return 'text-[var(--accent-yellow)]';
        return 'text-[var(--loss)]';
    };

    return (
        <div className="card">
            <div className="card-header">
                <div className="flex items-center gap-2">
                    <Radar className="w-4 h-4 text-[var(--accent-cyan)]" />
                    <span className="card-title">Scanner Signals</span>
                </div>
                <span className="text-xs text-[var(--text-muted)]">
                    {totalScanned} symbols
                </span>
            </div>

            {/* Top Signals */}
            <div className="mb-4">
                <div className="text-xs text-[var(--text-muted)] mb-2 uppercase tracking-wide">Top 5</div>
                <div className="space-y-2">
                    {topSignals.slice(0, 5).map((signal) => (
                        <div
                            key={signal.symbol}
                            className="flex items-center justify-between p-3 bg-[var(--bg-primary)]"
                        >
                            <div className="flex items-center gap-3">
                                <span className="font-medium text-sm">{signal.symbol}</span>
                                {getBiasIcon(signal.bias)}
                            </div>
                            <div className="flex items-center gap-3">
                                <span className="text-xs text-[var(--text-muted)] truncate max-w-[120px]">
                                    {signal.reason}
                                </span>
                                <span className={`text-sm font-semibold ${getScoreColor(signal.score)}`}>
                                    {signal.score}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Bottom Signals */}
            <div>
                <div className="text-xs text-[var(--text-muted)] mb-2 uppercase tracking-wide">Bottom 3</div>
                <div className="space-y-2">
                    {bottomSignals.slice(0, 3).map((signal) => (
                        <div
                            key={signal.symbol}
                            className="flex items-center justify-between p-3 bg-[var(--bg-primary)]"
                        >
                            <div className="flex items-center gap-3">
                                <span className="font-medium text-sm text-[var(--text-muted)]">{signal.symbol}</span>
                                {getBiasIcon(signal.bias)}
                            </div>
                            <span className={`text-sm font-semibold ${getScoreColor(signal.score)}`}>
                                {signal.score}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
