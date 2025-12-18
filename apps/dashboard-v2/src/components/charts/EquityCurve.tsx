'use client';

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

interface DataPoint {
    time: string;
    value: number;
}

interface EquityCurveProps {
    data: DataPoint[];
    loading?: boolean;
}

export function EquityCurve({ data, loading = false }: EquityCurveProps) {
    if (loading) {
        return (
            <div className="card">
                <div className="skeleton h-6 w-48 mb-4" />
                <div className="skeleton h-64 w-full" />
            </div>
        );
    }

    const formatCurrency = (value: number) =>
        new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0
        }).format(value);

    // Calculate if overall trend is positive
    const firstValue = data[0]?.value || 0;
    const lastValue = data[data.length - 1]?.value || 0;
    const isPositive = lastValue >= firstValue;

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-[var(--bg-card)] border border-[var(--border)] p-3 shadow-lg">
                    <p className="text-xs text-[var(--text-muted)] mb-1">{label}</p>
                    <p className="text-sm font-semibold text-[var(--text-primary)]">
                        {formatCurrency(payload[0].value)}
                    </p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="card">
            <div className="card-header">
                <span className="card-title">Cumulative PnL</span>
                <div className="flex gap-2">
                    {['24h', '7d', '30d', 'ALL'].map((period) => (
                        <button
                            key={period}
                            className="px-2 py-1 text-xs text-[var(--text-muted)] hover:bg-[var(--bg-primary)] transition-colors"
                        >
                            {period}
                        </button>
                    ))}
                </div>
            </div>

            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                                <stop
                                    offset="5%"
                                    stopColor={isPositive ? '#7CFF6B' : '#FF6B6B'}
                                    stopOpacity={0.3}
                                />
                                <stop
                                    offset="95%"
                                    stopColor={isPositive ? '#7CFF6B' : '#FF6B6B'}
                                    stopOpacity={0}
                                />
                            </linearGradient>
                        </defs>
                        <XAxis
                            dataKey="time"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#6B7C93', fontSize: 11 }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#6B7C93', fontSize: 11 }}
                            tickFormatter={(value) => `$${value}`}
                            dx={-10}
                        />
                        <Tooltip content={<CustomTooltip />} />
                        <Area
                            type="monotone"
                            dataKey="value"
                            stroke={isPositive ? '#7CFF6B' : '#FF6B6B'}
                            strokeWidth={2}
                            fill="url(#colorPnl)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
