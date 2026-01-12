"use client";

import React, { useMemo, useEffect, useRef } from 'react';
import { TrendingUp, TrendingDown, Activity, Wallet, Target, Clock, BarChart3, Zap } from 'lucide-react';

// Types
interface FullAnalytics {
    history: Array<{ time: string | number; value: number }>;
    pnl_history?: Array<{ time: string | number; value: number }>;
    pnl_24h?: number;
    pnl_7d?: number;
    pnl_30d?: number;
    pnl_total?: number;
    win_rate?: number;
    profit_factor?: number;
    total_trades?: number;
    wins?: number;
    losses?: number;
    volume?: number;
    best_trade_pnl?: number;
    worst_trade_pnl?: number;
    avg_duration_minutes?: number;
}

interface Position {
    symbol: string;
    side: string;
    size: number;
    entry_price: number;
    mark_price: number;
    unrealized_pnl: number;
    leverage?: number;
}

interface DashboardData {
    equity: number;
    unrealized_pnl: number;
    buying_power: number;
    positions_count: number;
    margin_usage: number;
    pnl_24h?: number;
}

interface FillInfo {
    timestamp?: string;
    symbol: string;
    side: string;
    price: number;
    size: number;
    value: number;
    closed_pnl?: number;
}

interface HyperDashOverviewProps {
    status: DashboardData | null;
    fullAnalytics: FullAnalytics | null;
    positions: Position[];
    recentFills: FillInfo[];
    period: '24H' | '7D' | '30D' | 'ALL';
    setPeriod: (p: '24H' | '7D' | '30D' | 'ALL') => void;
    isLoading: boolean;
}

// Equity Chart Component using Canvas
const EquityChart = ({ data, isLoading }: { data: Array<{ time: number; value: number }>; isLoading: boolean }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        if (!canvasRef.current || !data || data.length < 2) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Set canvas size
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * 2;
        canvas.height = rect.height * 2;
        ctx.scale(2, 2);

        const width = rect.width;
        const height = rect.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Calculate min/max
        const values = data.map(d => d.value);
        const minVal = Math.min(...values);
        const maxVal = Math.max(...values);
        const range = maxVal - minVal || 1;
        const padding = range * 0.1;

        // Determine trend
        const startVal = data[0].value;
        const endVal = data[data.length - 1].value;
        const isPositive = endVal >= startVal;

        // Colors
        const lineColor = isPositive ? '#22c55e' : '#ef4444';
        const gradientTop = isPositive ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)';
        const gradientBottom = 'rgba(0, 0, 0, 0)';

        // Draw grid lines
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = (height / 4) * i;
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }

        // Calculate points
        const points: [number, number][] = data.map((d, i) => {
            const x = (i / (data.length - 1)) * width;
            const y = height - ((d.value - minVal + padding) / (range + padding * 2)) * height;
            return [x, y];
        });

        // Draw gradient fill
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, gradientTop);
        gradient.addColorStop(1, gradientBottom);

        ctx.beginPath();
        ctx.moveTo(points[0][0], height);
        points.forEach(([x, y]) => ctx.lineTo(x, y));
        ctx.lineTo(points[points.length - 1][0], height);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();

        // Draw line
        ctx.beginPath();
        ctx.moveTo(points[0][0], points[0][1]);
        points.forEach(([x, y]) => ctx.lineTo(x, y));
        ctx.strokeStyle = lineColor;
        ctx.lineWidth = 2;
        ctx.stroke();

        // Draw current value dot
        const lastPoint = points[points.length - 1];
        ctx.beginPath();
        ctx.arc(lastPoint[0], lastPoint[1], 4, 0, Math.PI * 2);
        ctx.fillStyle = lineColor;
        ctx.fill();
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        ctx.stroke();

    }, [data]);

    if (isLoading || !data || data.length < 2) {
        return (
            <div className="w-full h-full flex items-center justify-center text-white/30">
                {isLoading ? 'Loading chart...' : 'Insufficient data for chart'}
            </div>
        );
    }

    return <canvas ref={canvasRef} className="w-full h-full" />;
};

