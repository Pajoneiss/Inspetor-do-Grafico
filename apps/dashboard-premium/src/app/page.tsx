"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Zap,
  Activity,
  Shield,
  Target,
  Terminal,
  ChevronRight,
  Wallet,
  Cpu,
  Globe,
  Bell,
  Settings,
  LayoutDashboard,
  BarChart3,
  ListFilter,
  BrainCircuit,
  RefreshCcw
} from "lucide-react";
import { cn } from "@/lib/utils";

// --- Types ---
interface DashboardData {
  equity: number;
  unrealized_pnl: number;
  buying_power: number;
  positions_count: number;
  margin_usage: number;
  last_update: string;
}

interface Position {
  symbol: string;
  side: string;
  size: number;
  entry_price: number;
  mark_price: number;
  unrealized_pnl: number;
}

interface AIThought {
  timestamp: string;
  emoji?: string;
  summary: string;
  confidence: number;
  actions?: any[];
}

// --- Components ---

const GlassCard = ({ children, className, delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.6, delay, ease: [0.23, 1, 0.32, 1] }}
    className={cn("glass-card rounded-[32px] p-6 overflow-hidden relative group", className)}
  >
    {children}
  </motion.div>
);

const StatCard = ({ title, value, sub, icon: Icon, trend }: { title: string; value: string; sub: string; icon: any; trend?: "up" | "down" | "neutral" }) => (
  <GlassCard className="flex flex-col gap-2">
    <div className="flex justify-between items-start">
      <div className="p-2.5 rounded-2xl bg-white/5 border border-white/10">
        <Icon className="w-5 h-5 text-primary" />
      </div>
      {trend && trend !== "neutral" && (
        <span className={cn(
          "px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider",
          trend === "up" ? "bg-primary/20 text-primary" : "bg-secondary/20 text-secondary"
        )}>
          {sub}
        </span>
      )}
    </div>
    <div className="mt-4">
      <p className="text-muted-foreground text-xs font-semibold tracking-widest uppercase">{title}</p>
      <h3 className="text-2xl font-bold tracking-tight mt-1">{value}</h3>
      <p className="text-muted-foreground text-[10px] mt-1">{trend === "neutral" ? sub : "Current Metric"}</p>
    </div>
  </GlassCard>
);

const MarketBar = ({ data }: { data: any }) => {
  if (!data || !data.macro) return null;
  const { macro } = data;
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-wrap items-center gap-6 mb-8 px-6 py-3.5 rounded-2xl bg-white/[0.03] border border-white/5 text-[10px] font-bold uppercase tracking-widest overflow-x-auto no-scrollbar"
    >
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-muted-foreground/50">S&P 500</span>
        <span className="text-primary">{macro.sp500 && macro.sp500 !== "N/A" ? Number(macro.sp500).toLocaleString() : '---'}</span>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-muted-foreground/50">NASDAQ</span>
        <span className="text-primary">{macro.nasdaq && macro.nasdaq !== "N/A" ? Number(macro.nasdaq).toLocaleString() : '---'}</span>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-muted-foreground/50">DXY</span>
        <span className="text-blue-400">{macro.dxy || '---'}</span>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-muted-foreground/50">USD/BRL</span>
        <span className="text-green-400">{macro.usd_brl ? `R$ ${Number(macro.usd_brl).toFixed(2)}` : '---'}</span>
      </div>
      <div className="h-4 w-px bg-white/10" />
      <div className="flex items-center gap-2 shrink-0">
        <span className="text-muted-foreground/50">F&G</span>
        <span className={cn(
          "px-2 py-0.5 rounded text-black",
          Number(data.fear_greed) > 70 ? "bg-primary" : Number(data.fear_greed) < 30 ? "bg-secondary" : "bg-yellow-400"
        )}>
          {data.fear_greed || '---'}
        </span>
      </div>
    </motion.div>
  );
};

