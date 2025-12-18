'use client'
import React from 'react'

interface Position {
    symbol: string
    side: string
    size: number
    entryPrice: number
    markPrice: number
    unrealizedPnl: number
    roe: number
    leverage?: number
    stopLoss?: number
    takeProfit?: number
}

interface PositionsTableProps {
    positions: Position[]
    loading?: boolean
}

export default function PositionsTable({ positions, loading }: PositionsTableProps) {
    if (loading) {
        return (
            <div className="glass p-10 animate-pulse">
                <div className="h-4 w-32 bg-white/5 rounded-full mb-6" />
                <div className="space-y-4">
                    {[1, 2, 3].map(i => <div key={i} className="h-10 bg-white/5 rounded-xl" />)}
                </div>
            </div>
        )
    }

    return (
        <div className="glass overflow-hidden animate-in">
            <div className="px-10 py-6 border-b border-white/5 flex items-center justify-between bg-white/5 backdrop-blur-md">
                <div className="flex items-center gap-3">
                    <span className="text-sm font-black text-[var(--color-text-primary)] uppercase tracking-widest">Active Fleet</span>
                    <span className="px-2 py-0.5 bg-[var(--color-accent-cyan)]/10 text-[var(--color-accent-cyan)] rounded-full text-[10px] font-black neon-glow-cyan">{positions.length}</span>
                </div>
                <div className="text-[11px] text-[var(--color-text-muted)] font-bold uppercase tracking-widest">
                    Fleet uPnL: <span className={`text-sm tracking-tighter ml-2 ${positions.reduce((a, b) => a + b.unrealizedPnl, 0) >= 0 ? 'text-[var(--color-profit)] neon-glow-emerald' : 'text-[var(--color-loss)] neon-glow-ruby'}`}>
                        ${positions.reduce((a, b) => a + b.unrealizedPnl, 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                </div>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-[11px] border-collapse">
                    <thead>
                        <tr className="bg-white/5 text-[var(--color-text-muted)] uppercase tracking-widest text-[9px] font-black border-b border-white/5">
                            <th className="text-left px-10 py-6">Symbol</th>
                            <th className="text-left px-2 py-4">Side</th>
                            <th className="text-right px-2 py-4">Size</th>
                            <th className="text-right px-2 py-4">Entry</th>
                            <th className="text-right px-2 py-4">Mark</th>
                            <th className="text-right px-2 py-4">uPnL</th>
                            <th className="text-right px-2 py-4">ROE</th>
                            <th className="text-right px-6 py-4">Execution Guard</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {!positions.length ? (
                            <tr>
                                <td colSpan={8} className="text-center py-12 text-[var(--color-text-muted)] font-medium italic opacity-50">No active positions currently patrolling.</td>
                            </tr>
                        ) : (
                            positions.map((p, i) => (
                                <tr key={i} className="group hover:bg-white/5 transition-all duration-300">
                                    <td className="px-10 py-6 font-black text-sm text-[var(--color-text-primary)] tracking-tight">{p.symbol}</td>
                                    <td className="px-2 py-4">
                                        <span className={`px-2 py-1 rounded-md font-black text-[9px] tracking-widest ${p.side.toLowerCase() === 'long' ? 'bg-[var(--color-profit)]/10 text-[var(--color-profit)] border border-[var(--color-profit)]/20 shadow-[0_0_10px_rgba(0,255,136,0.1)]' : 'bg-[var(--color-loss)]/10 text-[var(--color-loss)] border border-[var(--color-loss)]/20 shadow-[0_0_10px_rgba(255,59,105,0.1)]'
                                            }`}>
                                            {p.side.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="px-2 py-4 text-right font-bold text-[var(--color-text-secondary)]">
                                        {p.size.toFixed(4)} {p.leverage && <span className="text-[9px] opacity-70 px-1.5 py-0.5 bg-white/10 rounded ml-1">{p.leverage}x</span>}
                                    </td>
                                    <td className="px-2 py-4 text-right text-[var(--color-text-muted)] font-medium">${p.entryPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                                    <td className="px-2 py-4 text-right text-[var(--color-text-secondary)] font-semibold">${p.markPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                                    <td className={`px-2 py-4 text-right font-black text-sm tracking-tighter ${p.unrealizedPnl >= 0 ? 'text-[var(--color-profit)] text-glow' : 'text-[var(--color-loss)] text-glow'}`}>
                                        ${p.unrealizedPnl.toFixed(2)}
                                    </td>
                                    <td className={`px-2 py-4 text-right font-black text-sm tracking-tighter ${p.roe >= 0 ? 'text-[var(--color-profit)]' : 'text-[var(--color-loss)]'}`}>
                                        {p.roe.toFixed(2)}%
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex flex-col items-end gap-1">
                                            <div className="flex items-center gap-1.5">
                                                <span className="text-[8px] font-black text-[var(--color-loss)] opacity-50 uppercase">SL</span>
                                                <span className="text-[11px] font-black text-[var(--color-loss)] opacity-90">{p.stopLoss ? `$${p.stopLoss.toLocaleString()}` : '--'}</span>
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                <span className="text-[8px] font-black text-[var(--color-profit)] opacity-50 uppercase">TP</span>
                                                <span className="text-[11px] font-black text-[var(--color-profit)] opacity-90">{p.takeProfit ? `$${p.takeProfit.toLocaleString()}` : '--'}</span>
                                            </div>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