// Metric Card Component
const MetricCard = ({ label, value, subValue, trend, icon: Icon }: {
    label: string;
    value: string;
    subValue?: string;
    trend?: 'up' | 'down' | 'neutral';
    icon?: React.ElementType;
}) => (
    <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5 hover:border-white/10 transition-colors">
        <div className="flex items-center gap-2 mb-1">
            {Icon && <Icon className="w-3 h-3 text-white/40" />}
            <span className="text-[10px] text-white/40 uppercase tracking-wider">{label}</span>
        </div>
        <div className={`text-lg font-bold ${trend === 'up' ? 'text-green-400' :
                trend === 'down' ? 'text-red-400' :
                    'text-white'
            }`}>
            {value}
        </div>
        {subValue && (
            <div className={`text-xs ${trend === 'up' ? 'text-green-400/60' :
                    trend === 'down' ? 'text-red-400/60' :
                        'text-white/40'
                }`}>
                {subValue}
            </div>
        )}
    </div>
);

// Main Component
export default function HyperDashOverview({
    status,
    fullAnalytics,
    positions,
    recentFills,
    period,
    setPeriod,
    isLoading
}: HyperDashOverviewProps) {

    // Calculate derived values
    const equity = status?.equity || 0;
    const pnl24h = fullAnalytics?.pnl_24h || 0;
    const pnl7d = fullAnalytics?.pnl_7d || 0;
    const pnl30d = fullAnalytics?.pnl_30d || 0;
    const pnlTotal = fullAnalytics?.pnl_total || 0;
    const winRate = fullAnalytics?.win_rate || 0;
    const profitFactor = fullAnalytics?.profit_factor || 1;
    const totalTrades = fullAnalytics?.total_trades || 0;
    const bestTrade = fullAnalytics?.best_trade_pnl || 0;
    const worstTrade = fullAnalytics?.worst_trade_pnl || 0;
    const volume = fullAnalytics?.volume || 0;

    // Format chart data
    const chartData = useMemo(() => {
        if (!fullAnalytics?.history) return [];
        return fullAnalytics.history.map(h => ({
            time: typeof h.time === 'number' ? h.time : new Date(h.time).getTime(),
            value: h.value
        }));
    }, [fullAnalytics?.history]);

    // Calculate PnL percentage
    const pnlPercent = equity > 0 ? ((pnlTotal / (equity - pnlTotal)) * 100) : 0;

    // Period buttons
    const periods = [
        { key: '24H' as const, label: '1D' },
        { key: '7D' as const, label: '7D' },
        { key: '30D' as const, label: '30D' },
        { key: 'ALL' as const, label: 'ALL' },
    ];

    return (
        <div className="w-full h-full bg-[#0a0a0a] rounded-2xl border border-white/5 overflow-hidden">
            <div className="grid grid-cols-12 h-full">

                {/* Left Sidebar - Metrics */}
                <div className="col-span-3 border-r border-white/5 p-4 space-y-3 overflow-y-auto">
                    {/* Account Equity */}
                    <div className="mb-6">
                        <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Account Equity</p>
                        <p className="text-3xl font-bold text-white">${equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}</p>
                    </div>

                    {/* PnL Grid */}
                    <div className="grid grid-cols-2 gap-2">
                        <MetricCard
                            label="1D PnL"
                            value={`${pnl24h >= 0 ? '+' : ''}$${pnl24h.toFixed(2)}`}
                            trend={pnl24h >= 0 ? 'up' : 'down'}
                        />
                        <MetricCard
                            label="7D PnL"
                            value={`${pnl7d >= 0 ? '+' : ''}$${pnl7d.toFixed(2)}`}
                            trend={pnl7d >= 0 ? 'up' : 'down'}
                        />
                    </div>

                    {/* Cumulative PnL */}
                    <div className="p-4 rounded-xl bg-gradient-to-br from-white/[0.03] to-transparent border border-white/5">
                        <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Cumulative PnL</p>
                        <p className={`text-2xl font-bold ${pnlTotal >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {pnlTotal >= 0 ? '+' : ''}{pnlTotal.toFixed(2)}
                        </p>
                        <p className={`text-sm ${pnlPercent >= 0 ? 'text-green-400/60' : 'text-red-400/60'}`}>
                            {pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
                        </p>
                    </div>

                    {/* Stats Grid */}
                    <div className="space-y-2 pt-4 border-t border-white/5">
                        <MetricCard
                            label="Win Rate"
                            value={`${winRate.toFixed(1)}%`}
                            icon={Target}
                            trend={winRate >= 50 ? 'up' : 'down'}
                        />
                        <MetricCard
                            label="Profit Factor"
                            value={profitFactor.toFixed(2)}
                            icon={BarChart3}
                            trend={profitFactor >= 1 ? 'up' : 'down'}
                        />
                        <MetricCard
                            label="Total Trades"
                            value={totalTrades.toString()}
                            icon={Activity}
                        />
                        <MetricCard
                            label="Volume"
                            value={`$${(volume / 1000).toFixed(1)}K`}
                            icon={Zap}
                        />
                    </div>

                    {/* Best/Worst Trade */}
                    <div className="grid grid-cols-2 gap-2 pt-4 border-t border-white/5">
                        <MetricCard
                            label="Best Trade"
                            value={`+$${bestTrade.toFixed(2)}`}
                            trend="up"
                        />
                        <MetricCard
                            label="Worst Trade"
                            value={`$${worstTrade.toFixed(2)}`}
                            trend="down"
                        />
                    </div>
                </div>

                {/* Center - Chart */}
                <div className="col-span-9 flex flex-col">
                    {/* Period Selector */}
                    <div className="flex items-center justify-between p-4 border-b border-white/5">
                        <div className="flex items-center gap-2">
                            <span className="text-sm text-white/60">Portfolio Value</span>
                        </div>
                        <div className="flex gap-1 p-1 rounded-lg bg-white/5">
                            {periods.map(p => (
                                <button
                                    key={p.key}
                                    onClick={() => setPeriod(p.key)}
                                    className={`px-3 py-1.5 rounded text-xs font-medium transition-all ${period === p.key
                                            ? 'bg-white text-black'
                                            : 'text-white/40 hover:text-white hover:bg-white/5'
                                        }`}
                                >
                                    {p.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Chart Area */}
                    <div className="flex-1 p-4">
                        <div className="w-full h-full min-h-[300px]">
                            <EquityChart data={chartData} isLoading={isLoading} />
                        </div>
                    </div>

                    {/* Active Positions */}
                    <div className="border-t border-white/5 p-4">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-medium text-white/80">Active Positions</h3>
                            <span className="text-xs text-white/40">{positions.length} positions</span>
                        </div>

                        {positions.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="w-full text-xs">
                                    <thead>
                                        <tr className="text-white/40 border-b border-white/5">
                                            <th className="text-left py-2 font-medium">Symbol</th>
                                            <th className="text-left py-2 font-medium">Side</th>
                                            <th className="text-right py-2 font-medium">Size</th>
                                            <th className="text-right py-2 font-medium">Entry</th>
                                            <th className="text-right py-2 font-medium">Mark</th>
                                            <th className="text-right py-2 font-medium">PnL</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {positions.map((pos, idx) => (
                                            <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02]">
                                                <td className="py-2 font-medium text-white">{pos.symbol}</td>
                                                <td className={`py-2 ${pos.side === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
                                                    {pos.side}
                                                </td>
                                                <td className="py-2 text-right text-white/60">{pos.size.toFixed(4)}</td>
                                                <td className="py-2 text-right text-white/60">${pos.entry_price.toFixed(2)}</td>
                                                <td className="py-2 text-right text-white/60">${pos.mark_price.toFixed(2)}</td>
                                                <td className={`py-2 text-right font-medium ${pos.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                    {pos.unrealized_pnl >= 0 ? '+' : ''}${pos.unrealized_pnl.toFixed(2)}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="text-center py-8 text-white/30">
                                No active positions
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
