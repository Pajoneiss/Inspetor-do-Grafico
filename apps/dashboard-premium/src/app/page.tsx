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
  ChevronLeft,
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
  History,
  UserCircle,
  Newspaper,
  Calendar,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  ArrowLeft,
  Flame,
  Fuel,
  Layers,
  Timer,
  Gauge
} from "lucide-react";
import { cn } from "@/lib/utils";
import SettingsModal from "@/components/SettingsModal";
import { useSettings } from "@/hooks/useSettings";
import AnimatedBackground from "@/components/AnimatedBackground";
import UnifiedOverviewCard from "@/components/UnifiedOverviewCard";
import Link from "next/link";

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

const GlassCard = ({ children, className, delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.8, delay, ease: [0.23, 1, 0.32, 1] }}
    whileHover={{ y: -4, transition: { duration: 0.2 } }}
    className={cn(
      "glass-card rounded-[32px] p-6 overflow-hidden relative group transition-all duration-500",
      "hover:shadow-[0_20px_50px_-12px_rgba(0,0,0,0.5)] hover:border-white/20",
      className
    )}
  >
    {/* Animated Gradient Border on Hover */}
    <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
    <div className="relative z-10">{children}</div>
  </motion.div>
);

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

const StatCard = ({ title, value, sub, subValue, icon: Icon, trend, sensitive }: { title: string; value: string; sub: string; subValue?: string; icon: React.ElementType; trend?: "up" | "down" | "neutral"; sensitive?: boolean }) => {
  const { settings } = useSettings();
  const isMobile = useIsMobile();
  const isLoading = value === "---" || value === "$---" || value === "0.00%";

  // Translate titles for beginners
  const isEn = settings.language === 'en';
  const displayTitle = isEn ? title : (
    title === "Equity" ? "Seu Patrimônio" :
      title === "Unrealized PnL" ? "Lucro/Prejuízo" :
        title === "Open Positions" ? "Posições Ativas" : title
  );

  const content = (
    <div className={cn("transition-all duration-500", isLoading && "opacity-50")}>
      <div className="flex justify-between items-start">
        <div className="p-2 rounded-xl bg-white/5 border border-white/10 shadow-inner group-hover:bg-primary/10 transition-colors duration-500">
          <Icon className="w-4 h-4 text-primary group-hover:scale-110 transition-transform duration-500" />
        </div>
        {trend && trend !== "neutral" && (
          <div className="flex items-center gap-2">
            {/* Removed mock Sparkline data - only show if real data provided in future */}
            <span className={cn(
              "px-2 py-0.5 rounded-full text-[9px] font-black tracking-widest uppercase",
              trend === "up" ? "bg-primary/20 text-primary" : "bg-secondary/20 text-secondary"
            )}>
              {isLoading ? "..." : sub}
            </span>
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-white/40 text-[10px] font-extrabold tracking-[0.2em] uppercase mb-1">{displayTitle}</p>
        {isLoading ? (
          <div className="h-8 w-24 bg-white/5 rounded-lg animate-pulse mb-1" />
        ) : (
          <h3 className={cn(
            "text-2xl font-extrabold tracking-tighter text-white drop-shadow-md transition-all duration-500",
            sensitive && settings.hideSensitiveData && "blur-md select-none"
          )}>{value}</h3>
        )}
        <p className="text-white/30 text-[9px] font-medium mt-1 uppercase tracking-widest">
          {isLoading ? "Buscando dados..." : (trend === "neutral" ? (subValue || sub) : "Atualizado em tempo real")}
        </p>
      </div>
    </div>
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

  const formatValue = (val: any, prefix = '', suffix = '') => {
    if (val === null || val === undefined || val === "N/A" || val === "---") return '---';
    // Try to parse string numbers
    let numVal = val;
    if (typeof val === 'string') {
      const parsed = parseFloat(val);
      if (!isNaN(parsed)) numVal = parsed;
    }

    if (typeof numVal === 'number') {
      const formatted = numVal.toLocaleString('en-US', { maximumFractionDigits: 2, minimumFractionDigits: 2 });
      return `${prefix}${formatted}${suffix}`;
    }
    return String(val);
  };

  const items = [
    { label: "S&P 500", value: formatValue(macro.sp500), color: "text-[#00ff9d]" },
    { label: "NASDAQ", value: formatValue(macro.nasdaq), color: "text-[#00ff9d]" },
    { label: "Fear & Greed", value: (data.fear_greed ?? '---'), color: "text-yellow-400" },
    { label: "Market Cap", value: data.market_cap ? `$${(data.market_cap / 1e12).toFixed(2)}T` : '---', color: "text-primary" },
    { label: "USD/BRL", value: macro.usd_brl && macro.usd_brl !== "N/A" ? `R$ ${parseFloat(String(macro.usd_brl)).toFixed(2)}` : '---', color: "text-green-400" },
    { label: "BTC", value: formatValue(macro.btc, '$'), color: "text-orange-400" },
    { label: "ETH", value: formatValue(macro.eth, '$'), color: "text-purple-400" },
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

const TradingViewChart = ({ symbol, theme = 'dark' }: { symbol: string, theme?: 'dark' | 'light' }) => {
  const containerId = React.useId().replace(/:/g, '');

  useEffect(() => {
    const scriptId = 'tradingview-widget-script';
    let script = document.getElementById(scriptId) as HTMLScriptElement;

    const initWidget = () => {
      if ((window as any).TradingView) {
        new (window as any).TradingView.widget({
          "autosize": true,
          "symbol": symbol.includes(':') ? symbol : `BINANCE:${symbol}USDT.P`,
          "interval": "15",
          "timezone": "Etc/UTC",
          "theme": theme,
          "style": "1",
          "locale": "en",
          "enable_publishing": false,
          "hide_top_toolbar": false,
          "hide_legend": false,
          "save_image": false,
          "container_id": containerId,
          "backgroundColor": theme === 'dark' ? "rgba(10, 10, 10, 1)" : "rgba(255, 255, 255, 1)",
          "gridColor": theme === 'dark' ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.05)",
        });
      }
    };

    if (!script) {
      script = document.createElement('script');
      script.id = scriptId;
      script.src = 'https://s3.tradingview.com/tv.js';
      script.async = true;
      script.onload = initWidget;
      document.head.appendChild(script);
    } else {
      initWidget();
    }
  }, [symbol, theme, containerId]);

  return (
    <div className="w-full h-full min-h-[400px] rounded-2xl overflow-hidden border border-white/10 bg-black/20 shadow-2xl">
      <div id={containerId} className="w-full h-full" />
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
  const [allThoughts, setAllThoughts] = useState<AIThought[]>([]); // Full logs including HOLDs
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'charts' | 'analytics' | 'news' | 'chat' | 'logs'>('overview');
  const [activeFleetTab, setActiveFleetTab] = useState<'Asset Positions' | 'Open Orders' | 'Recent Fills' | 'Completed Trades' | 'TWAP' | 'Deposits & Withdrawals'>('Asset Positions');
  const [pnlData, setPnlData] = useState<any>(null);
  const [pnlHistory, setPnlHistory] = useState<any[]>([]);
  const [pnlPeriod, setPnlPeriod] = useState<'24H' | '7D' | '30D' | 'ALL'>('24H');
  const [chatMessages, setChatMessages] = useState<{ role: string, content: string }[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [tradeLog, setTradeLog] = useState<any>(null);
  const [_trade_logs, _setTradeLogs] = useState<any[]>([]);
  const [viewAllModalOpen, setViewAllModalOpen] = useState(false);
  const [fullAnalytics, setFullAnalytics] = useState<any>(null);
  const [openOrders, setOpenOrders] = useState<any[]>([]);
  const [recentFills, setRecentFills] = useState<any[]>([]);
  const [transfers, setTransfers] = useState<any[]>([]);
  const [cryptoPrices, setCryptoPrices] = useState<{ btc: any, eth: any } | null>(null);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [aiNotesLang, setAiNotesLang] = useState<'pt' | 'en'>('pt'); // Language toggle for AI Strategy Core

  // New states for UI improvements (Option B)
  const [journalStats, setJournalStats] = useState<{
    win_rate: number;
    total_trades: number;
    total_pnl_usd: number;
    best_trade_pct: number;
    worst_trade_pct: number;
    avg_duration_minutes: number;
  } | null>(null);
  const [sessionInfo, setSessionInfo] = useState<{
    session: string;
    current_time_utc: string;
    is_weekend: boolean;
  } | null>(null);
  const [aiMood, setAiMood] = useState<'aggressive' | 'defensive' | 'observing'>('observing');

  // News tab state
  const [realtimeNews, setRealtimeNews] = useState<Array<{ title: string; url: string; source?: string; published_at?: string }>>([]);
  const [trendingNews, setTrendingNews] = useState<Array<{ title: string; url: string; source?: string; published_at?: string }>>([]);
  const [calendarEvents, setCalendarEvents] = useState<Array<{ event: string; date: string; time?: string; importance?: string }>>([]);
  const [globalMarket, setGlobalMarket] = useState<{ market_cap?: number; volume_24h?: number; btc_dominance?: number; eth_dominance?: number; market_cap_change_24h?: number } | null>(null);
  const [topGainers, setTopGainers] = useState<Array<{ name: string; symbol: string; percent_change_24h: number }>>([]);
  const [topLosers, setTopLosers] = useState<Array<{ name: string; symbol: string; percent_change_24h: number }>>([]);
  // New Market Intelligence States
  const [halvingData, setHalvingData] = useState<any>(null);
  const [tvlData, setTvlData] = useState<any>(null);
  const [fundingData, setFundingData] = useState<any>(null);
  const [longShortData, setLongShortData] = useState<any>(null);
  const [trendingCoins, setTrendingCoins] = useState<any[]>([]);
  const [altSeasonData, setAltSeasonData] = useState<any>(null);
  const [ethGasData, setEthGasData] = useState<any>(null);
  const [rainbowData, setRainbowData] = useState<any>(null);

  const { settings, updateSetting, resetSettings } = useSettings();

  // Language helper
  const isPt = settings.language === 'pt';

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

  const fetchData = async () => {
    if (!API_URL) return;

    try {
      const [statusRes, posRes, thoughtRes, allThoughtRes, pnlRes, historyRes, tradeLogsRes, fullAnalyticsRes, ordersRes, fillsRes, transfersRes] = await Promise.all([
        fetch(`${API_URL}/api/status`).then(r => r.json()),
        fetch(`${API_URL}/api/positions`).then(r => r.json()),
        fetch(`${API_URL}/api/ai/thoughts`).then(r => r.json()), // Filtered for overview
        fetch(`${API_URL}/api/ai/thoughts?include_all=true`).then(r => r.json()), // Full for logs
        fetch(`${API_URL}/api/pnl`).then(r => r.json()),
        fetch(`${API_URL}/api/pnl/history?period=${pnlPeriod}`).then(r => r.json()),
        fetch(`${API_URL}/api/ai/trade-logs`).then(r => r.json()),
        fetch(`${API_URL}/api/analytics`).then(r => r.json()),
        fetch(`${API_URL}/api/orders`).then(r => r.json()).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/user/trades`).then(r => r.json()).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/transfers`).then(r => r.json()).catch(() => ({ ok: false }))
      ]);

      if (statusRes.ok) setStatus(statusRes.data);
      if (posRes.ok) setPositions(posRes.data);
      if (allThoughtRes.ok) setAllThoughts(allThoughtRes.data); // Full logs for Execution tab
      if (thoughtRes.ok) setThoughts(thoughtRes.data);
      if (pnlRes.ok) setPnlData(pnlRes.data);
      if (historyRes.ok && Array.isArray(historyRes.data)) setPnlHistory(historyRes.data);
      if (tradeLogsRes.ok && tradeLogsRes.data && tradeLogsRes.data.length > 0) {
        setTradeLog(tradeLogsRes.data[0]);
        _setTradeLogs(tradeLogsRes.data); // Save ALL logs for chart headers and multi-card display
      }
      if (fullAnalyticsRes.ok) setFullAnalytics(fullAnalyticsRes.data);
      if (ordersRes.ok && Array.isArray(ordersRes.data)) setOpenOrders(ordersRes.data);
      if (fillsRes.ok && Array.isArray(fillsRes.data)) setRecentFills(fillsRes.data);
      if (transfersRes.ok && Array.isArray(transfersRes.data)) setTransfers(transfersRes.data);

      // Fetch journal stats for Trading Performance widget
      try {
        const journalRes = await fetch(`${API_URL}/api/journal/stats`).then(r => r.json());
        if (journalRes.ok && journalRes.data) {
          setJournalStats(journalRes.data);
        }
      } catch (e) { /* Journal stats optional */ }

      // Fetch session info for Session Badge
      try {
        const sessionRes = await fetch(`${API_URL}/api/session`).then(r => r.json());
        if (sessionRes.ok && sessionRes.data) {
          setSessionInfo(sessionRes.data);
        }
      } catch (e) { /* Session info optional */ }

      // Determine AI mood from latest thought
      if (thoughtRes.ok && thoughtRes.data && thoughtRes.data.length > 0) {
        const latestThought = thoughtRes.data[0];
        const summary = (latestThought.summary || '').toLowerCase();
        if (summary.includes('entry') || summary.includes('open') || summary.includes('adding') || summary.includes('long') || summary.includes('short')) {
          setAiMood('aggressive');
        } else if (summary.includes('stop') || summary.includes('exit') || summary.includes('close') || summary.includes('protect') || summary.includes('tighten')) {
          setAiMood('defensive');
        } else {
          setAiMood('observing');
        }
      }

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

    // Fetch history when period changes
    useEffect(() => {
      const fetchHistory = async () => {
        if (!API_URL) return;
        try {
          const res = await fetch(`${API_URL}/api/pnl/history?period=${pnlPeriod}`);
          const data = await res.json();
          if (data.ok && Array.isArray(data.data)) setPnlHistory(data.data);
        } catch (e) { console.error(e); }
      };
      fetchHistory();
    }, [pnlPeriod]);

    // Fetch News tab data when active
    const fetchNewsData = async () => {
      if (!API_URL || activeTab !== 'news') return;
      try {
        const results = await Promise.all([
          fetch(`${API_URL}/api/news`).then(r => r.json()).catch(() => ({ ok: false })),
          fetch(`${API_URL}/api/economic-calendar?days=7`).then(r => r.json()).catch(() => ({ ok: false })),
          fetch(`${API_URL}/api/cmc/global`).then(r => r.json()).catch(() => ({ ok: false })),
          fetch(`${API_URL}/api/gainers-losers`).then(r => r.json()).catch(() => ({ ok: false })),
          // New Features
          fetch(`${API_URL}/api/halving`).then(r => r.json()).catch(() => ({ ok: false })),
          fetch(`${API_URL}/api/tvl`).then(r => r.json()).catch(() => ({ ok: false })),
          fetch(`${API_URL}/api/funding`).then(r => r.json()).catch(() => ({ ok: false })),
          fetch(`${API_URL}/api/long-short`).then(r => r.json()).catch(() => ({ ok: false })),
          fetch(`${API_URL}/api/trending`).then(r => r.json()).catch(() => ({ ok: false })),
          fetch(`${API_URL}/api/altseason`).then(r => r.json()).catch(() => ({ ok: false })),
          fetch(`${API_URL}/api/gas`).then(r => r.json()).catch(() => ({ ok: false })),
          fetch(`${API_URL}/api/rainbow`).then(r => r.json()).catch(() => ({ ok: false })),
        ]);

        const [newsRes, calendarRes, marketRes, moversRes, halvingRes, tvlRes, fundingRes, longShortRes, trendingRes, altSeasonRes, gasRes, rainbowRes] = results;

        if (newsRes.ok) {
          setRealtimeNews(newsRes.realtime || []);
          setTrendingNews(newsRes.trending || []);
        }
        if (calendarRes.ok && calendarRes.events) setCalendarEvents(calendarRes.events);
        if (marketRes.ok && marketRes.data) setGlobalMarket(marketRes.data);
        if (moversRes.ok) {
          setTopGainers(moversRes.gainers || []);
          setTopLosers(moversRes.losers || []);
        }

        // New Features State Updates
        if (halvingRes.ok) setHalvingData(halvingRes);
        if (tvlRes.ok) setTvlData(tvlRes);
        if (fundingRes.ok) setFundingData(fundingRes);
        if (longShortRes.ok) setLongShortData(longShortRes);
        if (trendingRes.ok) setTrendingCoins(trendingRes.coins || []);
        if (altSeasonRes.ok) setAltSeasonData(altSeasonRes);
        if (gasRes.ok) setEthGasData(gasRes);
        if (rainbowRes.ok) setRainbowData(rainbowRes);
      } catch (err) {
        console.error("News data fetch error:", err);
      }
    };
    if (activeTab === 'news') fetchNewsData();

    const timer = setInterval(() => setTime(new Date()), 1000);
    const apiTimer = setInterval(fetchData, 15000); // UI Refresh 15s
    const cryptoTimer = setInterval(fetchCryptoPrices, 15000); // Crypto prices every 15s
    const newsTimer = setInterval(fetchNewsData, 60000); // News data every 60s

    return () => {
      clearInterval(timer);
      clearInterval(apiTimer);
      clearInterval(cryptoTimer);
      clearInterval(newsTimer);
    };
  }, [activeTab]);

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
            { id: 'overview', label: isPt ? 'Visão Geral' : 'Overview', icon: LayoutDashboard },
            { id: 'charts', label: isPt ? 'Gráficos' : 'Charts', icon: LineChart },
            { id: 'analytics', label: isPt ? 'Análise' : 'Analytics', icon: BarChart3 },
            { id: 'news', label: isPt ? 'Notícias' : 'News', icon: Globe },
            { id: 'chat', label: isPt ? 'Chat IA' : 'AI Chat', icon: MessageSquare },
            { id: 'logs', label: isPt ? 'Logs de Execução' : 'Execution Logs', icon: Terminal },
          ].map((item) => {
            const content = (
              <>
                <item.icon className={cn("w-5 h-5", activeTab === item.id && "neon-glow")} />
                <span className="font-semibold text-sm">{item.label}</span>
                {activeTab === item.id && <motion.div layoutId="nav-pill" className="ml-auto w-1.5 h-1.5 rounded-full bg-primary neon-glow" />}
              </>
            );

            const className = cn(
              "w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl transition-all duration-300 group",
              activeTab === item.id ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-white/5 hover:text-white"
            );

            if ('href' in item && item.href) {
              return (
                <Link key={item.id} href={item.href} className={className}>
                  {content}
                </Link>
              );
            }

            return (
              <button
                key={item.id}
                onClick={() => { setActiveTab(item.id as any); setSidebarOpen(false); }}
                className={className}
              >
                {content}
              </button>
            );
          })}
        </nav>

        <div className="w-full pt-8 mt-8 border-t border-white/5 space-y-2">
          <button onClick={() => { setIsSettingsModalOpen(true); setSidebarOpen(false); }} className="w-full flex items-center gap-3 px-4 py-3 text-muted-foreground hover:text-white transition-colors">
            <Settings className="w-5 h-5" />
            <span className="font-semibold text-sm">{isPt ? 'Configurações' : 'Settings'}</span>
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
                {/* Session Badge */}
                {sessionInfo && (
                  <span className="flex items-center gap-2 text-cyan-400">
                    <Globe className="w-3 h-3" />
                    {sessionInfo.session === 'ASIA' && '🌏 Asia'}
                    {sessionInfo.session === 'LONDON' && '🇬🇧 London'}
                    {sessionInfo.session === 'NEW_YORK' && '🇺🇸 NY'}
                    {sessionInfo.session === 'OVERLAP_LONDON_NY' && '🔥 NY/London'}
                    {sessionInfo.session === 'QUIET' && '🌙 Quiet'}
                    {sessionInfo.is_weekend && ' (Weekend)'}
                  </span>
                )}
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

            {/* Simple History Dropdown */}
            <div className="relative">
              <motion.button
                className="p-3 rounded-2xl bg-white/5 border border-white/10 hover:border-white/20 transition-all"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setViewAllModalOpen(!viewAllModalOpen)}
              >
                <History className="w-5 h-5" />
              </motion.button>

              <AnimatePresence>
                {viewAllModalOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute right-0 top-full mt-2 w-64 p-4 rounded-xl glass-card border border-white/10 shadow-2xl z-50 origin-top-right"
                  >
                    <div className="flex items-center justify-between mb-3 pb-2 border-b border-white/5">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Recent History</h4>
                    </div>

                    <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                      {status?.data?.pnl_history_recent && status.data.pnl_history_recent.length > 0 ? (
                        status.data.pnl_history_recent.map((item: any, idx: number) => (
                          <div key={idx} className="flex items-center justify-between text-xs">
                            <span className="font-mono text-white/60">{new Date(item.timestamp).toLocaleDateString()} {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                            <span className={cn("font-bold", item.pnl >= 0 ? "text-primary" : "text-red-400")}>
                              {item.pnl >= 0 ? "WIN" : "LOSS"}
                            </span>
                          </div>
                        ))
                      ) : (
                        // Fallback mock data if real history is empty/loading
                        fullAnalytics?.history?.slice(-5).reverse().map((h: any, i: number) => {
                          const isWin = (h.value - (fullAnalytics?.history?.[fullAnalytics.history.length - i - 2]?.value || h.value)) >= 0;
                          return (
                            <div key={i} className="flex items-center justify-between text-xs">
                              <span className="font-mono text-white/60">{new Date(h.time).toLocaleDateString()}</span>
                              <span className={cn("font-bold", isWin ? "text-primary" : "text-red-400")}>
                                {isWin ? "WIN" : "LOSS"}
                              </span>
                            </div>
                          )
                        }) || <p className="text-xs text-center text-white/30 py-2">No recent history</p>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Language Toggle - 150% Larger */}
            <div className="flex bg-white/5 border border-white/10 rounded-xl p-1 gap-1 mr-2">
              <button
                onClick={() => updateSetting('language', 'pt')}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-black tracking-tight transition-all",
                  settings.language === 'pt' ? "bg-primary text-black shadow-[0_0_15px_rgba(0,255,157,0.3)]" : "text-white/40 hover:text-white hover:bg-white/5"
                )}
              >
                BR
              </button>
              <button
                onClick={() => updateSetting('language', 'en')}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-black tracking-tight transition-all",
                  settings.language === 'en' ? "bg-primary text-black shadow-[0_0_15px_rgba(0,255,157,0.3)]" : "text-white/40 hover:text-white hover:bg-white/5"
                )}
              >
                US
              </button>
            </div>

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
              <MarketBar data={{
                ...((status as any)?.market_data || {}),
                macro: {
                  ...((status as any)?.market_data?.macro || {}),
                  btc: cryptoPrices?.btc?.price || (status as any)?.market_data?.macro?.btc,
                  eth: cryptoPrices?.eth?.price || (status as any)?.market_data?.macro?.eth,
                }
              }} />

              <div className="mt-8 mb-8">
                <UnifiedOverviewCard
                  status={status || {}}
                  history={pnlHistory || []}
                  period={pnlPeriod}
                  setPeriod={setPnlPeriod}
                  journalStats={journalStats || {}}
                  sessionInfo={sessionInfo || {}}
                  isPt={isPt}
                  isLoading={!status}
                />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Chart Card */}
                <GlassCard className="lg:col-span-2 min-h-[440px] flex flex-col" delay={0.2}>
                  <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                      <div className="p-2 rounded-xl bg-primary/20 text-primary">
                        <BarChart3 className="w-5 h-5" />
                      </div>
                      <h3 className="text-xl font-bold tracking-tight">{isPt ? "Posições Ativas" : "Active Positions"}</h3>
                    </div>
                  </div>

                  <div className="flex-1">
                    {positions?.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center opacity-20">
                        <LayoutDashboard className="w-12 h-12 mb-4" />
                        <p className="text-xs font-bold uppercase tracking-widest">{isPt ? "Nenhuma posição ativa" : "No active positions"}</p>
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
                                <p className={cn("text-[10px] font-bold uppercase tracking-widest", pos.side === 'LONG' ? "text-primary" : "text-secondary")}>{(pos.side || "").toUpperCase()} {pos.leverage || 1}x</p>
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
                <GlassCard className="lg:col-span-1 flex flex-col" delay={0.3}>
                  <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                      <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400">
                        <BrainCircuit className="w-5 h-5" />
                      </div>
                      <h3 className="text-xl font-bold tracking-tight">{isPt ? "Núcleo de Estratégia de IA" : "AI Strategy Core"}</h3>
                      {/* AI Mood Indicator */}
                      <span className={cn(
                        "px-2 py-1 rounded-lg text-[10px] font-bold uppercase tracking-wider border",
                        aiMood === 'aggressive' && "bg-green-500/20 text-green-400 border-green-500/30",
                        aiMood === 'defensive' && "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
                        aiMood === 'observing' && "bg-blue-500/20 text-blue-400 border-blue-500/30"
                      )}>
                        {aiMood === 'aggressive' && (isPt ? '🚀 Agressivo' : '🚀 Aggressive')}
                        {aiMood === 'defensive' && (isPt ? '🛡️ Defensivo' : '🛡️ Defensive')}
                        {aiMood === 'observing' && (isPt ? '⏸️ Observando' : '⏸️ Observing')}
                      </span>
                    </div>
                    {/* Language Toggle */}
                    <div className="flex items-center gap-1 bg-white/5 p-1 rounded-lg border border-white/10">
                      <button
                        onClick={() => setAiNotesLang('pt')}
                        className={cn(
                          "px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all",
                          aiNotesLang === 'pt'
                            ? "bg-green-500/20 text-green-400 border border-green-500/30"
                            : "text-muted-foreground hover:text-white"
                        )}
                      >
                        🇧🇷 PT
                      </button>
                      <button
                        onClick={() => setAiNotesLang('en')}
                        className={cn(
                          "px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider transition-all",
                          aiNotesLang === 'en'
                            ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                            : "text-muted-foreground hover:text-white"
                        )}
                      >
                        🇺🇸 EN
                      </button>
                    </div>
                  </div>

                  <div className="flex-1 space-y-6">
                    {thoughts?.length > 0 ? (
                      // Show filtered thoughts (important decisions only)
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
                    ) : tradeLog ? (
                      // Fallback: Show last trade log when no new AI decisions
                      <div className="space-y-4">
                        <div className="flex items-center gap-2 mb-4">
                          <span className="px-2 py-1 rounded-lg bg-purple-500/20 text-purple-400 text-[10px] font-bold uppercase tracking-wider">
                            {isPt ? 'Posição Atual' : 'Current Position'}
                          </span>
                        </div>

                        {/* Trade Header */}
                        <div className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-purple-500/10 to-primary/10 border border-white/10">
                          <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center font-bold">
                            {tradeLog.symbol?.substring(0, 2) || 'BTC'}
                          </div>
                          <div>
                            <h4 className="font-bold">{tradeLog.symbol} {tradeLog.side}</h4>
                            <p className="text-xs text-muted-foreground">@ ${tradeLog.entry_price?.toLocaleString() || '0'}</p>
                          </div>
                          <div className="ml-auto text-right">
                            <span className={cn("text-lg font-bold", getConfidenceColor(tradeLog.confidence || 0))}>
                              {((tradeLog.confidence || 0) * 100).toFixed(0)}%
                            </span>
                            <p className="text-[9px] text-muted-foreground uppercase">{isPt ? "Confiabilidade" : "Confidence"}</p>
                          </div>
                        </div>

                        {/* Entry Rationale - Bilingual with toggle */}
                        {(() => {
                          const notes = tradeLog.ai_notes || tradeLog.entry_rationale || '';
                          let ptText = '';
                          let enText = '';

                          if (notes.includes('🇺🇸')) {
                            [ptText, enText] = notes.split('🇺🇸').map((s: string) => s.replace('🇧🇷', '').trim());
                          } else if (notes.includes('Position Analysis')) {
                            const idx = notes.indexOf('Position Analysis');
                            ptText = notes.substring(0, idx).replace('🇧🇷', '').trim();
                            enText = notes.substring(idx).trim();
                          } else {
                            // No separator - use same text for both
                            ptText = notes.replace('🇧🇷', '').replace('🇺🇸', '').trim();
                            enText = ptText;
                          }

                          const displayText = aiNotesLang === 'pt' ? ptText : enText;
                          const fallbackText = 'AI discretionary decision based on market structure.';

                          return (
                            <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                              <div className="flex items-center gap-2 mb-2">
                                <p className="text-[10px] font-bold text-primary uppercase tracking-wider">
                                  {aiNotesLang === 'pt' ? '🇧🇷 Análise da IA' : '🇺🇸 AI Analysis'}
                                </p>
                              </div>
                              <p className="text-sm text-white/80 leading-relaxed">{displayText || fallbackText}</p>
                            </div>
                          );
                        })()}

                        {/* Risk Levels */}
                        <div className="grid grid-cols-2 gap-2">
                          <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/20 text-center">
                            <p className="text-[9px] font-bold text-red-300 uppercase">Stop Loss</p>
                            <p className="text-sm font-bold text-red-400">${tradeLog.risk_management?.stop_loss?.toLocaleString() || '---'}</p>
                          </div>
                          <div className="p-2 rounded-lg bg-primary/10 border border-primary/20 text-center">
                            <p className="text-[9px] font-bold text-primary uppercase">Take Profit</p>
                            <p className="text-sm font-bold text-primary">${tradeLog.risk_management?.take_profit_1?.toLocaleString() || '---'}</p>
                          </div>
                        </div>
                      </div>
                    ) : (
                      // No thoughts and no trade log
                      <div className="h-full flex flex-col items-center justify-center opacity-20">
                        <BrainCircuit className="w-12 h-12 mb-4 animate-pulse" />
                        <p className="text-xs font-bold uppercase tracking-widest">{isPt ? "Aguardando decisões da IA..." : "Waiting for AI decisions..."}</p>
                      </div>
                    )}
                  </div>
                </GlassCard>
              </div>

              {/* Latest AI Trade Analysis - Full Featured with Carousel */}
              <div className="mt-10">
                <GlassCard className="border border-purple-500/20" delay={0.35}>
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-4">
                      <div className="p-3 rounded-2xl bg-purple-500/20 text-purple-400 neon-glow">
                        <BrainCircuit className="w-6 h-6" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold tracking-tight">{isPt ? "Análise de Trade Recente" : "Latest AI Trade Analysis"}</h3>
                        <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest mt-1">
                          {_trade_logs && _trade_logs.length > 1
                            ? `${_trade_logs.findIndex((log: any) => log === tradeLog) + 1} of ${_trade_logs.length} Active Positions`
                            : 'Detailed Strategy Breakdown'
                          }
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {_trade_logs && _trade_logs.length > 1 && (
                        <>
                          <button
                            onClick={() => {
                              const currentIndex = _trade_logs.findIndex((log: any) => log === tradeLog);
                              const prevIndex = currentIndex > 0 ? currentIndex - 1 : _trade_logs.length - 1;
                              setTradeLog(_trade_logs[prevIndex]);
                            }}
                            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-all"
                          >
                            <ChevronLeft className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => {
                              const currentIndex = _trade_logs.findIndex((log: any) => log === tradeLog);
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
                        {isPt ? "Ver Todos" : "View All"}
                      </button>
                    </div>
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
                            <p className="text-xs text-muted-foreground font-bold uppercase tracking-widest">{isPt ? "Qualidade do Setup" : "Setup Quality"}</p>
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
                            <h5 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">{isPt ? "Estratégia" : "Strategy"}</h5>
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
                              <h5 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">{isPt ? `Confluência (${tradeLog.strategy.confluence_factors.length} fatores)` : `Confluence (${tradeLog.strategy.confluence_factors.length} factors)`}</h5>
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
                                <p className="text-[10px] font-extrabold text-white/40 uppercase tracking-[0.15em] mb-1">{isPt ? "Risco" : "Risk"}</p>
                                <p className="text-xl font-bold text-white tracking-tight">${tradeLog.risk_management?.risk_usd?.toFixed(2) || '0'}</p>
                              </div>
                              <p className="text-[10px] font-medium text-white/40 mt-1">{tradeLog.risk_management?.risk_pct?.toFixed(2) || '0'}% of equity</p>
                            </div>
                          </div>
                        </div>

                        {/* AI Notes - Bilingual 2-Column Layout */}
                        {tradeLog.ai_notes && (() => {
                          // Parse bilingual notes - try multiple separators
                          const notes = tradeLog.ai_notes;
                          let ptText = '';
                          let enText = '';

                          if (notes.includes('🇺🇸')) {
                            [ptText, enText] = notes.split('🇺🇸').map((s: string) => s.replace('🇧🇷', '').trim());
                          } else if (notes.includes('Position Analysis')) {
                            // Fallback: split at "Position Analysis" which marks English start
                            const idx = notes.indexOf('Position Analysis');
                            ptText = notes.substring(0, idx).replace('🇧🇷', '').trim();
                            enText = notes.substring(idx).trim();
                          } else {
                            // No clear separator - show all in PT column
                            ptText = notes.replace('🇧🇷', '').trim();
                            enText = '';
                          }

                          return (
                            <div className="p-4 rounded-xl bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-500/20">
                              <div className="flex items-center gap-2 mb-3">
                                <BrainCircuit className="w-4 h-4 text-purple-400" />
                                <p className="text-xs font-bold uppercase tracking-widest text-purple-300">AI Notes</p>
                              </div>

                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* Coluna PT-BR */}
                                <div className="space-y-2 p-3 bg-black/20 rounded-lg border border-white/5">
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className="text-lg">🇧🇷</span>
                                    <span className="text-[9px] font-bold uppercase tracking-widest text-green-400">Português</span>
                                  </div>
                                  <div className="space-y-1.5 text-[11px] font-medium leading-relaxed text-white/90">
                                    {ptText}
                                  </div>
                                </div>

                                {/* Coluna EN */}
                                <div className="space-y-2 p-3 bg-black/20 rounded-lg border border-white/5">
                                  <div className="flex items-center gap-2 mb-2">
                                    <span className="text-lg">🇺🇸</span>
                                    <span className="text-[9px] font-bold uppercase tracking-widest text-blue-400">English</span>
                                  </div>
                                  <div className="space-y-1.5 text-[11px] font-medium leading-relaxed text-white/90">
                                    {enText}
                                  </div>
                                </div>
                              </div>
                            </div>
                          );
                        })()}

                        {/* Confidence - Circular Gauge */}
                        <div className="flex items-center justify-between p-5 rounded-2xl bg-gradient-to-br from-white/5 to-primary/5 border border-white/10 shadow-lg group hover:bg-white/[0.07] transition-all duration-500">
                          <div className="flex items-center gap-6">
                            <div className="relative w-20 h-20 flex items-center justify-center">
                              <svg className="w-full h-full transform -rotate-90 filter drop-shadow-[0_0_8px_rgba(0,255,157,0.3)]" viewBox="0 0 100 100">
                                <circle
                                  cx="50"
                                  cy="50"
                                  r="38"
                                  stroke="currentColor"
                                  strokeWidth="8"
                                  fill="none"
                                  className="text-white/5"
                                />
                                <motion.circle
                                  cx="50"
                                  cy="50"
                                  r="38"
                                  stroke="currentColor"
                                  strokeWidth="8"
                                  fill="none"
                                  strokeDasharray="238.76"
                                  initial={{ strokeDashoffset: 238.76 }}
                                  animate={{ strokeDashoffset: 238.76 - (238.76 * (tradeLog.confidence || 0.75)) }}
                                  transition={{ duration: 1.5, ease: "easeOut" }}
                                  className="text-primary"
                                  strokeLinecap="round"
                                />
                              </svg>
                              <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className="text-2xl font-extrabold tracking-tighter text-white drop-shadow-md">
                                  {((tradeLog.confidence || 0) * 100).toFixed(0)}
                                  <span className="text-xs text-primary ml-0.5">%</span>
                                </span>
                              </div>
                            </div>
                            <div>
                              <p className="text-[10px] font-extrabold text-muted-foreground uppercase tracking-[0.2em] mb-1 tooltip-trigger">AI Confidence</p>
                              <div className="h-1 w-20 bg-white/10 rounded-full overflow-hidden">
                                <div className="h-full bg-primary/40 w-full animate-shimmer" />
                              </div>
                            </div>
                          </div>
                          <div className="text-right max-w-[200px]">
                            <p className="text-[11px] font-bold text-white/90 leading-relaxed italic border-l-2 border-primary/30 pl-3">
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

              {/* View All Modal - Full Information */}
              <AnimatePresence>
                {viewAllModalOpen && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-md"
                    onClick={() => setViewAllModalOpen(false)}
                  >
                    <motion.div
                      initial={{ scale: 0.95, y: 20 }}
                      animate={{ scale: 1, y: 0 }}
                      exit={{ scale: 0.95, y: 20 }}
                      onClick={(e) => e.stopPropagation()}
                      className="max-w-7xl w-full max-h-[90vh] overflow-y-auto glass-card p-8 rounded-3xl border-2 border-primary/20"
                    >
                      <div className="flex items-center justify-between mb-8 sticky top-0 bg-black/60 backdrop-blur-md pb-4 border-b border-white/10 -mt-8 pt-8 -mx-8 px-8">
                        <div>
                          <h2 className="text-3xl font-bold">All AI Trade Analysis</h2>
                          <p className="text-sm text-muted-foreground mt-1">{_trade_logs.length} Active Positions</p>
                        </div>
                        <button
                          onClick={() => setViewAllModalOpen(false)}
                          className="p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all"
                        >
                          <X className="w-6 h-6" />
                        </button>
                      </div>

                      <div className="space-y-6">
                        {_trade_logs.map((log: any, idx: number) => (
                          <motion.div
                            key={log.id || idx}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.1 }}
                            className="p-6 rounded-2xl bg-gradient-to-br from-white/5 to-purple-500/5 border border-white/10 hover:border-purple-500/30 transition-all"
                          >
                            {/* Header */}
                            <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/10">
                              <div className="flex items-center gap-4">
                                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center font-bold text-xl border border-primary/30">
                                  {log.symbol?.substring(0, 2) || 'BTC'}
                                </div>
                                <div>
                                  <h3 className="text-2xl font-bold">{log.symbol} {log.side}</h3>
                                  <p className="text-sm text-muted-foreground">Entry @ ${log.entry_price?.toLocaleString() || '0'}</p>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="text-sm text-muted-foreground uppercase tracking-wider mb-1">AI Confidence</p>
                                <p className="text-4xl font-bold text-primary">{((log.confidence || 0) * 100).toFixed(0)}%</p>
                              </div>
                            </div>

                            {/* Content Grid */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                              {/* Left Column */}
                              <div className="space-y-4">
                                {/* Strategy */}
                                <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                                  <div className="flex items-center gap-2 mb-2">
                                    <Target className="w-4 h-4 text-primary" />
                                    <h5 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">Strategy</h5>
                                  </div>
                                  <p className="text-xs font-bold text-primary mb-2">{log.strategy?.name || 'N/A'} • {log.strategy?.timeframe || 'N/A'}</p>
                                  <p className="text-sm text-white/80 leading-relaxed">{log.entry_rationale || 'No rationale provided'}</p>
                                </div>

                                {/* Confluence */}
                                {log.strategy?.confluence_factors && (
                                  <div>
                                    <div className="flex items-center gap-2 mb-2">
                                      <Shield className="w-4 h-4 text-primary" />
                                      <h5 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">Confluence ({log.strategy.confluence_factors.length} factors)</h5>
                                    </div>
                                    <div className="grid grid-cols-1 gap-2">
                                      {log.strategy.confluence_factors.map((factor: any, i: number) => (
                                        <div key={i} className="flex items-start gap-2 p-2 rounded-lg bg-white/5 border border-white/5">
                                          <CheckCircle className="w-3 h-3 text-primary mt-0.5 flex-shrink-0" />
                                          <span className="text-xs text-white/80">{factor}</span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>

                              {/* Right Column */}
                              <div className="space-y-4">
                                {/* Risk Management */}
                                <div>
                                  <div className="flex items-center gap-2 mb-2">
                                    <Activity className="w-4 h-4 text-secondary" />
                                    <h5 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">Risk Management</h5>
                                  </div>
                                  <div className="grid grid-cols-2 gap-2">
                                    <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                                      <p className="text-[10px] font-bold text-red-300 uppercase mb-1">Stop Loss</p>
                                      <p className="text-lg font-bold text-red-400">${log.risk_management?.stop_loss?.toLocaleString() || '0'}</p>
                                    </div>
                                    <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                                      <p className="text-[10px] font-bold text-primary uppercase mb-1">TP1 ({log.risk_management?.tp1_size_pct || 0}%)</p>
                                      <p className="text-lg font-bold text-primary">${log.risk_management?.take_profit_1?.toLocaleString() || '0'}</p>
                                    </div>
                                    <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
                                      <p className="text-[10px] font-bold text-primary uppercase mb-1">TP2 ({log.risk_management?.tp2_size_pct || 0}%)</p>
                                      <p className="text-lg font-bold text-primary">${log.risk_management?.take_profit_2?.toLocaleString() || '0'}</p>
                                    </div>
                                    <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                                      <p className="text-[10px] font-bold text-white/40 uppercase mb-1">Risk</p>
                                      <p className="text-lg font-bold text-white">${log.risk_management?.risk_usd?.toFixed(2) || '0'}</p>
                                      <p className="text-[9px] text-white/40">{log.risk_management?.risk_pct?.toFixed(2) || '0'}% equity</p>
                                    </div>
                                  </div>
                                </div>

                                {/* AI Notes */}
                                {log.ai_notes && (() => {
                                  const notes = log.ai_notes;
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
                                  }

                                  return (
                                    <div className="p-3 rounded-xl bg-gradient-to-br from-purple-900/20 to-blue-900/20 border border-purple-500/20">
                                      <div className="flex items-center gap-2 mb-2">
                                        <BrainCircuit className="w-3 h-3 text-purple-400" />
                                        <p className="text-xs font-bold uppercase tracking-wider text-purple-300">AI Notes</p>
                                      </div>
                                      <div className="space-y-2">
                                        {ptText && (
                                          <div className="p-2 bg-black/20 rounded-lg">
                                            <div className="flex items-center gap-1 mb-1">
                                              <span className="text-sm">🇧🇷</span>
                                              <span className="text-[8px] font-bold uppercase text-green-400">PT-BR</span>
                                            </div>
                                            <p className="text-[10px] text-white/80 leading-relaxed">{ptText}</p>
                                          </div>
                                        )}
                                        {enText && (
                                          <div className="p-2 bg-black/20 rounded-lg">
                                            <div className="flex items-center gap-1 mb-1">
                                              <span className="text-sm">🇺🇸</span>
                                              <span className="text-[8px] font-bold uppercase text-blue-400">EN-US</span>
                                            </div>
                                            <p className="text-[10px] text-white/80 leading-relaxed">{enText}</p>
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  );
                                })()}
                              </div>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}

          {activeTab === 'charts' && (
            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.4 }}
              className="space-y-8"
            >
              <div className="flex flex-col gap-2">
                <h2 className="text-3xl font-bold tracking-tight">{isPt ? 'Gráficos de Mercado Ativos' : 'Active Market Charts'}</h2>
                <p className="text-muted-foreground">{isPt ? 'Análise em tempo real das posições da frota' : 'Real-time analysis for current fleet positions'}</p>
              </div>

              {positions.length > 0 ? (
                <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                  {positions.map((pos, i) => {
                    // Find matching trade log for this position
                    const posTradeLog = _trade_logs?.find((log: any) => log.symbol === pos.symbol) || tradeLog;

                    return (
                      <GlassCard key={pos.symbol} delay={i * 0.1} className="!p-0 border-none bg-transparent">
                        <div className="p-4 space-y-3 border-b border-white/5 bg-white/[0.02]">
                          {/* Header Row */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                                <Activity className="w-5 h-5 text-primary" />
                              </div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="font-bold text-white uppercase">{pos.symbol}</span>
                                  <span className={cn(
                                    "text-[10px] px-2 py-0.5 rounded-full font-bold uppercase",
                                    pos.side === 'Long' ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                                  )}>
                                    {pos.side} {pos.leverage}x
                                  </span>
                                </div>
                                <p className="text-[10px] text-muted-foreground uppercase tracking-widest">Entry: ${Number(pos.entry_price).toLocaleString()}</p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className={cn(
                                "text-lg font-bold tracking-tighter",
                                pos.unrealized_pnl >= 0 ? "text-primary" : "text-red-400"
                              )}>
                                {pos.unrealized_pnl >= 0 ? '+' : ''}${Number(pos.unrealized_pnl).toFixed(2)}
                              </p>
                              <p className="text-[10px] text-muted-foreground uppercase tracking-widest">{isPt ? 'PnL Não Realizado' : 'Unrealized PnL'}</p>
                            </div>
                          </div>

                          {/* TP/SL Row */}
                          {(pos.stop_loss || pos.take_profit || posTradeLog?.risk_management) && (
                            <div className="grid grid-cols-2 gap-2">
                              {(pos.stop_loss || posTradeLog?.risk_management?.stop_loss) && (
                                <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/20">
                                  <p className="text-[9px] font-bold text-red-300 uppercase tracking-wider mb-0.5">Stop Loss</p>
                                  <p className="text-sm font-bold text-red-400">${Number(pos.stop_loss || posTradeLog?.risk_management?.stop_loss).toLocaleString()}</p>
                                </div>
                              )}
                              {(pos.take_profit || posTradeLog?.risk_management?.take_profit_1) && (
                                <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
                                  <p className="text-[9px] font-bold text-primary uppercase tracking-wider mb-0.5">Take Profit</p>
                                  <p className="text-sm font-bold text-primary">${Number(pos.take_profit || posTradeLog?.risk_management?.take_profit_1).toLocaleString()}</p>
                                </div>
                              )}
                            </div>
                          )}

                          {/* AI Entry Rationale */}
                          {posTradeLog?.entry_rationale && (
                            <div className="p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/20">
                              <p className="text-[9px] font-bold text-purple-300 uppercase tracking-wider mb-1">{isPt ? 'Razão de Entrada IA' : 'AI Entry Reason'}</p>
                              <p className="text-[10px] text-white/80 leading-relaxed line-clamp-2">{posTradeLog.entry_rationale}</p>
                            </div>
                          )}
                        </div>
                        <div className="h-[500px]">
                          <TradingViewChart symbol={pos.symbol} theme={settings.theme} />
                        </div>
                      </GlassCard>
                    );
                  })}
                </div>
              ) : (
                <div className="h-[60vh] flex flex-col items-center justify-center rounded-[32px] border-2 border-dashed border-white/5 bg-white/[0.01]">
                  <div className="relative mb-6">
                    <LineChart className="w-16 h-16 text-muted-foreground/20" />
                    <motion.div
                      animate={{ scale: [1, 1.2, 1], opacity: [0.1, 0.3, 0.1] }}
                      transition={{ duration: 4, repeat: Infinity }}
                      className="absolute inset-0 bg-primary blur-3xl rounded-full"
                    />
                  </div>
                  <h3 className="text-xl font-bold mb-2">{isPt ? 'Nenhuma Posição Ativa' : 'No Active Positions'}</h3>
                  <p className="text-muted-foreground text-center max-w-sm px-8">
                    {isPt ? 'Posições abertas aparecerão automaticamente aqui com gráficos TradingView em tempo real.' : 'Open positions will automatically appear here with real-time TradingView charts.'}
                  </p>
                </div>
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
                      <h3 className="text-sm font-bold text-muted-foreground uppercase tracking-widest">{isPt ? 'Valor Total' : 'Total Value'}</h3>
                      <span className="px-1.5 py-0.5 rounded bg-white/10 text-[10px] font-bold text-white/50">{isPt ? 'Combinado' : 'Combined'}</span>
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
                        <span className="block text-[9px] mb-0.5">{isPt ? 'PnL Não Realizado' : 'Unrealized PnL'}</span>
                        <span className={cn("text-white", (status?.unrealized_pnl || 0) >= 0 ? "text-[#00ff9d]" : "text-red-500")}>
                          {(status?.unrealized_pnl || 0) >= 0 ? '+' : ''}${Number(status?.unrealized_pnl || 0).toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className="block text-[9px] mb-0.5">{isPt ? 'Uso Margem' : 'Margin Usage'}</span>
                        <span className="text-warning">{status?.margin_usage || 0}%</span>
                      </div>
                      <div>
                        <span className="block text-[9px] mb-0.5">{isPt ? 'Alavancagem' : 'Leverage'}</span>
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
                      <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{isPt ? 'PnL Total (Combinado)' : 'All PnL (Combined)'}</p>
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
                            <p className="text-xs font-bold uppercase tracking-widest">{isPt ? 'Dados insuficientes para este período' : 'Insufficient data for this period'}</p>
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
                      <p className="text-xs font-bold uppercase tracking-widest">{isPt ? 'Sincronizando Histórico Blockchain...' : 'Syncing Blockchain History...'}</p>
                    </div>
                  )}
                </div>

                {/* Footer Stats similar to HyperDash bottom bar */}
                {/* Position Distribution Bar */}
                <div className="mb-8 p-5 rounded-2xl bg-black/20 border border-white/5 shadow-inner">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">{isPt ? 'Distribuição de Posições (Ao Vivo)' : 'Live Position Distribution'}</p>
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
                        {isPt ? {
                          'Asset Positions': 'Posições',
                          'Open Orders': 'Ordens Abertas',
                          'Recent Fills': 'Execuções Recentes',
                          'Completed Trades': 'Trades Completos',
                          'TWAP': 'TWAP',
                          'Deposits & Withdrawals': 'Depósitos & Saques'
                        }[tab] : tab}
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
                            <th className="px-4 py-3 text-left text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">{isPt ? 'Moeda' : 'Symbol'}</th>
                            <th className="px-4 py-3 text-left text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">{isPt ? 'Lado' : 'Side'}</th>
                            <th className="px-4 py-3 text-right text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">{isPt ? 'Investimento' : 'Size (USD)'}</th>
                            <th className="px-4 py-3 text-right text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">{isPt ? 'Preço Entrada' : 'Entry Price'}</th>
                            <th className="px-4 py-3 text-right text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">{isPt ? 'Preço Atual' : 'Mark Price'}</th>
                            <th className="px-4 py-3 text-right text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">{isPt ? 'PnL (USD)' : 'PnL (USD)'}</th>
                            <th className="px-4 py-3 text-right text-[10px] font-extrabold text-white/40 uppercase tracking-[0.2em]">{isPt ? 'Funding' : 'Funding'}</th>
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
                                {isPt ? 'Nenhuma posição ativa na frota' : 'No active positions found in fleet'}
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


          {activeTab === 'news' && (
            <motion.div
              key="news"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
              className="space-y-8"
            >
              <div className="flex flex-col gap-2">
                <h2 className="text-3xl font-bold tracking-tight">{isPt ? 'Inteligência de Mercado' : 'Market Intelligence'}</h2>
                <p className="text-muted-foreground">{isPt ? 'Notícias globais em tempo real, eventos econômicos e destaques' : 'Real-time global news, economic events and top movers'}</p>
              </div>

              {/* Global Market Stats */}
              <GlassCard className="border border-cyan-500/20" delay={0.1}>
                <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                  <Globe className="w-5 h-5 text-cyan-400" />
                  <h2 className="text-lg font-bold">{isPt ? 'Visão Geral do Mercado' : 'Global Market Overview'}</h2>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-xl bg-white/5 text-center">
                    <p className="text-[10px] text-white/50 uppercase tracking-widest mb-2 font-bold">{isPt ? 'Cap. de Mercado' : 'Market Cap'}</p>
                    <p className="text-2xl font-bold">{globalMarket?.market_cap ? `$${(globalMarket.market_cap / 1e12).toFixed(2)}T` : "$0.00"}</p>
                    {globalMarket?.market_cap_change_24h !== undefined && (
                      <p className={cn("text-[10px] mt-1 font-bold", globalMarket.market_cap_change_24h >= 0 ? "text-primary" : "text-secondary")}>
                        {globalMarket.market_cap_change_24h >= 0 ? "+" : ""}{globalMarket.market_cap_change_24h.toFixed(2)}%
                      </p>
                    )}
                  </div>
                  <div className="p-4 rounded-xl bg-white/5 text-center">
                    <p className="text-[10px] text-white/50 uppercase tracking-widest mb-2 font-bold">{isPt ? 'Volume 24h' : '24h Volume'}</p>
                    <p className="text-2xl font-bold">{globalMarket?.volume_24h ? `$${(globalMarket.volume_24h / 1e9).toFixed(2)}B` : "$0.00"}</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white/5 text-center">
                    <p className="text-[10px] text-white/50 uppercase tracking-widest mb-2 font-bold">{isPt ? 'Dominância BTC' : 'BTC Dominance'}</p>
                    <p className="text-2xl font-bold">{globalMarket?.btc_dominance?.toFixed(1) || "0.0"}%</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white/5 text-center">
                    <p className="text-[10px] text-white/50 uppercase tracking-widest mb-2 font-bold">{isPt ? 'Dominância ETH' : 'ETH Dominance'}</p>
                    <p className="text-2xl font-bold">{globalMarket?.eth_dominance?.toFixed(1) || "0.0"}%</p>
                  </div>
                </div>
              </GlassCard>

              {/* Main Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Crypto News - Real-time */}
                <GlassCard className="border border-primary/20" delay={0.2}>
                  <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                    <Zap className="w-5 h-5 text-primary" />
                    <h2 className="text-lg font-bold">{isPt ? 'Notícias em Tempo Real' : 'Real-time News Feed'}</h2>
                  </div>
                  <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2 no-scrollbar">
                    {realtimeNews.length > 0 ? (
                      realtimeNews.map((item, i) => (
                        <a
                          key={i}
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/10 hover:border-primary/30 transition-all group"
                        >
                          <p className="font-bold text-sm mb-2 line-clamp-2 group-hover:text-primary transition-colors">{item.title}</p>
                          <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider">
                            <span className="text-primary">{item.source || "CryptoCompare"}</span>
                            <span className="text-white/40">{item.published_at ? new Date(item.published_at).toLocaleTimeString() : ""}</span>
                          </div>
                        </a>
                      ))
                    ) : (
                      <div className="text-center py-20 opacity-20">
                        <Newspaper className="w-12 h-12 mx-auto mb-4" />
                        <p className="text-xs font-bold uppercase tracking-widest">{isPt ? 'Nenhuma notícia disponível' : 'No news available'}</p>
                      </div>
                    )}
                  </div>
                </GlassCard>

                {/* Economic Calendar */}
                <GlassCard className="border border-yellow-500/20" delay={0.3}>
                  <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                    <Calendar className="w-5 h-5 text-yellow-400" />
                    <h2 className="text-lg font-bold">{isPt ? 'Calendário Econômico Global' : 'Global Economic Calendar'}</h2>
                  </div>
                  <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2 no-scrollbar">
                    {calendarEvents.length > 0 ? (
                      calendarEvents.map((event, i) => (
                        <div
                          key={i}
                          className={cn(
                            "p-4 rounded-2xl bg-white/5 border-l-4 transition-all hover:bg-white/[0.08]",
                            event.importance === "HIGH" ? "border-secondary shadow-[0_0_15px_rgba(255,59,48,0.1)]" : "border-yellow-500/50"
                          )}
                        >
                          <div className="flex justify-between items-start gap-4 mb-2">
                            <div className="flex flex-col gap-1">
                              <p className="font-bold text-sm leading-tight text-white/90">{event.event || "Unknown"}</p>
                              <div className="flex items-center gap-1.5 mt-1">
                                <span className="text-[9px] font-black bg-white/10 px-1.5 py-0.5 rounded text-white/60">{event.country}</span>
                                <div className="flex gap-0.5">
                                  {Array.from({ length: event.impact === 'high' ? 3 : event.impact === 'medium' ? 2 : 1 }).map((_, idx) => (
                                    <span key={idx} className={cn("text-[10px]", event.impact === 'high' ? "text-secondary" : "text-yellow-500")}>★</span>
                                  ))}
                                </div>
                              </div>
                            </div>
                            <span className="text-[10px] font-mono text-white/50 whitespace-nowrap bg-black/40 px-2 py-1 rounded border border-white/5">
                              {event.date !== "TBD" ? (event.date.includes(',') ? event.date.split(',').slice(1).join(',').trim() : event.date) : "TBD"} | {event.time || ""}
                            </span>
                          </div>
                          {(event.actual || event.estimate || event.previous) && (
                            <div className="grid grid-cols-3 gap-2 mt-3 text-[10px] font-bold uppercase tracking-widest border-t border-white/5 pt-2">
                              <div className="flex flex-col">
                                <span className="text-white/30 text-[8px] mb-0.5">{isPt ? 'Atual' : 'Actual'}</span>
                                <span className={cn("text-white", event.actual ? "text-primary" : "text-white/20")}>{event.actual || '---'}</span>
                              </div>
                              <div className="flex flex-col">
                                <span className="text-white/30 text-[8px] mb-0.5">{isPt ? 'Estimado' : 'Estimate'}</span>
                                <span className="text-white/60">{event.estimate || '---'}</span>
                              </div>
                              <div className="flex flex-col">
                                <span className="text-white/30 text-[8px] mb-0.5">{isPt ? 'Anterior' : 'Previous'}</span>
                                <span className="text-white/60">{event.previous || '---'}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-20 opacity-20">
                        <Calendar className="w-12 h-12 mx-auto mb-4" />
                        <p className="text-xs font-bold uppercase tracking-widest">{isPt ? 'Nenhum evento futuro' : 'No upcoming events'}</p>
                      </div>
                    )}
                  </div>
                </GlassCard>

                {/* Top Movers */}
                <GlassCard className="border border-primary/20" delay={0.4}>
                  <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                    <TrendingUp className="w-5 h-5 text-primary" />
                    <h2 className="text-lg font-bold">Top Gainers (24h)</h2>
                  </div>
                  <div className="space-y-2">
                    {topGainers.length > 0 ? (
                      topGainers.map((coin, i) => (
                        <div key={i} className="flex items-center justify-between p-3.5 rounded-2xl bg-white/5 border border-white/5 hover:border-primary/30 transition-all">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-xl bg-primary/10 flex items-center justify-center text-xs font-black text-primary border border-primary/20">
                              {i + 1}
                            </div>
                            <div>
                              <p className="font-bold text-sm leading-none mb-1">{coin.name}</p>
                              <p className="text-[10px] font-bold text-white/40 uppercase tracking-widest">{coin.symbol}</p>
                            </div>
                          </div>
                          <span className="text-primary font-black text-sm">
                            +{coin.percent_change_24h?.toFixed(2) || 0}%
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-10 opacity-20 text-[10px] font-bold uppercase tracking-widest">Awaiting market data...</div>
                    )}
                  </div>
                </GlassCard>

                <GlassCard className="border border-secondary/20" delay={0.5}>
                  <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                    <TrendingDown className="w-5 h-5 text-secondary" />
                    <h2 className="text-lg font-bold">{isPt ? 'Maiores Baixas (24h)' : 'Top Losers (24h)'}</h2>
                  </div>
                  <div className="space-y-2">
                    {topLosers.length > 0 ? (
                      topLosers.map((coin, i) => (
                        <div key={i} className="flex items-center justify-between p-3.5 rounded-2xl bg-white/5 border border-white/5 hover:border-secondary/30 transition-all">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-xl bg-secondary/10 flex items-center justify-center text-xs font-black text-secondary border border-secondary/20">
                              {i + 1}
                            </div>
                            <div>
                              <p className="font-bold text-sm leading-none mb-1">{coin.name}</p>
                              <p className="text-[10px] font-bold text-white/40 uppercase tracking-widest">{coin.symbol}</p>
                            </div>
                          </div>
                          <span className="text-secondary font-black text-sm">
                            {coin.percent_change_24h?.toFixed(2) || 0}%
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-10 opacity-20 text-[10px] font-bold uppercase tracking-widest">{isPt ? 'Aguardando dados...' : 'Awaiting market data...'}</div>
                    )}
                  </div>
                </GlassCard>
              </div>

              {/* --- NEW MARKET INTELLIGENCE CARDS --- */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">

                {/* 1. Rainbow Chart & Altcoin Season */}
                <GlassCard className="border border-purple-500/20" delay={0.6}>
                  <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                    <BarChart3 className="w-5 h-5 text-purple-400" />
                    <h2 className="text-lg font-bold">{isPt ? 'Gráfico Arco-íris & Altseason' : 'Bitcoin Rainbow & Altseason'}</h2>
                  </div>

                  <div className="space-y-6">
                    {/* Rainbow Chart Section */}
                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="text-sm font-bold text-white/70 uppercase tracking-widest flex items-center gap-2">
                          <i className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
                          BTC Rainbow Band
                        </h3>
                        <span className={cn("px-2 py-1 rounded text-[10px] font-black uppercase",
                          rainbowData?.band === 'sell' || rainbowData?.band === 'max_bubble' ? "bg-red-500/20 text-red-400" :
                            rainbowData?.band === 'buy' || rainbowData?.band === 'fire_sale' ? "bg-green-500/20 text-green-400" :
                              "bg-yellow-500/20 text-yellow-400"
                        )}>
                          {rainbowData?.band_name || "Loading..."}
                        </span>
                      </div>

                      {rainbowData && (
                        <div className="space-y-3">
                          <div className="flex justify-between text-xs font-bold text-white/50">
                            <span>{isPt ? 'Preço BTC:' : 'BTC Price:'} <span className="text-white">${rainbowData.btc_price?.toLocaleString()}</span></span>
                            <span>{isPt ? 'Preço Justo:' : 'Fair Value:'} <span className="text-white">${rainbowData.log_price?.toLocaleString()}</span></span>
                          </div>
                          <div className="relative h-2 bg-white/10 rounded-full overflow-hidden">
                            <div
                              className={cn("absolute top-0 bottom-0 w-full transition-all duration-1000",
                                rainbowData.band_index <= 2 ? "bg-gradient-to-r from-green-500 to-green-300" :
                                  rainbowData.band_index >= 6 ? "bg-gradient-to-r from-red-500 to-red-300" :
                                    "bg-gradient-to-r from-yellow-500 to-orange-500"
                              )}
                              style={{ width: `${Math.min(100, Math.max(0, ((rainbowData.band_index ?? 4) / 8) * 100))}%` }}
                            />
                          </div>
                          <div className="flex justify-between text-[8px] text-white/20 font-black uppercase tracking-widest">
                            <span>{isPt ? 'Promoção' : 'Fire Sale'}</span>
                            <span>HODL</span>
                            <span>{isPt ? 'Bolha' : 'Bubble'}</span>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Altcoin Season Section */}
                    <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="text-sm font-bold text-white/70 uppercase tracking-widest flex items-center gap-2">
                          <Gauge className="w-3 h-3 text-cyan-400" />
                          {isPt ? 'Índice Altcoin Season' : 'Altcoin Season Index'}
                        </h3>
                        <span className="text-xl font-black text-cyan-400">
                          {altSeasonData?.blockchaincenter?.season_index !== undefined ? altSeasonData.blockchaincenter.season_index : (altSeasonData?.index || "---")}
                        </span>
                      </div>
                      {(altSeasonData?.blockchaincenter?.season_index !== undefined || altSeasonData?.index !== undefined) && (
                        <div className="space-y-2">
                          <div className="relative h-4 bg-white/10 rounded-full overflow-hidden border border-white/5">
                            <div
                              className="absolute top-0 bottom-0 left-0 bg-gradient-to-r from-orange-500 via-yellow-500 to-cyan-500 transition-all duration-1000"
                              style={{ width: `${altSeasonData.blockchaincenter?.season_index ?? altSeasonData.index ?? 0}%` }}
                            />
                            {/* Markers */}
                            <div className="absolute top-0 bottom-0 left-[25%] w-0.5 bg-white/30" />
                            <div className="absolute top-0 bottom-0 left-[75%] w-0.5 bg-white/30" />
                          </div>
                          <div className="flex justify-between text-[9px] font-bold uppercase tracking-widest pt-1">
                            <span className={cn((altSeasonData.blockchaincenter?.season_index ?? altSeasonData.index) < 25 ? "text-orange-400" : "text-white/30")}>Bitcoin Season</span>
                            <span className={cn((altSeasonData.blockchaincenter?.season_index ?? altSeasonData.index) > 75 ? "text-cyan-400" : "text-white/30")}>Altcoin Season</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </GlassCard>

                {/* 2. Halving & ETH Gas */}
                <GlassCard className="border border-blue-500/20" delay={0.7}>
                  <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                    <Timer className="w-5 h-5 text-blue-400" />
                    <h2 className="text-lg font-bold">{isPt ? 'Halving & Network Stats' : 'Halving & Network Stats'}</h2>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Halving */}
                    <div className="p-4 rounded-xl bg-black/20 border border-white/5 flex flex-col justify-between relative overflow-hidden group">
                      <div className="bg-orange-500/5 absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                      <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-1">{isPt ? 'Próximo Halving BTC' : 'Next BTC Halving'}</h3>
                      <p className="text-xs text-white/50 mb-3">({isPt ? 'Est:' : 'Est:'} {halvingData?.next_halving_date || '---'})</p>

                      <div className="text-center py-2">
                        <span className="text-2xl font-black text-orange-500 tracking-tighter">
                          {halvingData?.days_until_halving !== undefined ? halvingData.days_until_halving : '---'}
                        </span>
                        <span className="text-[10px] block font-bold text-white/30 uppercase mt-1">{isPt ? 'Dias Restantes' : 'Days Remaining'}</span>
                      </div>
                    </div>

                    {/* ETH Gas */}
                    <div className="p-4 rounded-xl bg-black/20 border border-white/5 flex flex-col justify-between relative overflow-hidden group">
                      <div className="bg-blue-500/5 absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                      <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-2 flex items-center gap-2">
                        <Fuel className="w-3 h-3 text-white/40" /> {isPt ? 'Gás Ethereum (Gwei)' : 'ETH Gas'}
                      </h3>
                      {ethGasData && ethGasData.standard ? (
                        <div className="space-y-2">
                          <div className="flex justify-between items-center text-xs border-b border-white/5 pb-1">
                            <span className="text-white/50">{isPt ? 'Padrão' : 'Standard'}</span>
                            <span className="font-bold text-blue-400">{ethGasData.standard || 0}</span>
                          </div>
                          <div className="flex justify-between items-center text-xs">
                            <span className="text-white/50">{isPt ? 'Rápido' : 'Fast'}</span>
                            <span className="font-bold text-green-400">{ethGasData.fast || 0}</span>
                          </div>
                        </div>
                      ) : (
                        <div className="text-center text-[10px] opacity-30 uppercase">{isPt ? 'Sem Dados' : 'No Data'}</div>
                      )}
                    </div>
                  </div>

                  {/* Funding Rates Mini-Table */}
                  <div className="mt-6">
                    <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3 flex items-center gap-2">
                      <Activity className="w-3 h-3" /> {isPt ? 'Taxas de Financiamento (Top)' : 'Top Funding Rates (Binance)'}
                    </h3>
                    {fundingData && fundingData.funding_rates ? (
                      <div className="grid grid-cols-3 gap-2">
                        {fundingData.funding_rates.slice(0, 3).map((rate: any, i: number) => (
                          <div key={i} className="bg-white/5 rounded-lg p-2 text-center border border-white/5">
                            <div className="text-[9px] font-black text-white/60 mb-1">{rate.symbol}</div>
                            <div className={cn("text-xs font-bold", parseFloat(rate.lastFundingRate) > 0.01 ? "text-orange-400" : "text-green-400")}>
                              {(parseFloat(rate.lastFundingRate) * 100).toFixed(4)}%
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (<div className="text-xs text-center opacity-30">Loading...</div>)}
                  </div>
                </GlassCard>

                {/* 3. DeFi TVL & Trending */}
                <GlassCard className="border border-green-500/20" delay={0.8}>
                  <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                    <Layers className="w-5 h-5 text-green-400" />
                    <h2 className="text-lg font-bold">{isPt ? 'DeFi & Trending' : 'DeFi & Trending'}</h2>
                  </div>

                  <div className="space-y-6">
                    {/* TVL */}
                    <div className="flex items-center justify-between p-4 bg-gradient-to-r from-green-500/10 to-transparent rounded-xl border border-green-500/20">
                      <div>
                        <p className="text-[10px] font-bold text-green-400 uppercase tracking-widest mb-1">{isPt ? 'Valor Total Bloqueado (DeFi)' : 'Total Value Locked'}</p>
                        <p className="text-2xl font-black text-white drop-shadow-md">
                          {tvlData?.total_tvl ? `$${(tvlData.total_tvl / 1e9).toFixed(2)}B` : '---'}
                        </p>
                      </div>
                      <Layers className="w-8 h-8 text-green-500/20" />
                    </div>

                    {/* Trending Coins (Simple List) */}
                    <div>
                      <h3 className="text-[10px] font-bold text-white/40 uppercase tracking-widest mb-3 flex items-center gap-2">
                        <Flame className="w-3 h-3 text-orange-500" /> {isPt ? 'Em Alta no CoinGecko' : 'Trending on CoinGecko'}
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {trendingCoins.length > 0 ? (
                          trendingCoins.slice(0, 4).map((coin: any, i: number) => (
                            <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-white/5 border border-white/5">
                              <img src={coin.thumb} alt={coin.symbol} className="w-5 h-5 rounded-full opacity-80" />
                              <div className="flex flex-col">
                                <span className="text-xs font-bold">{coin.name} <span className="text-[9px] text-white/40">{coin.symbol}</span></span>
                                <span className="text-[9px] text-white/50">Rank #{coin.rank}</span>
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="text-[10px] opacity-30 uppercase col-span-2 text-center py-2">{isPt ? 'Sem Dados de Tendência' : 'No Trending Data'}</div>
                        )}
                      </div>
                    </div>
                  </div>
                </GlassCard>

                {/* 4. Long/Short Ratio */}
                <GlassCard className="border border-pink-500/20" delay={0.9}>
                  <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                    <Activity className="w-5 h-5 text-pink-400" />
                    <h2 className="text-lg font-bold">{isPt ? 'Sentimento Futuros' : 'Futures Sentiment'}</h2>
                  </div>

                  {longShortData && longShortData.global_ratio ? (
                    <div className="space-y-4">
                      {longShortData.global_ratio.map((item: any, i: number) => (
                        <div key={i} className="p-3 rounded-xl bg-white/5 border border-white/5">
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-xs font-bold text-white/70">{item.symbol} Long/Short</span>
                            <div className="flex items-center gap-3">
                              {item.openInterest && (
                                <span className="text-[9px] font-bold text-white/30 uppercase">OI: <span className="text-white/60">{item.openInterest}</span></span>
                              )}
                              <span className="text-xs font-black text-pink-400">{parseFloat(item.longShortRatio).toFixed(2)}</span>
                            </div>
                          </div>

                          <div className="relative h-4 bg-white/10 rounded-full overflow-hidden flex text-[8px] font-bold text-black/70">
                            <div
                              className="h-full bg-green-400 flex items-center justify-center transition-all duration-500"
                              style={{ width: `${parseFloat(item.longAccount) * 100}%` }}
                            >
                              {(parseFloat(item.longAccount) * 100).toFixed(0)}% L
                            </div>
                            <div
                              className="h-full bg-red-400 flex items-center justify-center transition-all duration-500"
                              style={{ width: `${parseFloat(item.shortAccount) * 100}%` }}
                            >
                              {(parseFloat(item.shortAccount) * 100).toFixed(0)}% S
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-10 opacity-20 text-[10px] font-bold uppercase">{isPt ? 'Carregando Taxas...' : 'Loading Ratios...'}</div>
                  )}
                </GlassCard>

              </div>

            </motion.div>
          )}


          {
            activeTab === 'chat' && (
              <motion.div key="chat" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.3 }}>
                <GlassCard className="h-[700px] flex flex-col">
                  <div className="flex items-center gap-4 mb-8">
                    <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400">
                      <MessageSquare className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-2xl font-bold tracking-tight">{isPt ? 'Comunicação Frota IA' : 'AI Fleet Communication'}</h3>
                      <p className="text-xs text-muted-foreground font-bold uppercase tracking-widest mt-1">{isPt ? 'Link Neural Direto com Núcleo do Bot' : 'Direct Neural Link with Bot Core'}</p>
                    </div>
                  </div>

                  <div className="flex-1 overflow-y-auto space-y-4 mb-6 pr-2 no-scrollbar">
                    {chatMessages.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center opacity-20">
                        <BrainCircuit className="w-16 h-16 mb-4 animate-pulse" />
                        <p className="text-sm font-bold uppercase tracking-widest">{isPt ? 'Inicie uma conversa...' : 'Start a conversation...'}</p>
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
                              <span className="text-xs font-bold">{isPt ? 'VOCÊ' : 'YOU'}</span>
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
                    <input type="text" value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyPress={e => e.key === 'Enter' && sendChatMessage()} placeholder={isPt ? "Pergunte-me qualquer coisa..." : "Ask me anything..."} disabled={chatLoading} className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-primary/50 focus:outline-none text-sm placeholder:text-muted-foreground" />
                    <button onClick={sendChatMessage} disabled={chatLoading || !chatInput.trim()} className="px-6 py-3 rounded-xl bg-primary text-black font-bold flex items-center gap-2">
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                </GlassCard>
              </motion.div>
            )
          }

          {
            activeTab === 'logs' && (
              <motion.div key="logs" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.3 }}>
                <GlassCard className="min-h-[600px] bg-black/60 border border-white/5 font-mono">
                  <div className="flex items-center gap-4 mb-10">
                    <div className="p-3 rounded-2xl bg-white/10 text-white">
                      <Terminal className="w-6 h-6" />
                    </div>
                    <h3 className="text-2xl font-bold tracking-tight">{isPt ? 'Fluxo de Execução' : 'Execution Stream'}</h3>
                  </div>
                  <div className="space-y-3 h-[450px] overflow-y-auto no-scrollbar">
                    {allThoughts?.length > 0 ? (
                      allThoughts.map((thought, i) => (
                        <div key={i} className="text-xs border-b border-white/5 pb-2">
                          <span className="text-muted-foreground mr-3">[{new Date(thought.timestamp).toLocaleTimeString()}]</span>
                          <span className="text-primary mr-2">[{thought.emoji || '🤖'}]</span>
                          <span className="text-white/80">{thought.summary}</span>
                          <span className="ml-2 px-1 rounded bg-white/5 text-[8px] text-muted-foreground">CONF {(thought.confidence * 100).toFixed(0)}%</span>
                        </div>
                      ))
                    ) : (
                      <div className="text-xs text-secondary/70 italic text-center py-20">{isPt ? 'Monitorando link neural seguro...' : 'Monitoring secure neural link...'}</div>
                    )}
                  </div>
                </GlassCard>
              </motion.div>
            )
          }
        </AnimatePresence >

        <footer className="mt-12 pt-8 border-t border-white/5 flex justify-between items-center text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
          <div className="flex gap-8">
            <span>Hyperliquid API: <span className={cn(error ? "text-secondary" : "text-primary")}>{error ? (isPt ? "Offline" : "Offline") : (isPt ? "Conectado" : "Connected")}</span></span>
            <span>OpenAI gpt-4o-mini: <span className="text-primary">{isPt ? "Operacional" : "Operational"}</span></span>
          </div>
          <div>© 2025 Ladder Labs</div>
        </footer>
      </main >

      {/* Animated Background with Floating BTC/ETH Coins */}
      < AnimatedBackground />

      {/* Settings Modal */}
      < SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)
        }
        settings={settings}
        updateSetting={updateSetting}
        resetSettings={resetSettings}
      />
    </div >
  );
}
