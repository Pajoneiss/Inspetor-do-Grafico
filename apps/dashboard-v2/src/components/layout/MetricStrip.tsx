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
    <div className="bg-dark-card rounded-lg border border-dark-border p-3 flex flex-col justify-between hover:border-dark-borderLight transition-all">
        <div className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">{label}</div>
        <div className="flex items-baseline gap-2 mt-1">
            {loading ? (
                <div className="h-6 w-20 bg-dark-border animate-pulse rounded" />
            ) : (
                <>
                    <span className="text-xl font-bold text-text-primary tracking-tight">{value}</span>
                    {delta !== undefined && (
                        <span className={`text-[10px] font-bold ${deltaColor === 'profit' ? 'text-profit' :
                            deltaColor === 'loss' ? 'text-loss' : 'text-text-muted'
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
