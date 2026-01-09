
"use client";

import React, { useMemo } from "react";
import {
    Wallet, Activity, Globe, ArrowUpRight, ArrowDownRight, LayoutDashboard,
    BrainCircuit, Target, CheckCircle, Clock, ChevronLeft, ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { DashboardData } from "@/app/page";

// --- Types ---
interface Position {
    symbol: string;
    side: string;
    size: number;
    entry_price: number;
    mark_price: number;
    unrealized_pnl: number;
    leverage?: number;
    stop_loss?: number;
    take_profit?: number;
    margin_used?: number;
}

interface TradeLog {
    id: string;
    symbol: string;
    side: string;
    entry_price: number;
    confidence?: number;
    strategy: {
        name: string;
        timeframe: string;
        confluence_factors: string[];
    };
    entry_rationale: string;
    risk_management: {
        stop_loss: number;
        stop_loss_reason: string;
        take_profit_1: number;
        tp1_reason: string;
        take_profit_2: number;
        tp2_reason: string;
        risk_usd: number;
        risk_pct: number;
        tp1_size_pct?: number;
        tp2_size_pct?: number;
    };
    ai_notes: string;
    timestamp?: string;
}

interface AIThought {
    timestamp: string;
    thought?: string;
    summary?: string;
    confidence?: number;
    actions?: string[];
}
interface FullAnalytics {
    history: Array<{ time: string | number; value: number }>;
    pnl_24h?: number;
    pnl_total?: number;
}

interface UnifiedOverviewProps {
    status: DashboardData | null;
    history: { time: string | number; value: number }[];
    period: '24H' | '7D' | '30D' | 'ALL';
    setPeriod: (p: '24H' | '7D' | '30D' | 'ALL') => void;
    journalStats: { win_rate?: number; total_trades?: number } | null;
    sessionInfo: { session?: string; current_time_utc?: string; is_weekend?: boolean } | null;
    isPt: boolean;
    isLoading: boolean;
    positions: Position[];
    tradeLog: TradeLog | null;
    _trade_logs: TradeLog[];
    setTradeLog: (log: TradeLog | null) => void;
    aiNotesLang: 'pt' | 'en';
    setAiNotesLang: (lang: 'pt' | 'en') => void;
    aiMood: 'aggressive' | 'defensive' | 'observing';
    thoughts: AIThought[];
    setViewAllModalOpen: (open: boolean) => void;
    // Phase 1: Hyperliquid Analytics Integration
    fullAnalytics?: FullAnalytics | null;
    pnlPeriod?: '24H' | '7D' | '30D' | 'ALL';
    setPnlPeriod?: (p: '24H' | '7D' | '30D' | 'ALL') => void;
}

// --- Helper Components ---

const getSmoothPath = (points: { x: number; y: number }[]) => {
    if (!points || points.length < 2) return "";

    let d = `M ${points[0].x} ${points[0].y}`;

    for (let i = 0; i < points.length - 1; i++) {
        const p0 = i > 0 ? points[i - 1] : points[0];
        const p1 = points[i];
        const p2 = points[i + 1];
        const p3 = i != points.length - 2 ? points[i + 2] : p2;

        const cp1x = p1.x + (p2.x - p0.x) / 6;
        const cp1y = p1.y + (p2.y - p0.y) / 6;
        const cp2x = p2.x - (p3.x - p1.x) / 6;
        const cp2y = p2.y - (p3.y - p1.y) / 6;

        d += ` C ${cp1x} ${cp1y} ${cp2x} ${cp2y} ${p2.x} ${p2.y}`;
    }
    return d;
};

const StatValue = ({ value, label, sub, trend = 'neutral', icon: Icon, loading }: { value: string; label: string; sub: string; trend?: 'up' | 'down' | 'neutral'; icon: React.ElementType; loading: boolean }) => (
    <div className="flex flex-col gap-1 z-10">
        <div className="flex items-center gap-2 mb-1">
            <div className={cn("p-1.5 rounded-lg", trend === 'up' ? "bg-primary/10 text-primary" : trend === 'down' ? "bg-secondary/10 text-secondary" : "bg-white/5 text-white/60")}>
                <Icon className="w-4 h-4" />
            </div>
            <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">{label}</span>
        </div>
        {loading ? (
            <div className="h-8 w-24 bg-white/5 rounded animate-pulse" />
        ) : (
            <div className="flex items-baseline gap-2">
                <h3 className="text-2xl font-bold tracking-tight">{value}</h3>
            </div>
        )}
        <div className="flex items-center gap-1.5">
            {trend !== 'neutral' && (
                <div className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1",
                    trend === 'up' ? "bg-primary/10 text-primary" : "bg-secondary/10 text-secondary")}>
                    {trend === 'up' ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                    {sub}
                </div>
            )}
            {trend === 'neutral' && <span className="text-[10px] font-medium text-white/40">{sub}</span>}
        </div>
    </div>
);

