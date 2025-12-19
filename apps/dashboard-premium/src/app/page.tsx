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
  TrendingUp,
  TrendingDown,
  Bitcoin,
  DollarSign,
  AlertTriangle,
  Clock
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
  market_data?: {
    macro?: {
      btc?: string;
      eth?: string;
      fear_greed?: string;
    };
  };
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

// --- Tile Components ---

// Animated Icon Wrapper
const AnimatedIcon = ({ icon: Icon, color = "primary", className = "" }: { icon: any; color?: string; className?: string }) => (
  <motion.div
    animate={{ rotate: [0, 5, -5, 0] }}
    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
    className={cn("flex items-center justify-center", className)}
  >
    <Icon className={cn("w-5 h-5 md:w-6 md:h-6", color === "primary" ? "text-primary" : `text-${color}`)} />
  </motion.div>
);

// Individual Tile Card (Preview Square) - Mobile Optimized
const TileCard = ({
  title,
  value,
  subValue,
  icon: Icon,
  color = "primary",
  onClick,
  size = "normal",
  trend,
  animateIcon = false
}: {
  title: string;
  value: string;
  subValue?: string;
  icon: any;
  color?: "primary" | "secondary" | "purple" | "orange" | "blue";
  onClick: () => void;
  size?: "normal" | "large";
  trend?: "up" | "down" | "neutral";
  animateIcon?: boolean;
}) => {
  const colorMap = {
    primary: "from-primary/20 to-primary/5 border-primary/30 text-primary",
    secondary: "from-secondary/20 to-secondary/5 border-secondary/30 text-secondary",
    purple: "from-purple-500/20 to-purple-500/5 border-purple-500/30 text-purple-400",
    orange: "from-orange-500/20 to-orange-500/5 border-orange-500/30 text-orange-400",
    blue: "from-blue-500/20 to-blue-500/5 border-blue-500/30 text-blue-400"
  };

  const iconColorClass = color === "primary" ? "text-primary" : color === "secondary" ? "text-secondary" : color === "purple" ? "text-purple-400" : color === "orange" ? "text-orange-400" : "text-blue-400";
  const trendColor = trend === "up" ? "text-primary" : trend === "down" ? "text-secondary" : "text-white";

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.02, y: -4 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        "relative w-full aspect-square rounded-2xl md:rounded-3xl p-3 md:p-4 flex flex-col justify-between",
        "bg-gradient-to-br border backdrop-blur-xl",
        "transition-all duration-300 group cursor-pointer overflow-hidden",
        "hover:shadow-[0_20px_60px_-15px_rgba(0,255,157,0.3)]",
        colorMap[color],
        size === "large" && "col-span-2 aspect-auto min-h-[140px] md:min-h-[180px]"
      )}
    >
      {/* Glow Effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      {/* Icon with optional animation */}
      <div className={cn(
        "w-9 h-9 md:w-12 md:h-12 rounded-xl md:rounded-2xl flex items-center justify-center transition-transform duration-500 group-hover:scale-110",
        `bg-white/10`
      )}>
        {animateIcon ? (
          <motion.div
            animate={{ scale: [1, 1.1, 1], rotate: [0, 5, -5, 0] }}
            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          >
            <Icon className={cn("w-4 h-4 md:w-6 md:h-6", iconColorClass)} />
          </motion.div>
        ) : (
          <Icon className={cn("w-4 h-4 md:w-6 md:h-6", iconColorClass)} />
        )}
      </div>

      {/* Value - Mobile optimized: smaller text, no wrap */}
      <div className="relative z-10 text-left min-w-0">
        <h3 className={cn(
          "text-lg md:text-2xl lg:text-3xl font-black tracking-tighter truncate",
          trendColor
        )}>
          {value}
        </h3>
        {subValue && (
          <p className="text-[8px] md:text-[10px] font-bold text-white/40 uppercase tracking-wider mt-0.5 truncate">
            {subValue}
          </p>
        )}
      </div>

      {/* Title Label - Smaller on mobile */}
      <p className="absolute bottom-0 left-0 right-0 py-2 md:py-3 px-2 text-[9px] md:text-xs font-bold text-white/60 uppercase tracking-wide md:tracking-widest text-center bg-gradient-to-t from-black/60 to-transparent truncate">
        {title}
      </p>

      {/* Expand Arrow */}
      <ChevronRight className="absolute top-2 md:top-4 right-2 md:right-4 w-4 h-4 md:w-5 md:h-5 text-white/20 group-hover:text-white/60 transition-colors" />
    </motion.button>
  );
};

