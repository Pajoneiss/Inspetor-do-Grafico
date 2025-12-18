'use client';

import { Shield, AlertTriangle, TrendingUp, Layers } from 'lucide-react';

interface RiskMonitorProps {
    marginUsage: number;
    liquidationBuffer: number;
    totalExposure: number;
    openPositions: number;
    errorCount?: number;
    loading?: boolean;
}

export function RiskMonitorCard({
    marginUsage,
    liquidationBuffer,
    totalExposure,
    openPositions,
    errorCount = 0,
    loading = false
}: RiskMonitorProps) {
    if (loading) {
        return (
            <div className="card">
                <div className="skeleton h-6 w-32 mb-4" />
                <div className="space-y-4">
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className="skeleton h-12 w-full" />
                    ))}
                </div>
            </div>
        );
    }

    const formatPercent = (value: number) => `${value.toFixed(1)}%`;
    const formatCurrency = (value: number) =>
        new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);

    const getMarginColor = (value: number) => {
        if (value < 30) return 'text-[var(--profit)]';
        if (value < 60) return 'text-[var(--accent-yellow)]';
        return 'text-[var(--loss)]';
    };

    const getLiqColor = (value: number) => {
        if (value > 50) return 'text-[var(--profit)]';
        if (value > 20) return 'text-[var(--accent-yellow)]';
        return 'text-[var(--loss)]';
    };

    return (
        <div className="card">
            <div className="card-header">
                <span className="card-title">Risk Monitor</span>
                <Shield className="w-4 h-4 text-[var(--accent-cyan)]" />
            </div>

            <div className="space-y-4">
                {/* Margin Usage */}
                <div className="flex justify-between items-center">
                    <span className="text-sm text-[var(--text-secondary)]">Margin Usage</span>
                    <span className={`text-sm font-semibold ${getMarginColor(marginUsage)}`}>
                        {formatPercent(marginUsage)}
                    </span>
                </div>
                <div className="h-1.5 bg-[var(--bg-primary)] overflow-hidden">
                    <div
                        className={`h-full ${marginUsage < 30 ? 'bg-[var(--profit)]' : marginUsage < 60 ? 'bg-[var(--accent-yellow)]' : 'bg-[var(--loss)]'}`}
                        style={{ width: `${Math.min(marginUsage, 100)}%` }}
                    />
                </div>

                {/* Liquidation Buffer */}
                <div className="flex justify-between items-center">
                    <span className="text-sm text-[var(--text-secondary)]">Liq. Buffer</span>
                    <span className={`text-sm font-semibold ${getLiqColor(liquidationBuffer)}`}>
                        {formatPercent(liquidationBuffer)}
                    </span>
                </div>

                {/* Total Exposure */}
                <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <TrendingUp className="w-3 h-3 text-[var(--text-muted)]" />
                        <span className="text-sm text-[var(--text-secondary)]">Total Exposure</span>
                    </div>
                    <span className="text-sm font-semibold text-[var(--text-primary)]">
                        {formatCurrency(totalExposure)}
                    </span>
                </div>

                {/* Open Positions */}
                <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <Layers className="w-3 h-3 text-[var(--text-muted)]" />
                        <span className="text-sm text-[var(--text-secondary)]">Open Positions</span>
                    </div>
                    <span className="text-sm font-semibold text-[var(--text-primary)]">
                        {openPositions}
                    </span>
                </div>

                {/* Error Count */}
                {errorCount > 0 && (
                    <div className="flex justify-between items-center p-4 bg-[var(--accent-red-bg)]">
                        <div className="flex items-center gap-2">
                            <AlertTriangle className="w-3 h-3 text-[var(--loss)]" />
                            <span className="text-sm text-[var(--loss)]">Errors</span>
                        </div>
                        <span className="text-sm font-semibold text-[var(--loss)]">
                            {errorCount}
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
}
