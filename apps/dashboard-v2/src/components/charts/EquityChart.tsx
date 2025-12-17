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
    <div className={`bg-dark-card rounded-xl border border-dark-border p-4 transition-all hover:border-dark-borderLight ${className}`}>{children}</div>
)

export default function EquityChart({ data, loading }: EquityChartProps) {
    if (loading || !data?.length) {
        return (
            <Card className="h-full min-h-[300px] flex items-center justify-center">
                <div className="flex flex-col items-center gap-2">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-accent-cyan" />
                    <span className="text-text-muted text-xs">Wait for data...</span>
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
        <Card className="h-full min-h-[300px] flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
                <div className="flex flex-col">
                    <span className="text-[10px] text-text-muted uppercase font-bold tracking-widest">Account Health</span>
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-black text-text-primary tracking-tighter">${last.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                        <span className={`text-xs font-bold ${pnl >= 0 ? 'text-profit' : 'text-loss'}`}>
                            {pnl >= 0 ? '↑' : '↓'} ${Math.abs(pnl).toFixed(2)}
                        </span>
                    </div>
                </div>
                <div className="flex gap-1 bg-dark-bg/50 p-1 rounded-lg border border-dark-border">
                    {['24H', '1W', '1M', 'All'].map(r => (
                        <button
                            key={r}
                            className={`px-3 py-1 rounded-md text-[10px] font-black uppercase tracking-tight transition-all ${r === '24H' ? 'bg-accent-cyan text-dark-bg shadow-lg shadow-accent-cyan/20' : 'text-text-muted hover:text-text-secondary'}`}
                        >
                            {r}
                        </button>
                    ))}
                </div>
            </div>
            <div className="flex-1 h-full min-h-[180px] mt-4">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id="equityGrad" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={color} stopOpacity={0.2} />
                                <stop offset="95%" stopColor={color} stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e222d" vertical={false} />
                        <XAxis dataKey="time" stroke="#475569" tick={{ fill: '#475569', fontSize: 9 }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                        <YAxis
                            stroke="#475569"
                            tick={{ fill: '#475569', fontSize: 9 }}
                            tickLine={false}
                            axisLine={false}
                            domain={[min * 0.999, max * 1.001]}
                            tickFormatter={v => `$${v.toFixed(0)}`}
                            orientation="right"
                            width={40}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#11141d', border: '1px solid #1e222d', borderRadius: '8px', fontSize: '11px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' }}
                            itemStyle={{ color: '#f8fafc' }}
                            labelStyle={{ color: '#64748b', marginBottom: '4px', fontWeight: 'bold' }}
                            formatter={(v: number) => [`$${v.toLocaleString(undefined, { minimumFractionDigits: 2 })}`, 'Equity']}
                        />
                        <Area type="monotone" dataKey="value" stroke={color} fill="url(#equityGrad)" strokeWidth={3} dot={false} animationDuration={1000} />
                        <ReferenceDot x={data[data.length - 1]?.time} y={last} r={4} fill={color} stroke="#07090e" strokeWidth={2} />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </Card>
    )
}