// Modal Overlay for Tile Content
const TileModal = ({
  isOpen,
  onClose,
  title,
  icon: Icon,
  children,
  color = "primary"
}: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  icon: any;
  children: React.ReactNode;
  color?: string;
}) => {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/80 backdrop-blur-md z-50"
          />

          {/* Modal Content */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 50 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 50 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed inset-4 md:inset-10 lg:inset-20 z-50 overflow-hidden"
          >
            <div className="w-full h-full bg-[#0a0a0f] border border-white/10 rounded-3xl overflow-hidden flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-white/5">
                <div className="flex items-center gap-4">
                  <div className={cn("p-3 rounded-2xl", `bg-${color}/20`)}>
                    <Icon className={cn("w-6 h-6", `text-${color === "primary" ? "primary" : color}`)} />
                  </div>
                  <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
                </div>
                <button
                  onClick={onClose}
                  className="p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {children}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

// Sparkline component
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
    <svg width="60" height="20" viewBox="0 0 60 20" className="opacity-70">
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
          <p className="text-muted-foreground max-w-md mb-8">A client-side exception occurred.</p>
          <button
            onClick={() => window.location.reload()}
            className="px-8 py-4 rounded-2xl bg-primary text-black font-bold uppercase tracking-widest"
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
  const [pnlData, setPnlData] = useState<any>(null);
  const [pnlHistory, setPnlHistory] = useState<any[]>([]);
  const [tradeLog, setTradeLog] = useState<any>(null);
  const [fullAnalytics, setFullAnalytics] = useState<any>(null);
  const [chatMessages, setChatMessages] = useState<{ role: string; content: string }[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  // Modal states for each tile
  const [activeModal, setActiveModal] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "";
  const isMobile = useIsMobile();

  const fetchData = async () => {
    if (!API_URL) return;

    try {
      const [statusRes, posRes, thoughtRes, pnlRes, historyRes, tradeLogsRes, fullAnalyticsRes] = await Promise.all([
        fetch(`${API_URL}/api/status`).then(r => r.json()),
        fetch(`${API_URL}/api/positions`).then(r => r.json()),
        fetch(`${API_URL}/api/ai/thoughts`).then(r => r.json()),
        fetch(`${API_URL}/api/pnl`).then(r => r.json()),
        fetch(`${API_URL}/api/pnl/history`).then(r => r.json()),
        fetch(`${API_URL}/api/ai/trade-logs`).then(r => r.json()),
        fetch(`${API_URL}/api/analytics`).then(r => r.json())
      ]);

      if (statusRes.ok) setStatus(statusRes.data);
      if (posRes.ok) setPositions(posRes.data);
      if (thoughtRes.ok) setThoughts(thoughtRes.data);
      if (pnlRes.ok) setPnlData(pnlRes.data);
      if (historyRes.ok && Array.isArray(historyRes.data)) setPnlHistory(historyRes.data);
      if (tradeLogsRes.ok && tradeLogsRes.data?.length > 0) setTradeLog(tradeLogsRes.data[0]);
      if (fullAnalyticsRes.ok) setFullAnalytics(fullAnalyticsRes.data);

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
    setChatInput("");
    setChatMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setChatLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/ai/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userMessage })
      });
      const data = await response.json();
      if (data.ok) {
        setChatMessages(prev => [...prev, { role: "assistant", content: data.answer }]);
      } else {
        setChatMessages(prev => [...prev, { role: "assistant", content: data.message || "Failed to get response" }]);
      }
    } catch {
      setChatMessages(prev => [...prev, { role: "assistant", content: "Failed to connect to AI." }]);
    } finally {
      setChatLoading(false);
    }
  };

  useEffect(() => {
    setMounted(true);
    fetchData();
    const timer = setInterval(() => setTime(new Date()), 1000);
    const apiTimer = setInterval(fetchData, 5000);
    return () => {
      clearInterval(timer);
      clearInterval(apiTimer);
    };
  }, []);

  if (!mounted) return null;

  // Helper functions
  const formatCurrency = (val: number) => `$${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  const formatPercent = (val: number) => `${val >= 0 ? "+" : ""}${val.toFixed(2)}%`;

  // BTC/ETH from market data
  const btcPrice = status?.market_data?.macro?.btc || "---";
  const ethPrice = status?.market_data?.macro?.eth || "---";

  return (
    <div className="min-h-screen bg-[#050508] text-white overflow-y-auto">
      {/* Compact Header */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-[#050508]/90 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-3 md:px-4 py-3 md:py-4 flex items-center justify-between">
          <div className="flex items-center gap-2 md:gap-3">
            <motion.div
              className="w-8 h-8 md:w-10 md:h-10 rounded-xl md:rounded-2xl bg-primary flex items-center justify-center"
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
            >
              <BrainCircuit className="w-5 h-5 md:w-6 md:h-6 text-black" />
            </motion.div>
            <div>
              <h1 className="font-bold text-sm md:text-lg tracking-tight">O Inspetor do Gráfico</h1>
              <div className="flex items-center gap-2 text-[9px] md:text-[10px]">
                <span className={cn("flex items-center gap-1", error ? "text-secondary" : "text-primary")}>
                  <motion.span
                    className={cn("w-1.5 h-1.5 rounded-full", error ? "bg-secondary" : "bg-primary")}
                    animate={{ scale: [1, 1.3, 1], opacity: [1, 0.7, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                  {error ? "Offline" : "Live"}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 md:gap-4">
            <div className="hidden md:flex flex-col items-end">
              <span className="text-[10px] text-white/40 uppercase tracking-widest">{time.toLocaleDateString()}</span>
              <span className="font-mono text-sm">{time.toLocaleTimeString()}</span>
            </div>
            <span className="text-[10px] md:hidden text-white/40 font-mono">{time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          </div>
        </div>
      </header>

      {/* Main Tile Grid */}
      <main className="max-w-7xl mx-auto p-4 md:p-6 lg:p-8">
        {/* Primary Tiles Row */}
        <div className={cn(
          "grid gap-4 mb-4",
          isMobile ? "grid-cols-2" : "grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
        )}>
          {/* Equity Tile */}
          <TileCard
            title="Seu Patrimônio"
            value={status?.equity ? formatCurrency(status.equity) : "---"}
            subValue={status ? `${status.margin_usage}% utilizado` : undefined}
            icon={Wallet}
            color="primary"
            onClick={() => setActiveModal("equity")}
          />

          {/* PnL Tile */}
          <TileCard
            title="Lucro/Prejuízo"
            value={pnlData?.pnl_24h !== undefined ? `${pnlData.pnl_24h >= 0 ? "+" : ""}$${pnlData.pnl_24h.toFixed(2)}` : "---"}
            subValue="24h"
            icon={BarChart3}
            color={pnlData?.pnl_24h >= 0 ? "primary" : "secondary"}
            trend={pnlData?.pnl_24h >= 0 ? "up" : "down"}
            onClick={() => setActiveModal("pnl")}
          />

          {/* AI Status Tile */}
          <TileCard
            title="IA Status"
            value={tradeLog?.confidence ? `${(tradeLog.confidence * 100).toFixed(0)}%` : thoughts?.[0]?.confidence ? `${(thoughts[0].confidence * 100).toFixed(0)}%` : "---"}
            subValue="Confiança"
            icon={BrainCircuit}
            color="purple"
            animateIcon={true}
            onClick={() => setActiveModal("ai")}
          />

          {/* Positions Tile */}
          <TileCard
            title="Posições"
            value={`${positions?.length || 0}`}
            subValue={positions?.length > 0 ? `${positions.filter(p => p.side === "LONG").length} Long / ${positions.filter(p => p.side === "SHORT").length} Short` : "Nenhuma ativa"}
            icon={Activity}
            color={positions?.length > 0 ? "primary" : "blue"}
            onClick={() => setActiveModal("positions")}
          />
        </div>

        {/* Secondary Tiles Row */}
        <div className={cn(
          "grid gap-3 md:gap-4 mb-4",
          isMobile ? "grid-cols-3" : "grid-cols-3 md:grid-cols-4 lg:grid-cols-6"
        )}>
          {/* Trade Log Tile */}
          <TileCard
            title="Trade"
            value={tradeLog?.symbol || "---"}
            subValue={tradeLog?.side || "---"}
            icon={Target}
            color={tradeLog?.side === "LONG" ? "primary" : tradeLog?.side === "SHORT" ? "secondary" : "blue"}
            onClick={() => setActiveModal("trade")}
          />

          {/* Risk Tile */}
          <TileCard
            title="Risco"
            value={tradeLog?.risk_management?.risk_pct ? `${tradeLog.risk_management.risk_pct.toFixed(1)}%` : "---"}
            icon={Shield}
            color="secondary"
            onClick={() => setActiveModal("risk")}
          />

          {/* BTC Price Tile */}
          <TileCard
            title="BTC"
            value={btcPrice !== "---" ? `$${Math.round(Number(btcPrice) / 1000)}K` : "---"}
            icon={Bitcoin}
            color="orange"
            onClick={() => setActiveModal("btc")}
          />

          {/* ETH Price Tile */}
          <TileCard
            title="ETH"
            value={ethPrice !== "---" ? `$${Number(ethPrice).toLocaleString()}` : "---"}
            icon={DollarSign}
            color="blue"
            onClick={() => setActiveModal("eth")}
          />

          {/* Alerts Tile */}
          <TileCard
            title="Alertas"
            value="🔔"
            subValue={thoughts?.length > 0 ? `${thoughts.length} novos` : undefined}
            icon={Bell}
            color="purple"
            animateIcon={true}
            onClick={() => setActiveModal("alerts")}
          />

          {/* Chat Tile */}
          <TileCard
            title="Chat"
            value="💬"
            subValue={chatMessages.length > 0 ? `${chatMessages.length}` : undefined}
            icon={MessageSquare}
            color="purple"
            onClick={() => setActiveModal("chat")}
          />
        </div>

        {/* Footer */}
        <footer className="mt-8 pt-6 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-4 text-[10px] font-bold uppercase tracking-widest text-white/30">
          <div className="flex gap-6">
            <span>Hyperliquid: <span className={error ? "text-secondary" : "text-primary"}>{error ? "Offline" : "Connected"}</span></span>
            <span>AI: <span className="text-primary">Operational</span></span>
          </div>
          <span>© 2025 InspetorBot</span>
        </footer>
      </main>

      {/* ========== MODALS ========== */}

      {/* Equity Modal */}
      <TileModal isOpen={activeModal === "equity"} onClose={() => setActiveModal(null)} title="Seu Patrimônio" icon={Wallet} color="primary">
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-6 rounded-2xl bg-primary/10 border border-primary/20">
              <p className="text-sm text-white/60 mb-2">Total Equity</p>
              <p className="text-4xl font-black text-primary">{status?.equity ? formatCurrency(status.equity) : "---"}</p>
            </div>
            <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
              <p className="text-sm text-white/60 mb-2">Poder de Compra</p>
              <p className="text-4xl font-black">{status?.buying_power ? formatCurrency(status.buying_power) : "---"}</p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-white/5">
              <p className="text-xs text-white/40 uppercase tracking-widest mb-1">Margem Usada</p>
              <p className="text-xl font-bold">{status?.margin_usage || 0}%</p>
            </div>
            <div className="p-4 rounded-xl bg-white/5">
              <p className="text-xs text-white/40 uppercase tracking-widest mb-1">PnL Não Realizado</p>
              <p className={cn("text-xl font-bold", (status?.unrealized_pnl || 0) >= 0 ? "text-primary" : "text-secondary")}>
                {status?.unrealized_pnl !== undefined ? `${status.unrealized_pnl >= 0 ? "+" : ""}$${status.unrealized_pnl.toFixed(2)}` : "---"}
              </p>
            </div>
            <div className="p-4 rounded-xl bg-white/5">
              <p className="text-xs text-white/40 uppercase tracking-widest mb-1">Posições Abertas</p>
              <p className="text-xl font-bold">{positions?.length || 0}</p>
            </div>
          </div>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <p className="text-xs text-white/40 uppercase tracking-widest mb-2">Última Atualização</p>
            <p className="text-sm text-white/80">{status?.last_update || time.toLocaleString()}</p>
          </div>
        </div>
      </TileModal>

      {/* PnL Modal */}
      <TileModal isOpen={activeModal === "pnl"} onClose={() => setActiveModal(null)} title="Lucro/Prejuízo" icon={BarChart3} color="primary">
        <div className="space-y-6">
          {/* PnL Stats Grid */}
          <div className="grid grid-cols-3 gap-4">
            <div className="p-5 rounded-2xl bg-white/5 border border-white/10 text-center">
              <p className="text-xs text-white/40 uppercase tracking-widest mb-2">24 Horas</p>
              <p className={cn("text-2xl font-black", (pnlData?.pnl_24h || 0) >= 0 ? "text-primary" : "text-secondary")}>
                {pnlData?.pnl_24h !== undefined ? `${pnlData.pnl_24h >= 0 ? "+" : ""}$${pnlData.pnl_24h.toFixed(2)}` : "---"}
              </p>
            </div>
            <div className="p-5 rounded-2xl bg-white/5 border border-white/10 text-center">
              <p className="text-xs text-white/40 uppercase tracking-widest mb-2">7 Dias</p>
              <p className={cn("text-2xl font-black", (pnlData?.pnl_7d || 0) >= 0 ? "text-primary" : "text-secondary")}>
                {pnlData?.pnl_7d !== undefined ? `${pnlData.pnl_7d >= 0 ? "+" : ""}$${pnlData.pnl_7d.toFixed(2)}` : "---"}
              </p>
            </div>
            <div className="p-5 rounded-2xl bg-white/5 border border-white/10 text-center">
              <p className="text-xs text-white/40 uppercase tracking-widest mb-2">30 Dias</p>
              <p className={cn("text-2xl font-black", (pnlData?.pnl_30d || 0) >= 0 ? "text-primary" : "text-secondary")}>
                {pnlData?.pnl_30d !== undefined ? `${pnlData.pnl_30d >= 0 ? "+" : ""}$${pnlData.pnl_30d.toFixed(2)}` : "---"}
              </p>
            </div>
          </div>

          {/* PnL Chart */}
          <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
            <p className="text-xs text-white/40 uppercase tracking-widest mb-4">Histórico de PnL</p>
            <div className="h-48 w-full">
              {pnlHistory?.length > 0 ? (
                <svg width="100%" height="100%" viewBox="0 0 100 40" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#00ff9d" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="#00ff9d" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <path
                    d={`M 0 40 ${pnlHistory.map((p: any, i: number) => {
                      const x = (i / (pnlHistory.length - 1)) * 100;
                      const minVal = Math.min(...pnlHistory.map((d: any) => d.value));
                      const maxVal = Math.max(...pnlHistory.map((d: any) => d.value));
                      const range = maxVal - minVal || 1;
                      const y = 35 - ((p.value - minVal) / range) * 30;
                      return `L ${x} ${y}`;
                    }).join(" ")} L 100 40 Z`}
                    fill="url(#pnlGradient)"
                  />
                  <path
                    d={`M ${pnlHistory.map((p: any, i: number) => {
                      const x = (i / (pnlHistory.length - 1)) * 100;
                      const minVal = Math.min(...pnlHistory.map((d: any) => d.value));
                      const maxVal = Math.max(...pnlHistory.map((d: any) => d.value));
                      const range = maxVal - minVal || 1;
                      const y = 35 - ((p.value - minVal) / range) * 30;
                      return `${x} ${y}`;
                    }).join(" L ")}`}
                    fill="none"
                    stroke="#00ff9d"
                    strokeWidth="0.5"
                  />
                </svg>
              ) : (
                <div className="h-full flex items-center justify-center text-white/30 text-sm">
                  Carregando histórico...
                </div>
              )}
            </div>
          </div>
        </div>
      </TileModal>

      {/* AI Status Modal */}
      <TileModal isOpen={activeModal === "ai"} onClose={() => setActiveModal(null)} title="IA Status" icon={BrainCircuit} color="purple">
        <div className="space-y-6">
          {/* Confidence Gauge */}
          <div className="flex items-center justify-center p-8">
            <div className="relative w-40 h-40">
              <svg className="w-full h-full transform -rotate-90">
                <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="8" fill="none" className="text-white/5" />
                <circle
                  cx="80" cy="80" r="70"
                  stroke="currentColor" strokeWidth="8" fill="none"
                  strokeDasharray="440"
                  strokeDashoffset={440 - (440 * (tradeLog?.confidence || thoughts?.[0]?.confidence || 0))}
                  className="text-purple-500"
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-5xl font-black text-white">
                  {((tradeLog?.confidence || thoughts?.[0]?.confidence || 0) * 100).toFixed(0)}
                </span>
                <span className="text-sm text-purple-400">% Confiança</span>
              </div>
            </div>
          </div>

          {/* AI Notes */}
          {tradeLog?.ai_notes && (
            <div className="p-6 rounded-2xl bg-purple-500/10 border border-purple-500/20">
              <p className="text-xs text-purple-300 uppercase tracking-widest mb-3">Notas da IA</p>
              <p className="text-sm text-white/80 leading-relaxed">{tradeLog.ai_notes}</p>
            </div>
          )}

          {/* Recent Thoughts */}
          <div className="space-y-3">
            <p className="text-xs text-white/40 uppercase tracking-widest">Pensamentos Recentes</p>
            {thoughts?.slice(0, 5).map((thought, i) => (
              <div key={i} className="p-4 rounded-xl bg-white/5 border border-white/5">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">{thought.emoji || "🤖"}</span>
                  <span className="text-[10px] text-white/40">
                    {thought.timestamp ? new Date(thought.timestamp).toLocaleTimeString() : "--:--"}
                  </span>
                  <span className={cn(
                    "px-2 py-0.5 rounded text-[9px] font-bold",
                    thought.confidence >= 0.8 ? "bg-primary/20 text-primary" : "bg-white/10 text-white/60"
                  )}>
                    {(thought.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-sm text-white/70">{thought.summary}</p>
              </div>
            ))}
          </div>
        </div>
      </TileModal>

      {/* Positions Modal */}
      <TileModal isOpen={activeModal === "positions"} onClose={() => setActiveModal(null)} title="Posições Ativas" icon={Activity} color="primary">
        <div className="space-y-4">
          {positions?.length > 0 ? (
            positions.map((pos, idx) => (
              <div key={idx} className="p-5 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className={cn(
                    "w-12 h-12 rounded-xl flex items-center justify-center font-bold text-sm",
                    pos.side === "LONG" ? "bg-primary/20 text-primary" : "bg-secondary/20 text-secondary"
                  )}>
                    {pos.symbol.substring(0, 3)}
                  </div>
                  <div>
                    <p className="font-bold text-lg">{pos.symbol}</p>
                    <p className={cn(
                      "text-xs font-bold uppercase",
                      pos.side === "LONG" ? "text-primary" : "text-secondary"
                    )}>
                      {pos.side} • {pos.size} unidades
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-white/60">Entry: ${pos.entry_price?.toFixed(4)}</p>
                  <p className={cn(
                    "text-lg font-bold",
                    pos.unrealized_pnl >= 0 ? "text-primary" : "text-secondary"
                  )}>
                    {pos.unrealized_pnl >= 0 ? "+" : ""}${pos.unrealized_pnl?.toFixed(2)}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <div className="py-20 text-center text-white/30">
              <Activity className="w-16 h-16 mx-auto mb-4 opacity-30" />
              <p className="text-sm uppercase tracking-widest">Nenhuma posição ativa</p>
            </div>
          )}
        </div>
      </TileModal>

      {/* Trade Log Modal */}
      <TileModal isOpen={activeModal === "trade"} onClose={() => setActiveModal(null)} title="Última Trade" icon={Target} color="purple">
        {tradeLog ? (
          <div className="space-y-6">
            {/* Trade Header */}
            <div className="p-6 rounded-2xl bg-gradient-to-r from-purple-500/20 to-primary/10 border border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-white/10 flex items-center justify-center font-bold text-2xl">
                  {tradeLog.symbol?.substring(0, 2) || "??"}
                </div>
                <div>
                  <h3 className="text-2xl font-bold">{tradeLog.symbol} <span className={tradeLog.side === "LONG" ? "text-primary" : "text-secondary"}>{tradeLog.side}</span></h3>
                  <p className="text-white/60">Entry: ${tradeLog.entry_price?.toLocaleString()}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs text-white/40 uppercase">Confiança</p>
                <p className="text-3xl font-black text-purple-400">{((tradeLog.confidence || 0) * 100).toFixed(0)}%</p>
              </div>
            </div>

            {/* Strategy */}
            {tradeLog.strategy && (
              <div className="p-5 rounded-xl bg-white/5">
                <p className="text-xs text-white/40 uppercase tracking-widest mb-2">Estratégia</p>
                <p className="text-sm font-bold text-primary">{tradeLog.strategy.name} • {tradeLog.strategy.timeframe}</p>
                <p className="text-sm text-white/70 mt-2">{tradeLog.entry_rationale}</p>
              </div>
            )}

            {/* Risk Management */}
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-secondary/10 border border-secondary/20">
                <p className="text-xs text-secondary uppercase mb-1">Stop Loss</p>
                <p className="text-xl font-bold text-secondary">${tradeLog.risk_management?.stop_loss?.toLocaleString() || "---"}</p>
              </div>
              <div className="p-4 rounded-xl bg-primary/10 border border-primary/20">
                <p className="text-xs text-primary uppercase mb-1">Take Profit 1</p>
                <p className="text-xl font-bold text-primary">${tradeLog.risk_management?.take_profit_1?.toLocaleString() || "---"}</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="py-20 text-center text-white/30">
            <Target className="w-16 h-16 mx-auto mb-4 opacity-30" />
            <p className="text-sm uppercase tracking-widest">Aguardando próxima trade</p>
          </div>
        )}
      </TileModal>

      {/* Risk Modal */}
      <TileModal isOpen={activeModal === "risk"} onClose={() => setActiveModal(null)} title="Gerenciamento de Risco" icon={Shield} color="secondary">
        <div className="space-y-6">
          {tradeLog?.risk_management ? (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-6 rounded-2xl bg-secondary/10 border border-secondary/20">
                  <p className="text-xs text-secondary uppercase mb-2">Risco Total</p>
                  <p className="text-3xl font-black text-secondary">${tradeLog.risk_management.risk_usd?.toFixed(2) || "0"}</p>
                  <p className="text-sm text-white/40 mt-1">{tradeLog.risk_management.risk_pct?.toFixed(2) || "0"}% do equity</p>
                </div>
                <div className="p-6 rounded-2xl bg-white/5 border border-white/10">
                  <p className="text-xs text-white/40 uppercase mb-2">Stop Loss</p>
                  <p className="text-3xl font-black">${tradeLog.risk_management.stop_loss?.toLocaleString() || "---"}</p>
                  <p className="text-sm text-white/40 mt-1">{tradeLog.risk_management.stop_loss_reason || "---"}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-5 rounded-xl bg-primary/10 border border-primary/20">
                  <p className="text-xs text-primary uppercase mb-1">TP1 ({tradeLog.risk_management.tp1_size_pct || 0}%)</p>
                  <p className="text-xl font-bold text-primary">${tradeLog.risk_management.take_profit_1?.toLocaleString() || "---"}</p>
                </div>
                <div className="p-5 rounded-xl bg-primary/10 border border-primary/20">
                  <p className="text-xs text-primary uppercase mb-1">TP2 ({tradeLog.risk_management.tp2_size_pct || 0}%)</p>
                  <p className="text-xl font-bold text-primary">${tradeLog.risk_management.take_profit_2?.toLocaleString() || "---"}</p>
                </div>
              </div>

              {/* Confluence Factors */}
              {tradeLog.strategy?.confluence_factors && (
                <div className="p-5 rounded-xl bg-white/5 border border-white/10">
                  <p className="text-xs text-white/40 uppercase tracking-widest mb-3">Fatores de Confluência</p>
                  <div className="flex flex-wrap gap-2">
                    {tradeLog.strategy.confluence_factors.map((factor: string, i: number) => (
                      <span key={i} className="px-3 py-1.5 rounded-lg bg-primary/10 text-primary text-xs font-medium flex items-center gap-1">
                        <CheckCircle className="w-3 h-3" />
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="py-20 text-center text-white/30">
              <Shield className="w-16 h-16 mx-auto mb-4 opacity-30" />
              <p className="text-sm uppercase tracking-widest">Sem dados de risco</p>
            </div>
          )}
        </div>
      </TileModal>

      {/* BTC Modal */}
      <TileModal isOpen={activeModal === "btc"} onClose={() => setActiveModal(null)} title="Bitcoin" icon={Bitcoin} color="orange">
        <div className="space-y-6">
          <div className="text-center py-10">
            <Bitcoin className="w-20 h-20 text-orange-500 mx-auto mb-4" />
            <p className="text-5xl font-black text-orange-400">
              {btcPrice !== "---" ? `$${Number(btcPrice).toLocaleString()}` : "---"}
            </p>
            <p className="text-white/40 uppercase tracking-widest mt-2">BTC/USD</p>
          </div>
          <div className="p-5 rounded-xl bg-white/5">
            <p className="text-xs text-white/40 uppercase mb-2">Dados de Mercado</p>
            <p className="text-sm text-white/60">Preço atualizado em tempo real via Hyperliquid API.</p>
          </div>
        </div>
      </TileModal>

      {/* ETH Modal */}
      <TileModal isOpen={activeModal === "eth"} onClose={() => setActiveModal(null)} title="Ethereum" icon={DollarSign} color="blue">
        <div className="space-y-6">
          <div className="text-center py-10">
            <div className="w-20 h-20 rounded-full bg-blue-500/20 flex items-center justify-center mx-auto mb-4">
              <span className="text-4xl">Ξ</span>
            </div>
            <p className="text-5xl font-black text-blue-400">
              {ethPrice !== "---" ? `$${Number(ethPrice).toLocaleString()}` : "---"}
            </p>
            <p className="text-white/40 uppercase tracking-widest mt-2">ETH/USD</p>
          </div>
          <div className="p-5 rounded-xl bg-white/5">
            <p className="text-xs text-white/40 uppercase mb-2">Dados de Mercado</p>
            <p className="text-sm text-white/60">Preço atualizado em tempo real via Hyperliquid API.</p>
          </div>
        </div>
      </TileModal>

      {/* Config Modal */}
      <TileModal isOpen={activeModal === "config"} onClose={() => setActiveModal(null)} title="Configurações" icon={Settings} color="blue">
        <div className="py-20 text-center text-white/30">
          <Settings className="w-16 h-16 mx-auto mb-4 opacity-30 animate-spin-slow" />
          <p className="text-lg font-bold mb-2">Configurações</p>
          <p className="text-sm">Em breve: Gerenciamento de parâmetros do bot</p>
        </div>
      </TileModal>

      {/* Chat Modal */}
      <TileModal isOpen={activeModal === "chat"} onClose={() => setActiveModal(null)} title="Chat com IA" icon={MessageSquare} color="purple">
        <div className="flex flex-col h-[60vh]">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 mb-4">
            {chatMessages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-white/30">
                <BrainCircuit className="w-16 h-16 mb-4 animate-pulse" />
                <p className="text-sm uppercase tracking-widest">Inicie uma conversa...</p>
              </div>
            ) : (
              chatMessages.map((msg, i) => (
                <div key={i} className={cn("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}>
                  {msg.role === "assistant" && (
                    <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center shrink-0">
                      <BrainCircuit className="w-5 h-5 text-purple-400" />
                    </div>
                  )}
                  <div className={cn(
                    "max-w-[80%] px-4 py-3 rounded-2xl",
                    msg.role === "user"
                      ? "bg-primary/20 text-white border border-primary/30"
                      : "bg-white/5 text-white/90 border border-white/10"
                  )}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  </div>
                  {msg.role === "user" && (
                    <div className="w-10 h-10 rounded-xl bg-primary/20 flex items-center justify-center shrink-0">
                      <span className="text-xs font-bold">YOU</span>
                    </div>
                  )}
                </div>
              ))
            )}
            {chatLoading && (
              <div className="flex gap-3">
                <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center">
                  <BrainCircuit className="w-5 h-5 text-purple-400 animate-pulse" />
                </div>
                <div className="bg-white/5 px-4 py-3 rounded-2xl border border-white/10">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-2 h-2 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="flex gap-3 pt-4 border-t border-white/5">
            <input
              type="text"
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyPress={e => e.key === "Enter" && sendChatMessage()}
              placeholder="Pergunte algo..."
              disabled={chatLoading}
              className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-purple-500/50 focus:outline-none text-sm placeholder:text-white/30"
            />
            <button
              onClick={sendChatMessage}
              disabled={chatLoading || !chatInput.trim()}
              className="px-6 py-3 rounded-xl bg-purple-500 text-white font-bold flex items-center gap-2 disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </TileModal>

      {/* Alerts Modal */}
      <TileModal isOpen={activeModal === "alerts"} onClose={() => setActiveModal(null)} title="Alertas & Notificações" icon={Bell} color="purple">
        <div className="space-y-4">
          {thoughts?.length > 0 ? (
            thoughts.slice(0, 10).map((thought, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center shrink-0">
                    <span className="text-lg">{thought.emoji || "🤖"}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] text-white/40 font-mono">
                        {thought.timestamp ? new Date(thought.timestamp).toLocaleTimeString() : "--:--"}
                      </span>
                      <span className={cn(
                        "px-2 py-0.5 rounded text-[9px] font-bold",
                        thought.confidence >= 0.8 ? "bg-primary/20 text-primary" : thought.confidence >= 0.5 ? "bg-yellow-500/20 text-yellow-400" : "bg-white/10 text-white/50"
                      )}>
                        {(thought.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-sm text-white/80 leading-relaxed">{thought.summary}</p>
                  </div>
                </div>
              </motion.div>
            ))
          ) : (
            <div className="py-20 text-center text-white/30">
              <Bell className="w-16 h-16 mx-auto mb-4 opacity-30" />
              <p className="text-sm uppercase tracking-widest">Nenhum alerta recente</p>
            </div>
          )}
        </div>
      </TileModal>
    </div>
  );
}