export default function UnifiedOverviewCard({
    status, history, period, setPeriod, journalStats, sessionInfo, isPt, isLoading, positions,
    tradeLog, _trade_logs, setTradeLog, aiNotesLang, setAiNotesLang, aiMood, thoughts, setViewAllModalOpen,
    fullAnalytics, pnlPeriod, setPnlPeriod
}: UnifiedOverviewProps) {

    // Calculate total unrealized PnL from open positions
    const unrealizedPnl = useMemo(() => {
        try {
            return positions.reduce((sum, pos) => sum + (pos.unrealized_pnl || 0), 0);
        } catch {
            return 0;
        }
    }, [positions]);

    // Safely calculate PnL (realized from history + unrealized from open positions)
    const pnlValue = useMemo(() => {
        try {
            let realizedPnl = 0;
            if (history && history.length > 1 && history[0]?.value !== undefined && history[history.length - 1]?.value !== undefined) {
                const start = Number(history[0].value);
                const end = Number(history[history.length - 1].value);
                if (!isNaN(start) && !isNaN(end)) {
                    realizedPnl = end - start;
                }
            } else {
                realizedPnl = Number(status?.pnl_24h || 0);
            }
            // Add unrealized PnL for complete picture
            return realizedPnl + unrealizedPnl;
        } catch (error) {
            console.error("PnL Calc error:", error);
            return unrealizedPnl; // At least show unrealized if calculation fails
        }
    }, [history, status, unrealizedPnl]);

    const pnlPercent = useMemo(() => {
        try {
            const equity = Number(status?.equity || 1);
            if (equity === 0) return "0.00";
            return ((pnlValue / equity) * 100).toFixed(2);
        } catch {
            return "0.00";
        }
    }, [pnlValue, status]);

    // Chart Logic
    const chartPath = useMemo(() => {
        if (!history || history.length < 2) return "";

        try {
            const points = history.map((pt, i) => ({
                x: (i / (history.length - 1)) * 100,
                y: Number(pt.value)
            })).filter(p => !isNaN(p.y));

            if (points.length < 2) return "";

            const values = points.map(p => p.y);
            const min = Math.min(...values);
            const max = Math.max(...values);
            const range = max - min || 1;

            const normalizedPoints = points.map(p => ({
                x: p.x * 8, // scale width
                y: max === min ? 75 : 150 - ((p.y - min) / range) * 120 // Center if flat, else scale
            }));

            return getSmoothPath(normalizedPoints);
        } catch {
            return "";
        }
    }, [history]);

    // AI Confidence Color Helper
    const getConfidenceColor = (conf: number) => {
        if (conf >= 0.8) return "text-primary bg-primary/10";
        if (conf >= 0.5) return "text-yellow-400 bg-yellow-400/10";
        return "text-secondary bg-secondary/10";
    };

    // Win Rate Logic
    const winRate = Number(journalStats?.win_rate || 0);
    const winRateColor = winRate >= 50 ? "#00ff9d" : "#ef4444";
    const circumference = 2 * Math.PI * 18;
    const offset = circumference - (Math.min(100, Math.max(0, winRate)) / 100) * circumference;

    return (
        <div className="col-span-1 lg:col-span-full xl:col-span-3 relative overflow-hidden rounded-[32px] bg-[#0a0a0a] border border-white/5 shadow-2xl group transition-all duration-300 hover:border-white/10">
            {/* Background Ambience */}
            <div className={cn(
                "absolute top-0 right-0 w-[500px] h-[500px] bg-gradient-to-br opacity-10 blur-[100px] rounded-full mix-blend-screen pointer-events-none transition-colors duration-1000",
                pnlValue >= 0 ? "from-primary/30 to-blue-500/20" : "from-red-500/30 to-orange-500/20"
            )} />

            {/* Grid Pattern */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

            <div className="relative z-10 p-6 lg:p-8">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 backdrop-blur-md">
                            <Globe className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                            <span className="text-[10px] font-bold tracking-widest uppercase text-white/80">
                                {sessionInfo?.session || 'MARKET'} SESSION
                            </span>
                            <span className="w-1 h-1 rounded-full bg-white/20" />
                            <span className="text-[10px] font-mono text-white/40">
                                {sessionInfo?.current_time_utc ?
                                    (sessionInfo.current_time_utc.includes('T') ? sessionInfo.current_time_utc.split('T')[1].substring(0, 5) : sessionInfo.current_time_utc)
                                    : '--:--'} UTC
                            </span>
                        </div>
                    </div>

                    <div className="flex p-1 rounded-xl bg-white/5 border border-white/10 self-start md:self-auto">
                        {(['24H', '7D', '30D', 'ALL'] as const).map((p) => (
                            <button
                                key={p}
                                onClick={() => setPeriod(p)}
                                className={cn(
                                    "px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all duration-300",
                                    period === p
                                        ? "bg-white text-black shadow-[0_0_15px_rgba(255,255,255,0.3)]"
                                        : "text-white/40 hover:text-white hover:bg-white/5"
                                )}
                            >
                                {p}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12 mb-8">
                    <StatValue
                        label={isPt ? "Patrimônio Total" : "Total Equity"}
                        value={status?.equity ? `$${Number(status.equity).toLocaleString('en-US', { minimumFractionDigits: 2 })}` : "---"}
                        sub={isPt ? "Saldo disponível" : "Available Balance"}
                        trend="neutral"
                        icon={Wallet}
                        loading={isLoading}
                    />

                    <StatValue
                        label={isPt ? `PnL Total (${period})` : `Total PnL (${period})`}
                        value={!isNaN(pnlValue) ? `${pnlValue >= 0 ? '+' : ''}$${Math.abs(pnlValue).toFixed(2)}` : "---"}
                        sub={positions.length > 0
                            ? (isPt ? `${pnlValue >= 0 ? '+' : ''}${pnlPercent}% • incl. ${positions.length} aberta${positions.length > 1 ? 's' : ''}`
                                : `${pnlValue >= 0 ? '+' : ''}${pnlPercent}% • incl. ${positions.length} open`)
                            : `${pnlValue >= 0 ? '+' : ''}${pnlPercent}%`}
                        trend={pnlValue >= 0 ? "up" : "down"}
                        icon={Activity}
                        loading={isLoading}
                    />

                    <div className="relative flex items-center gap-4">
                        <div className="relative w-12 h-12">
                            <svg className="w-full h-full transform -rotate-90">
                                <circle cx="24" cy="24" r="18" stroke="currentColor" strokeWidth="4" fill="none" className="text-white/5" />
                                <circle
                                    cx="24" cy="24" r="18" stroke={winRateColor} strokeWidth="4" fill="none" strokeLinecap="round"
                                    strokeDasharray={circumference}
                                    strokeDashoffset={isNaN(offset) ? circumference : offset}
                                    className={cn("transition-all duration-1000", winRateColor === '#00ff9d' ? "shadow-[#00ff9d]" : "shadow-red-500")}
                                    style={{ filter: `drop-shadow(0 0 4px ${winRateColor})` }}
                                />
                            </svg>
                        </div>
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">{isPt ? "Taxa de Vitória" : "Win Rate"}</p>
                            <h3 className="text-2xl font-bold tracking-tight">{!isNaN(winRate) ? winRate.toFixed(1) : '0.0'}%</h3>
                            <p className="text-[9px] text-white/40 font-medium">{journalStats?.total_trades || 0} Trades</p>
                        </div>
                    </div>
                </div>

                {/* Chart Area */}
                <div className="relative h-[200px] w-full mt-4">
                    {history && history.length > 1 ? (
                        <svg width="100%" height="100%" viewBox="0 0 800 150" className="overflow-visible" preserveAspectRatio="none">
                            <defs>
                                <linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor={pnlValue >= 0 ? "#00ff9d" : "#ef4444"} stopOpacity="0.2" />
                                    <stop offset="100%" stopColor={pnlValue >= 0 ? "#00ff9d" : "#ef4444"} stopOpacity="0" />
                                </linearGradient>
                                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                                    <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                                    <feMerge>
                                        <feMergeNode in="coloredBlur" />
                                        <feMergeNode in="SourceGraphic" />
                                    </feMerge>
                                </filter>
                            </defs>

                            {chartPath && (
                                <path
                                    d={`${chartPath} L 800 150 L 0 150 Z`}
                                    fill="url(#chartFill)"
                                    className="transition-all duration-500"
                                />
                            )}

                            {chartPath && (
                                <path
                                    d={chartPath}
                                    fill="none"
                                    stroke={pnlValue >= 0 ? "#00ff9d" : "#ef4444"}
                                    strokeWidth="3"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    filter="url(#glow)"
                                    className="transition-all duration-500"
                                />
                            )}
                        </svg>
                    ) : (
                        <div className="h-full flex items-center justify-center opacity-30">
                            <p className="text-xs font-bold uppercase tracking-widest animate-pulse">Loading Chart Data...</p>
                        </div>
                    )}
                    <div className="absolute bottom-0 left-0 right-0 flex justify-between px-2 text-[10px] font-bold text-white/20 uppercase tracking-widest">
                        <span>{history?.[0]?.time || ''}</span>
                        <span>{history?.[Math.floor((history?.length || 0) / 2)]?.time || ''}</span>
                        <span>{history?.[(history?.length || 0) - 1]?.time || 'NOW'}</span>
                    </div>
                </div>
            </div>

            {/* Active Positions Section */}
            <div className="mt-8 pt-8 border-t border-white/5">
                <div className="flex items-center gap-4 mb-6">
                    <div className="p-2 rounded-xl bg-primary/20 text-primary">
                        <Activity className="w-5 h-5" />
                    </div>
                    <h3 className="text-xl font-bold tracking-tight">{isPt ? "Posições Ativas" : "Active Positions"}</h3>
                </div>

                {positions && positions.length > 0 ? (
                    <div className="space-y-4">
                        {positions.map((pos, idx) => (
                            <div key={idx} className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/[0.08] transition-all group/item">
                                <div className="flex items-center gap-4">
                                    <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center font-bold text-xs transition-colors",
                                        pos.side === 'LONG' ? "bg-primary/20 text-primary group-hover/item:bg-primary/30" : "bg-secondary/20 text-secondary group-hover/item:bg-secondary/30")}>
                                        {(pos.symbol || "??").substring(0, 2)}
                                    </div>
                                    <div>
                                        <p className="text-sm font-bold tracking-tight">{pos.symbol || "Unknown"}</p>
                                        <div className="flex items-center gap-2">
                                            <span className={cn("text-[10px] font-bold uppercase tracking-widest", pos.side === 'LONG' ? "text-primary" : "text-secondary")}>
                                                {(pos.side || "").toUpperCase()} {pos.leverage || 1}x
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm font-bold tracking-tight">${Number(pos.entry_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                                    <div className="flex items-center justify-end gap-1">
                                        <p className={cn("text-xs font-bold", (pos.unrealized_pnl || 0) >= 0 ? "text-primary" : "text-secondary")}>
                                            {(pos.unrealized_pnl || 0) >= 0 ? '+' : ''}{Number(pos.unrealized_pnl || 0).toFixed(2)}
                                        </p>
                                        {(pos.unrealized_pnl || 0) >= 0 ? <ArrowUpRight className="w-3 h-3 text-primary" /> : <ArrowDownRight className="w-3 h-3 text-secondary" />}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="py-12 flex flex-col items-center justify-center rounded-2xl border border-dashed border-white/5 bg-white/[0.01]">
                        <LayoutDashboard className="w-10 h-10 text-muted-foreground/20 mb-3" />
                        <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground/50">{isPt ? "Nenhuma posição ativa" : "No active positions"}</p>
                    </div>
                )}
            </div>

            {/* AI Strategy Core Section */}
            <div className="mt-8 pt-8 border-t border-white/5">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-4">
                        <div className="p-3 rounded-2xl bg-purple-500/20 text-purple-400 neon-glow">
                            <BrainCircuit className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold tracking-tight">{isPt ? "Núcleo de Estratégia de IA" : "AI Strategy Core"}</h3>
                            <div className="flex items-center gap-3 mt-1">
                                <span className={cn(
                                    "px-2 py-0.5 rounded-lg text-[10px] font-bold uppercase tracking-wider border",
                                    aiMood === 'aggressive' && "bg-green-500/20 text-green-400 border-green-500/30",
                                    aiMood === 'defensive' && "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
                                    aiMood === 'observing' && "bg-blue-500/20 text-blue-400 border-blue-500/30"
                                )}>
                                    {aiMood === 'aggressive' && (isPt ? '🚀 Agressivo' : '🚀 Aggressive')}
                                    {aiMood === 'defensive' && (isPt ? '🛡️ Defensivo' : '🛡️ Defensive')}
                                    {aiMood === 'observing' && (isPt ? '⏸️ Observando' : '⏸️ Observing')}
                                </span>
                                <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest">
                                    {tradeLog
                                        ? (_trade_logs && _trade_logs.length > 1 ? `${_trade_logs.findIndex((log: TradeLog) => log === tradeLog) + 1} of ${_trade_logs.length} Active` : 'Detailed Strategy Breakdown')
                                        : (isPt ? "Monitoramento de Mercado em Tempo Real" : "Real-time Market Monitoring")
                                    }
                                </p>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {/* Language Toggle */}
                        <div className="flex items-center gap-1 bg-white/5 p-1 rounded-lg border border-white/10 mr-2">
                            <button onClick={() => setAiNotesLang('pt')} className={cn("px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all", aiNotesLang === 'pt' ? "bg-green-500/20 text-green-400 border border-green-500/30" : "text-muted-foreground hover:text-white")}>🇧🇷 PT</button>
                            <button onClick={() => setAiNotesLang('en')} className={cn("px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all", aiNotesLang === 'en' ? "bg-blue-500/20 text-blue-400 border border-blue-500/30" : "text-muted-foreground hover:text-white")}>🇺🇸 EN</button>
                        </div>

                        {/* Navigation for multiple trades */}
                        {tradeLog && _trade_logs && _trade_logs.length > 1 && (
                            <>
                                <button
                                    onClick={() => {
                                        const currentIndex = _trade_logs.findIndex((log: TradeLog) => log === tradeLog);
                                        const prevIndex = currentIndex > 0 ? currentIndex - 1 : _trade_logs.length - 1;
                                        setTradeLog(_trade_logs[prevIndex]);
                                    }}
                                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-all"
                                >
                                    <ChevronLeft className="w-4 h-4" />
                                </button>
                                <button
                                    onClick={() => {
                                        const currentIndex = _trade_logs.findIndex((log: TradeLog) => log === tradeLog);
                                        const nextIndex = currentIndex < _trade_logs.length - 1 ? currentIndex + 1 : 0;
                                        setTradeLog(_trade_logs[nextIndex]);
                                    }}
                                    className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-all"
                                >
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </>
                        )}
                        <button
                            onClick={() => setViewAllModalOpen(true)}
                            className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-all text-xs font-bold uppercase tracking-wider"
                        >
                            {isPt ? "Histórico" : "History"}
                        </button>
                    </div>
                </div>

                {tradeLog ? (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in fade-in duration-500">
                        <div className="space-y-6">
                            {/* Trade Header */}
                            <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-purple-500/10 to-primary/10 border border-white/10">
                                <div className="flex items-center gap-4">
                                    <div className="w-12 h-12 rounded-lg bg-white/5 flex items-center justify-center font-bold text-lg border border-white/10">
                                        {tradeLog.symbol?.substring(0, 2)}
                                    </div>
                                    <div>
                                        <h4 className="text-xl font-bold">{tradeLog.symbol} <span className={cn("text-sm uppercase px-2 py-0.5 rounded ml-2", tradeLog.side === 'LONG' ? "bg-primary/20 text-primary" : "bg-secondary/20 text-secondary")}>{tradeLog.side}</span></h4>
                                        <p className="text-xs text-muted-foreground uppercase tracking-widest">Entry: ${tradeLog.entry_price?.toLocaleString()}</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Confidence</p>
                                    <p className="text-2xl font-bold text-primary">{((tradeLog.confidence || 0) * 100).toFixed(0)}%</p>
                                </div>
                            </div>

                            {/* Strategy Info */}
                            <div className="p-5 rounded-2xl bg-white/5 border border-white/5">
                                <div className="flex items-center gap-2 mb-3">
                                    <Target className="w-4 h-4 text-primary" />
                                    <h5 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">{isPt ? "Estratégia" : "Strategy"}</h5>
                                </div>
                                <p className="text-lg font-bold text-white mb-1">{tradeLog.strategy?.name || 'N/A'}</p>
                                <p className="text-sm text-white/60 mb-4">{tradeLog.entry_rationale || 'No rationale available.'}</p>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                    {tradeLog.strategy.confluence_factors.map((factor: string, i: number) => (
                                        <div
                                            key={i}
                                            className={cn(
                                                "flex items-start gap-2 p-2.5 rounded-xl border transition-all duration-300 hover:scale-[1.02]",
                                                i === 0
                                                    ? "bg-gradient-to-r from-primary/20 to-purple-500/10 border-primary/30 shadow-lg shadow-primary/5"
                                                    : "bg-white/5 border-white/5 hover:bg-white/10"
                                            )}
                                        >
                                            <div className={cn(
                                                "p-1 rounded-full",
                                                i === 0 ? "bg-primary/20 text-primary" : "bg-white/10 text-primary"
                                            )}>
                                                <CheckCircle className="w-3 h-3" />
                                            </div>
                                            <span className={cn(
                                                "text-[11px] font-medium leading-tight",
                                                i === 0 ? "text-white" : "text-white/70"
                                            )}>{factor}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="space-y-6">
                            {/* Risk Management */}
                            <div>
                                <div className="flex items-center gap-2 mb-3">
                                    <Activity className="w-4 h-4 text-secondary" />
                                    <h5 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">{isPt ? "Gestão de Risco" : "Risk Management"}</h5>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {/* Stop Loss */}
                                    <div className="p-3.5 rounded-2xl bg-secondary/10 border border-secondary/20 flex flex-col justify-between min-h-[100px] transition-all hover:bg-secondary/15">
                                        <div>
                                            <p className="text-[10px] font-extrabold text-secondary/70 uppercase tracking-[0.15em] mb-1">Stop Loss</p>
                                            <p className="text-xl font-bold text-secondary tracking-tight">${tradeLog.risk_management?.stop_loss?.toLocaleString() || '0'}</p>
                                        </div>
                                        <p className="text-[10px] font-medium text-white/40 mt-1">{tradeLog.risk_management?.stop_loss_reason || 'N/A'}</p>
                                    </div>

                                    {/* Take Profit 1 */}
                                    <div className="p-3.5 rounded-2xl bg-primary/10 border border-primary/20 flex flex-col justify-between min-h-[100px] transition-all hover:bg-primary/15">
                                        <div>
                                            <p className="text-[10px] font-extrabold text-primary/70 uppercase tracking-[0.15em] mb-1">Take Profit 1</p>
                                            <p className="text-xl font-bold text-primary tracking-tight">${tradeLog.risk_management?.take_profit_1?.toLocaleString() || '0'}</p>
                                        </div>
                                        <p className="text-[10px] font-medium text-white/40 mt-1">{tradeLog.risk_management?.tp1_reason || 'N/A'}</p>
                                    </div>

                                    {/* Risk */}
                                    <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10 flex flex-col justify-between min-h-[100px] transition-all hover:bg-white/10">
                                        <div>
                                            <p className="text-[10px] font-extrabold text-white/40 uppercase tracking-[0.15em] mb-1">{isPt ? "Risco" : "Risk"}</p>
                                            <p className="text-xl font-bold text-white tracking-tight">${tradeLog.risk_management?.risk_usd?.toFixed(2) || '0'}</p>
                                        </div>
                                        <p className="text-[10px] font-medium text-white/40 mt-1">{tradeLog.risk_management?.risk_pct?.toFixed(2) || '0'}%</p>
                                    </div>
                                </div>
                            </div>

                            {/* AI Notes - Bilingual */}
                            {tradeLog.ai_notes && (() => {
                                const notes = tradeLog.ai_notes;
                                let ptText = '';
                                let enText = '';

                                if (notes.includes('🇺🇸')) {
                                    [ptText, enText] = notes.split('🇺🇸').map((s: string) => s.replace('🇧🇷', '').trim());
                                } else if (notes.includes('Position Analysis')) {
                                    const idx = notes.indexOf('Position Analysis');
                                    ptText = notes.substring(0, idx).replace('🇧🇷', '').trim();
                                    enText = notes.substring(idx).trim();
                                } else {
                                    ptText = notes.replace('🇧🇷', '').trim();
                                    enText = ptText;
                                }

                                const displayText = aiNotesLang === 'pt' ? ptText : enText;

                                return (
                                    <div className="p-4 rounded-xl bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-500/20">
                                        <div className="flex items-center gap-2 mb-3">
                                            <BrainCircuit className="w-4 h-4 text-purple-400" />
                                            <p className="text-xs font-bold uppercase tracking-widest text-purple-300">AI Notes</p>
                                        </div>
                                        <p className="text-sm font-medium leading-relaxed text-white/90">
                                            {displayText}
                                        </p>
                                    </div>
                                );
                            })()}
                        </div>
                    </div>
                ) : (
                    // Detailed AI Insight View (No Active Trade)
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 h-full min-h-[300px] animate-in fade-in duration-500">
                        {/* Left: General Market Sentiment / Thoughts */}
                        <div className="md:col-span-2 space-y-6">
                            <div className="p-6 rounded-2xl bg-white/5 border border-white/5 h-full relative overflow-hidden">
                                <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 blur-[80px] rounded-full pointer-events-none" />
                                <div className="flex items-center gap-3 mb-4 relative z-10">
                                    <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
                                        <span className="text-xl">💭</span>
                                    </div>
                                    <div>
                                        <h4 className="text-lg font-bold text-white">{isPt ? "Insight de Mercado" : "Market Insight"}</h4>
                                        <p className="text-xs text-muted-foreground uppercase tracking-wider">{thoughts && thoughts.length > 0 ? "Latest AI Thought" : "System Status"}</p>
                                    </div>
                                </div>

                                <div className="relative z-10">
                                    {thoughts && thoughts.length > 0 ? (
                                        <div className="prose prose-invert prose-sm max-w-none">
                                            <p className="text-lg font-medium leading-relaxed text-white/90">
                                                &quot;{thoughts[0].thought || thoughts[0].summary}&quot;
                                            </p>
                                            <div className="flex items-center gap-4 mt-6 pt-6 border-t border-white/10">
                                                <div className="flex items-center gap-2">
                                                    <Clock className="w-4 h-4 text-white/40" />
                                                    <span className="text-xs font-bold text-white/40 uppercase tracking-widest">{new Date(thoughts[0].timestamp).toLocaleTimeString()}</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <div className={cn("w-2 h-2 rounded-full", getConfidenceColor(thoughts[0].confidence || 0).replace("text-", "bg-"))} />
                                                    <span className={cn("text-xs font-bold uppercase tracking-widest", getConfidenceColor(thoughts[0].confidence || 0))}>Confidence: {((thoughts[0].confidence || 0) * 100).toFixed(0)}%</span>
                                                </div>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center h-40 text-center">
                                            <BrainCircuit className="w-12 h-12 text-white/20 mb-4 animate-pulse" />
                                            <p className="text-sm text-white/40 font-medium">Analyzing market structure...</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Right: Operational Status / Next Steps */}
                        <div className="space-y-4">
                            <div className="p-5 rounded-2xl bg-white/5 border border-white/5 h-full flex flex-col justify-center relative">
                                <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/20 pointer-events-none" />
                                <h5 className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-4 text-center z-10">{isPt ? "Estado Operacional" : "Operational Status"}</h5>

                                <div className="flex flex-col items-center gap-4 z-10">
                                    <div className="relative">
                                        <div className={cn(
                                            "w-20 h-20 rounded-full flex items-center justify-center text-3xl shadow-2xl transition-all duration-1000",
                                            aiMood === 'aggressive' ? "bg-green-500/20 text-green-400 shadow-green-500/20" :
                                                aiMood === 'defensive' ? "bg-yellow-500/20 text-yellow-400 shadow-yellow-500/20" :
                                                    "bg-blue-500/20 text-blue-400 shadow-blue-500/20"
                                        )}>
                                            {aiMood === 'aggressive' ? "🚀" : aiMood === 'defensive' ? "🛡️" : "🔎"}
                                        </div>
                                        <div className={cn(
                                            "absolute inset-0 rounded-full animate-ping opacity-20",
                                            aiMood === 'aggressive' ? "bg-green-500" :
                                                aiMood === 'defensive' ? "bg-yellow-500" :
                                                    "bg-blue-500"
                                        )} />
                                    </div>

                                    <div className="text-center space-y-1">
                                        <p className="text-sm font-bold text-white">{aiMood === 'aggressive' ? "Seeking Opportunities" : (aiMood === 'defensive' ? "Protecting Capital" : "Monitoring Structure")}</p>
                                        <p className="text-xs text-white/40">Scanning for high-probability setups</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
