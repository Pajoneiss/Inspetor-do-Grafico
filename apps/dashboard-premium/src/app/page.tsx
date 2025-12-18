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
  BrainCircuit
} from "lucide-react";
import { cn } from "@/lib/utils";

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

const StatCard = ({ title, value, sub, icon: Icon, trend }: { title: string; value: string; sub: string; icon: any; trend?: "up" | "down" }) => (
  <GlassCard className="flex flex-col gap-2">
    <div className="flex justify-between items-start">
      <div className="p-2.5 rounded-2xl bg-white/5 border border-white/10">
        <Icon className="w-5 h-5 text-primary" />
      </div>
      {trend && (
        <span className={cn(
          "px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wider",
          trend === "up" ? "bg-primary/20 text-primary" : "bg-secondary/20 text-secondary"
        )}>
          {trend === "up" ? "+" : "-"}{sub}
        </span>
      )}
    </div>
    <div className="mt-4">
      <p className="text-muted-foreground text-xs font-semibold tracking-widest uppercase">{title}</p>
      <h3 className="text-2xl font-bold tracking-tight mt-1">{value}</h3>
      {!trend && <p className="text-muted-foreground text-[10px] mt-1">{sub}</p>}
    </div>
  </GlassCard>
);

// --- Main Page ---

export default function Dashboard() {
  const [mounted, setMounted] = useState(false);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    setMounted(true);
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  if (!mounted) return null;

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
              <span className="flex items-center gap-2 text-primary">
                <span className="w-2 h-2 rounded-full bg-primary animate-pulse neon-glow" />
                System Live
              </span>
              <span className="text-muted-foreground">/</span>
              <span className="flex items-center gap-2 text-white/50">
                <Activity className="w-3 h-3" />
                98.4% Efficiency
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex flex-col items-end mr-4">
              <span className="text-[10px] text-muted-foreground tracking-widest uppercase font-bold">Server Time</span>
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
                <p className="text-xs font-bold">0x742d...424</p>
              </div>
            </div>
          </div>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <StatCard title="Total Equity" value="$28.84" sub="4.2%" trend="up" icon={Wallet} />
          <StatCard title="Unrealized PnL" value="+$0.33" sub="1.15%" trend="up" icon={Activity} />
          <StatCard title="Buying Power" value="$186.42" sub="Max Leverage: 20x" icon={Shield} />
          <StatCard title="Active Fleet" value="1 Symbol" sub="SOL Perpetuals" icon={Target} />
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
                <h3 className="text-xl font-bold tracking-tight">Portfolio Performance</h3>
              </div>
              <div className="flex gap-1 p-1 bg-white/5 rounded-xl border border-white/10">
                {['1H', '4H', '1D', '1W'].map(f => (
                  <button key={f} className={cn("px-3 py-1 rounded-lg text-[10px] font-bold tracking-tighter transition-all", f === '1D' ? "bg-white/10 text-white" : "text-muted-foreground hover:text-white")}>
                    {f}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex-1 flex items-center justify-center text-muted-foreground/20 italic font-mono uppercase tracking-[0.2em]">
              <div className="relative w-full h-full min-h-[200px] flex flex-col items-center justify-center">
                {/* Visual Placeholder for a liquid chart */}
                <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-primary/10 to-transparent rounded-b-[32px]" />
                <svg className="w-full h-40 text-primary/30" viewBox="0 0 1000 100" preserveAspectRatio="none">
                  <path d="M0,80 Q150,20 300,50 T600,30 T1000,10" fill="none" stroke="currentColor" strokeWidth="2" />
                </svg>
                <span className="relative z-10 text-xs font-bold tracking-[0.5em] mt-8">Establishing Data Stream...</span>
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
              {[
                { time: '2m ago', emoji: '🧐', text: 'Analyzing SOL structure on 15m. Identifying support at $122.50.', conf: '88%' },
                { time: '14m ago', emoji: '⚖️', text: 'Momentum steady. Maintaining LONG position. Target set at $128.', conf: '92%' },
                { time: '1h ago', emoji: '🚀', text: 'Bullish breakout confirmed on 1h timeframe. Opening SOL LONG.', conf: '84%' },
              ].map((thought, i) => (
                <div key={i} className="flex gap-4 group">
                  <div className="flex flex-col items-center">
                    <div className="w-8 h-8 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-lg">{thought.emoji}</div>
                    {i !== 2 && <div className="w-px flex-1 bg-white/10 my-2" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{thought.time}</span>
                      <span className="px-1.5 py-0.5 rounded-md bg-purple-500/10 text-purple-400 text-[8px] font-bold tracking-wider">CONF: {thought.conf}</span>
                    </div>
                    <p className="text-sm text-white/80 leading-relaxed font-medium group-hover:text-white transition-colors">{thought.text}</p>
                  </div>
                </div>
              ))}
            </div>

            <button className="mt-8 w-full py-4 rounded-2xl bg-primary/10 border border-primary/20 text-primary font-bold text-xs uppercase tracking-widest hover:bg-primary/20 hover:neon-glow transition-all flex items-center justify-center gap-2">
              View Strategy Graph <ChevronRight className="w-4 h-4" />
            </button>
          </GlassCard>
        </div>

        {/* Footer info */}
        <footer className="mt-12 pt-8 border-t border-white/5 flex justify-between items-center text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
          <div className="flex gap-8">
            <span>Hyperliquid API: <span className="text-primary">Connected</span></span>
            <span>OpenAI gpt-4o-mini: <span className="text-primary">Operational</span></span>
          </div>
          <div>© 2025 Ladder Labs</div>
        </footer>
      </main>
    </div>
  );
}
