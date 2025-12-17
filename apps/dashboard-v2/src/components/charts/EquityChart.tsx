'use client'
import React from 'react'
import { ResponsiveContainer, AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip, ReferenceDot } from 'recharts'

interface EquityPoint {
    time: string
    value: number
}

interface EquityChartProps {
    data: EquityPoint[]
    loading?: boolean
}

const Card = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
    <div className={`glass glass-hover rounded-2xl p-6 flex flex-col animate-in ${className}`}>{children}</div>
)

export default function EquityChart({ data, loading }: EquityChartProps) {
    if (loading || !data?.length) {
        return (
            <Card className="h-full min-h-[350px] flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="relative">
                        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-[var(--color-accent-cyan)]" />
                        <div className="absolute inset-0 animate-pulse rounded-full h-10 w-10 border-2 border-[var(--color-accent-cyan)]/20 shadow-[0_0_15px_var(--color-accent-cyan)]" />
                    </div>
                    <span className="text-[var(--color-text-muted)] text-[10px] font-black uppercase tracking-widest animate-pulse">Syncing Equity Core...</span>
                </div>
            </Card>
        )
    }

    const vals = data.map(d => d.value)
    const min = Math.min(...vals)
    const max = Math.max(...vals)
    const last = vals[vals.length - 1] || 0
    const first = vals[0] || 0
    const pnl = last - first
    const color = pnl >= 0 ? '#00ff88' : '#ff3b69'

    return (
        <Card className="h-full min-h-[350px]">
            <div className="flex items-center justify-between mb-6">
                <div className="flex flex-col">
                    <span className="text-[10px] text-[var(--color-text-muted)] uppercase font-black tracking-[0.2em] opacity-80 mb-1">Portfolio Performance</span>
                    <div className="flex items-baseline gap-3">
                        <span className="text-3xl font-black text-[var(--color-text-primary)] tracking-tighter shadow-sm">${last.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                        <span className={`px-2 py-0.5 rounded-md text-xs font-black flex items-center gap-1 ${pnl >= 0 ? 'bg-[var(--color-profit)]/10 text-[var(--color-profit)] neon-glow-emerald' : 'bg-[var(--color-loss)]/10 text-[var(--color-loss)] neon-glow-ruby'}`}>
                            {pnl >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                            ${Math.abs(pnl).toFixed(2)}
                        </span>
                    </div>
                </div>
                <div className="flex gap-1.5 p-1 rounded-xl bg-white/5 border border-white/5">
                    {['24H', '1W', '1M', 'All'].map(r => (
                        <button
                            key={r}
                            className={`px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all duration-300 ${r === '24H' ? 'bg-[var(--color-accent-cyan)] text-[var(--bg-deep)] shadow-[0_0_20px_rgba(0,229,255,0.4)]' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-white/5'}`}
                        >
                            {r}
                        </button>
                    ))}
                </div>
            </div>
            <div className="flex-1 w-full min-h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                                <stop offset="50%" stopColor={color} stopOpacity={0.1} />
                                <stop offset="100%" stopColor={color} stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="6 6" stroke="rgba(255,255,255,0.03)" vertical={false} />
                        <XAxis dataKey="time" stroke="rgba(255,255,255,0.2)" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 9, fontWeight: 700 }} tickLine={false} axisLine={false} interval="preserveStartEnd" padding={{ left: 10, right: 10 }} />
                        <YAxis
                            stroke="rgba(255,255,255,0.2)"
                            tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 9, fontWeight: 700 }}
                            tickLine={false}
                            axisLine={false}
                            domain={[min * 0.9995, max * 1.0005]}
                            tickFormatter={v => `$${v.toFixed(0)}`}
                            orientation="right"
                            width={45}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: 'rgba(10, 13, 18, 0.9)', backdropFilter: 'blur(12px)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '11px', boxShadow: '0 20px 40px -10px rgba(0,0,0,0.5)' }}
                            itemStyle={{ color: '#00e5ff', fontWeight: 800 }}
                            labelStyle={{ color: '#94a3b8', marginBottom: '6px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em' }}
                            formatter={(v: number) => [`$${v.toLocaleString(undefined, { minimumFractionDigits: 2 })}`, 'Balance']}
                        />
                        <Area type="monotone" dataKey="value" stroke={color} fill="url(#equityGrad)" strokeWidth={4} dot={false} animationDuration={1500} strokeLinecap="round" />
                        <ReferenceDot x={data[data.length - 1]?.time} y={last} r={5} fill={color} stroke="#040608" strokeWidth={3} isFront={true} className="neon-glow-emerald" />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </Card>
    )
}

import { TrendingUp, TrendingDown } from 'lucide-react'
