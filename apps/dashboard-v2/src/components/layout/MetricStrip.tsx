'use client'
import React from 'react'

interface MetricProps {
    label: string
    value: string | number
    delta?: string | number
    deltaColor?: 'profit' | 'loss' | 'neutral'
    loading?: boolean
}

const KpiCard = ({ label, value, delta, deltaColor, loading }: MetricProps) => (
    <div className="glass glass-hover rounded-xl p-4 flex flex-col justify-between animate-in">
        <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-[0.1em] font-bold">{label}</div>
        <div className="flex items-baseline gap-2 mt-2">
            {loading ? (
                <div className="h-8 w-24 bg-[var(--glass-border)] animate-pulse rounded-md" />
            ) : (
                <>
                    <span className="text-2xl font-black text-[var(--color-text-primary)] tracking-tighter">{value}</span>
                    {delta !== undefined && (
                        <span className={`text-[11px] font-bold px-1.5 py-0.5 rounded-md ${deltaColor === 'profit' ? 'bg-[var(--color-accent-green)]/10 text-[var(--color-accent-green)] neon-glow-emerald' :
                            deltaColor === 'loss' ? 'bg-[var(--color-loss)]/10 text-[var(--color-loss)] neon-glow-ruby' : 'bg-white/5 text-[var(--color-text-muted)]'
                            }`}>
                            {delta}
                        </span>
                    )}
                </>
            )}
        </div>
    </div>
)

interface MetricStripProps {
    account: any
    loading?: boolean
}

interface MetricItem {
    label: string
    value: string | number
    delta?: string | number
    deltaColor?: 'profit' | 'loss' | 'neutral'
}

export default function MetricStrip({ account, loading }: MetricStripProps) {
    if (!account && !loading) return null

    const metrics: MetricItem[] = [
        { label: 'Equity', value: `$${(account?.equity || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` },
        {
            label: 'Unrealized PnL',
            value: `$${(account?.unrealized_pnl || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
            delta: `${(account?.pnl_pct || 0) >= 0 ? '+' : ''}${(account?.pnl_pct || 0).toFixed(2)}%`,
            deltaColor: (account?.pnl_pct || 0) >= 0 ? 'profit' : 'loss'
        },
        {
            label: 'Day PnL',
            value: `$${(account?.realizedPnl24h || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
            delta: `${(account?.day_pnl_pct || 0) >= 0 ? '+' : ''}${(account?.day_pnl_pct || 0).toFixed(2)}%`,
            deltaColor: (account?.day_pnl_pct || 0) >= 0 ? 'profit' : 'loss'
        },
        { label: 'Leverage', value: `${(account?.leverage || 1).toFixed(2)}x` },
        {
            label: 'Margin Usage',
            value: `${(account?.marginUsage || 0).toFixed(1)}%`,
            delta: (account?.marginUsage || 0) > 80 ? 'HIGH' : 'SAFE',
            deltaColor: (account?.marginUsage || 0) > 80 ? 'loss' : 'profit'
        },
        { label: 'Positions', value: account?.openPositions || 0 },
        { label: 'Buying Power', value: `$${(account?.buyingPower || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}` }
    ]

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2 mb-3">
            {metrics.map((m, i) => (
                <KpiCard key={i} {...m} loading={loading} />
            ))}
        </div>
    )
}
