'use client';

import { TrendingUp, TrendingDown, DollarSign, Wallet, Activity, Percent } from 'lucide-react';

interface AccountValueProps {
    equity: number;
    buyingPower: number;
    unrealizedPnl: number;
    realizedPnl24h: number;
    fees24h?: number;
    funding24h?: number;
    loading?: boolean;
}

export function AccountValueCard({
    equity,
    buyingPower,
    unrealizedPnl,
    realizedPnl24h,
    fees24h = 0,
    funding24h = 0,
    loading = false
}: AccountValueProps) {
    if (loading) {
        return (
            <div className="card">
                <div className="skeleton h-6 w-32 mb-4" />
                <div className="skeleton h-10 w-48 mb-6" />
                <div className="grid grid-cols-2 gap-4">
                    <div className="skeleton h-16 w-full" />
                    <div className="skeleton h-16 w-full" />
                </div>
            </div>
        );
    }

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(value);
    };

    const formatPnl = (value: number) => {
        const formatted = formatCurrency(Math.abs(value));
        return value >= 0 ? `+${formatted}` : `-${formatted}`;
    };

    return (
        <div className="card">
            <div className="card-header">
                <span className="card-title">Account Value</span>
                <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-[var(--accent-cyan)]" />
                </div>
            </div>

            {/* Main Value */}
            <div className="mb-6">
                <div className="text-4xl font-bold text-[var(--text-primary)]">
                    {formatCurrency(equity)}
                </div>
                <div className="flex items-center gap-1 mt-1">
                    {unrealizedPnl >= 0 ? (
                        <TrendingUp className="w-4 h-4 text-[var(--profit)]" />
                    ) : (
                        <TrendingDown className="w-4 h-4 text-[var(--loss)]" />
                    )}
                    <span className={unrealizedPnl >= 0 ? 'profit' : 'loss'}>
                        {formatPnl(unrealizedPnl)} unrealized
                    </span>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-[var(--bg-primary)] border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                        <Wallet className="w-3 h-3 text-[var(--text-muted)]" />
                        <span className="text-xs text-[var(--text-muted)]">Buying Power</span>
                    </div>
                    <div className="text-lg font-semibold">{formatCurrency(buyingPower)}</div>
                </div>

                <div className="p-4 bg-[var(--bg-primary)] border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                        <DollarSign className="w-3 h-3 text-[var(--text-muted)]" />
                        <span className="text-xs text-[var(--text-muted)]">Realized 24h</span>
                    </div>
                    <div className={`text-lg font-semibold ${realizedPnl24h >= 0 ? 'profit' : 'loss'}`}>
                        {formatPnl(realizedPnl24h)}
                    </div>
                </div>

                <div className="p-4 bg-[var(--bg-primary)] border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                        <Percent className="w-3 h-3 text-[var(--text-muted)]" />
                        <span className="text-xs text-[var(--text-muted)]">Fees 24h</span>
                    </div>
                    <div className="text-lg font-semibold text-[var(--loss)]">
                        -{formatCurrency(Math.abs(fees24h))}
                    </div>
                </div>

                <div className="p-4 bg-[var(--bg-primary)] border border-white/5">
                    <div className="flex items-center gap-2 mb-1">
                        <Activity className="w-3 h-3 text-[var(--text-muted)]" />
                        <span className="text-xs text-[var(--text-muted)]">Funding 24h</span>
                    </div>
                    <div className={`text-lg font-semibold ${funding24h >= 0 ? 'profit' : 'loss'}`}>
                        {formatPnl(funding24h)}
                    </div>
                </div>
            </div>
        </div>
    );
}
