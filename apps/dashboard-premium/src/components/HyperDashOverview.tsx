"use client";

import React, { useMemo, useEffect, useRef, useState } from 'react';
import { BrainCircuit, Terminal } from 'lucide-react';

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

interface OrderInfo {
    symbol: string;
    type: string;
    side: string;
    price: number;
    size: number;
    trigger_px?: number;
}

interface AIThought {
    id?: string;
    timestamp: string;
    emoji?: string;
    summary: string;
    thought?: string;
    confidence: number;
    actions?: string[];
}

interface HyperDashOverviewProps {
    status: DashboardData | null;
    fullAnalytics: FullAnalytics | null;
    positions: Position[];
    recentFills: FillInfo[];
    openOrders?: OrderInfo[];
    period: '24H' | '7D' | '30D' | 'ALL';
    setPeriod: (p: '24H' | '7D' | '30D' | 'ALL') => void;
    isLoading: boolean;
    // AI Strategy Core props
    thoughts?: AIThought[];
    aiMood?: 'aggressive' | 'defensive' | 'observing';
    sessionInfo?: { session: string; current_time_utc: string; is_weekend: boolean } | null;
}

// Equity Chart Component - HyperDash style
const EquityChart = ({
    data,
    isLoading,
    pnlValue,
    pnlPeriod
}: {
    data: Array<{ time: number; value: number }>;
    isLoading: boolean;
    pnlValue: number;
    pnlPeriod: string;
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        if (!canvasRef.current || !data || data.length < 2) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * 2;
        canvas.height = rect.height * 2;
        ctx.scale(2, 2);

        const width = rect.width;
        const height = rect.height;

        ctx.clearRect(0, 0, width, height);

        const values = data.map(d => d.value);
        const minVal = Math.min(...values);
        const maxVal = Math.max(...values);
        const range = maxVal - minVal || 1;
        const padding = range * 0.1;

        const startVal = data[0].value;
        const endVal = data[data.length - 1].value;
        const isPositive = endVal >= startVal;

        const lineColor = isPositive ? '#22c55e' : '#ef4444';
        const gradientTop = isPositive ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)';

        // Draw grid
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 5; i++) {
            const y = (height / 5) * i;
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
        gradient.addColorStop(1, 'transparent');

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
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Draw current value dot
        const lastPoint = points[points.length - 1];
        ctx.beginPath();
        ctx.arc(lastPoint[0], lastPoint[1], 3, 0, Math.PI * 2);
        ctx.fillStyle = lineColor;
        ctx.fill();

        // Draw time labels
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.font = '10px Inter, sans-serif';
        const labelCount = 6;
        for (let i = 0; i < labelCount; i++) {
            const idx = Math.floor((i / (labelCount - 1)) * (data.length - 1));
            const d = data[idx];
            const x = (idx / (data.length - 1)) * width;
            const date = new Date(d.time);
            const label = `${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
            ctx.fillText(label, x - 15, height - 5);
        }

    }, [data]);

    if (isLoading || !data || data.length < 2) {
        return (
            <div className="w-full h-full flex items-center justify-center text-white/30">
                {isLoading ? 'Loading chart...' : 'Insufficient data for chart'}
            </div>
        );
    }

    return (
        <div className="relative w-full h-full">
            {/* PnL Badge - Top Right */}
            <div className="absolute top-2 right-2 z-10">
                <div className={`px-3 py-1.5 rounded-lg ${pnlValue >= 0 ? 'bg-green-500/20 border border-green-500/30' : 'bg-red-500/20 border border-red-500/30'}`}>
                    <div className="text-[10px] text-white/50 uppercase tracking-wider">{pnlPeriod} PERPS PNL</div>
                    <div className={`text-sm font-bold ${pnlValue >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {pnlValue >= 0 ? '+' : '-'}US$ {Math.abs(pnlValue).toFixed(2)}
                    </div>
                </div>
            </div>
            <canvas ref={canvasRef} className="w-full h-full" />
        </div>
    );
};

// Left Sidebar Section Component
const SidebarSection = ({ title, children, collapsible = false }: {
    title: string;
    children: React.ReactNode;
    collapsible?: boolean;
}) => {
    const [isExpanded, setIsExpanded] = useState(true);

    return (
        <div className="border-b border-white/5 pb-3 mb-3">
            <div
                className={`flex items-center justify-between mb-2 ${collapsible ? 'cursor-pointer' : ''}`}
                onClick={() => collapsible && setIsExpanded(!isExpanded)}
            >
                <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest">{title}</span>
                {collapsible && (
                    <span className="text-white/30 text-xs">{isExpanded ? '▼' : '▶'}</span>
                )}
            </div>
            {(!collapsible || isExpanded) && children}
        </div>
    );
};

// Metric Row Component
const MetricRow = ({ label, value, valueColor = 'text-white' }: {
    label: string;
    value: string;
    valueColor?: string;
}) => (
    <div className="flex items-center justify-between py-1">
        <span className="text-xs text-white/40">{label}</span>
        <span className={`text-xs font-medium ${valueColor}`}>{value}</span>
    </div>
);

// Main Component
export default function HyperDashOverview({
    status,
    fullAnalytics,
    positions,
    recentFills,
    openOrders = [],
    period,
    setPeriod,
    isLoading,
    thoughts = [],
    aiMood = 'observing',
    sessionInfo
}: HyperDashOverviewProps) {

    const [activeTab, setActiveTab] = useState<'POSITIONS' | 'BALANCES' | 'ORDERS' | 'FILLS' | 'TRADES' | 'TWAP' | 'TRANSFERS'>('POSITIONS');
    const [rightTab, setRightTab] = useState<'BEST_TRADES' | 'AI_STRATEGY'>('BEST_TRADES');

    // Calculate values
    const equity = status?.equity || 0;
    const unrealizedPnl = status?.unrealized_pnl || 0;
    const marginUsage = status?.margin_usage || 0;
    const pnl24h = fullAnalytics?.pnl_24h || 0;
    const pnl7d = fullAnalytics?.pnl_7d || 0;
    const pnl30d = fullAnalytics?.pnl_30d || 0;
    const pnlTotal = fullAnalytics?.pnl_total || 0;
    const winRate = fullAnalytics?.win_rate || 0;
    const volume = fullAnalytics?.volume || 0;
    const avgDuration = fullAnalytics?.avg_duration_minutes || 0;

    // Get current period PnL for badge
    const currentPnl = period === '24H' ? pnl24h : period === '7D' ? pnl7d : period === '30D' ? pnl30d : pnlTotal;

    // Format chart data - use history (equity) or fall back to pnl_history
    const chartData = useMemo(() => {
        // Try equity history first
        if (fullAnalytics?.history && fullAnalytics.history.length > 1) {
            return fullAnalytics.history.map(h => ({
                time: typeof h.time === 'number' ? h.time : new Date(h.time).getTime(),
                value: h.value
            }));
        }
        // Fall back to PnL history if equity history is empty
        if (fullAnalytics?.pnl_history && fullAnalytics.pnl_history.length > 1) {
            // Convert PnL to simulated equity (starting from current equity - total pnl)
            const baseEquity = equity - pnlTotal;
            return fullAnalytics.pnl_history.map(h => ({
                time: typeof h.time === 'number' ? h.time : new Date(h.time).getTime(),
                value: baseEquity + h.value
            }));
        }
        return [];
    }, [fullAnalytics?.history, fullAnalytics?.pnl_history, equity, pnlTotal]);

    // Format duration
    const formatDuration = (mins: number) => {
        if (mins < 60) return `${Math.round(mins)}m`;
        const hours = Math.floor(mins / 60);
        const remainMins = Math.round(mins % 60);
        if (hours < 24) return `${hours}h ${remainMins}m`;
        const days = Math.floor(hours / 24);
        return `${days}d ${hours % 24}h`;
    };

    // Period buttons
    const periods = [
        { key: 'VALUE', label: 'VALUE' },
        { key: '24H' as const, label: '24H' },
        { key: '7D' as const, label: '1W' },
        { key: '30D' as const, label: '1M' },
        { key: 'ALL' as const, label: 'ALL' },
    ];

    // Bottom tabs
    const tabs = ['POSITIONS', 'BALANCES', 'ORDERS', 'FILLS', 'TRADES', 'TWAP', 'TRANSFERS'] as const;

    // AI Mood config
    const moodConfig = {
        aggressive: { color: 'text-green-400', bg: 'bg-green-500/10', label: '🔥 Aggressive' },
        defensive: { color: 'text-yellow-400', bg: 'bg-yellow-500/10', label: '🛡️ Defensive' },
        observing: { color: 'text-blue-400', bg: 'bg-blue-500/10', label: '👁️ Observing' }
    };

    return (
        <div className="w-full bg-[#0a0a0a] rounded-xl border border-white/5 overflow-hidden">
            <div className="grid grid-cols-12 min-h-[600px]">

                {/* Left Sidebar - 2 cols */}
                <div className="col-span-2 border-r border-white/5 p-3 overflow-y-auto bg-[#080808]">

                    {/* Account Header */}
                    <div className="mb-3 pb-3 border-b border-white/5">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="w-5 h-5 rounded-full bg-gradient-to-br from-purple-500 to-pink-500" />
                            <span className="text-[10px] font-mono text-white/60 truncate">0x96E0...bA24</span>
                        </div>
                        <span className={`px-2 py-0.5 text-[8px] rounded ${pnlTotal >= 0 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'} uppercase`}>
                            {pnlTotal >= 0 ? 'Profitable' : 'Slightly Unprofitable'}
                        </span>
                    </div>

                    {/* Account Value */}
                    <SidebarSection title="Account Value">
                        <div className="text-xl font-bold text-white">${equity.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                    </SidebarSection>

                    {/* Account Equity */}
                    <SidebarSection title="Account Equity">
                        <MetricRow label="PERPS" value={`$${equity.toFixed(2)}`} />
                        <MetricRow label="SPOT" value="$0.00" valueColor="text-white/40" />
                    </SidebarSection>

                    {/* Perps Overview */}
                    <SidebarSection title="Perps Overview">
                        <MetricRow
                            label="UNREALIZED PNL"
                            value={`${unrealizedPnl >= 0 ? '+' : ''}$${unrealizedPnl.toFixed(2)}`}
                            valueColor={unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}
                        />
                        <MetricRow label="MARGIN USAGE" value={`${marginUsage.toFixed(2)}%`} />
                        <MetricRow
                            label="ALL TIME PNL"
                            value={`${pnlTotal >= 0 ? '+' : ''}$${pnlTotal.toFixed(2)}`}
                            valueColor={pnlTotal >= 0 ? 'text-green-400' : 'text-red-400'}
                        />
                        <MetricRow label="VOLUME" value={`$${volume.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} />
                    </SidebarSection>

                    {/* Execution Profile */}
                    <SidebarSection title="Execution Profile" collapsible>
                        <MetricRow label="TRADING STYLE" value="Intraday" />
                        <MetricRow label="AVG DURATION" value={formatDuration(avgDuration)} />
                    </SidebarSection>

                    {/* Performance */}
                    <SidebarSection title="Performance" collapsible>
                        <MetricRow label="WIN RATE" value={`${winRate.toFixed(0)}%`} />
                        <MetricRow label="DRAWDOWN" value="0%" />
                    </SidebarSection>
                </div>

                {/* Center - Chart Area - 7 cols */}
                <div className="col-span-7 flex flex-col border-r border-white/5">

                    {/* Chart Header */}
                    <div className="flex items-center justify-between p-3 border-b border-white/5">
                        <div className="flex items-center gap-3">
                            <div className="flex gap-1">
                                <button className="px-2 py-1 text-[10px] bg-white/10 text-white rounded">PNL</button>
                                <button className="px-2 py-1 text-[10px] text-white/40 hover:text-white transition">CALENDAR</button>
                            </div>
                            <div className="flex gap-1">
                                <button className="px-2 py-1 text-[10px] bg-white/5 text-white/60 rounded">PERPS</button>
                                <button className="px-2 py-1 text-[10px] text-white/40 hover:text-white transition">COMBINED</button>
                            </div>
                        </div>
                        <div className="flex gap-1 p-0.5 rounded bg-white/5">
                            {periods.map(p => (
                                <button
                                    key={p.key}
                                    onClick={() => p.key !== 'VALUE' && setPeriod(p.key as '24H' | '7D' | '30D' | 'ALL')}
                                    className={`px-2 py-1 rounded text-[10px] font-medium transition-all ${(p.key === 'VALUE' || period === p.key)
                                        ? 'bg-white/10 text-white'
                                        : 'text-white/40 hover:text-white'
                                        }`}
                                >
                                    {p.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Chart */}
                    <div className="flex-1 p-4 min-h-[300px]">
                        <EquityChart
                            data={chartData}
                            isLoading={isLoading}
                            pnlValue={currentPnl}
                            pnlPeriod={period}
                        />
                    </div>

                    {/* Bottom Tabs */}
                    <div className="border-t border-white/5">
                        <div className="flex items-center gap-1 p-2 border-b border-white/5 overflow-x-auto">
                            {tabs.map(tab => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveTab(tab)}
                                    className={`px-2 py-1 text-[9px] font-medium whitespace-nowrap transition-all rounded ${activeTab === tab
                                        ? 'bg-white/10 text-white'
                                        : 'text-white/40 hover:text-white'
                                        }`}
                                >
                                    {tab}
                                    {tab === 'POSITIONS' && positions.length > 0 && (
                                        <span className="ml-1 px-1 text-[8px] bg-primary/20 text-primary rounded">{positions.length}</span>
                                    )}
                                </button>
                            ))}
                        </div>

                        {/* Tab Content */}
                        <div className="p-2 max-h-[150px] overflow-y-auto">
                            {activeTab === 'POSITIONS' && (
                                positions.length > 0 ? (
                                    <table className="w-full text-[10px]">
                                        <thead>
                                            <tr className="text-white/40 border-b border-white/5">
                                                <th className="text-left py-1.5 font-medium">ASSET</th>
                                                <th className="text-right py-1.5 font-medium">SIZE</th>
                                                <th className="text-right py-1.5 font-medium">LEV</th>
                                                <th className="text-right py-1.5 font-medium">VALUE</th>
                                                <th className="text-right py-1.5 font-medium">ENTRY</th>
                                                <th className="text-right py-1.5 font-medium">MARK</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {positions.map((pos, idx) => (
                                                <tr key={idx} className="border-b border-white/5">
                                                    <td className="py-1.5">
                                                        <div className="flex items-center gap-1.5">
                                                            <div className="w-4 h-4 rounded-full bg-gradient-to-br from-orange-500 to-yellow-500 flex items-center justify-center text-[7px] font-bold">
                                                                {pos.symbol.substring(0, 2)}
                                                            </div>
                                                            <span className="font-medium text-white">{pos.symbol}</span>
                                                            <span className={`text-[8px] px-1 rounded ${pos.side === 'LONG' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                                                {pos.side}
                                                            </span>
                                                        </div>
                                                    </td>
                                                    <td className="py-1.5 text-right text-white/60">{pos.size.toFixed(4)}</td>
                                                    <td className="py-1.5 text-right text-yellow-400 font-medium">{pos.leverage || 20}x</td>
                                                    <td className="py-1.5 text-right text-white/60">${(pos.size * pos.mark_price).toFixed(2)}</td>
                                                    <td className="py-1.5 text-right text-white/60">${pos.entry_price.toFixed(2)}</td>
                                                    <td className="py-1.5 text-right text-white/60">${pos.mark_price.toFixed(2)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                ) : (
                                    <div className="text-center py-6 text-white/30 text-xs">No active positions</div>
                                )
                            )}
                            {activeTab === 'FILLS' && (
                                recentFills.length > 0 ? (
                                    <div className="space-y-1">
                                        {recentFills.slice(0, 5).map((fill, idx) => (
                                            <div key={idx} className="flex items-center justify-between py-1 border-b border-white/5">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-white font-medium">{fill.symbol}</span>
                                                    <span className={`text-[8px] px-1 rounded ${fill.side === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                                        {fill.side.toUpperCase()}
                                                    </span>
                                                </div>
                                                <span className={`${(fill.closed_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                    {fill.closed_pnl ? `${fill.closed_pnl >= 0 ? '+' : ''}$${fill.closed_pnl.toFixed(2)}` : `$${fill.price.toFixed(2)}`}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-6 text-white/30 text-xs">No recent fills</div>
                                )
                            )}
                            {activeTab === 'ORDERS' && (
                                openOrders.length > 0 ? (
                                    <table className="w-full text-[10px]">
                                        <thead>
                                            <tr className="text-white/40 border-b border-white/5">
                                                <th className="text-left py-1.5 font-medium">ASSET</th>
                                                <th className="text-right py-1.5 font-medium">TYPE</th>
                                                <th className="text-right py-1.5 font-medium">SIDE</th>
                                                <th className="text-right py-1.5 font-medium">SIZE</th>
                                                <th className="text-right py-1.5 font-medium">PRICE</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {openOrders.slice(0, 5).map((order, idx) => (
                                                <tr key={idx} className="border-b border-white/5">
                                                    <td className="py-1.5 text-white font-medium">{order.symbol}</td>
                                                    <td className="py-1.5 text-right text-white/60">{order.type}</td>
                                                    <td className="py-1.5 text-right">
                                                        <span className={`text-[8px] px-1 rounded ${order.side === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                                            {order.side.toUpperCase()}
                                                        </span>
                                                    </td>
                                                    <td className="py-1.5 text-right text-white/60">{order.size}</td>
                                                    <td className="py-1.5 text-right text-white/60">${order.price.toFixed(2)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                ) : (
                                    <div className="text-center py-6 text-white/30 text-xs">No open orders</div>
                                )
                            )}
                            {activeTab === 'BALANCES' && (
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between py-2 border-b border-white/5">
                                        <span className="text-white font-medium">Account Equity</span>
                                        <span className="text-green-400 font-bold">${equity.toFixed(2)}</span>
                                    </div>
                                    <div className="flex items-center justify-between py-2 border-b border-white/5">
                                        <span className="text-white/60">Unrealized PnL</span>
                                        <span className={unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}>${unrealizedPnl.toFixed(2)}</span>
                                    </div>
                                    <div className="flex items-center justify-between py-2 border-b border-white/5">
                                        <span className="text-white/60">Margin Used</span>
                                        <span className="text-yellow-400">{(marginUsage * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="flex items-center justify-between py-2">
                                        <span className="text-white/60">Available Balance</span>
                                        <span className="text-white">${(equity * (1 - marginUsage)).toFixed(2)}</span>
                                    </div>
                                </div>
                            )}
                            {(activeTab !== 'POSITIONS' && activeTab !== 'FILLS' && activeTab !== 'ORDERS' && activeTab !== 'BALANCES') && (
                                <div className="text-center py-6 text-white/30 text-xs">No data</div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Sidebar - Recent Activity / AI Strategy - 3 cols */}
                <div className="col-span-3 bg-[#080808] flex flex-col">
                    {/* Tabs */}
                    <div className="flex border-b border-white/5">
                        <button
                            onClick={() => setRightTab('BEST_TRADES')}
                            className={`flex-1 px-3 py-2.5 text-[10px] font-medium transition-all ${rightTab === 'BEST_TRADES' ? 'text-white border-b-2 border-primary' : 'text-white/40 hover:text-white'}`}
                        >
                            📊 Recent Activity
                        </button>
                        <button
                            onClick={() => setRightTab('AI_STRATEGY')}
                            className={`flex-1 px-3 py-2.5 text-[10px] font-medium transition-all ${rightTab === 'AI_STRATEGY' ? 'text-white border-b-2 border-primary' : 'text-white/40 hover:text-white'}`}
                        >
                            🤖 AI Strategy
                        </button>
                    </div>

                    {/* Content */}
                    <div className="flex-1 overflow-y-auto p-3">
                        {rightTab === 'BEST_TRADES' && (
                            <div className="space-y-2">
                                <div className="flex items-center gap-2 mb-3">
                                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                    <span className="text-[10px] text-white/40 uppercase tracking-wider">Live Trade History</span>
                                </div>
                                {recentFills.length > 0 ? (
                                    recentFills.slice(0, 15).map((fill, idx) => (
                                        <div key={idx} className="p-2 rounded-lg bg-white/[0.02] border border-white/5 hover:border-white/10 transition-all">
                                            <div className="flex items-center justify-between mb-1">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-5 h-5 rounded-full bg-gradient-to-br from-orange-500 to-yellow-500 flex items-center justify-center text-[8px] font-bold">
                                                        {fill.symbol.substring(0, 2)}
                                                    </div>
                                                    <span className="text-xs font-medium text-white">{fill.symbol}</span>
                                                    <span className={`text-[9px] px-1.5 py-0.5 rounded ${fill.side === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                                        {fill.side === 'buy' ? 'Long' : 'Short'}
                                                    </span>
                                                </div>
                                                <span className={`text-xs font-bold ${(fill.closed_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                    {fill.closed_pnl ? `${fill.closed_pnl >= 0 ? '+' : ''}$${fill.closed_pnl.toFixed(2)}` : '--'}
                                                </span>
                                            </div>
                                            <div className="flex items-center justify-between text-[9px] text-white/40">
                                                <span>${fill.price.toFixed(2)} × {fill.size}</span>
                                                <span>{fill.timestamp ? new Date(fill.timestamp).toLocaleString() : '--'}</span>
                                            </div>
                                        </div>
                                    ))
                                ) : (
                                    <div className="text-center py-8 text-white/30 text-xs">No trade history</div>
                                )}
                            </div>
                        )}

                        {rightTab === 'AI_STRATEGY' && (
                            <div className="space-y-3">
                                {/* AI Status */}
                                <div className={`p-3 rounded-lg ${moodConfig[aiMood].bg} border border-white/5`}>
                                    <div className="flex items-center gap-2 mb-2">
                                        <BrainCircuit className="w-4 h-4 text-primary" />
                                        <span className="text-xs font-bold text-white">AI Strategy Core</span>
                                    </div>
                                    <div className="flex items-center justify-between">
                                        <span className={`text-xs ${moodConfig[aiMood].color}`}>{moodConfig[aiMood].label}</span>
                                        <span className="text-[10px] text-white/40">{sessionInfo?.session || 'Unknown Session'}</span>
                                    </div>
                                </div>

                                {/* Execution Logs */}
                                <div>
                                    <div className="flex items-center gap-2 mb-2">
                                        <Terminal className="w-3 h-3 text-white/40" />
                                        <span className="text-[10px] text-white/40 uppercase tracking-wider">Execution Logs</span>
                                    </div>
                                    <div className="space-y-2">
                                        {thoughts.length > 0 ? (
                                            thoughts.slice(0, 10).map((thought, idx) => (
                                                <div key={idx} className="p-2 rounded-lg bg-white/[0.02] border border-white/5">
                                                    <div className="flex items-start gap-2">
                                                        <span className="text-sm">{thought.emoji || '🤖'}</span>
                                                        <div className="flex-1 min-w-0">
                                                            <p className="text-[10px] text-white/80 line-clamp-2">{thought.summary}</p>
                                                            <div className="flex items-center gap-2 mt-1">
                                                                <span className="text-[9px] text-white/30">
                                                                    {new Date(thought.timestamp).toLocaleTimeString()}
                                                                </span>
                                                                <span className={`text-[9px] px-1 rounded ${thought.confidence >= 70 ? 'bg-green-500/20 text-green-400' : thought.confidence >= 40 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}`}>
                                                                    {thought.confidence}%
                                                                </span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            ))
                                        ) : (
                                            <div className="text-center py-6 text-white/30 text-xs">No recent thoughts</div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
