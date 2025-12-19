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
  ChevronDown,
  ChevronUp,
  Maximize2,
  Wallet,
  Cpu,
  Globe,
  Bell,
  Settings,
  LayoutDashboard,
  BarChart3,
  ListFilter,
  BrainCircuit,
  RefreshCcw,
  MessageSquare,
  Send,
  Menu,
  X,
  CheckCircle,
  LineChart,
  History,
  UserCircle,
  Grid,
  ShieldCheck,
  CandlestickChart
} from "lucide-react";
import { cn } from "@/lib/utils";
import SettingsModal from "@/components/SettingsModal";
import { useSettingsStandalone, Settings as SettingsType, defaultSettings } from "@/hooks/useSettings";

// --- Hooks ---
const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);
  return isMobile;
};

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

const GlassCard = ({ children, className, delay = 0, noPadding = false }: { children: React.ReactNode; className?: string; delay?: number; noPadding?: boolean }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.8, delay, ease: [0.23, 1, 0.32, 1] }}
    whileHover={{ y: -4, transition: { duration: 0.2 } }}
    className={cn(
      "glass-card rounded-[32px] overflow-hidden relative group transition-all duration-500",
      noPadding ? "" : "p-6",
      "hover:shadow-[0_20px_50px_-12px_rgba(0,0,0,0.5)] hover:border-white/20",
      className
    )}
  >
    {/* Animated Gradient Border on Hover */}
    <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
    <div className="relative z-10 h-full flex flex-col">{children}</div>
  </motion.div>
);

