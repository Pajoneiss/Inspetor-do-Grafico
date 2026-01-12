"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Timer,
  Gauge,
  BrainCircuit,
  MessageSquare,
  Globe,
  Zap,
  Calendar,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Layers,
  Flame,
  Activity,
  Fuel,
  LineChart,
  LayoutDashboard,
  Settings,
  Menu,
  X,
  Shield,
  Send,
  Terminal,
  Newspaper,
  UserCircle,
  History as HistoryIcon
} from "lucide-react";
import { cn } from "@/lib/utils";
import SettingsModal from "@/components/SettingsModal";
import { useSettings } from "@/hooks/useSettings";
// AnimatedBackground removed for Matrix theme
// UnifiedOverviewCard replaced by HyperDashOverview
import HyperDashOverview from "@/components/HyperDashOverview";
import Link from "next/link";
import Image from "next/image";

// --- Hooks ---
// useIsMobile removed

// --- Types ---
export interface DashboardData {
  equity: number;
  unrealized_pnl: number;
  buying_power: number;
  positions_count: number;
  margin_usage: number;
  last_update: string;
  pnl_24h: number;
  pnl_history_recent?: { timestamp: string; pnl: number }[];
  market_data?: {
    macro?: {
      sp500?: number | string;
      nasdaq?: number | string;
      usd_brl?: number | string;
      btc?: number | string;
      eth?: number | string;
    };
    fear_greed?: number | string;
    market_cap?: number;
  };
  total_exposure?: number;
}

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

interface AIThought {
  id?: string;
  timestamp: string;
  emoji?: string;
  summary: string;
  thought?: string;
  confidence: number;
  actions?: string[];
}

interface TradeLog {
  id?: string;
  symbol: string;
  side: string;
  entry_price: number;
  expected_outcome?: string;
  confidence: number;
  strategy?: {
    name: string;
    timeframe: string;
    confluence_factors: string[];
    setup_quality?: string;
  };
  entry_rationale?: string;
  risk_management?: {
    stop_loss: number;
    take_profit_1: number;
    take_profit_2: number;
    tp1_size_pct: number;
    tp2_size_pct: number;
    risk_usd: number;
    risk_pct: number;
    stop_loss_reason?: string;
    tp1_reason?: string;
    tp2_reason?: string;
  };
  ai_notes?: string;
}

interface HalvingData { ok: boolean; days_until_halving?: number; next_halving_date?: string; days_to_next?: number; next_date?: string; current_block?: number; halving_block?: number }
interface TvlData { ok: boolean; total_tvl: number; total_change_24h?: number }
interface FundingData { ok: boolean; symbol: string; funding_rate: number; funding_time: number; funding_rates?: { symbol: string; lastFundingRate: string }[] }
interface LongShortData { ok: boolean; symbol: string; global_ratio: { symbol: string; longShortRatio: string; longAccount: string; shortAccount: string }[] }
interface AltSeasonData { ok: boolean; altseason_index?: number; is_altseason?: boolean; index?: number; blockchaincenter?: { season_index: number } }
interface EthGasData { ok: boolean; fast: number; standard: number; slow: number }
interface RainbowData { ok: boolean; price?: number; band_index?: number; band_name?: string; band?: string; btc_price?: number; log_price?: number }

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

