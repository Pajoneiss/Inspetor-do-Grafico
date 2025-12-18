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

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

  const fetchData = async () => {
    if (!API_URL) {
      setError("API URL not configured (NEXT_PUBLIC_API_URL)");
      return;
    }

    try {
      const [statusRes, posRes, thoughtRes] = await Promise.all([
        fetch(`${API_URL}/api/status`).then(r => r.json()),
        fetch(`${API_URL}/api/positions`).then(r => r.json()),
        fetch(`${API_URL}/api/ai/thoughts`).then(r => r.json())
      ]);

      if (statusRes.ok) setStatus(statusRes.data);
      if (posRes.ok) setPositions(posRes.data);
      if (thoughtRes.ok) setThoughts(thoughtRes.data);

      setError(null);
    } catch (err) {
      console.error("Fetch error:", err);
      // Don't set error on background refreshes unless first load
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
            { id: 'overview', label: 'Overview', icon: LayoutDashboard, active: true },
            { id: 'analytics', label: 'Analytics', icon: BarChart3 },
            { id: 'fleet', label: 'Fleet Status', icon: Globe },
            { id: 'strategy', label: 'AI Strategy', icon: BrainCircuit },
            { id: 'logs', label: 'Execution Logs', icon: Terminal },
          ].map((item) => (
            <button
              key={item.id}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300 group",
                item.active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-white/5 hover:text-white"
              )}
            >
              <item.icon className={cn("w-5 h-5", item.active && "neon-glow")} />
              <span className="hidden lg:block font-semibold text-sm">{item.label}</span>
              {item.active && <motion.div layoutId="nav-pill" className="ml-auto w-1.5 h-1.5 rounded-full bg-primary neon-glow" />}
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
            title="Buying Power"
            value={status?.buying_power !== undefined ? `$${Number(status.buying_power).toFixed(0)}` : "---"}
            sub={`Usage: ${status?.margin_usage || 0}%`}
            icon={Shield}
          />
          <StatCard
            title="Active Fleet"
            value={status?.positions_count !== undefined ? `${status.positions_count} Symbols` : "---"}
            sub={positions?.length > 0 ? (positions || []).map(p => p.symbol).join(', ') : "No positions"}
            icon={Target}
          />
        </div>

        {/* Dynamic Center Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Chart Card */}
          <GlassCard className="lg:col-span-2 min-h-[440px] flex flex-col" delay={0.2}>
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-4">
                <div className="p-2 rounded-xl bg-primary/20 text-primary">
                  <BarChart3 className="w-5 h-5" />
                </div>
                <h3 className="text-xl font-bold tracking-tight">Active Positions</h3>
              </div>
            </div>

            <div className="flex-1">
              {positions.length === 0 ? (
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

            <button className="mt-8 w-full py-4 rounded-2xl bg-primary/10 border border-primary/20 text-primary font-bold text-xs uppercase tracking-widest hover:bg-primary/20 hover:neon-glow transition-all flex items-center justify-center gap-2">
              Refresh Feed <RefreshCcw className="w-4 h-4" />
            </button>
          </GlassCard>
        </div>

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