// New Collapsible Component for Mobile
const CollapsibleSection = ({ title, children, icon: Icon, isExpanded, onToggle, badge, className }: any) => {
  return (
    <div className={cn("flex flex-col h-full", className)}>
      <div
        className="flex items-center justify-between p-5 cursor-pointer lg:cursor-default"
        onClick={() => { if (window.innerWidth < 1024) onToggle(); }}
      >
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary/10 text-primary group-hover:bg-primary/20 transition-colors">
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold tracking-tight text-white">{title}</h3>
            {badge && <span className="inline-block px-1.5 py-0.5 rounded bg-primary/20 text-primary text-[8px] font-bold uppercase tracking-wider mt-0.5">{badge}</span>}
          </div>
        </div>
        <div className="lg:hidden p-2 rounded-lg bg-white/5">
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.3 }}
          >
            <ChevronDown className="w-4 h-4 text-white/50" />
          </motion.div>
        </div>
      </div>
      <AnimatePresence initial={false}>
        {(isExpanded || (typeof window !== 'undefined' && window.innerWidth >= 1024)) && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden flex-1"
          >
            <div className="px-5 pb-5 pt-0 h-full flex flex-col">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Mobile Accordion Card - iPhone folder style
const MobileAccordionCard = ({ title, icon: Icon, children, defaultOpen = false }: { title: string; icon: any; children: React.ReactNode; defaultOpen?: boolean }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <motion.div
      className="glass-card rounded-2xl overflow-hidden border border-white/10"
      layout
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-gradient-to-r from-white/5 to-transparent active:bg-white/10 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-primary/20">
            <Icon className="w-5 h-5 text-primary" />
          </div>
          <span className="text-sm font-bold text-white">{title}</span>
        </div>
        <motion.div animate={{ rotate: isOpen ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown className="w-5 h-5 text-white/40" />
        </motion.div>
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="p-4 pt-0">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

const StatCard = ({ title, value, sub, icon: Icon, trend }: { title: string; value: string; sub: string; icon: any; trend?: "up" | "down" | "neutral" }) => {
  const isMobile = useIsMobile();

  // Translate titles for beginners
  const displayTitle = title === "Equity" ? "Seu Patrimônio" :
    title === "Buying Power" ? "Poder de Compra" :
      title === "Open Positions" ? "Posições Ativas" : title;

  const content = (
    <>
      <div className="flex justify-between items-start">
        <div className="p-2 rounded-xl bg-white/5 border border-white/10 shadow-inner group-hover:bg-primary/10 transition-colors duration-500">
          <Icon className="w-4 h-4 text-primary group-hover:scale-110 transition-transform duration-500" />
        </div>
        {trend && trend !== "neutral" && (
          <div className="flex items-center gap-2">
            <Sparkline data={trend === "up" ? [10, 15, 12, 18, 20] : [20, 15, 18, 12, 10]} color={trend === "up" ? "#00ff9d" : "#ff3b30"} />
            <span className={cn(
              "px-2 py-0.5 rounded-full text-[9px] font-black tracking-widest uppercase",
              trend === "up" ? "bg-primary/20 text-primary" : "bg-secondary/20 text-secondary"
            )}>
              {sub}
            </span>
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-white/40 text-[10px] font-extrabold tracking-[0.2em] uppercase mb-1">{displayTitle}</p>
        <h3 className="text-2xl font-extrabold tracking-tighter text-white drop-shadow-md">{value}</h3>
        <p className="text-white/30 text-[9px] font-medium mt-1 uppercase tracking-widest">{trend === "neutral" ? sub : "Atualizado em tempo real"}</p>
      </div>
    </>
  );

  if (isMobile) {
    return (
      <MobileAccordionCard title={displayTitle} icon={Icon} defaultOpen={title === "Equity"}>
        {content}
      </MobileAccordionCard>
    );
  }

  return (
    <GlassCard className="flex flex-col gap-1.5">
      {content}
    </GlassCard>
  );
};


const Sparkline = ({ data, color = "#00ff9d" }: { data: number[]; color?: string }) => {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * 60;
    const y = 20 - ((d - min) / range) * 16 - 2;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width="60" height="20" viewBox="0 0 60 20" className="opacity-50">
      <polyline
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
};

const MarketBar = ({ data }: { data: any }) => {
  if (!data || !data.macro) return null;
  const { macro } = data;

  const items = [
    { label: "S&P 500", value: macro.sp500 && macro.sp500 !== "N/A" ? Number(macro.sp500).toLocaleString() : '---', color: "text-[#00ff9d]" },
    { label: "NASDAQ", value: macro.nasdaq && macro.nasdaq !== "N/A" ? Number(macro.nasdaq).toLocaleString() : '---', color: "text-[#00ff9d]" },
    { label: "DXY", value: macro.dxy || '---', color: "text-blue-400" },
    { label: "USD/BRL", value: macro.usd_brl ? `R$ ${Number(macro.usd_brl).toFixed(2)}` : '---', color: "text-green-400" },
    { label: "BTC", value: macro.btc || '---', color: "text-orange-400" },
    { label: "ETH", value: macro.eth || '---', color: "text-purple-400" },
  ];

  return (
    <div className="relative mb-8 overflow-hidden w-full py-4 border-y border-white/5 bg-gradient-to-r from-transparent via-white/5 to-transparent">
      <motion.div
        animate={{ x: [0, -1000] }}
        transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
        className="flex items-center gap-12 whitespace-nowrap"
      >
        {items.concat(items).concat(items).map((item, i) => (
          <div key={i} className="flex items-center gap-2.5">
            <span className="text-[10px] font-extrabold text-white/30 uppercase tracking-[0.2em]">{item.label}</span>
            <span className={cn("text-[11px] font-bold tracking-tight", item.color)}>{item.value}</span>
          </div>
        ))}
      </motion.div>
    </div>
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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [time, setTime] = useState(new Date());
  const [status, setStatus] = useState<DashboardData | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [thoughts, setThoughts] = useState<AIThought[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'analytics' | 'chat' | 'logs' | 'all' | 'charts'>('overview');
  const [activeFleetTab, setActiveFleetTab] = useState<'Asset Positions' | 'Open Orders' | 'Recent Fills' | 'Completed Trades' | 'TWAP' | 'Deposits & Withdrawals'>('Asset Positions');
  const [pnlData, setPnlData] = useState<any>(null);
  const [pnlHistory, setPnlHistory] = useState<any[]>([]);
  const [pnlPeriod, setPnlPeriod] = useState<'24H' | '7D' | '30D' | 'ALL'>('24H');
  const [chatMessages, setChatMessages] = useState<{ role: string, content: string }[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [tradeLog, setTradeLog] = useState<any>(null);
  const [fullAnalytics, setFullAnalytics] = useState<any>(null);
  const [openOrders, setOpenOrders] = useState<any[]>([]);
  const [recentFills, setRecentFills] = useState<any[]>([]);
  const [transfers, setTransfers] = useState<any[]>([]);
  const [cryptoPrices, setCryptoPrices] = useState<{ btc: any, eth: any } | null>(null);

  // --- UI Expanded/Modal States ---
  const [isTradeLogModalOpen, setIsTradeLogModalOpen] = useState(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isPositionsExpanded, setIsPositionsExpanded] = useState(true);
  const [isPnLExpanded, setIsPnLExpanded] = useState(true);
  const [isStrategyExpanded, setIsStrategyExpanded] = useState(true);
  const [isAnalysisExpanded, setIsAnalysisExpanded] = useState(true);

  // --- Settings Hook ---
  const { settings, updateSetting, resetSettings } = useSettingsStandalone();

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

  const fetchData = async () => {
    if (!API_URL) return;

    try {
      const [statusRes, posRes, thoughtRes, pnlRes, historyRes, tradeLogsRes, fullAnalyticsRes, ordersRes, fillsRes, transfersRes] = await Promise.all([
        fetch(`${API_URL}/api/status`).then(r => r.json()),
        fetch(`${API_URL}/api/positions`).then(r => r.json()),
        fetch(`${API_URL}/api/ai/thoughts`).then(r => r.json()),
        fetch(`${API_URL}/api/pnl`).then(r => r.json()),
        fetch(`${API_URL}/api/pnl/history`).then(r => r.json()),
        fetch(`${API_URL}/api/ai/trade-logs`).then(r => r.json()),
        fetch(`${API_URL}/api/analytics`).then(r => r.json()),
        fetch(`${API_URL}/api/orders`).then(r => r.json()).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/user/trades`).then(r => r.json()).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/transfers`).then(r => r.json()).catch(() => ({ ok: false }))
      ]);

      if (statusRes.ok) setStatus(statusRes.data);
      if (posRes.ok) setPositions(posRes.data);
      if (thoughtRes.ok) setThoughts(thoughtRes.data);
      if (pnlRes.ok) setPnlData(pnlRes.data);
      if (historyRes.ok && Array.isArray(historyRes.data)) setPnlHistory(historyRes.data);
      if (tradeLogsRes.ok && tradeLogsRes.data && tradeLogsRes.data.length > 0) setTradeLog(tradeLogsRes.data[0]);
      if (fullAnalyticsRes.ok) setFullAnalytics(fullAnalyticsRes.data);
      if (ordersRes.ok && Array.isArray(ordersRes.data)) setOpenOrders(ordersRes.data);
      if (fillsRes.ok && Array.isArray(fillsRes.data)) setRecentFills(fillsRes.data);
      if (transfersRes.ok && Array.isArray(transfersRes.data)) setTransfers(transfersRes.data);

      setError(null);
    } catch (err) {
      console.error("Fetch error:", err);
      if (loading) setError("Failed to connect to Bot API");
    } finally {
      setLoading(false);
    }
  };


  const sendChatMessage = async () => {
    if (!chatInput.trim() || chatLoading) return;

    const userMessage = chatInput.trim();
    setChatInput('');

    // Add user message
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setChatLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/ai/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userMessage })
      });

      const data = await response.json();

      if (data.ok) {
        setChatMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
      } else {
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: data.message || data.error || 'Failed to get response'
        }]);
      }
    } catch (err) {
      console.error('Chat error:', err);
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Failed to connect to AI. Please try again.'
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  useEffect(() => {
    setMounted(true);
    fetchData();

    // Fetch crypto prices separately
    const fetchCryptoPrices = async () => {
      if (!API_URL) return;
      try {
        const res = await fetch(`${API_URL}/api/crypto-prices`);
        const data = await res.json();
        if (data.ok) setCryptoPrices(data.data);
      } catch (err) {
        console.error("Crypto prices fetch error:", err);
      }
    };
    fetchCryptoPrices();

    const timer = setInterval(() => setTime(new Date()), 1000);
    const apiTimer = setInterval(fetchData, 5000); // UI Refresh 5s
    const cryptoTimer = setInterval(fetchCryptoPrices, 10000); // Crypto prices every 10s

    return () => {
      clearInterval(timer);
      clearInterval(apiTimer);
      clearInterval(cryptoTimer);
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
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-sm"
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed lg:relative z-50 h-full w-64 border-r border-white/5 flex flex-col items-start py-8 px-4 glass shrink-0 transition-transform duration-300",
        sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )}>
        <div className="flex items-center justify-between w-full px-3 mb-12">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-primary flex items-center justify-center neon-glow">
              <Zap className="text-black w-6 h-6 fill-current" />
            </div>
            <div>
              <h1 className="font-bold tracking-tight text-lg leading-tight uppercase">Ladder Labs</h1>
              <p className="text-[10px] text-muted-foreground tracking-widest uppercase font-bold opacity-50">Fleet Commander</p>
            </div>
          </div>
          {/* Close button for mobile */}
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 w-full space-y-2">
          {[
            { id: 'overview', label: 'Overview', icon: LayoutDashboard },
            { id: 'analytics', label: 'Analytics', icon: BarChart3 },
            { id: 'charts', label: 'Charts', icon: CandlestickChart },
            { id: 'all', label: 'All Indicators', icon: Grid },
            { id: 'chat', label: 'AI Chat', icon: MessageSquare },
            { id: 'logs', label: 'Execution Logs', icon: Terminal },
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => { setActiveTab(item.id as 'overview' | 'analytics' | 'chat' | 'logs' | 'all' | 'charts'); setSidebarOpen(false); }}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300 group",
                activeTab === item.id ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-white/5 hover:text-white"
              )}
            >
              <item.icon className={cn("w-5 h-5", activeTab === item.id && "neon-glow")} />
              <span className="font-semibold text-sm">{item.label}</span>
              {activeTab === item.id && <motion.div layoutId="nav-pill" className="ml-auto w-1.5 h-1.5 rounded-full bg-primary neon-glow" />}
            </button>
          ))}
        </nav>

        <div className="w-full pt-8 mt-8 border-t border-white/5 space-y-2">
          <button onClick={() => { setIsSettingsModalOpen(true); setSidebarOpen(false); }} className="w-full flex items-center gap-3 px-4 py-3 text-muted-foreground hover:text-white transition-colors">
            <Settings className="w-5 h-5" />
            <span className="font-semibold text-sm">Settings</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto relative scroll-smooth p-6 lg:p-10">
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-12">
          <div className="flex items-center gap-4">
            {/* Mobile hamburger button */}
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition-all"
            >
              <Menu className="w-6 h-6" />
            </button>
            <div>
              <h2 className="text-2xl lg:text-3xl font-bold tracking-tight mb-1">O Inspetor Do Gráfico</h2>
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
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden sm:flex flex-col items-end mr-4">
              <span className="text-[10px] text-muted-foreground tracking-widest uppercase font-bold">Local Time</span>
              <span className="text-sm font-mono tracking-tighter text-white/80">{time.toLocaleTimeString()}</span>
            </div>
            <motion.button
              className="p-3 rounded-2xl bg-white/5 border border-white/10 hover:border-white/20 transition-all"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <History className="w-5 h-5" />
            </motion.button>
            <div className="h-10 w-px bg-white/10 mx-2" />
            <div className="flex items-center gap-3 bg-white/5 border border-white/10 rounded-2xl pl-1.5 pr-4 py-1.5 hover:border-primary/50 transition-all cursor-pointer">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-blue-500 flex items-center justify-center font-bold text-xs text-black">
                <UserCircle className="w-5 h-5" />
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
                  title="Equity"
                  value={status?.equity !== undefined ? `$${Number(status.equity).toFixed(2)}` : "---"}
                  sub="Update Live"
                  subValue="Atualizado em tempo real"
                  trend="neutral"
                  icon={Wallet}
                />
                <StatCard
                  title="Unrealized PnL"
                  value={status?.unrealized_pnl !== undefined ? `${status.unrealized_pnl >= 0 ? '+' : ''}$${Number(status.unrealized_pnl).toFixed(2)}` : "---"}
                  sub={status?.equity ? `${((Number(status.unrealized_pnl || 0) / Number(status.equity)) * 100).toFixed(2)}%` : "---"}
                  subValue="Lucro/Prejuízo não realizado"
                  trend={status && (status.unrealized_pnl || 0) >= 0 ? "up" : "down"}
                  icon={Activity}
                />
                <StatCard
                  title="Fear & Greed"
                  value={(status as any)?.market_data?.fear_greed || "---"}
                  sub={Number((status as any)?.market_data?.fear_greed) > 50 ? "Bullish" : "Bearish"}
                  subValue="Sentimento do mercado"
                  trend={Number((status as any)?.market_data?.fear_greed) > 50 ? "up" : "down"}
                  icon={Zap}
                />
                <StatCard
                  title="Market Cap"
                  value={(status as any)?.market_data?.market_cap ? `$${((status as any).market_data.market_cap / 1e12).toFixed(2)}T` : "---"}
                  sub="Crypto Global"
                  subValue="Capitalização de mercado global"
                  trend="neutral"
                  icon={Globe}
                />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Active Positions */}
                <GlassCard className="lg:col-span-1 min-h-[440px] flex flex-col overflow-hidden" delay={0.2} noPadding>
                  <CollapsibleSection
                    title="Active Positions"
                    icon={ShieldCheck}
                    isExpanded={isPositionsExpanded}
                    onToggle={() => setIsPositionsExpanded(!isPositionsExpanded)}
                    badge={positions?.length || 0}
                  >
                    <div className="flex-1">

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
                        </div>
                    </div>
                  </CollapsibleSection>
                </GlassCard>

                {/* Daily PnL Chart */}
                <GlassCard className="lg:col-span-2 overflow-hidden" delay={0.2} noPadding>
                  <CollapsibleSection
                    title="PnL Performance"
                    icon={BarChart3}
                    isExpanded={isPnLExpanded}
                    onToggle={() => setIsPnLExpanded(!isPnLExpanded)}
                    badge={pnlPeriod}
                  >
                    <div className="flex items-center justify-between mb-4">
                      <div className="hidden lg:flex gap-1.5 bg-white/5 p-1 rounded-xl border border-white/5">
                        {(['24H', '7D', '30D', 'ALL'] as const).map((period) => (
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

                    {/* PNL Chart Card */}
                    <GlassCard className="lg:col-span-1 flex flex-col" delay={0.25}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2.5">
                          <div className="p-1.5 rounded-lg bg-gradient-to-br from-primary/30 to-primary/10 text-primary">
                            <Activity className="w-4 h-4" />
                          </div>
                          <h3 className="text-base font-bold tracking-tight">PnL Performance</h3>
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
                      <div className="text-center mb-2.5">
                        <p className={cn("text-2xl font-bold", (pnlData?.[`pnl_${pnlPeriod.toLowerCase()}`] || pnlData?.pnl_24h || 0) >= 0 ? "text-primary neon-glow" : "text-secondary")}>
                          {(pnlData?.[`pnl_${pnlPeriod.toLowerCase()}`] || pnlData?.pnl_24h || 0) >= 0 ? '+' : ''}${(pnlData?.[`pnl_${pnlPeriod.toLowerCase()}`] || pnlData?.pnl_24h || 0).toFixed(2)}
                        </p>
                        <p className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest mt-0.5">Realized PnL ({pnlPeriod})</p>
                      </div>

                      {/* Chart */}
                      <div className="h-32 w-full overflow-hidden px-1">
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
                      <div className="grid grid-cols-3 gap-2 pt-2.5 border-t border-white/5 mt-2.5">
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
                    <GlassCard className="lg:col-span-1 flex flex-col overflow-hidden" delay={0.3} noPadding>
                      <CollapsibleSection
                        title="AI Strategy Core"
                        icon={BrainCircuit}
                        isExpanded={isStrategyExpanded}
                        onToggle={() => setIsStrategyExpanded(!isStrategyExpanded)}
                        badge="LIVE"
                      >
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
                                  <p className="text-sm text-white/80 leading-relaxed font-medium group-hover:text-white transition-colors">
                                    {(thought.summary || "No summary").toUpperCase().includes('INSUFFICIENT DATA')
                                      ? "📊 Monitoring market conditions..."
                                      : thought.summary || "No summary"}
                                  </p>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      </CollapsibleSection>
                    </GlassCard>
                  </div>

                  {/* Latest AI Trade Analysis - Full Width WOW Feature */}
                  <div className="mt-10">
                    <GlassCard className="border border-purple-500/20" delay={0.35}>
                      <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-4">
                          <div className="p-3 rounded-2xl bg-purple-500/20 text-purple-400 neon-glow">
                            <BrainCircuit className="w-6 h-6" />
                          </div>
                          <div>
                            <h3 className="text-xl font-bold tracking-tight">Latest AI Trade Analysis</h3>
                            <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest mt-1">Detailed Strategy Breakdown</p>
                          </div>
                        </div>
                        <button className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-all text-xs font-bold uppercase tracking-wider">
                          View All
                        </button>
                      </div>

                      {tradeLog ? (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                          <div className="space-y-6">
                            {/* Trade Header */}
                            <div className="flex items-center justify-between p-4 rounded-2xl bg-gradient-to-r from-purple-500/10 to-primary/10 border border-white/10">
                              <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center font-bold text-lg">
                                  {tradeLog.symbol?.substring(0, 2) || 'BTC'}
                                </div>
                                <div>
                                  <h4 className="text-lg font-bold">{tradeLog.symbol} {tradeLog.side}</h4>
                                  <p className="text-xs text-muted-foreground font-bold">@ ${tradeLog.entry_price?.toLocaleString() || '0'}</p>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="text-xs text-muted-foreground font-bold uppercase tracking-widest">Setup Quality</p>
                                <div className="flex items-center gap-2 mt-1">
                                  <div className="h-2 w-24 bg-white/10 rounded-full overflow-hidden">
                                    <motion.div
                                      initial={{ width: 0 }}
                                      animate={{ width: `${(tradeLog.strategy?.setup_quality || 0) * 10}%` }}
                                      className="h-full bg-gradient-to-r from-primary to-purple-500 neon-glow"
                                    />
                                  </div>
                                  <span className="text-sm font-bold text-primary">{tradeLog.strategy?.setup_quality || 0}/10</span>
                                </div>
                              </div>
                            </div>

                            {/* Strategy */}
                            <div>
                              <div className="flex items-center gap-2 mb-3">
                                <Target className="w-4 h-4 text-primary" />
                                <h5 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Strategy</h5>
                              </div>
                              <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                                <p className="text-xs font-bold text-primary mb-1">{tradeLog.strategy?.name || 'N/A'} • {tradeLog.strategy?.timeframe || 'N/A'}</p>
                                <p className="text-sm text-white/80 leading-relaxed">{tradeLog.entry_rationale || 'No rationale provided'}</p>
                              </div>
                            </div>

                            {/* Confluence Factors */}
                            {tradeLog.strategy?.confluence_factors && (
                              <div>
                                <div className="flex items-center gap-2 mb-3">
                                  <Shield className="w-4 h-4 text-primary" />
                                  <h5 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Confluence ({tradeLog.strategy.confluence_factors.length} factors)</h5>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                  {tradeLog.strategy.confluence_factors.map((factor: any, i: number) => (
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
                            )}
                          </div>

                          <div className="space-y-6">
                            {/* Risk Management */}
                            <div>
                              <div className="flex items-center gap-2 mb-3">
                                <Activity className="w-4 h-4 text-secondary" />
                                <h5 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Risk Management</h5>
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
                                    <p className="text-[10px] font-extrabold text-primary/70 uppercase tracking-[0.15em] mb-1">Take Profit 1 ({tradeLog.risk_management?.tp1_size_pct || 0}%)</p>
                                    <p className="text-xl font-bold text-primary tracking-tight">${tradeLog.risk_management?.take_profit_1?.toLocaleString() || '0'}</p>
                                  </div>
                                  <p className="text-[10px] font-medium text-white/40 mt-1">{tradeLog.risk_management?.tp1_reason || 'N/A'}</p>
                                </div>

                                {/* TP2 */}
                                <div className="p-3.5 rounded-2xl bg-primary/10 border border-primary/20 flex flex-col justify-between min-h-[100px] transition-all hover:bg-primary/15">
                                  <div>
                                    <p className="text-[10px] font-extrabold text-primary/70 uppercase tracking-[0.15em] mb-1">Take Profit 2 ({tradeLog.risk_management?.tp2_size_pct || 0}%)</p>
                                    <p className="text-xl font-bold text-primary tracking-tight">${tradeLog.risk_management?.take_profit_2?.toLocaleString() || '0'}</p>
                                  </div>
                                  <p className="text-[10px] font-medium text-white/40 mt-1">{tradeLog.risk_management?.tp2_reason || 'N/A'}</p>
                                </div>

                                {/* Risk */}
                                <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10 flex flex-col justify-between min-h-[100px] transition-all hover:bg-white/10">
                                  <div>
                                    <p className="text-[10px] font-extrabold text-white/40 uppercase tracking-[0.15em] mb-1">Risk</p>
                                    <p className="text-xl font-bold text-white tracking-tight">${tradeLog.risk_management?.risk_usd?.toFixed(2) || '0'}</p>
                                  </div>
                                  <p className="text-[10px] font-medium text-white/40 mt-1">{tradeLog.risk_management?.risk_pct?.toFixed(2) || '0'}% of equity</p>
                                </div>
                              </div>
                            </div>

                            {/* AI Notes - Bilingual 2-Column Layout */}
                            {tradeLog.ai_notes && (() => {
                              const notes = tradeLog.ai_notes;
                              const [ptNotes, enNotes] = notes.split('🇺🇸');
                              const ptText = (ptNotes || '').replace('🇧🇷', '').trim();
                              const enText = (enNotes || '').trim();

                              return (
                                <div className="p-3 lg:p-4 rounded-xl bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-500/20">
                                  <div className="flex items-center gap-2 mb-2">
                                    <BrainCircuit className="w-3.5 h-3.5 text-purple-400" />
                                    <p className="text-[10px] font-bold uppercase tracking-widest text-purple-300">AI Notes</p>
                                  </div>

                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    <div className="space-y-1.5 p-2.5 bg-black/20 rounded-lg border border-white/5">
                                      <div className="flex items-center gap-2 mb-1">
                                        <span className="text-base">🇧🇷</span>
                                        <span className="text-[8px] font-bold uppercase tracking-widest text-green-400">Português</span>
                                      </div>
                                      <div className="text-[10px] lg:text-[11px] font-medium leading-relaxed text-white/90">
                                        {ptText}
                                      </div>
                                    </div>

                                    <div className="space-y-1.5 p-2.5 bg-black/20 rounded-lg border border-white/5">
                                      <div className="flex items-center gap-2 mb-1">
                                        <span className="text-base">🇺🇸</span>
                                        <span className="text-[8px] font-bold uppercase tracking-widest text-blue-400">English</span>
                                      </div>
                                      <div className="text-[10px] lg:text-[11px] font-medium leading-relaxed text-white/90">
                                        {enText}
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              );
                            })()}

                            {/* Confidence - Circular Gauge */}
                            <div className="flex items-center justify-between p-4 lg:p-5 rounded-2xl bg-gradient-to-br from-white/5 to-primary/5 border border-white/10 shadow-lg group hover:bg-white/[0.07] transition-all duration-500">
                              <div className="flex items-center gap-4 lg:gap-6">
                                <div className="relative w-16 h-16 lg:w-24 lg:h-24 flex items-center justify-center">
                                  <svg className="w-full h-full transform -rotate-90 filter drop-shadow-[0_0_8px_rgba(0,255,157,0.3)]">
                                    <circle
                                      cx="50%" cy="50%" r="42%"
                                      stroke="currentColor"
                                      strokeWidth="5"
                                      fill="none"
                                      className="text-white/5"
                                    />
                                    <motion.circle
                                      cx="50%" cy="50%" r="42%"
                                      stroke="currentColor"
                                      strokeWidth="5"
                                      fill="none"
                                      strokeDasharray="100 100"
                                      initial={{ strokeDashoffset: 100 }}
                                      animate={{ strokeDashoffset: 100 - (tradeLog.confidence || 0.75) * 100 }}
                                      transition={{ duration: 1.5, ease: "easeOut" }}
                                      className="text-primary"
                                      strokeLinecap="round"
                                    />
                                  </svg>
                                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                                    <span className="text-lg lg:text-3xl font-extrabold tracking-tighter text-white drop-shadow-md">
                                      {((tradeLog.confidence || 0) * 100).toFixed(0)}
                                      <span className="text-[10px] text-primary ml-0.5">%</span>
                                    </span>
                                  </div>
                                </div>
                                <div>
                                  <p className="text-[9px] font-extrabold text-muted-foreground uppercase tracking-[0.2em] mb-1">AI Confidence</p>
                                  <div className="h-0.5 w-12 lg:w-20 bg-white/10 rounded-full overflow-hidden">
                                    <div className="h-full bg-primary/40 w-full animate-shimmer" />
                                  </div>
                                </div>
                              </div>
                              <div className="text-right max-w-[140px] lg:max-w-[200px]">
                                <p className="text-[10px] lg:text-[11px] font-bold text-white/90 leading-relaxed italic border-l-2 border-primary/30 pl-2 lg:pl-3">
                                  "{tradeLog.expected_outcome || 'AI is monitoring and will adjust targets based on market structure.'}"
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="h-64 flex flex-col items-center justify-center opacity-40">
                          <div className="relative mb-6">
                            <BrainCircuit className="w-16 h-16 text-purple-500 animate-pulse" />
                            <motion.div
                              animate={{ scale: [1, 1.2, 1], opacity: [0.3, 0.6, 0.3] }}
                              transition={{ duration: 2, repeat: Infinity }}
                              className="absolute inset-0 bg-purple-500/20 blur-2xl rounded-full"
                            />
                          </div>
                          <h4 className="text-lg font-bold text-white mb-2">Awaiting AI Analysis</h4>
                          <p className="text-xs text-muted-foreground font-bold uppercase tracking-widest text-center px-12">
                            Detailed strategy breakdown will appear here <br /> once the AI initiates its next trade.
                          </p>
                        </div>
                      )}
                    </GlassCard>
                  </div>
                </motion.div>
          )}

                {activeTab === 'all' && (
                  <motion.div
                    key="all"
                    initial={{ opacity: 0, y: 10, filter: 'blur(10px)' }}
                    animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                    exit={{ opacity: 0, y: -10, filter: 'blur(10px)' }}
                    transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
                  >
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                      {/* Account Card */}
                      <GlassCard className="flex flex-col overflow-hidden" delay={0.1} noPadding>
                        <CollapsibleSection title="Account" icon={Wallet} isExpanded={true} onToggle={() => { }} badge="Live">
                          <div className="space-y-4">
                            <div>
                              <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest mb-1">Equity</p>
                              <p className="text-2xl font-black text-white">${Number(status?.equity || 0).toLocaleString()}</p>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <p className="text-[9px] text-muted-foreground uppercase font-bold tracking-widest">Margin</p>
                                <p className="text-sm font-bold text-primary">{status?.margin_usage || 0}%</p>
                              </div>
                              <div>
                                <p className="text-[9px] text-muted-foreground uppercase font-bold tracking-widest">Available</p>
                                <p className="text-sm font-bold text-white">${Number((status as any)?.withdrawable || 0).toLocaleString()}</p>
                              </div>
                            </div>
                          </div>
                        </CollapsibleSection>
                      </GlassCard>

                      {/* AI Strategy Quick View */}
                      <GlassCard className="flex flex-col overflow-hidden" delay={0.2} noPadding>
                        <CollapsibleSection title="AI Thinking" icon={BrainCircuit} isExpanded={true} onToggle={() => { }} badge="Active">
                          <div className="space-y-3">
                            {(thoughts || []).slice(0, 3).map((t, i) => (
                              <div key={i} className="flex gap-3 items-start p-2 rounded-lg bg-white/5 border border-white/5">
                                <span className="text-base shrink-0">{t.emoji || '🧐'}</span>
                                <p className="text-[10px] text-white/80 line-clamp-2">{t.summary}</p>
                              </div>
                            ))}
                          </div>
                        </CollapsibleSection>
                      </GlassCard>

                      {/* Market Pulse */}
                      <GlassCard className="flex flex-col overflow-hidden" delay={0.3} noPadding>
                        <CollapsibleSection title="Market Pulse" icon={Activity} isExpanded={true} onToggle={() => { }} badge="Global">
                          <div className="space-y-4">
                            <div className="flex justify-between items-center bg-white/5 p-3 rounded-xl">
                              <span className="text-[10px] font-bold text-muted-foreground uppercase">Fear & Greed</span>
                              <span className={cn("text-sm font-black", Number((status as any)?.market_data?.fear_greed) > 50 ? "text-primary" : "text-secondary")}>
                                {(status as any)?.market_data?.fear_greed || "---"}
                              </span>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                              <div className="p-2.5 rounded-xl bg-white/5 border border-white/5">
                                <p className="text-[8px] text-muted-foreground font-bold uppercase mb-1">BTC Dominance</p>
                                <p className="text-xs font-bold text-white">{(status as any)?.market_data?.btc_dominance?.toFixed(1) || "---"}%</p>
                              </div>
                              <div className="p-2.5 rounded-xl bg-white/5 border border-white/5">
                                <p className="text-[8px] text-muted-foreground font-bold uppercase mb-1">Vol 24h</p>
                                <p className="text-xs font-bold text-white">${((status as any)?.market_data?.volume_24h / 1e9).toFixed(1) || "---"}B</p>
                              </div>
                            </div>
                          </div>
                        </CollapsibleSection>
                      </GlassCard>

                      {/* Active Positions Summary */}
                      <GlassCard className="flex flex-col overflow-hidden" delay={0.4} noPadding>
                        <CollapsibleSection title="Positions" icon={ShieldCheck} isExpanded={true} onToggle={() => { }} badge={positions?.length || 0}>
                          <div className="space-y-3">
                            {positions?.length === 0 ? (
                              <p className="text-[10px] text-muted-foreground italic text-center py-4">No positions open</p>
                            ) : (
                              (positions || []).slice(0, 4).map((p, i) => (
                                <div key={i} className="flex justify-between items-center p-2 rounded-lg bg-white/5">
                                  <span className="text-[10px] font-black">{p.symbol}</span>
                                  <span className={cn("text-[10px] font-bold", p.unrealized_pnl >= 0 ? "text-primary" : "text-secondary")}>
                                    {p.unrealized_pnl >= 0 ? '+' : ''}${p.unrealized_pnl.toFixed(1)}
                                  </span>
                                </div>
                              ))
                            )}
                          </div>
                        </CollapsibleSection>
                      </GlassCard>

                      {/* Performance Card */}
                      <GlassCard className="flex flex-col overflow-hidden" delay={0.5} noPadding>
                        <CollapsibleSection title="Performance" icon={BarChart3} isExpanded={true} onToggle={() => { }} badge={pnlPeriod}>
                          <div className="space-y-2">
                            <div className="flex justify-between items-end mb-2">
                              <p className={cn("text-xl font-black", (pnlData?.[`pnl_${pnlPeriod.toLowerCase()}`] || 0) >= 0 ? "text-primary" : "text-secondary")}>
                                ${(pnlData?.[`pnl_${pnlPeriod.toLowerCase()}`] || 0).toFixed(2)}
                              </p>
                              <span className="text-[10px] text-white/50 font-bold uppercase">{pnlPeriod} PnL</span>
                            </div>
                            <div className="h-10 w-full opacity-50">
                              {/* Mini sparkline placeholder */}
                              <svg className="w-full h-full" viewBox="0 0 100 20">
                                <path d="M0,15 L10,12 L20,18 L30,5 L40,10 L50,8 L60,15 L70,3 L80,10 L90,2 L100,8" fill="none" strokeWidth="2" stroke="currentColor" className={cn((pnlData?.[`pnl_${pnlPeriod.toLowerCase()}`] || 0) >= 0 ? "text-primary" : "text-secondary")} />
                              </svg>
                            </div>
                          </div>
                        </CollapsibleSection>
                      </GlassCard>

                      {/* Risk & Safety */}
                      <GlassCard className="flex flex-col overflow-hidden" delay={0.6} noPadding>
                        <CollapsibleSection title="Risk Gauge" icon={Shield} isExpanded={true} onToggle={() => { }} badge="Secure">
                          <div className="space-y-4">
                            <div className="flex justify-between items-center">
                              <span className="text-[10px] font-bold text-muted-foreground uppercase">Margin Usage</span>
                              <span className="text-xs font-black text-warning">{status?.margin_usage || 0}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${status?.margin_usage || 0}%` }}
                                className="h-full bg-warning"
                              />
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-[10px] font-bold text-muted-foreground uppercase">Effective Leverage</span>
                              <span className="text-xs font-black text-primary">{(((status as any)?.total_exposure || 0) / (status?.equity || 1)).toFixed(2)}x</span>
                            </div>
                          </div>
                        </CollapsibleSection>
                      </GlassCard>

                      {/* Strategy State */}
                      <GlassCard className="flex flex-col overflow-hidden" delay={0.7} noPadding>
                        <CollapsibleSection title="Strategy" icon={Target} isExpanded={true} onToggle={() => { }} badge="Active">
                          <div className="space-y-3">
                            <div className="p-3 rounded-xl bg-primary/10 border border-primary/20">
                              <p className="text-[10px] font-bold text-primary uppercase mb-1">Current Bias</p>
                              <p className="text-sm font-black text-white">{tradeLog?.side || "NEUTRAL"}</p>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                              <div className="p-2 rounded-lg bg-white/5 border border-white/5 text-center">
                                <p className="text-[8px] text-muted-foreground uppercase mb-1">Confidence</p>
                                <p className="text-xs font-bold text-white">{((tradeLog?.confidence || 0) * 100).toFixed(0)}%</p>
                              </div>
                              <div className="p-2 rounded-lg bg-white/5 border border-white/5 text-center">
                                <p className="text-[8px] text-muted-foreground uppercase mb-1">Quality</p>
                                <p className="text-xs font-bold text-white">{tradeLog?.strategy?.setup_quality || 0}/10</p>
                              </div>
                            </div>
                          </div>
                        </CollapsibleSection>
                      </GlassCard>

                      <div className="md:col-span-2 lg:col-span-1 p-6 flex flex-col items-center justify-center opacity-30 border-2 border-dashed border-white/10 rounded-[32px] min-h-[160px]">
                        <Grid className="w-8 h-8 mb-2" />
                        <p className="text-[9px] font-bold uppercase tracking-widest text-center leading-tight">Neural Link Stable<br />More cards coming</p>
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* CHARTS Tab - Live Candlestick Charts for Each Position */}
                {activeTab === 'charts' && (
                  <motion.div
                    key="charts"
                    initial={{ opacity: 0, y: 10, filter: 'blur(10px)' }}
                    animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                    exit={{ opacity: 0, y: -10, filter: 'blur(10px)' }}
                    transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
                  >
                    {/* Charts Header */}
                    <div className="flex items-center justify-between mb-6">
                      <div>
                        <h2 className="text-2xl font-bold tracking-tight">Live Charts</h2>
                        <p className="text-sm text-muted-foreground">Real-time candlestick charts for your active positions</p>
                      </div>
                      <div className="flex gap-1 bg-white/5 p-1 rounded-xl border border-white/10">
                        {['1m', '5m', '15m', '1h', '4h'].map((tf) => (
                          <button
                            key={tf}
                            className="px-3 py-1.5 text-xs font-bold rounded-lg transition-all hover:bg-white/10 text-white/60 hover:text-white"
                          >
                            {tf}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Chart Grid */}
                    {positions.length > 0 ? (
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {positions.map((pos, idx) => (
                          <GlassCard key={pos.symbol} className="overflow-hidden" delay={idx * 0.1}>
                            {/* Chart Header */}
                            <div className="flex items-center justify-between mb-4">
                              <div className="flex items-center gap-3">
                                <div className={cn(
                                  "w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold",
                                  pos.side === 'LONG' ? "bg-primary/20 text-primary" : "bg-secondary/20 text-secondary"
                                )}>
                                  {pos.symbol.slice(0, 2)}
                                </div>
                                <div>
                                  <h3 className="font-bold tracking-tight">{pos.symbol}/USD</h3>
                                  <div className="flex items-center gap-2">
                                    <span className={cn(
                                      "text-[10px] font-bold px-1.5 py-0.5 rounded",
                                      pos.side === 'LONG' ? "bg-primary/20 text-primary" : "bg-secondary/20 text-secondary"
                                    )}>
                                      {pos.side} {pos.leverage}x
                                    </span>
                                    <span className="text-xs text-muted-foreground">
                                      Size: ${pos.size.toLocaleString()}
                                    </span>
                                  </div>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className={cn(
                                  "text-lg font-bold",
                                  pos.unrealized_pnl >= 0 ? "text-primary" : "text-secondary"
                                )}>
                                  {pos.unrealized_pnl >= 0 ? '+' : ''}${pos.unrealized_pnl.toFixed(2)}
                                </p>
                                <p className={cn(
                                  "text-xs font-bold",
                                  pos.pnl_pct >= 0 ? "text-primary/70" : "text-secondary/70"
                                )}>
                                  {pos.pnl_pct >= 0 ? '+' : ''}{pos.pnl_pct.toFixed(2)}%
                                </p>
                              </div>
                            </div>

                            {/* Chart Area Placeholder */}
                            <div className="relative h-64 bg-white/[0.02] rounded-2xl border border-white/5 overflow-hidden">
                              {/* Placeholder Chart Lines */}
                              <div className="absolute inset-0 flex flex-col justify-between py-4 px-2">
                                {[...Array(5)].map((_, i) => (
                                  <div key={i} className="w-full h-px bg-white/5" />
                                ))}
                              </div>

                              {/* Entry Line */}
                              <div className="absolute left-0 right-0 top-1/2 flex items-center">
                                <div className="flex-1 h-px bg-cyan-500/50 border-dashed" style={{ borderTopWidth: 1, borderStyle: 'dashed' }} />
                                <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 text-[9px] font-bold rounded">
                                  ENTRY ${pos.entry.toFixed(2)}
                                </span>
                              </div>

                              {/* Chart Coming Soon Message */}
                              <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <CandlestickChart className="w-12 h-12 text-white/10 mb-3" />
                                <p className="text-xs font-bold text-white/30 uppercase tracking-widest">TradingView Integration</p>
                                <p className="text-[10px] text-white/20">Coming Soon</p>
                              </div>

                              {/* Current Price Indicator */}
                              <div className="absolute right-2 top-1/3 bg-primary/20 text-primary px-2 py-1 rounded text-xs font-bold">
                                ${pos.mark.toFixed(2)}
                              </div>
                            </div>

                            {/* Quick Stats */}
                            <div className="grid grid-cols-4 gap-2 mt-4">
                              <div className="text-center p-2 bg-white/5 rounded-lg">
                                <p className="text-[8px] text-muted-foreground uppercase mb-0.5">Entry</p>
                                <p className="text-xs font-bold text-white">${pos.entry.toFixed(2)}</p>
                              </div>
                              <div className="text-center p-2 bg-white/5 rounded-lg">
                                <p className="text-[8px] text-muted-foreground uppercase mb-0.5">Mark</p>
                                <p className="text-xs font-bold text-white">${pos.mark.toFixed(2)}</p>
                              </div>
                              <div className="text-center p-2 bg-white/5 rounded-lg">
                                <p className="text-[8px] text-muted-foreground uppercase mb-0.5">Liq. Price</p>
                                <p className="text-xs font-bold text-secondary">${pos.liq_price?.toFixed(2) || '—'}</p>
                              </div>
                              <div className="text-center p-2 bg-white/5 rounded-lg">
                                <p className="text-[8px] text-muted-foreground uppercase mb-0.5">ROE</p>
                                <p className={cn("text-xs font-bold", pos.pnl_pct >= 0 ? "text-primary" : "text-secondary")}>
                                  {pos.pnl_pct >= 0 ? '+' : ''}{(pos.pnl_pct * pos.leverage).toFixed(2)}%
                                </p>
                              </div>
                            </div>
                          </GlassCard>
                        ))}
                      </div>
                    ) : (
                      <GlassCard className="min-h-[400px] flex flex-col items-center justify-center">
                        <CandlestickChart className="w-16 h-16 text-white/10 mb-4" />
                        <h3 className="text-lg font-bold text-white/40 mb-2">No Active Positions</h3>
                        <p className="text-sm text-muted-foreground text-center max-w-md">
                          Charts will appear here once you have active trading positions. The AI is analyzing the market...
                        </p>
                      </GlassCard>
                    )}
                  </motion.div>
                )}


                {activeTab === 'analytics' && (
                  <motion.div
                    key="analytics"
                    initial={{ opacity: 0, y: 10, filter: 'blur(10px)' }}
                    animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                    exit={{ opacity: 0, y: -10, filter: 'blur(10px)' }}
                    transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
                  >
                    <GlassCard className="mb-10 min-h-[600px] flex flex-col border border-white/5 bg-[#0b0c10]">
                      {/* HyperDash Header */}
                      <div className="flex flex-col md:flex-row md:items-start justify-between gap-8 mb-8">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">Total Value</h3>
                            <span className="px-1.5 py-0.5 rounded bg-white/10 text-[10px] font-bold text-white/50">Combined</span>
                          </div>
                          <div className="flex items-baseline gap-3">
                            <h2 className="text-3xl md:text-5xl font-extrabold tracking-tighter text-white drop-shadow-2xl">
                              <motion.span
                                key={fullAnalytics?.history?.[fullAnalytics.history.length - 1]?.value}
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="inline-block"
                              >
                                ${fullAnalytics?.history ? fullAnalytics.history[fullAnalytics.history.length - 1].value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "---"}
                              </motion.span>
                            </h2>
                            {/* Live PnL Indicator */}
                            {fullAnalytics?.pnl_24h !== undefined && (
                              <div className={cn("flex items-center gap-1.5 px-2 py-1 rounded-lg bg-white/5 border border-white/5", fullAnalytics.pnl_24h >= 0 ? "text-[#00ff9d]" : "text-red-500")}>
                                <span className="text-xs font-black">
                                  {fullAnalytics.pnl_24h >= 0 ? '▲' : '▼'} {Math.abs(fullAnalytics.pnl_24h).toFixed(2)} (24h)
                                </span>
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-6 mt-4 text-xs font-bold uppercase tracking-widest text-muted-foreground/60">
                            <div>
                              <span className="block text-[9px] mb-0.5">Unrealized PnL</span>
                              <span className={cn("text-white", (status?.unrealized_pnl || 0) >= 0 ? "text-[#00ff9d]" : "text-red-500")}>
                                {(status?.unrealized_pnl || 0) >= 0 ? '+' : ''}${Number(status?.unrealized_pnl || 0).toFixed(2)}
                              </span>
                            </div>
                            <div>
                              <span className="block text-[9px] mb-0.5">Margin Usage</span>
                              <span className="text-warning">{status?.margin_usage || 0}%</span>
                            </div>
                            <div>
                              <span className="block text-[9px] mb-0.5">Leverage</span>
                              <span className="text-primary">{(((status as any)?.total_exposure || 0) / (status?.equity || 1)).toFixed(2)}x</span>
                            </div>
                          </div>
                        </div>

                        {/* Time Controls & Secondary Stats */}
                        <div className="flex flex-col items-end gap-4">
                          <div className="bg-white/5 p-1 rounded-lg flex items-center">
                            {(['24H', '7D', '30D', 'ALL'] as const).map((range) => (
                              <button
                                key={range}
                                onClick={() => setPnlPeriod(range as any)}
                                className={cn(
                                  "px-4 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all",
                                  pnlPeriod === range
                                    ? "bg-[#1c1d25] text-white shadow-sm"
                                    : "text-muted-foreground hover:text-white"
                                )}
                              >
                                {range}
                              </button>
                            ))}
                          </div>
                          <div className="text-right">
                            <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">All PnL (Combined)</p>
                            <p className={cn("text-lg font-bold", (fullAnalytics?.pnl_total || 0) >= 0 ? "text-[#00ff9d]" : "text-red-500")}>
                              {(fullAnalytics?.pnl_total || 0) >= 0 ? '+' : ''}${Number(fullAnalytics?.pnl_total || 0).toFixed(2)}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Main Area Chart */}
                      <div className="w-full relative h-64">
                        {fullAnalytics?.history?.length > 0 ? (
                          (() => {
                            // Filter Logic
                            const now = Date.now();
                            const periodMap = { '24H': 24 * 3600 * 1000, '7D': 7 * 24 * 3600 * 1000, '30D': 30 * 24 * 3600 * 1000, 'ALL': Infinity };
                            const cutoff = now - periodMap[pnlPeriod as keyof typeof periodMap];
                            const filteredHistory = pnlPeriod === 'ALL'
                              ? fullAnalytics.history
                              : fullAnalytics.history.filter((h: any) => h.time > cutoff);

                            if (filteredHistory.length < 2) {
                              return (
                                <div className="absolute inset-0 flex items-center justify-center opacity-30">
                                  <p className="text-xs font-bold uppercase tracking-widest">Insufficient data for this period</p>
                                </div>
                              );
                            }

                            // Chart Calc
                            const values = filteredHistory.map((h: any) => h.value);
                            const minVal = Math.min(...values);
                            const maxVal = Math.max(...values);
                            const range = maxVal - minVal || 1;
                            const width = 1000;
                            const height = 400;

                            // Line Color Logic: Green if End > Start
                            const isProfit = values[values.length - 1] >= values[0];
                            const color = isProfit ? "#00ff9d" : "#ff3b30";

                            const points = filteredHistory.map((h: any, i: number) => {
                              const x = (i / (filteredHistory.length - 1)) * width;
                              const y = height - ((h.value - minVal) / range) * (height * 0.8) - (height * 0.1); // 10% padding
                              return `${x},${y}`;
                            }).join(' ');

                            const areaPath = `${points} ${width},${height} 0,${height}`;

                            return (
                              <div className="w-full h-full relative group/chart">
                                <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible" preserveAspectRatio="none">
                                  <defs>
                                    <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                                      <stop offset="0%" stopColor={color} stopOpacity="0.4" />
                                      <stop offset="60%" stopColor={color} stopOpacity="0.1" />
                                      <stop offset="100%" stopColor={color} stopOpacity="0" />
                                    </linearGradient>
                                    <filter id="glow">
                                      <feGaussianBlur stdDeviation="2" result="blur" />
                                      <feComposite in="SourceGraphic" in2="blur" operator="over" />
                                    </filter>
                                  </defs>

                                  {/* Grid Lines */}
                                  <line x1="0" y1={height} x2={width} y2={height} stroke="white" strokeOpacity="0.03" />
                                  <line x1="0" y1={0} x2={width} y2="0" stroke="white" strokeOpacity="0.03" />
                                  <line x1="0" y1={height / 2} x2={width} y2={height / 2} stroke="white" strokeOpacity="0.02" strokeDasharray="4,4" />

                                  {/* Area Fill */}
                                  <motion.path
                                    d={`M ${areaPath} Z`}
                                    fill="url(#areaGradient)"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ duration: 1 }}
                                  />

                                  {/* Stroke Line with Glow */}
                                  <motion.polyline
                                    points={points}
                                    fill="none"
                                    stroke={color}
                                    strokeWidth="3"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    filter="url(#glow)"
                                    initial={{ pathLength: 0 }}
                                    animate={{ pathLength: 1 }}
                                    transition={{ duration: 1.2, ease: [0.23, 1, 0.32, 1] }}
                                  />
                                </svg>

                                {/* Live Indicator Dot at the end of the line */}
                                <motion.div
                                  className="absolute rounded-full w-2 h-2 shadow-[0_0_10px_currentColor]"
                                  style={{
                                    color,
                                    backgroundColor: color,
                                    left: '100%',
                                    top: `${height - ((values[values.length - 1] - minVal) / range) * (height * 0.8) - (height * 0.1)}px`,
                                    transform: 'translate(-50%, -50%)'
                                  }}
                                  animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
                                  transition={{ duration: 2, repeat: Infinity }}
                                />
                              </div>
                            );
                          })()
                        ) : (
                          <div className="h-full flex flex-col items-center justify-center opacity-40">
                            <Activity className={cn("w-16 h-16 animate-pulse mb-4", (fullAnalytics?.pnl_total || 0) >= 0 ? "text-[#00ff9d]" : "text-red-500")} />
                            <p className="text-xs font-bold uppercase tracking-widest">Syncing Blockchain History...</p>
                          </div>
                        )}
                      </div>

                      {/* Footer Stats similar to HyperDash bottom bar */}
                      {/* Position Distribution Bar */}
                      <div className="mb-8 p-5 rounded-2xl bg-black/20 border border-white/5 shadow-inner">
                        <div className="flex items-center justify-between mb-3">
                          <p className="text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">Live Position Distribution</p>
                          <div className="flex gap-4">
                            <div className="flex items-center gap-1.5">
                              <div className="w-1.5 h-1.5 rounded-full bg-[#00ff9d]" />
                              <span className="text-[10px] font-bold text-[#00ff9d]">LONG {(positions?.filter((p: any) => p.side === 'LONG').length / (positions?.length || 1) * 100).toFixed(0)}%</span>
                            </div>
                            <div className="flex items-center gap-1.5">
                              <div className="w-1.5 h-1.5 rounded-full bg-[#ff3b30]" />
                              <span className="text-[10px] font-bold text-[#ff3b30]">SHORT {(positions?.filter((p: any) => p.side === 'SHORT').length / (positions?.length || 1) * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                        </div>
                        <div className="h-2.5 w-full bg-black/40 rounded-full overflow-hidden flex ring-1 ring-white/5">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${(positions?.filter((p: any) => p.side === 'LONG').length / (positions?.length || 1) * 100)}%` }}
                            className="h-full bg-gradient-to-r from-green-500 to-[#00ff9d] transition-all duration-1000 ease-out"
                          />
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${(positions?.filter((p: any) => p.side === 'SHORT').length / (positions?.length || 1) * 100)}%` }}
                            className="h-full bg-gradient-to-r from-red-600 to-[#ff3b30] transition-all duration-1000 ease-out"
                          />
                        </div>
                      </div>

                      {/* Fleet Assets Bottom Section */}
                      <div className="flex-1 mt-4">
                        {/* Tabs */}
                        <div className="flex items-center gap-1 mb-4 overflow-x-auto no-scrollbar border-b border-white/5 pb-2">
                          {(['Asset Positions', 'Open Orders', 'Recent Fills', 'Completed Trades', 'TWAP', 'Deposits & Withdrawals'] as const).map((tab) => (
                            <button
                              key={tab}
                              onClick={() => setActiveFleetTab(tab)}
                              className={cn(
                                "px-3 py-1.5 rounded-md text-[10px] font-bold uppercase tracking-wider whitespace-nowrap transition-all",
                                activeFleetTab === tab
                                  ? "bg-[#1c1d25] text-[#00ff9d] shadow-sm ring-1 ring-[#00ff9d]/20"
                                  : "text-muted-foreground hover:text-white"
                              )}
                            >
                              {tab}
                            </button>
                          ))}
                          <div className="flex-1" />
                          <div className="flex gap-1">
                            <span className="px-2 py-1 rounded bg-[#1c1d25] text-[9px] text-[#00ff9d] font-bold">Perpetual</span>
                            <span className="px-2 py-1 rounded hover:bg-white/5 text-[9px] text-muted-foreground font-bold cursor-not-allowed">Spot</span>
                          </div>
                        </div>

                        {/* Dynamic Table Content */}
                        <div className="overflow-x-auto min-h-[200px]">
                          {activeFleetTab === 'Asset Positions' && (
                            <table className="w-full text-left border-collapse">
                              <thead className="bg-black/40">
                                <tr>
                                  <th className="px-4 py-3 text-left text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">Moeda</th>
                                  <th className="px-4 py-3 text-left text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">Lado</th>
                                  <th className="px-4 py-3 text-right text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">Investimento</th>
                                  <th className="px-4 py-3 text-right text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">Preço Entrada</th>
                                  <th className="px-4 py-3 text-right text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">Preço Atual</th>
                                  <th className="px-4 py-3 text-right text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">Lucro/Prejuízo</th>
                                  <th className="px-4 py-3 text-right text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">Status</th>
                                </tr>
                              </thead>
                              <tbody className="text-sm">
                                {positions?.length > 0 ? (
                                  positions.map((pos: any, idx: number) => (
                                    <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.05] transition-all duration-300 group cursor-default">
                                      <td className="py-3 pl-2">
                                        <div className="font-bold text-white">{pos.symbol}</div>
                                        <div className="text-[10px] text-muted-foreground">10x</div>
                                      </td>
                                      <td className="py-3">
                                        <span className={cn(
                                          "relative px-2 py-1 rounded-full text-[9px] font-bold uppercase tracking-wider overflow-hidden inline-flex items-center gap-1",
                                          pos.side === 'LONG' ? "bg-green-500/20 text-[#00ff9d]" : "bg-red-500/20 text-red-400"
                                        )}>
                                          <span className={cn(
                                            "w-1 h-1 rounded-full animate-pulse",
                                            pos.side === 'LONG' ? "bg-[#00ff9d]" : "bg-red-400"
                                          )} />
                                          {pos.side}
                                        </span>
                                      </td>
                                      <td className="py-3">
                                        <div className="font-mono text-white">${(pos.size * pos.entry_price).toFixed(2)}</div>
                                        <div className="text-[10px] text-muted-foreground">{pos.size} {pos.symbol}</div>
                                      </td>
                                      <td className="py-3">
                                        <div className={cn("font-mono font-bold", pos.unrealized_pnl >= 0 ? "text-[#00ff9d]" : "text-[#ff3b30]")}>
                                          {pos.unrealized_pnl >= 0 ? '+' : ''}${pos.unrealized_pnl?.toFixed(2)}
                                        </div>
                                        <div className="text-[10px] text-[#00ff9d]">{((pos.unrealized_pnl / (pos.margin_used || 1)) * 100).toFixed(2)}%</div>
                                      </td>
                                      <td className="py-3 font-mono text-muted-foreground">${pos.entry_price?.toFixed(4)}</td>
                                      <td className="py-3 font-mono text-white">${(pos.entry_price * (1 + (Math.random() * 0.01 - 0.005))).toFixed(4)}</td>
                                      <td className="py-3 font-mono text-muted-foreground">${(pos.entry_price * (pos.side === 'LONG' ? 0.9 : 1.1)).toFixed(4)}</td>
                                      <td className="py-3 font-mono text-white">${(pos.size * pos.entry_price / 10).toFixed(2)}</td>
                                      <td className="py-3 pr-2 font-mono text-[#00ff9d] text-right">$0.00</td>
                                    </tr>
                                  ))
                                ) : (
                                  <tr className="border-b border-white/5">
                                    <td colSpan={9} className="py-12 text-center text-muted-foreground/50 text-xs uppercase tracking-widest font-bold">
                                      No active positions found in fleet
                                    </td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
                          )}

                          {activeFleetTab === 'Open Orders' && (
                            <table className="w-full text-left border-collapse">
                              <thead>
                                <tr className="text-[9px] text-muted-foreground uppercase tracking-widest border-b border-white/5">
                                  <th className="pb-3 pl-2 font-bold">Symbol</th>
                                  <th className="pb-3 font-bold">Type</th>
                                  <th className="pb-3 font-bold">Side</th>
                                  <th className="pb-3 font-bold">Price</th>
                                  <th className="pb-3 font-bold">Size</th>
                                  <th className="pb-3 pr-2 font-bold text-right">Trigger</th>
                                </tr>
                              </thead>
                              <tbody className="text-sm">
                                {openOrders.length > 0 ? (
                                  openOrders.map((order: any, idx: number) => (
                                    <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                                      <td className="py-3 pl-2 font-bold text-white">{order.symbol}</td>
                                      <td className="py-3 font-mono text-muted-foreground">{order.type}</td>
                                      <td className="py-3">
                                        <span className={cn("px-1.5 py-0.5 rounded text-[9px] font-bold uppercase", order.side === 'BUY' ? "bg-[#00ff9d]/10 text-[#00ff9d]" : "bg-[#ff3b30]/10 text-[#ff3b30]")}>
                                          {order.side}
                                        </span>
                                      </td>
                                      <td className="py-3 font-mono text-white">${order.price?.toFixed(2)}</td>
                                      <td className="py-3 font-mono text-muted-foreground">{order.size}</td>
                                      <td className="py-3 pr-2 text-right font-mono text-muted-foreground">{order.trigger_px ? `$${order.trigger_px.toFixed(2)}` : '—'}</td>
                                    </tr>
                                  ))
                                ) : (
                                  <tr className="border-b border-white/5">
                                    <td colSpan={6} className="py-12 text-center text-muted-foreground/50 text-xs uppercase tracking-widest font-bold">
                                      No open orders
                                    </td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
                          )}

                          {activeFleetTab === 'Recent Fills' && (
                            <table className="w-full text-left border-collapse">
                              <thead>
                                <tr className="text-[9px] text-muted-foreground uppercase tracking-widest border-b border-white/5">
                                  <th className="pb-3 pl-2 font-bold">Time</th>
                                  <th className="pb-3 font-bold">Symbol</th>
                                  <th className="pb-3 font-bold">Side</th>
                                  <th className="pb-3 font-bold">Price</th>
                                  <th className="pb-3 font-bold">Size</th>
                                  <th className="pb-3 font-bold">Value</th>
                                  <th className="pb-3 pr-2 font-bold text-right">PnL</th>
                                </tr>
                              </thead>
                              <tbody className="text-sm">
                                {recentFills.length > 0 ? (
                                  recentFills.slice(0, 20).map((fill: any, idx: number) => (
                                    <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                                      <td className="py-3 pl-2 font-mono text-muted-foreground text-xs">{fill.timestamp ? new Date(fill.timestamp).toLocaleTimeString() : '—'}</td>
                                      <td className="py-3 font-bold text-white">{fill.symbol}</td>
                                      <td className="py-3">
                                        <span className={cn("px-1.5 py-0.5 rounded text-[9px] font-bold uppercase", fill.side === 'BUY' ? "bg-[#00ff9d]/10 text-[#00ff9d]" : "bg-[#ff3b30]/10 text-[#ff3b30]")}>
                                          {fill.side}
                                        </span>
                                      </td>
                                      <td className="py-3 font-mono text-white">${fill.price?.toFixed(4)}</td>
                                      <td className="py-3 font-mono text-muted-foreground">{fill.size}</td>
                                      <td className="py-3 font-mono text-muted-foreground">${fill.value?.toFixed(2)}</td>
                                      <td className={cn("py-3 pr-2 text-right font-mono font-bold", fill.closed_pnl >= 0 ? "text-[#00ff9d]" : "text-[#ff3b30]")}>
                                        {fill.closed_pnl ? `${fill.closed_pnl >= 0 ? '+' : ''}$${fill.closed_pnl.toFixed(2)}` : '—'}
                                      </td>
                                    </tr>
                                  ))
                                ) : (
                                  <tr className="border-b border-white/5">
                                    <td colSpan={7} className="py-12 text-center text-muted-foreground/50 text-xs uppercase tracking-widest font-bold">
                                      No recent fills
                                    </td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
                          )}

                          {activeFleetTab === 'Deposits & Withdrawals' && (
                            <table className="w-full text-left border-collapse">
                              <thead>
                                <tr className="text-[9px] text-muted-foreground uppercase tracking-widest border-b border-white/5">
                                  <th className="pb-3 pl-2 font-bold">Time</th>
                                  <th className="pb-3 font-bold">Type</th>
                                  <th className="pb-3 font-bold">Amount</th>
                                  <th className="pb-3 pr-2 font-bold text-right">Status</th>
                                </tr>
                              </thead>
                              <tbody className="text-sm">
                                {transfers.length > 0 ? (
                                  transfers.map((transfer: any, idx: number) => (
                                    <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                                      <td className="py-3 pl-2 font-mono text-muted-foreground text-xs">{transfer.timestamp ? new Date(transfer.timestamp).toLocaleDateString() : '—'}</td>
                                      <td className="py-3">
                                        <span className={cn("px-1.5 py-0.5 rounded text-[9px] font-bold uppercase", transfer.type === 'DEPOSIT' ? "bg-[#00ff9d]/10 text-[#00ff9d]" : "bg-[#ff3b30]/10 text-[#ff3b30]")}>
                                          {transfer.type}
                                        </span>
                                      </td>
                                      <td className={cn("py-3 font-mono font-bold", transfer.amount >= 0 ? "text-[#00ff9d]" : "text-[#ff3b30]")}>
                                        ${Math.abs(transfer.amount).toFixed(2)}
                                      </td>
                                      <td className="py-3 pr-2 text-right font-mono text-[#00ff9d] text-xs uppercase">{transfer.status}</td>
                                    </tr>
                                  ))
                                ) : (
                                  <tr className="border-b border-white/5">
                                    <td colSpan={4} className="py-12 text-center text-muted-foreground/50 text-xs uppercase tracking-widest font-bold">
                                      No deposits or withdrawals
                                    </td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
                          )}

                          {/* Generic handler for other tabs */}
                          {['Completed Trades', 'TWAP'].includes(activeFleetTab) && (
                            <div className="py-20 flex flex-col items-center justify-center text-muted-foreground/50">
                              <span className="text-xs uppercase tracking-widest font-bold mb-2">No data for {activeFleetTab}</span>
                              <span className="text-[10px]">Feature coming soon...</span>
                            </div>
                          )}
                        </div>
                      </div>

                    </GlassCard>
                  </motion.div>
                )}

                {activeTab === 'chat' && (
                  <motion.div key="chat" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.3 }}>
                    <GlassCard className="h-[700px] flex flex-col">
                      <div className="flex items-center gap-4 mb-8">
                        <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400">
                          <MessageSquare className="w-6 h-6" />
                        </div>
                        <div>
                          <h3 className="text-2xl font-bold tracking-tight">AI Fleet Communication</h3>
                          <p className="text-xs text-muted-foreground font-bold uppercase tracking-widest mt-1">Direct Neural Link with Bot Core</p>
                        </div>
                      </div>

                      <div className="flex-1 overflow-y-auto space-y-4 mb-6 pr-2 no-scrollbar">
                        {chatMessages.length === 0 ? (
                          <div className="h-full flex flex-col items-center justify-center opacity-20">
                            <BrainCircuit className="w-16 h-16 mb-4 animate-pulse" />
                            <p className="text-sm font-bold uppercase tracking-widest">Start a conversation...</p>
                          </div>
                        ) : (
                          chatMessages.map((msg, i) => (
                            <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={cn("flex gap-3", msg.role === 'user' ? "justify-end" : "justify-start")}>
                              {msg.role === 'assistant' && (
                                <div className="w-8 h-8 rounded-xl bg-purple-500/20 flex items-center justify-center shrink-0">
                                  <BrainCircuit className="w-4 h-4 text-purple-400" />
                                </div>
                              )}
                              <div className={cn("max-w-[80%] px-4 py-3 rounded-2xl", msg.role === 'user' ? "bg-primary/20 text-white border border-primary/30" : "bg-white/5 text-white/90 border border-white/10")}>
                                <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                              </div>
                              {msg.role === 'user' && (
                                <div className="w-8 h-8 rounded-xl bg-primary/20 flex items-center justify-center shrink-0">
                                  <span className="text-xs font-bold">YOU</span>
                                </div>
                              )}
                            </motion.div>
                          ))
                        )}
                        {chatLoading && (
                          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                            <div className="w-8 h-8 rounded-xl bg-purple-500/20 flex items-center justify-center">
                              <BrainCircuit className="w-4 h-4 text-purple-400 animate-pulse" />
                            </div>
                            <div className="bg-white/5 px-4 py-3 rounded-2xl border border-white/10">
                              <div className="flex gap-1">
                                <span className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '0ms' }} />
                                <span className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '150ms' }} />
                                <span className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '300ms' }} />
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </div>

                      <div className="flex gap-3 pt-4 border-t border-white/5">
                        <input type="text" value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyPress={e => e.key === 'Enter' && sendChatMessage()} placeholder="Ask me anything..." disabled={chatLoading} className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-primary/50 focus:outline-none text-sm placeholder:text-muted-foreground" />
                        <button onClick={sendChatMessage} disabled={chatLoading || !chatInput.trim()} className="px-6 py-3 rounded-xl bg-primary text-black font-bold flex items-center gap-2">
                          <Send className="w-4 h-4" />
                        </button>
                      </div>
                    </GlassCard>
                  </motion.div>
                )
                }

                {activeTab === 'logs' && (
                  <motion.div key="logs" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.3 }}>
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
                )
                }
              </AnimatePresence >

              <footer className="mt-12 pt-8 border-t border-white/5 flex justify-between items-center text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                <div className="flex gap-8">
                  <span>Hyperliquid API: <span className={cn(error ? "text-secondary" : "text-primary")}>{error ? "Offline" : "Connected"}</span></span>
                  <span>OpenAI gpt-4o-mini: <span className="text-primary">Operational</span></span>
                </div>
                <div>© 2025 Ladder Labs</div>
              </footer>
            </main>

          {/* Settings Modal */}
          <SettingsModal
            isOpen={isSettingsModalOpen}
            onClose={() => setIsSettingsModalOpen(false)}
            settings={settings}
            updateSetting={updateSetting}
            resetSettings={resetSettings}
          />
        </div>
        );
}