interface OrderInfo {
  symbol: string;
  type: string;
  side: string;
  price: number;
  size: number;
  trigger_px?: number;
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

interface TransferInfo {
  timestamp?: string;
  type: string;
  amount: number;
  status: string;
}

// --- Components ---

const GlassCard = ({ children, className, delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) => (
  <div
    className={cn(
      "glass-card p-6 overflow-hidden relative group transition-all duration-500 animate-in fade-in slide-in-from-bottom-4",
      "hover:shadow-[0_20px_50px_-12px_rgba(0,0,0,0.5)] hover:border-white/20 hover:-translate-y-1",
      className
    )}
    style={{ animationDelay: `${delay}s` }}
  >
    {/* Animated Gradient Border on Hover */}
    <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
    <div className="relative z-10">{children}</div>
  </div>
);

// Mobile Accordion Card - iPhone folder style
// MobileAccordionCard removed

// StatCard and Sparkline removed as they were not used or were replaced by UnifiedOverviewCard


// Sparkline removed

const MarketBar = ({ data }: { data: { market_cap?: number; fear_greed?: number | string; macro?: Record<string, number | string | null | undefined> } }) => {
  if (!data || !data.macro) return null;
  const { macro } = data;

  const formatValue = (val: number | string | null | undefined, prefix = '', suffix = '') => {
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
      {/* Scroll Container */}
      <div className="flex w-max animate-marquee gap-12 hover:[animation-play-state:paused]">
        {/* Create 4 copies for smooth infinite loop */}
        {[...items, ...items, ...items, ...items].map((item, i) => (
          <div key={i} className="flex items-center gap-2.5">
            <span className="text-[10px] font-extrabold text-white/30 uppercase tracking-[0.2em] whitespace-nowrap">{item.label}</span>
            <span className={cn("text-[11px] font-bold tracking-tight whitespace-nowrap", item.color)}>{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

const TradingViewChart = ({ symbol, theme = 'dark' }: { symbol: string, theme?: 'dark' | 'light' }) => {
  const containerId = React.useId().replace(/:/g, '');

  useEffect(() => {
    const scriptId = 'tradingview-widget-script';
    let script = document.getElementById(scriptId) as HTMLScriptElement;

    const initWidget = () => {
      const gWindow = (window as unknown as { TradingView?: { widget: new (p: Record<string, unknown>) => void } });
      if (gWindow.TradingView) {
        new gWindow.TradingView.widget({
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

// Helper to safely parse dates, returning null for invalid dates
const safeDate = (dateString: string | number | Date | null | undefined): Date | null => {
  if (!dateString) return null;
  const date = new Date(dateString);
  return isNaN(date.getTime()) ? null : date;
};

// --- Error Boundary ---
// --- Error Boundary ---
interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  info: React.ErrorInfo | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, info: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error, info: null };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Dashboard Crash:", error, errorInfo);
    (this as unknown as { setState: (p: { info: React.ErrorInfo }) => void }).setState({ info: errorInfo });
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-black text-white p-10 text-center font-mono">
          <div className="w-20 h-20 rounded-full bg-red-500/20 flex items-center justify-center mb-6 animate-pulse">
            <Shield className="w-10 h-10 text-red-500" />
          </div>
          <h1 className="text-3xl font-bold mb-2 uppercase tracking-tighter text-red-500">System Malfunction</h1>
          <p className="text-muted-foreground max-w-md mb-8">CRITICAL FAILURE DETECTED</p>

          <div className="w-full max-w-3xl bg-black/50 border border-red-500/30 rounded-xl p-6 mb-8 text-left overflow-x-auto shadow-[0_0_30px_rgba(239,68,68,0.1)]">
            <p className="text-red-400 font-bold mb-2">ERROR:</p>
            <p className="text-red-300 mb-4 whitespace-pre-wrap break-all">{this.state.error?.toString() || 'Unknown Error'}</p>

            <p className="text-red-400 font-bold mb-2 text-xs">STACK TRACE:</p>
            <pre className="text-[10px] text-red-white/50 whitespace-pre-wrap font-mono">
              {this.state.info?.componentStack || 'No stack trace available'}
            </pre>
          </div>

          <button
            onClick={() => window.location.reload()}
            className="px-8 py-4 rounded-xl bg-red-600 text-white font-bold uppercase tracking-widest hover:bg-red-700 transition-all shadow-[0_0_20px_rgba(220,38,38,0.5)]"
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
  const [activeTab, setActiveTab] = useState<'overview' | 'charts' | 'news' | 'chat' | 'logs'>('overview');
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_pnlHistory, _setPnlHistory] = useState<{ time: string | number; value: number }[]>([]);
  const [pnlPeriod, setPnlPeriod] = useState<'24H' | '7D' | '30D' | 'ALL'>('24H');
  const [chatMessages, setChatMessages] = useState<{ role: string, content: string }[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [tradeLog, setTradeLog] = useState<TradeLog | null>(null);
  const [_trade_logs, _setTradeLogs] = useState<TradeLog[]>([]);
  const [viewAllModalOpen, setViewAllModalOpen] = useState(false);
  const [fullAnalytics, setFullAnalytics] = useState<FullAnalytics | null>(null);
  const [activeFleetTab, setActiveFleetTab] = useState<'Asset Positions' | 'Open Orders' | 'Recent Fills' | 'Completed Trades' | 'TWAP' | 'Deposits & Withdrawals'>('Asset Positions');
  const [openOrders, setOpenOrders] = useState<OrderInfo[]>([]);
  const [recentFills, setRecentFills] = useState<FillInfo[]>([]);
  const [transfers, setTransfers] = useState<TransferInfo[]>([]);
  const [cryptoPrices, setCryptoPrices] = useState<{ btc: { price: number }, eth: { price: number } } | null>(null);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_aiNotesLang, _setAiNotesLang] = useState<'pt' | 'en'>('pt'); // Language toggle for AI Strategy Core

  // New states for UI improvements (Option B)
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_journalStats, setJournalStats] = useState<{
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
  const [calendarEvents, setCalendarEvents] = useState<Array<{ event: string; country: string; impact: string; importance?: string; date: string; time?: string; actual?: string; estimate?: string; previous?: string }>>([]);
  const [globalMarket, setGlobalMarket] = useState<{ market_cap?: number; volume_24h?: number; btc_dominance?: number; eth_dominance?: number; market_cap_change_24h?: number } | null>(null);
  const [topGainers, setTopGainers] = useState<Array<{ name: string; symbol: string; percent_change_24h: number }>>([]);
  const [topLosers, setTopLosers] = useState<Array<{ name: string; symbol: string; percent_change_24h: number }>>([]);
  // New Market Intelligence States
  const [halvingData, setHalvingData] = useState<HalvingData | null>(null);
  const [tvlData, setTvlData] = useState<TvlData | null>(null);
  const [fundingData, setFundingData] = useState<FundingData | null>(null);
  const [longShortData, setLongShortData] = useState<LongShortData | null>(null);
  const [trendingCoins, setTrendingCoins] = useState<Array<{ thumb: string; symbol: string; name: string; rank: number }>>([]);
  const [altSeasonData, setAltSeasonData] = useState<AltSeasonData | null>(null);
  const [ethGasData, setEthGasData] = useState<EthGasData | null>(null);
  const [rainbowData, setRainbowData] = useState<RainbowData | null>(null);

  const { settings, updateSetting, resetSettings } = useSettings();

  // Language helper
  const isPt = settings.language === 'pt';

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

  const fetchData = useCallback(async () => {
    if (!API_URL) return;

    try {
      const [statusRes, posRes, thoughtRes, allThoughtRes, pnlRes, historyRes, tradeLogsRes, fullAnalyticsRes, ordersRes, fillsRes, transfersRes] = await Promise.all([
        fetch(`${API_URL}/api/status`).then(r => r.json()),
        fetch(`${API_URL}/api/positions`).then(r => r.json()),
        fetch(`${API_URL}/api/ai/thoughts`).then(r => r.json()),
        fetch(`${API_URL}/api/ai/thoughts?include_all=true`).then(r => r.json()),
        fetch(`${API_URL}/api/pnl`).then(r => r.json()),
        fetch(`${API_URL}/api/pnl/history?period=${pnlPeriod}`).then(r => r.json()),
        fetch(`${API_URL}/api/ai/trade-logs`).then(r => r.json()),
        fetch(`${API_URL}/api/analytics`).then(r => r.json()),
        fetch(`${API_URL}/api/orders`).then(r => r.json()),
        fetch(`${API_URL}/api/user/trades`).then(r => r.json()),
        fetch(`${API_URL}/api/transfers`).then(r => r.json())
      ]);

      if (statusRes.ok) setStatus(statusRes.data);
      if (posRes.ok) setPositions(posRes.data);
      if (allThoughtRes.ok) setAllThoughts(allThoughtRes.data);
      if (thoughtRes.ok) setThoughts(thoughtRes.data);
      if (pnlRes.ok) { /* setPnlData(pnlRes.data); - pnlData removed as unused */ }
      if (historyRes.ok && Array.isArray(historyRes.data)) _setPnlHistory(historyRes.data);
      if (tradeLogsRes.ok && tradeLogsRes.data && tradeLogsRes.data.length > 0) {
        setTradeLog(tradeLogsRes.data[0]);
        _setTradeLogs(tradeLogsRes.data);
      }
      if (fullAnalyticsRes.ok) setFullAnalytics(fullAnalyticsRes.data);
      if (ordersRes.ok) setOpenOrders(ordersRes.data || []);
      if (fillsRes.ok) setRecentFills(fillsRes.data || []);
      if (transfersRes.ok) setTransfers(transfersRes.data || []);

      try {
        const journalRes = await fetch(`${API_URL}/api/journal/stats`).then(r => r.json());
        if (journalRes.ok && journalRes.data) {
          setJournalStats(journalRes.data);
        }
      } catch { /* Journal stats optional */ }

      try {
        const sessionRes = await fetch(`${API_URL}/api/session`).then(r => r.json());
        if (sessionRes.ok && sessionRes.data) {
          setSessionInfo(sessionRes.data);
        }
      } catch { /* Session info optional */ }

      // Analytics is already fetched in Promise.all above, no duplicate needed

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
  }, [API_URL, pnlPeriod, loading]);


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

  const fetchHistory = useCallback(async () => {
    if (!API_URL) return;
    try {
      const res = await fetch(`${API_URL}/api/pnl/history?period=${pnlPeriod}`);
      const data = await res.json();
      if (data.ok && Array.isArray(data.data)) _setPnlHistory(data.data);
    } catch (e) {
      console.error("History fetch error:", e);
    }
  }, [API_URL, pnlPeriod]);

  const fetchCryptoPrices = useCallback(async () => {
    if (!API_URL) return;
    try {
      const res = await fetch(`${API_URL}/api/crypto-prices`);
      const data = await res.json();
      if (data.ok) setCryptoPrices(data.data);
    } catch (err) {
      console.error("Crypto prices fetch error:", err);
    }
  }, [API_URL]);

  const fetchNewsData = useCallback(async () => {
    if (!API_URL || activeTab !== 'news') return;
    try {
      const results = await Promise.all([
        fetch(`${API_URL}/api/news`).then(r => r.json()).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/economic-calendar?days=7`).then(r => r.json()).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/cmc/global`).then(r => r.json()).catch(() => ({ ok: false })),
        fetch(`${API_URL}/api/gainers-losers`).then(r => r.json()).catch(() => ({ ok: false })),
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
      }
      if (calendarRes.ok && calendarRes.events) setCalendarEvents(calendarRes.events);
      if (marketRes.ok && marketRes.data) setGlobalMarket(marketRes.data);
      if (moversRes.ok) {
        setTopGainers(moversRes.gainers || []);
        setTopLosers(moversRes.losers || []);
      }

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
  }, [API_URL, activeTab]);

  useEffect(() => {
    setMounted(true);
    fetchData();
    fetchCryptoPrices();

    const timer = setInterval(() => setTime(new Date()), 1000);
    const apiTimer = setInterval(fetchData, (settings.refreshRate || 10) * 1000);
    const cryptoTimer = setInterval(fetchCryptoPrices, 15000);

    return () => {
      clearInterval(timer);
      clearInterval(apiTimer);
      clearInterval(cryptoTimer);
    };
  }, [fetchData, fetchCryptoPrices, settings.refreshRate]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  useEffect(() => {
    if (activeTab === 'news') {
      fetchNewsData();
      const newsTimer = setInterval(fetchNewsData, 60000);
      return () => clearInterval(newsTimer);
    }
  }, [activeTab, fetchNewsData]);

  if (!mounted) return null;


  return (
    <div className="flex h-screen overflow-hidden text-foreground">
      {/* Sidebar - Pro Design */}
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          onClick={() => setSidebarOpen(false)}
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-sm animate-in fade-in duration-200"
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
            { id: 'news', label: isPt ? 'Notícias' : 'News', icon: Globe },
            { id: 'chat', label: isPt ? 'Chat IA' : 'AI Chat', icon: MessageSquare },
            { id: 'logs', label: isPt ? 'Logs de Execução' : 'Execution Logs', icon: Terminal },
          ].map((item) => {
            const content = (
              <>
                <item.icon className={cn("w-5 h-5", activeTab === item.id && "neon-glow")} />
                <span className="font-semibold text-sm">{item.label}</span>
                {activeTab === item.id && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary neon-glow" />}
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
                onClick={() => { setActiveTab(item.id as 'overview' | 'charts' | 'news' | 'chat' | 'logs'); setSidebarOpen(false); }}
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
              <button
                className="p-3 rounded-2xl bg-white/5 border border-white/10 hover:border-white/20 transition-all hover:scale-105 active:scale-95"
                onClick={() => setViewAllModalOpen(!viewAllModalOpen)}
              >
                <HistoryIcon className="w-5 h-5" />
              </button>

              {viewAllModalOpen && (
                <div
                  className="absolute right-0 top-full mt-2 w-64 p-4 rounded-xl glass-card border border-white/10 shadow-2xl z-50 origin-top-right animate-in fade-in zoom-in-95 duration-200"
                >
                  <div className="flex items-center justify-between mb-3 pb-2 border-b border-white/5">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Recent History</h4>
                  </div>

                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {status?.pnl_history_recent && status.pnl_history_recent.length > 0 ? (
                      status.pnl_history_recent.map((item: { timestamp: string | number; pnl: number }, idx: number) => (
                        <div key={idx} className="flex items-center justify-between text-xs">
                          <span className="font-mono text-white/60">
                            {safeDate(item.timestamp)?.toLocaleDateString()} {safeDate(item.timestamp)?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                          <span className={cn("font-bold", item.pnl >= 0 ? "text-primary" : "text-red-400")}>
                            {item.pnl >= 0 ? "WIN" : "LOSS"}
                          </span>
                        </div>
                      ))
                    ) : (
                      // Fallback mock data if real history is empty/loading
                      (fullAnalytics?.history || []).slice(-5).reverse().map((h: { time: string | number; value: number }, i: number) => {
                        const isWin = (h.value - (fullAnalytics?.history?.[fullAnalytics.history.length - i - 2]?.value || h.value)) >= 0;
                        return (
                          <div key={i} className="flex items-center justify-between text-xs">
                            <span className="font-mono text-white/60">{safeDate(h.time)?.toLocaleDateString()}</span>
                            <span className={cn("font-bold", isWin ? "text-primary" : "text-red-400")}>
                              {isWin ? "WIN" : "LOSS"}
                            </span>
                          </div>
                        )
                      }) || <p className="text-xs text-center text-white/30 py-2">No recent history</p>
                    )}
                  </div>
                </div>
              )}
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
        {activeTab === 'overview' && (
          <div
            key="overview"
            className="animate-in fade-in slide-in-from-right-2 duration-300"
          >
            <MarketBar data={{
              ...(status?.market_data || {}),
              macro: {
                ...(status?.market_data?.macro || {}),
                btc: cryptoPrices?.btc?.price || status?.market_data?.macro?.btc,
                eth: cryptoPrices?.eth?.price || status?.market_data?.macro?.eth,
              }
            }} />

            <div className="mt-8 mb-8">
              <HyperDashOverview
                status={status}
                fullAnalytics={fullAnalytics}
                positions={positions}
                recentFills={recentFills}
                openOrders={openOrders}
                period={pnlPeriod}
                setPeriod={setPnlPeriod}
                isLoading={loading}
                thoughts={thoughts}
                aiMood={aiMood}
                sessionInfo={sessionInfo}
              />
            </div>

            {/* Portfolio History Section - functionality unified in HyperDashOverview */}
            {false && (
              <GlassCard className="min-h-[400px] flex flex-col border border-white/5 bg-[#0b0c10]/50 mt-8" delay={0.2}>
                <div className="flex-1">
                  {/* Tabs */}
                  <div className="flex items-center gap-1 mb-6 overflow-x-auto no-scrollbar border-b border-white/5 pb-4">
                    {(['Open Orders', 'Recent Fills', 'Completed Trades', 'TWAP', 'Deposits & Withdrawals'] as const).map((tab) => (
                      <button
                        key={tab}
                        onClick={() => setActiveFleetTab(tab)}
                        className={cn(
                          "px-4 py-2 rounded-xl text-[10px] font-bold uppercase tracking-widest whitespace-nowrap transition-all",
                          activeFleetTab === tab
                            ? "bg-primary/20 text-primary shadow-sm ring-1 ring-primary/30"
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
                  </div>

                  {/* Dynamic Table Content */}
                  <div className="overflow-x-auto min-h-[300px]">
                    {activeFleetTab === 'Open Orders' && (
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="text-[10px] text-muted-foreground uppercase tracking-[0.2em] border-b border-white/5">
                            <th className="pb-4 pl-2 font-bold">Symbol</th>
                            <th className="pb-4 font-bold">Type</th>
                            <th className="pb-4 font-bold">Side</th>
                            <th className="pb-4 font-bold text-right">Price</th>
                            <th className="pb-4 font-bold text-right">Size</th>
                            <th className="pb-4 pr-2 font-bold text-right">Trigger</th>
                          </tr>
                        </thead>
                        <tbody className="text-sm">
                          {openOrders.length > 0 ? (
                            openOrders.map((order, idx) => (
                              <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                                <td className="py-4 pl-2 font-bold text-white">{order.symbol}</td>
                                <td className="py-4 font-mono text-muted-foreground text-xs">{order.type}</td>
                                <td className="py-4">
                                  <span className={cn("px-2 py-0.5 rounded text-[9px] font-black uppercase", order.side === 'BUY' ? "bg-primary/10 text-primary" : "bg-red-500/10 text-red-400")}>
                                    {order.side}
                                  </span>
                                </td>
                                <td className="py-4 font-mono text-white text-right">${Number(order.price)?.toFixed(2)}</td>
                                <td className="py-4 font-mono text-muted-foreground text-right">{order.size}</td>
                                <td className="py-4 pr-2 text-right font-mono text-muted-foreground text-xs">{order.trigger_px ? `$${Number(order.trigger_px).toFixed(2)}` : '—'}</td>
                              </tr>
                            ))
                          ) : (
                            <tr className="border-b border-white/5">
                              <td colSpan={6} className="py-20 text-center text-muted-foreground/30 text-xs uppercase tracking-widest font-bold">
                                No open orders found in current session
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    )}

                    {activeFleetTab === 'Recent Fills' && (
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="text-[10px] text-muted-foreground uppercase tracking-[0.2em] border-b border-white/5">
                            <th className="pb-4 pl-2 font-bold">Time</th>
                            <th className="pb-4 font-bold">Symbol</th>
                            <th className="pb-4 font-bold">Side</th>
                            <th className="pb-4 font-bold text-right">Price</th>
                            <th className="pb-4 font-bold text-right">Value</th>
                            <th className="pb-4 pr-2 font-bold text-right">PnL</th>
                          </tr>
                        </thead>
                        <tbody className="text-sm">
                          {recentFills.length > 0 ? (
                            recentFills.map((fill, idx) => (
                              <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                                <td className="py-4 pl-2 font-mono text-muted-foreground text-[10px]">{fill.timestamp ? new Date(fill.timestamp).toLocaleString() : '—'}</td>
                                <td className="py-4 font-bold text-white">{fill.symbol}</td>
                                <td className="py-4">
                                  <span className={cn("px-2 py-0.5 rounded text-[9px] font-black uppercase", fill.side === 'BUY' ? "bg-primary/10 text-primary" : "bg-red-500/10 text-red-400")}>
                                    {fill.side}
                                  </span>
                                </td>
                                <td className="py-4 font-mono text-white text-right">${Number(fill.price)?.toFixed(2)}</td>
                                <td className="py-4 font-mono text-muted-foreground text-right">${Number(fill.value)?.toFixed(2)}</td>
                                <td className={cn("py-4 pr-2 text-right font-mono font-bold", (fill.closed_pnl ?? 0) >= 0 ? "text-primary" : "text-red-400")}>
                                  {fill.closed_pnl !== undefined ? `${fill.closed_pnl >= 0 ? '+' : ''}$${Number(fill.closed_pnl).toFixed(2)}` : '—'}
                                </td>
                              </tr>
                            ))
                          ) : (
                            <tr className="border-b border-white/5">
                              <td colSpan={6} className="py-20 text-center text-muted-foreground/30 text-xs uppercase tracking-widest font-bold">
                                No recent portfolio history detected
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    )}

                    {activeFleetTab === 'Deposits & Withdrawals' && (
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr className="text-[10px] text-muted-foreground uppercase tracking-[0.2em] border-b border-white/5">
                            <th className="pb-4 pl-2 font-bold">Time</th>
                            <th className="pb-4 font-bold">Type</th>
                            <th className="pb-4 font-bold text-right">Amount</th>
                            <th className="pb-4 pr-2 font-bold text-right">Status</th>
                          </tr>
                        </thead>
                        <tbody className="text-sm">
                          {transfers.length > 0 ? (
                            transfers.map((transfer, idx) => (
                              <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                                <td className="py-4 pl-2 font-mono text-muted-foreground text-[10px]">{transfer.timestamp ? new Date(transfer.timestamp).toLocaleDateString() : '—'}</td>
                                <td className="py-4">
                                  <span className={cn("px-2 py-0.5 rounded text-[9px] font-black uppercase", transfer.type === 'DEPOSIT' ? "bg-primary/10 text-primary" : "bg-red-500/10 text-red-400")}>
                                    {transfer.type}
                                  </span>
                                </td>
                                <td className={cn("py-4 font-mono font-bold text-right", transfer.amount >= 0 ? "text-primary" : "text-red-400")}>
                                  {transfer.amount >= 0 ? '+' : ''}${Math.abs(transfer.amount).toFixed(2)}
                                </td>
                                <td className="py-4 pr-2 text-right font-mono text-primary text-[10px] uppercase font-black">{transfer.status}</td>
                              </tr>
                            ))
                          ) : (
                            <tr className="border-b border-white/5">
                              <td colSpan={4} className="py-20 text-center text-muted-foreground/30 text-xs uppercase tracking-widest font-bold">
                                No transfer history available
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    )}

                    {['Completed Trades', 'TWAP'].includes(activeFleetTab) && (
                      <div className="py-20 flex flex-col items-center justify-center text-muted-foreground/30">
                        <Layers className="w-12 h-12 mb-4 opacity-10" />
                        <span className="text-xs uppercase tracking-widest font-bold mb-2">Detailed {activeFleetTab} analysis coming soon</span>
                        <span className="text-[10px]">Syncing with Hyperliquid nodes...</span>
                      </div>
                    )}
                  </div>
                </div>
              </GlassCard>
            )}

            {/* AI Strategy & Active Positions are now unified in the card above */}
          </div>
        )}

        {activeTab === 'charts' && (
          <div className="space-y-8 animate-in fade-in zoom-in-95 duration-300">
            <div className="flex flex-col gap-2">
              <h2 className="text-3xl font-bold tracking-tight">{isPt ? 'Gráficos de Mercado Ativos' : 'Active Market Charts'}</h2>
              <p className="text-muted-foreground">{isPt ? 'Análise em tempo real das posições da frota' : 'Real-time analysis for current fleet positions'}</p>
            </div>

            {positions.length > 0 ? (
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {positions.map((pos: Position, i: number) => {
                  // Find matching trade log for this position
                  const posTradeLog = _trade_logs?.find((log: TradeLog) => log.symbol === pos.symbol) || tradeLog;

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
                  <div
                    className="absolute inset-0 bg-primary blur-3xl rounded-full animate-pulse"
                  />
                </div>
                <h3 className="text-xl font-bold mb-2">{isPt ? 'Nenhuma Posição Ativa' : 'No Active Positions'}</h3>
                <p className="text-muted-foreground text-center max-w-sm px-8">
                  {isPt ? 'Posições abertas aparecerão automaticamente aqui com gráficos TradingView em tempo real.' : 'Open positions will automatically appear here with real-time TradingView charts.'}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Analytics tab removed - functionality merged into Overview */}

        {activeTab === 'news' && (
          <div
            key="news"
            className="space-y-8 animate-in fade-in slide-in-from-right-2 duration-300"
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
                    calendarEvents.map((event: { event: string; country: string; impact: string; importance?: string; date: string; time?: string; actual?: string; estimate?: string; previous?: string }, i: number) => (
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
                              (rainbowData.band_index ?? 0) <= 2 ? "bg-gradient-to-r from-green-500 to-green-300" :
                                (rainbowData.band_index ?? 0) >= 6 ? "bg-gradient-to-r from-red-500 to-red-300" :
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
                          <span className={cn((altSeasonData.blockchaincenter?.season_index ?? altSeasonData.index ?? 0) < 25 ? "text-orange-400" : "text-white/30")}>Bitcoin Season</span>
                          <span className={cn((altSeasonData.blockchaincenter?.season_index ?? altSeasonData.index ?? 0) > 75 ? "text-cyan-400" : "text-white/30")}>Altcoin Season</span>
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
                      {fundingData.funding_rates.slice(0, 3).map((rate: { symbol: string; lastFundingRate: string }, i: number) => (
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
                        trendingCoins.slice(0, 4).map((coin: { thumb: string; symbol: string; name: string; rank: number }, i: number) => (
                          <div key={i} className="flex items-center gap-3 p-2 rounded-lg bg-white/5 border border-white/5">
                            <Image src={coin.thumb} alt={coin.symbol} width={20} height={20} className="rounded-full opacity-80" unoptimized />
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
                    {longShortData.global_ratio.map((item: { symbol: string; longShortRatio: string; longAccount: string; shortAccount: string; openInterest?: string }, i: number) => (
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

          </div>
        )}


        {
          activeTab === 'chat' && (
            <div key="chat" className="animate-in fade-in slide-in-from-right-2 duration-300">
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
                    chatMessages.map((msg: { role: string; content: string }, i: number) => (
                      <div key={i} className={cn("flex gap-3 animate-in fade-in slide-in-from-bottom-2 duration-300", msg.role === 'user' ? "justify-end" : "justify-start")}>
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
                      </div>
                    ))
                  )}
                  {chatLoading && (
                    <div className="flex gap-3 animate-pulse">
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
                    </div>
                  )}
                </div>

                <div className="flex gap-3 pt-4 border-t border-white/5">
                  <input type="text" value={chatInput} onChange={e => setChatInput(e.target.value)} onKeyPress={e => e.key === 'Enter' && sendChatMessage()} placeholder={isPt ? "Pergunte-me qualquer coisa..." : "Ask me anything..."} disabled={chatLoading} className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 focus:border-primary/50 focus:outline-none text-sm placeholder:text-muted-foreground" />
                  <button onClick={sendChatMessage} disabled={chatLoading || !chatInput.trim()} className="px-6 py-3 rounded-xl bg-primary text-black font-bold flex items-center gap-2">
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </GlassCard>
            </div>
          )
        }

        {
          activeTab === 'logs' && (
            <div key="logs" className="animate-in fade-in slide-in-from-right-2 duration-300">
              <GlassCard className="min-h-[600px] bg-black/60 border border-white/5 font-mono">
                <div className="flex items-center gap-4 mb-10">
                  <div className="p-3 rounded-2xl bg-white/10 text-white">
                    <Terminal className="w-6 h-6" />
                  </div>
                  <h3 className="text-2xl font-bold tracking-tight">{isPt ? 'Fluxo de Execução' : 'Execution Stream'}</h3>
                </div>
                <div className="space-y-3 h-[450px] overflow-y-auto no-scrollbar">
                  {allThoughts?.length > 0 ? (
                    allThoughts.map((thought: AIThought, i: number) => (
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
            </div>
          )
        }

        <footer className="mt-12 pt-8 border-t border-white/5 flex justify-between items-center text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
          <div className="flex gap-8">
            <span>Hyperliquid API: <span className={cn(error ? "text-secondary" : "text-primary")}>{error ? (isPt ? "Offline" : "Offline") : (isPt ? "Conectado" : "Connected")}</span></span>
            <span>OpenAI gpt-4o-mini: <span className="text-primary">{isPt ? "Operacional" : "Operational"}</span></span>
          </div>
          <div>© 2025 Ladder Labs</div>
        </footer>
      </main >

      {/* Background Grid handled by global CSS */}

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
