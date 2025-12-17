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
            <div className="bg-dark-card rounded-xl border border-dark-border p-4 animate-pulse">
                <div className="h-4 w-32 bg-dark-border rounded mb-4" />
                <div className="space-y-3">
                    {[1, 2, 3].map(i => <div key={i} className="h-8 bg-dark-border rounded" />)}
                </div>
            </div>
        )
    }

    return (
        <div className="bg-dark-card rounded-xl border border-dark-border overflow-hidden">
            <div className="px-4 py-3 border-b border-dark-border flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-text-primary">Open Positions</span>
                    <span className="px-1.5 py-0.5 bg-dark-border rounded text-[10px] font-bold text-text-muted">{positions.length}</span>
                </div>
                <div className="text-[10px] text-text-muted font-bold uppercase tracking-wider">
                    Total uPnL: <span className={positions.reduce((a, b) => a + b.unrealizedPnl, 0) >= 0 ? 'text-profit' : 'text-loss'}>
                        ${positions.reduce((a, b) => a + b.unrealizedPnl, 0).toFixed(2)}
                    </span>
                </div>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-[11px] border-collapse">
                    <thead>
                        <tr className="bg-dark-bg/30 text-text-muted uppercase tracking-tighter text-[9px] font-bold border-b border-dark-border">
                            <th className="text-left px-4 py-2">Symbol</th>
                            <th className="text-left px-2 py-2">Side</th>
                            <th className="text-right px-2 py-2">Size</th>
                            <th className="text-right px-2 py-2">Entry</th>
                            <th className="text-right px-2 py-2">Mark</th>
                            <th className="text-right px-2 py-2">uPnL</th>
                            <th className="text-right px-2 py-2">ROE</th>
                            <th className="text-right px-4 py-2">SL / TP</th>
                        </tr>
                    </thead>
                    <tbody>
                        {!positions.length ? (
                            <tr>
                                <td colSpan={8} className="text-center py-8 text-text-muted italic">No open positions found</td>
                            </tr>
                        ) : (
                            positions.map((p, i) => (
                                <tr key={i} className="border-b border-dark-border/50 hover:bg-dark-border/10 transition-colors">
                                    <td className="px-4 py-2.5 font-bold text-text-primary">{p.symbol}</td>
                                    <td className="px-2 py-2.5">
                                        <span className={`px-1.5 py-0.5 rounded-[3px] font-black text-[9px] ${p.side.toLowerCase() === 'long' ? 'bg-profit/10 text-profit border border-profit/20' : 'bg-loss/10 text-loss border border-loss/20'
                                            }`}>
                                            {p.side.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="px-2 py-2.5 text-right font-medium text-text-secondary">
                                        {p.size.toFixed(4)} {p.leverage && <span className="text-[9px] opacity-50 px-1 bg-dark-border rounded">{p.leverage}x</span>}
                                    </td>
                                    <td className="px-2 py-2.5 text-right text-text-muted">${p.entryPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                                    <td className="px-2 py-2.5 text-right text-text-secondary">${p.markPrice.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                                    <td className={`px-2 py-2.5 text-right font-bold ${p.unrealizedPnl >= 0 ? 'text-profit' : 'text-loss'}`}>
                                        ${p.unrealizedPnl.toFixed(2)}
                                    </td>
                                    <td className={`px-2 py-2.5 text-right font-bold ${p.roe >= 0 ? 'text-profit' : 'text-loss'}`}>
                                        {p.roe.toFixed(2)}%
                                    </td>
                                    <td className="px-4 py-2.5 text-right flex flex-col items-end">
                                        <div className="text-[10px] font-bold text-loss">{p.stopLoss ? `$${p.stopLoss.toLocaleString()}` : '--'}</div>
                                        <div className="text-[10px] font-bold text-profit">{p.takeProfit ? `$${p.takeProfit.toLocaleString()}` : '--'}</div>
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
