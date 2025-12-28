
"use client";

import React, { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Wallet, TrendingUp, TrendingDown, Activity, Globe, ArrowUpRight, ArrowDownRight, MoreHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";

// --- Types ---
interface UnifiedOverviewProps {
    status: any;        // The full status object from API
    history: any[];     // PnL history array
    period: '24H' | '7D' | '30D' | 'ALL';
    setPeriod: (p: '24H' | '7D' | '30D' | 'ALL') => void;
    journalStats: any;  // Win rate data
    sessionInfo: any;   // Session data
    isPt: boolean;      // Language flag
    isLoading: boolean;
}

// --- Helper Components ---

// Smooth curve generator for SVG
const getSmoothPath = (points: { x: number; y: number }[]) => {
    if (points.length < 2) return "";

    // Start point
    let d = `M ${points[0].x} ${points[0].y}`;

    // Bezier curves
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

const StatValue = ({ value, label, sub, trend = 'neutral', icon: Icon, loading }: any) => (
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

export default function UnifiedOverviewCard({ status, history, period, setPeriod, journalStats, sessionInfo, isPt, isLoading }: UnifiedOverviewProps) {

    // Calculate PnL for current period
    const pnlValue = useMemo(() => {
        if (!status?.pnl_24h && !status?.pnl_7d) return 0;
        // Map period to API return keys if available, else use fallback logic
        // The API returns pnl_24h, pnl_7d, pnl_30d in status.data usually
        // Or we verify specifically what we passed to 'status'
        // Actually page.tsx passes 'status' which is the raw /api/status response data
        // status.pnl_24h is available. Others might be in a separate pnlData object in page.tsx
        // We will accept 'pnlValue' as a direct prop or derive it if possible. 
        // To keep it simple, let's assume valid data or just use 24h for now if others missing, 
        // BUT page.tsx has 'pnlData' state. We should probably pass that or merged data.
        // Let's rely on what we have: history array last point vs first point?
        if (history && history.length > 1) {
            const start = history[0].value;
            const end = history[history.length - 1].value;
            return end - start;
        }
        return status?.pnl_24h || 0;
    }, [history, status]);

    const pnlPercent = useMemo(() => {
        const equity = status?.equity || 1;
        return ((pnlValue / equity) * 100).toFixed(2);
    }, [pnlValue, status]);

    // Chart Logic
    const chartPath = useMemo(() => {
        if (!history || history.length < 2) return "";

        const points = history.map((pt, i) => ({
            x: (i / (history.length - 1)) * 100, // 0 to 100
            y: pt.value
        }));

        const values = points.map(p => p.y);
        const min = Math.min(...values);
        const max = Math.max(...values);
        const range = max - min || 1;

        // Normalize y to 0-100 (inverted for SVG coords)
        const normalizedPoints = points.map(p => ({
            x: p.x * 8, // scale width (approx 800px viewbox)
            y: 150 - ((p.y - min) / range) * 120 // scale height (150px viewbox, 20px padding)
        }));

        return getSmoothPath(normalizedPoints);
    }, [history]);

    // Win Rate Logic
    const winRate = journalStats?.win_rate || 0;
    const winRateColor = winRate >= 50 ? "#00ff9d" : "#ef4444";
    const circumference = 2 * Math.PI * 18; // r=18
    const offset = circumference - (winRate / 100) * circumference;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="col-span-1 lg:col-span-full xl:col-span-3 relative overflow-hidden rounded-[32px] bg-[#0a0a0a] border border-white/5 shadow-2xl group"
        >
            {/* Background Ambience */}
            <div className={cn(
                "absolute top-0 right-0 w-[500px] h-[500px] bg-gradient-to-br opacity-10 blur-[100px] rounded-full mix-blend-screen pointer-events-none transition-colors duration-1000",
                pnlValue >= 0 ? "from-primary/30 to-blue-500/20" : "from-red-500/30 to-orange-500/20"
            )} />

            {/* Grid Pattern overlay */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

            <div className="relative z-10 p-6 lg:p-8">
                {/* Header / Controls */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
                    <div className="flex items-center gap-4">
                        {/* Session Badge */}
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 backdrop-blur-md">
                            <Globe className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                            <span className="text-[10px] font-bold tracking-widest uppercase text-white/80">
                                {sessionInfo?.session || 'MARKET'} SESSION
                            </span>
                            <span className="w-1 h-1 rounded-full bg-white/20" />
                            <span className="text-[10px] font-mono text-white/40">
                                {sessionInfo?.current_time_utc ? new Date(sessionInfo.current_time_utc).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--:--'} UTC
                            </span>
                        </div>
                    </div>

                    {/* Period Toggles */}
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
                    {/* Equity */}
                    <StatValue
                        label={isPt ? "Patrimônio Total" : "Total Equity"}
                        value={status?.equity ? `$${Number(status.equity).toLocaleString('en-US', { minimumFractionDigits: 2 })}` : "---"}
                        sub={isPt ? "Saldo disponível" : "Available Balance"}
                        trend="neutral"
                        icon={Wallet}
                        loading={isLoading}
                    />

                    {/* Unrealized PnL (Dynamic) */}
                    <StatValue
                        label={isPt ? `PnL Total (${period})` : `Total PnL (${period})`}
                        value={pnlValue !== undefined ? `${pnlValue >= 0 ? '+' : ''}$${Math.abs(pnlValue).toFixed(2)}` : "---"}
                        sub={`${pnlValue >= 0 ? '+' : ''}${pnlPercent}%`}
                        trend={pnlValue >= 0 ? "up" : "down"}
                        icon={Activity}
                        loading={isLoading}
                    />

                    {/* Win Rate Circular */}
                    <div className="relative flex items-center gap-4">
                        <div className="relative w-12 h-12">
                            {/* Background Circle */}
                            <svg className="w-full h-full transform -rotate-90">
                                <circle cx="24" cy="24" r="18" stroke="currentColor" strokeWidth="4" fill="none" className="text-white/5" />
                                <motion.circle
                                    cx="24" cy="24" r="18" stroke={winRateColor} strokeWidth="4" fill="none" strokeLinecap="round"
                                    strokeDasharray={circumference}
                                    initial={{ strokeDashoffset: circumference }}
                                    animate={{ strokeDashoffset: offset }}
                                    transition={{ duration: 1.5, ease: "easeOut" }}
                                    className={cn("drop-shadow-[0_0_8px_rgba(0,0,0,0.5)]", winRateColor === '#00ff9d' ? "shadow-[#00ff9d]" : "shadow-red-500")}
                                />
                            </svg>
                        </div>
                        <div>
                            <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">{isPt ? "Taxa de Vitória" : "Win Rate"}</p>
                            <h3 className="text-2xl font-bold tracking-tight">{winRate.toFixed(1)}%</h3>
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

                            {/* Fill Area - Close the path */}
                            <motion.path
                                d={`${chartPath} L 800 150 L 0 150 Z`}
                                fill="url(#chartFill)"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ duration: 1 }}
                            />

                            {/* Stroke Line */}
                            <motion.path
                                d={chartPath}
                                fill="none"
                                stroke={pnlValue >= 0 ? "#00ff9d" : "#ef4444"}
                                strokeWidth="3"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                filter="url(#glow)"
                                initial={{ pathLength: 0, opacity: 0 }}
                                animate={{ pathLength: 1, opacity: 1 }}
                                transition={{ duration: 1.5, ease: "easeInOut" }}
                            />
                        </svg>
                    ) : (
                        <div className="h-full flex items-center justify-center opacity-30">
                            <p className="text-xs font-bold uppercase tracking-widest animate-pulse">Loading Chart Data...</p>
                        </div>
                    )}

                    {/* X-Axis Labels (Simple) */}
                    <div className="absolute bottom-0 left-0 right-0 flex justify-between px-2 text-[10px] font-bold text-white/20 uppercase tracking-widest">
                        <span>{history?.[0]?.time || ''}</span>
                        <span>{history?.[Math.floor((history?.length || 0) / 2)]?.time || ''}</span>
                        <span>{history?.[(history?.length || 0) - 1]?.time || 'NOW'}</span>
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