// --- Error Boundary ---
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(error: any, errorInfo: any) { console.error("UI Crash:", error, errorInfo); }
  render() {
    if (this.state.hasError) {
      return (
        <div className="h-screen flex flex-col items-center justify-center bg-black text-white p-10 text-center">
          <div className="w-20 h-20 rounded-full bg-secondary/20 flex items-center justify-center mb-6">
            <Shield className="w-10 h-10 text-secondary" />
          </div>
          <h1 className="text-2xl font-bold mb-2 uppercase tracking-tighter">System Malfunction</h1>
          <p className="text-muted-foreground max-w-md mb-8">A client-side exception occurred. The neural link with the fleet has been interrupted.</p>
          <button
            onClick={() => window.location.reload()}
            className="px-8 py-4 rounded-2xl bg-primary text-black font-bold uppercase tracking-widest hover:neon-glow transition-all"
          >
            Re-initialize System
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function Dashboard() {
  return (
    <ErrorBoundary>
      <DashboardContent />
    </ErrorBoundary>
  );
}

function DashboardContent() {
  const [mounted, setMounted] = useState(false);
  const [time, setTime] = useState(new Date());
  const [status, setStatus] = useState<DashboardData | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [thoughts, setThoughts] = useState<AIThought[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [pnlData, setPnlData] = useState<any>(null);
  const [pnlHistory, setPnlHistory] = useState<any[]>([]);
  const [pnlPeriod, setPnlPeriod] = useState<'24H' | '7D' | '30D' | 'ALL'>('24H');

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

  const fetchData = async () => {
    if (!API_URL) return;

    try {
      const [statusRes, posRes, thoughtRes, pnlRes, historyRes] = await Promise.all([
        fetch(`${API_URL}/api/status`).then(r => r.json()),
        fetch(`${API_URL}/api/positions`).then(r => r.json()),
        fetch(`${API_URL}/api/ai/thoughts`).then(r => r.json()),
        fetch(`${API_URL}/api/pnl`).then(r => r.json()),
        fetch(`${API_URL}/api/pnl/history`).then(r => r.json())
      ]);

      if (statusRes.ok) setStatus(statusRes.data);
      if (posRes.ok) setPositions(posRes.data);
      if (thoughtRes.ok) setThoughts(thoughtRes.data);
      if (pnlRes.ok) setPnlData(pnlRes.data);
      if (historyRes.ok && Array.isArray(historyRes.data)) setPnlHistory(historyRes.data);

      setError(null);
    } catch (err) {
      console.error("Fetch error:", err);
      if (loading) setError("Failed to connect to Bot API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setMounted(true);
    fetchData();
    const timer = setInterval(() => setTime(new Date()), 1000);
    const apiTimer = setInterval(fetchData, 5000); // UI Refresh 5s
    return () => {
      clearInterval(timer);
      clearInterval(apiTimer);
    };
  }, []);

  if (!mounted) return null;

  const getConfidenceColor = (conf: number) => {
    if (conf >= 0.8) return "text-primary bg-primary/10";
    if (conf >= 0.5) return "text-yellow-400 bg-yellow-400/10";
    return "text-secondary bg-secondary/10";
  };

  return (
    <div className="flex h-screen overflow-hidden text-foreground">
      {/* Sidebar - Pro Design */}
      <aside className="w-20 lg:w-64 border-r border-white/5 flex flex-col items-center lg:items-start py-8 px-4 glass shrink-0">
        <div className="flex items-center gap-3 px-3 mb-12">
          <div className="w-10 h-10 rounded-2xl bg-primary flex items-center justify-center neon-glow">
            <Zap className="text-black w-6 h-6 fill-current" />
          </div>
          <div className="hidden lg:block">
            <h1 className="font-bold tracking-tight text-lg leading-tight uppercase">Ladder Labs</h1>
            <p className="text-[10px] text-muted-foreground tracking-widest uppercase font-bold opacity-50">Fleet Commander</p>
          </div>
        </div>

        <nav className="flex-1 w-full space-y-2">
          {[
            { id: 'overview', label: 'Overview', icon: LayoutDashboard },
            { id: 'analytics', label: 'Analytics', icon: BarChart3 },
            { id: 'fleet', label: 'Fleet Status', icon: Globe },
            { id: 'strategy', label: 'AI Strategy', icon: BrainCircuit },
            { id: 'logs', label: 'Execution Logs', icon: Terminal },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300 group",
                activeTab === item.id ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-white/5 hover:text-white"
              )}
            >
              <item.icon className={cn("w-5 h-5", activeTab === item.id && "neon-glow")} />
              <span className="hidden lg:block font-semibold text-sm">{item.label}</span>
              {activeTab === item.id && <motion.div layoutId="nav-pill" className="ml-auto w-1.5 h-1.5 rounded-full bg-primary neon-glow" />}
            </button>
          ))}
        </nav>

        <div className="w-full pt-8 mt-8 border-t border-white/5 space-y-2">
          <button className="w-full flex items-center gap-3 px-4 py-3 text-muted-foreground hover:text-white transition-colors">
            <Settings className="w-5 h-5" />
            <span className="hidden lg:block font-semibold text-sm">Settings</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto relative scroll-smooth p-6 lg:p-10">
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
          <div>
            <h2 className="text-3xl font-bold tracking-tight mb-2">Operational Dashboard</h2>
            <div className="flex items-center gap-4 text-xs font-bold uppercase tracking-widest">
              <span className={cn("flex items-center gap-2", error ? "text-secondary" : "text-primary")}>
                <span className={cn("w-2 h-2 rounded-full", error ? "bg-secondary" : "bg-primary animate-pulse neon-glow")} />
                {error ? "API Disconnected" : "System Live"}
              </span>
              <span className="text-muted-foreground">/</span>
              <span className="flex items-center gap-2 text-white/50">
                <Activity className="w-3 h-3" />
                {status ? `${status.margin_usage}% Margin Use` : "Fetching Data..."}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex flex-col items-end mr-4">
              <span className="text-[10px] text-muted-foreground tracking-widest uppercase font-bold">Local Time</span>
              <span className="text-sm font-mono tracking-tighter text-white/80">{time.toLocaleTimeString()}</span>
            </div>
            <button className="p-3 rounded-2xl bg-white/5 border border-white/10 hover:border-white/20 transition-all">
              <Bell className="w-5 h-5" />
            </button>
            <div className="h-10 w-px bg-white/10 mx-2" />
            <div className="flex items-center gap-3 bg-white/5 border border-white/10 rounded-2xl pl-1.5 pr-4 py-1.5 hover:border-primary/50 transition-all cursor-pointer">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-blue-500 flex items-center justify-center font-bold text-xs text-black">
                LB
              </div>
              <div className="hidden lg:block">
                <p className="text-[10px] font-bold tracking-widest uppercase opacity-50 leading-none mb-1">Commander</p>
                <p className="text-xs font-bold">Trading Mode: LIVE</p>
              </div>
            </div>
          </div>
        </header>

        {/* Content Views */}
        <AnimatePresence mode="wait">
          {activeTab === 'overview' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <MarketBar data={(status as any)?.market_data} />

              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
                <StatCard
                  title="Total Equity"
                  value={status?.equity !== undefined ? `$${Number(status.equity).toFixed(2)}` : "---"}
                  sub="Update Live"
                  trend="neutral"
                  icon={Wallet}
                />
                <StatCard
                  title="Unrealized PnL"
                  value={status?.unrealized_pnl !== undefined ? `${status.unrealized_pnl >= 0 ? '+' : ''}$${Number(status.unrealized_pnl).toFixed(2)}` : "---"}
                  sub={status?.equity ? `${((Number(status.unrealized_pnl || 0) / Number(status.equity)) * 100).toFixed(2)}%` : "---"}
                  trend={status && (status.unrealized_pnl || 0) >= 0 ? "up" : "down"}
                  icon={Activity}
                />
                <StatCard
                  title="Fear & Greed"
                  value={(status as any)?.market_data?.fear_greed || "---"}
                  sub={Number((status as any)?.market_data?.fear_greed) > 50 ? "Bullish" : "Bearish"}
                  trend={Number((status as any)?.market_data?.fear_greed) > 50 ? "up" : "down"}
                  icon={Zap}
                />
                <StatCard
                  title="Market Cap"
                  value={(status as any)?.market_data?.market_cap ? `$${((status as any).market_data.market_cap / 1e12).toFixed(2)}T` : "---"}
                  sub="Crypto Global"
                  trend="neutral"
                  icon={Globe}
                />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Chart Card */}
                <GlassCard className="lg:col-span-1 min-h-[440px] flex flex-col" delay={0.2}>
                  <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                      <div className="p-2 rounded-xl bg-primary/20 text-primary">
                        <BarChart3 className="w-5 h-5" />
                      </div>
                      <h3 className="text-xl font-bold tracking-tight">Active Positions</h3>
                    </div>
                  </div>

                  <div className="flex-1">
                    {positions?.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center opacity-20">
                        <LayoutDashboard className="w-12 h-12 mb-4" />
                        <p className="text-xs font-bold uppercase tracking-widest">No active positions</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {(positions || []).map((pos, idx) => (
                          <div key={idx} className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/[0.08] transition-all">
                            <div className="flex items-center gap-4">
                              <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center font-bold text-xs", pos.side === 'LONG' ? "bg-primary/20 text-primary" : "bg-secondary/20 text-secondary")}>
                                {(pos.symbol || "??").substring(0, 2)}
                              </div>
                              <div>
                                <p className="text-sm font-bold tracking-tight">{pos.symbol || "Unknown"}</p>
                                <p className={cn("text-[10px] font-bold uppercase tracking-widest", pos.side === 'LONG' ? "text-primary" : "text-secondary")}>{(pos.side || "").toUpperCase()} {pos.size || 0}x</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-sm font-bold tracking-tight">${Number(pos.entry_price || 0).toFixed(2)}</p>
                              <p className={cn("text-xs font-bold", (pos.unrealized_pnl || 0) >= 0 ? "text-primary" : "text-secondary")}>
                                {(pos.unrealized_pnl || 0) >= 0 ? '+' : ''}{Number(pos.unrealized_pnl || 0).toFixed(2)}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </GlassCard>

                {/* PNL Chart Card */}
                <GlassCard className="lg:col-span-1 min-h-[440px] flex flex-col" delay={0.25}>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <div className="p-2 rounded-xl bg-primary/20 text-primary">
                        <Activity className="w-5 h-5" />
                      </div>
                      <h3 className="text-xl font-bold tracking-tight">PnL Performance</h3>
                    </div>
                    <div className="flex gap-1">
                      {(['24H', '7D', '30D', 'ALL'] as const).map(period => (
                        <button
                          key={period}
                          onClick={() => setPnlPeriod(period)}
                          className={cn(
                            "px-2.5 py-1 rounded-lg text-[9px] font-bold uppercase tracking-wider transition-all",
                            pnlPeriod === period
                              ? "bg-primary text-black"
                              : "bg-white/5 text-muted-foreground hover:bg-white/10"
                          )}
                        >
                          {period}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* PNL Summary */}
                  <div className="text-center mb-4">
                    <p className={cn("text-3xl font-bold", (pnlData?.[`pnl_${pnlPeriod.toLowerCase()}`] || pnlData?.pnl_24h || 0) >= 0 ? "text-primary neon-glow" : "text-secondary")}>
                      {(pnlData?.[`pnl_${pnlPeriod.toLowerCase()}`] || pnlData?.pnl_24h || 0) >= 0 ? '+' : ''}${(pnlData?.[`pnl_${pnlPeriod.toLowerCase()}`] || pnlData?.pnl_24h || 0).toFixed(2)}
                    </p>
                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mt-1">Realized PnL ({pnlPeriod})</p>
                  </div>

                  {/* Chart */}
                  <div className="flex-1 w-full overflow-hidden px-2">
                    {pnlHistory?.length > 0 ? (
                      <svg width="100%" height="100%" viewBox="0 0 100 40" preserveAspectRatio="none">
                        <defs>
                          <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#00ff9d" stopOpacity="0.3" />
                            <stop offset="100%" stopColor="#00ff9d" stopOpacity="0" />
                          </linearGradient>
                        </defs>
                        <motion.path
                          d={`M 0 40 ${pnlHistory.map((p: any, i: number) => {
                            const x = (i / (pnlHistory.length - 1)) * 100;
                            const minVal = Math.min(...pnlHistory.map((d: any) => d.value));
                            const maxVal = Math.max(...pnlHistory.map((d: any) => d.value));
                            const range = maxVal - minVal || 1;
                            const y = 35 - ((p.value - minVal) / range) * 30;
                            return `L ${x} ${y}`;
                          }).join(' ')} L 100 40 Z`}
                          fill="url(#chartGradient)"
                        />
                        <motion.path
                          d={`M ${pnlHistory.map((p: any, i: number) => {
                            const x = (i / (pnlHistory.length - 1)) * 100;
                            const minVal = Math.min(...pnlHistory.map((d: any) => d.value));
                            const maxVal = Math.max(...pnlHistory.map((d: any) => d.value));
                            const range = maxVal - minVal || 1;
                            const y = 35 - ((p.value - minVal) / range) * 30;
                            return `${x} ${y}`;
                          }).join(' L ')}`}
                          fill="none"
                          stroke="#00ff9d"
                          strokeWidth="0.8"
                          initial={{ pathLength: 0 }}
                          animate={{ pathLength: 1 }}
                          transition={{ duration: 1.5 }}
                          className="neon-glow"
                        />
                      </svg>
                    ) : (
                      <div className="h-full flex items-center justify-center opacity-20 italic text-sm">
                        Waiting for history data...
                      </div>
                    )}
                  </div>

                  {/* Stats Row */}
                  <div className="grid grid-cols-3 gap-2 pt-4 border-t border-white/5 mt-4">
                    <div className="text-center">
                      <p className="text-[9px] font-bold text-muted-foreground uppercase">24H</p>
                      <p className={cn("text-sm font-bold", (pnlData?.pnl_24h || 0) >= 0 ? "text-primary" : "text-secondary")}>
                        {(pnlData?.pnl_24h || 0) >= 0 ? '+' : ''}${(pnlData?.pnl_24h || 0).toFixed(2)}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-[9px] font-bold text-muted-foreground uppercase">7D</p>
                      <p className={cn("text-sm font-bold", (pnlData?.pnl_7d || 0) >= 0 ? "text-primary" : "text-secondary")}>
                        {(pnlData?.pnl_7d || 0) >= 0 ? '+' : ''}${(pnlData?.pnl_7d || 0).toFixed(2)}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-[9px] font-bold text-muted-foreground uppercase">30D</p>
                      <p className={cn("text-sm font-bold", (pnlData?.pnl_30d || 0) >= 0 ? "text-primary" : "text-secondary")}>
                        {(pnlData?.pnl_30d || 0) >= 0 ? '+' : ''}${(pnlData?.pnl_30d || 0).toFixed(2)}
                      </p>
                    </div>
                  </div>
                </GlassCard>

                {/* AI Thinking Feed */}
                <GlassCard className="flex flex-col" delay={0.3}>
                  <div className="flex items-center gap-4 mb-8">
                    <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400">
                      <BrainCircuit className="w-5 h-5" />
                    </div>
                    <h3 className="text-xl font-bold tracking-tight">AI Strategy Core</h3>
                  </div>

                  <div className="flex-1 space-y-6">
                    {thoughts?.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center opacity-20">
                        <BrainCircuit className="w-12 h-12 mb-4 animate-pulse" />
                        <p className="text-xs font-bold uppercase tracking-widest">Syncing AI Feed...</p>
                      </div>
                    ) : (
                      (thoughts || []).slice(0, 5).map((thought, i) => (
                        <div key={i} className="flex gap-4 group">
                          <div className="flex flex-col items-center">
                            <div className="w-8 h-8 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-lg">{thought.emoji || '🧐'}</div>
                            {i !== Math.min((thoughts || []).length, 5) - 1 && <div className="w-px flex-1 bg-white/10 my-2" />}
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                                {thought.timestamp ? new Date(thought.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "--:--"}
                              </span>
                              <span className={cn("px-1.5 py-0.5 rounded-md text-[8px] font-bold tracking-wider", getConfidenceColor(thought.confidence || 0))}>
                                CONF: {((thought.confidence || 0) * 100).toFixed(0)}%
                              </span>
                            </div>
                            <p className="text-sm text-white/80 leading-relaxed font-medium group-hover:text-white transition-colors">{thought.summary || "No summary"}</p>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </GlassCard>
              </div>
            </motion.div>
          )}

          {activeTab === 'analytics' && (
            <motion.div key="analytics" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
              <GlassCard className="mb-10 min-h-[500px] flex flex-col border border-white/5 bg-white/[0.02]">
                <div className="flex items-center justify-between mb-10">
                  <div className="flex items-center gap-4">
                    <div className="p-3 rounded-2xl bg-primary/20 text-primary neon-glow">
                      <BarChart3 className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold tracking-tight">Portfolio Analytics</h3>
                      <p className="text-xs text-muted-foreground font-bold uppercase tracking-widest mt-1">Equity & PnL History</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {['24H', '7D', '30D', 'ALL'].map(t => (
                      <button key={t} className={cn("px-4 py-1.5 rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all", t === '24H' ? "bg-primary text-black" : "bg-white/5 text-muted-foreground hover:bg-white/10")}>
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex-1 flex flex-col items-center justify-center relative py-12">
                  <div className="text-center">
                    <p className="text-4xl font-bold text-primary neon-glow mb-2">
                      {pnlData?.pnl_24h >= 0 ? '+' : ''}${pnlData?.pnl_24h?.toFixed(2) || '0.00'}
                    </p>
                    <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">PnL Realizado (24h)</p>
                  </div>

                  {/* Real-time Dynamic Sparkline */}
                  <div className="w-full h-48 mt-12 overflow-hidden px-4">
                    {pnlData?.length > 0 ? (
                      <svg width="100%" height="100%" viewBox="0 0 100 20" preserveAspectRatio="none">
                        <motion.path
                          d={`M ${pnlData.map((p: any, i: number) => {
                            const x = (i / (pnlData.length - 1)) * 100;
                            const minVal = Math.min(...pnlData.map((d: any) => d.value));
                            const maxVal = Math.max(...pnlData.map((d: any) => d.value));
                            const range = maxVal - minVal || 1;
                            const y = 20 - ((p.value - minVal) / range) * 15 - 2;
                            return `${x} ${y}`;
                          }).join(' L ')}`}
                          fill="none"
                          stroke="#00ff9d"
                          strokeWidth="0.8"
                          initial={{ pathLength: 0 }}
                          animate={{ pathLength: 1 }}
                          transition={{ duration: 1.5 }}
                          className="neon-glow"
                        />
                      </svg>
                    ) : (
                      <div className="h-full flex items-center justify-center opacity-20 italic text-sm">Waiting for history snapshots...</div>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-6 pt-10 border-t border-white/5">
                  <div className="text-center">
                    <p className="text-sm font-bold text-white/50 uppercase tracking-widest mb-1">Win Rate</p>
                    <p className="text-xl font-bold">--%</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-bold text-white/50 uppercase tracking-widest mb-1">Total Trades</p>
                    <p className="text-xl font-bold">{pnlData?.trades_24h || 0}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-bold text-white/50 uppercase tracking-widest mb-1">Profit Factor</p>
                    <p className="text-xl font-bold">--</p>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          )}

          {activeTab === 'fleet' && (
            <motion.div key="fleet" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
              <GlassCard className="min-h-[600px] border border-white/5">
                <div className="flex items-center gap-4 mb-10">
                  <div className="p-3 rounded-2xl bg-blue-500/20 text-blue-400">
                    <Globe className="w-6 h-6" />
                  </div>
                  <h3 className="text-2xl font-bold tracking-tight">Fleet Intelligence</h3>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {((status as any)?.market_data?.top_symbols || []).map((sym: string) => {
                    const brief = (status as any)?.market_data?.symbol_briefs?.[sym] || {};
                    const score = brief.score || 50;
                    const trend = brief.trend || "Neutral";
                    return (
                      <div key={sym} className="p-6 rounded-3xl bg-white/5 border border-white/5 hover:border-primary/20 transition-all group">
                        <div className="flex justify-between items-start mb-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-2xl bg-white/5 flex items-center justify-center font-bold">{sym.substring(0, 2)}</div>
                            <div>
                              <h4 className="font-bold">{sym}</h4>
                              <p className="text-[8px] font-bold text-muted-foreground uppercase opacity-50 tracking-tighter">Market Score: {score}</p>
                            </div>
                          </div>
                          <div className={cn(
                            "px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider",
                            score > 70 ? "bg-primary/10 text-primary" : score < 40 ? "bg-secondary/10 text-secondary" : "bg-yellow-400/10 text-yellow-400"
                          )}>
                            {trend}
                          </div>
                        </div>
                        <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${score}%` }}
                            className={cn("h-full neon-glow", score > 50 ? "bg-primary" : "bg-secondary")}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </GlassCard>
            </motion.div>
          )}

          {activeTab === 'strategy' && (
            <motion.div key="strategy" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <GlassCard className="min-h-[600px] border border-white/5">
                  <div className="flex items-center gap-4 mb-10">
                    <div className="p-3 rounded-2xl bg-purple-500/20 text-purple-400">
                      <BrainCircuit className="w-6 h-6" />
                    </div>
                    <h3 className="text-2xl font-bold tracking-tight">AI Strategy Core</h3>
                  </div>
                  <div className="space-y-8">
                    {(thoughts || []).map((thought, i) => (
                      <div key={i} className="flex gap-6">
                        <div className="flex flex-col items-center">
                          <div className="w-10 h-10 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-xl shadow-xl">{thought.emoji || '🧐'}</div>
                          {i !== thoughts.length - 1 && <div className="w-px flex-1 bg-white/10 my-3" />}
                        </div>
                        <div className="pt-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-xs font-bold text-muted-foreground">{new Date(thought.timestamp).toLocaleString()}</span>
                            <span className={cn("px-2 py-0.5 rounded-lg text-[8px] font-bold tracking-widest uppercase", getConfidenceColor(thought.confidence))}>CONF {(thought.confidence * 100).toFixed(0)}%</span>
                          </div>
                          <p className="text-white/80 leading-relaxed font-medium">{thought.summary}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </GlassCard>
                <GlassCard className="border border-white/5">
                  <div className="flex items-center gap-4 mb-10">
                    <div className="p-3 rounded-2xl bg-secondary/20 text-secondary">
                      <Shield className="w-6 h-6" />
                    </div>
                    <h3 className="text-2xl font-bold tracking-tight">Risk Parameters</h3>
                  </div>
                  <div className="space-y-6">
                    {[
                      { label: 'Max Leverage', value: '40x', status: 'Active' },
                      { label: 'Isolation Mode', value: 'Enabled', status: 'Operational' },
                      { label: 'Max Drawdown', value: '2.5%', status: 'Hard Limit' },
                      { label: 'Min Notional', value: '$10.00', status: 'Live' }
                    ].map(p => (
                      <div key={p.label} className="p-5 rounded-3xl bg-white/5 flex justify-between items-center">
                        <div>
                          <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{p.label}</p>
                          <p className="text-lg font-bold mt-1">{p.value}</p>
                        </div>
                        <span className="px-3 py-1 rounded-full bg-white/5 text-[8px] font-bold uppercase tracking-widest text-primary">{p.status}</span>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              </div>
            </motion.div>
          )}

          {activeTab === 'logs' && (
            <motion.div key="logs" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }}>
              <GlassCard className="min-h-[600px] bg-black/60 border border-white/5 font-mono">
                <div className="flex items-center gap-4 mb-10">
                  <div className="p-3 rounded-2xl bg-white/10 text-white">
                    <Terminal className="w-6 h-6" />
                  </div>
                  <h3 className="text-2xl font-bold tracking-tight">Execution Stream</h3>
                </div>
                <div className="space-y-3 h-[450px] overflow-y-auto no-scrollbar">
                  {thoughts?.length > 0 ? (
                    thoughts.map((thought, i) => (
                      <div key={i} className="text-xs border-b border-white/5 pb-2">
                        <span className="text-muted-foreground mr-3">[{new Date(thought.timestamp).toLocaleTimeString()}]</span>
                        <span className="text-primary mr-2">[{thought.emoji || '🤖'}]</span>
                        <span className="text-white/80">{thought.summary}</span>
                        <span className="ml-2 px-1 rounded bg-white/5 text-[8px] text-muted-foreground">CONF {(thought.confidence * 100).toFixed(0)}%</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-secondary/70 italic text-center py-20">Monitoring secure neural link...</div>
                  )}
                </div>
              </GlassCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer info */}
        <footer className="mt-12 pt-8 border-t border-white/5 flex justify-between items-center text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
          <div className="flex gap-8">
            <span>Hyperliquid API: <span className={cn(error ? "text-secondary" : "text-primary")}>{error ? "Offline" : "Connected"}</span></span>
            <span>OpenAI gpt-4o-mini: <span className="text-primary">Operational</span></span>
          </div>
          <div>© 2025 Ladder Labs</div>
        </footer>
      </main>
    </div>
  );
}
