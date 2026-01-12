"use client";

import React, { useState, useEffect } from "react";
import {
  ArrowLeft,
  Globe,
  Newspaper,
  Calendar,
  TrendingUp,
  TrendingDown,
  AlertCircle,
} from "lucide-react";
import Link from "next/link";
import AnimatedBackground from "@/components/AnimatedBackground";
import { cn } from "@/lib/utils";
import { useSettings } from "@/hooks/useSettings";

interface NewsItem {
  title: string;
  url: string;
  source?: string;
  published_at?: string;
}

interface CalendarEvent {
  event: string;
  date: string;
  time?: string;
  importance?: string;
  estimate?: string;
  previous?: string;
}

interface MarketData {
  market_cap?: number;
  volume_24h?: number;
  btc_dominance?: number;
  eth_dominance?: number;
  market_cap_change_24h?: number;
  fear_greed?: number | string;
}

interface Mover {
  name: string;
  symbol: string;
  percent_change_24h: number;
}

export default function NewsPage() {
  const [realtimeNews, setRealtimeNews] = useState<NewsItem[]>([]);
  const [calendar, setCalendar] = useState<CalendarEvent[]>([]);
  const [market, setMarket] = useState<MarketData | null>(null);
  const [gainers, setGainers] = useState<Mover[]>([]);
  const [losers, setLosers] = useState<Mover[]>([]);
  const [loading, setLoading] = useState(true);
  const { settings } = useSettings();
  const isPt = settings.language === 'pt';

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

  useEffect(() => {
    const fetchData = async () => {
      if (!API_URL) {
        setLoading(false);
        return;
      }

      try {
        const [newsRes, calendarRes, marketRes, moversRes] = await Promise.all([
          fetch(`${API_URL}/api/news`).then(r => r.json()).catch(() => ({ ok: false })),
          fetch(`${API_URL}/api/economic-calendar?days=7`).then(r => r.json()).catch(() => ({ ok: false })),
          fetch(`${API_URL}/api/cmc/global`).then(r => r.json()).catch(() => ({ ok: false })),
          fetch(`${API_URL}/api/gainers-losers`).then(r => r.json()).catch(() => ({ ok: false }))
        ]);

        if (newsRes.ok) {
          if (newsRes.realtime) setRealtimeNews(newsRes.realtime);
          // newsRes.trending removed as unused
          // Fallback if backend doesn't have dual fields yet
          if (!newsRes.realtime && !newsRes.trending && newsRes.news) {
            setRealtimeNews(newsRes.news);
          }
        }
        if (calendarRes.ok && calendarRes.events) setCalendar(calendarRes.events);
        if (marketRes.ok && marketRes.data) setMarket(marketRes.data);
        if (moversRes.ok && (moversRes.data || moversRes.gainers)) {
          const moversData = moversRes.data || moversRes;
          setGainers(moversData.gainers || []);
          setLosers(moversData.losers || []);
        }

        // Market Intelligence Data
        // Market Intelligence Data removed as unused in UI
      } catch (err) {
        console.error("News fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [API_URL]);

  const formatCurrency = (value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toFixed(2)}`;
  };

  const timeAgo = (timestamp: string) => {
    if (!timestamp) return "";
    const date = new Date(timestamp);
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6 lg:p-10 relative overflow-hidden">
      {/* Animated Background with Blockchain Energy Flows */}
      <AnimatedBackground />

      {/* Header */}
      <div className="flex items-center justify-between mb-8 pb-6 border-b border-white/10">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
            {isPt ? "📰 Notícias e Inteligência" : "📰 News & Market Intelligence"}
          </h1>
          <p className="text-sm text-white/50 mt-1">
            {isPt ? "Atualizações em tempo real, notícias e eventos econômicos" : "Live market updates, news, and economic events"}
          </p>
        </div>
        <Link
          href="/"
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:border-white/20 transition-all font-bold"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="text-sm">{isPt ? "Voltar ao Dashboard" : "Back to Dashboard"}</span>
        </Link>
      </div>

      {/* Global Market Stats */}
      <div className="glass-card rounded-2xl p-6 mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
          <Globe className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-bold">{isPt ? "Visão Geral do Mercado Global" : "Global Market Overview"}</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-white/5 text-center">
            <p className="text-xs text-white/50 uppercase tracking-wider mb-2">
              {isPt ? "Capitalização" : "Market Cap"}
            </p>
            <p className="text-2xl font-bold">{market?.market_cap ? formatCurrency(market.market_cap) : "$0.00"}</p>
            {market?.market_cap_change_24h !== undefined && (
              <p className={cn("text-xs mt-1", market.market_cap_change_24h >= 0 ? "text-green-400" : "text-red-400")}>
                {market.market_cap_change_24h >= 0 ? "+" : ""}{market.market_cap_change_24h.toFixed(2)}%
              </p>
            )}
          </div>
          <div className="p-4 rounded-xl bg-white/5 text-center">
            <p className="text-xs text-white/50 uppercase tracking-wider mb-2">
              {isPt ? "Volume 24h" : "24h Volume"}
            </p>
            <p className="text-2xl font-bold">{market?.volume_24h ? formatCurrency(market.volume_24h) : "$0.00"}</p>
          </div>
          <div className="p-4 rounded-xl bg-white/5 text-center">
            <p className="text-xs text-white/50 uppercase tracking-wider mb-2">BTC DOM</p>
            <p className="text-2xl font-bold">{market?.btc_dominance?.toFixed(1) || "0.0"}%</p>
          </div>
          <div className="p-4 rounded-xl bg-white/5 text-center">
            <p className="text-xs text-white/50 uppercase tracking-wider mb-2">ETH DOM</p>
            <p className="text-2xl font-bold">{market?.eth_dominance?.toFixed(1) || "0.0"}%</p>
          </div>
          <div className="p-4 rounded-xl bg-white/5 text-center">
            <p className="text-xs text-secondary uppercase tracking-wider mb-2">Fear & Greed</p>
            <p className="text-2xl font-bold text-secondary shadow-secondary/20 drop-shadow-[0_0_8px_rgba(255,215,0,0.3)]">
              {market?.fear_greed ?? "---"}
            </p>
          </div>
        </div>
      </div>

      {/* Real-time Crypto News - Full Width */}
      <div className="glass-card rounded-2xl p-6 mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500" style={{ animationDelay: '0.1s' }}>
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
          <Newspaper className="w-5 h-5 text-cyan-400" />
          <h2 className="text-lg font-bold">{isPt ? "Notícias em Tempo Real (CryptoCompare)" : "Real-time News (CryptoCompare)"}</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[600px] overflow-y-auto pr-2">
          {loading ? (
            <div className="col-span-full flex items-center justify-center py-10">
              <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : realtimeNews.length > 0 ? (
            realtimeNews.map((item, i) => (
              <a
                key={i}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all border border-transparent hover:border-cyan-400/30"
              >
                <p className="font-medium text-sm mb-2 line-clamp-2">{item.title}</p>
                <div className="flex items-center gap-4 text-xs text-white/50">
                  <span className="text-cyan-400">{item.source}</span>
                  {item.published_at && <span>{timeAgo(item.published_at)}</span>}
                </div>
              </a>
            ))
          ) : (
            <div className="col-span-full text-center py-10 text-white/40">
              <AlertCircle className="w-8 h-8 mx-auto mb-2" />
              <p>{isPt ? "Nenhuma notícia disponível" : "No news available"}</p>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Economic Calendar */}
        <div className="glass-card rounded-2xl p-6 animate-in fade-in slide-in-from-bottom-4 duration-500" style={{ animationDelay: '0.2s' }}>
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
            <Calendar className="w-5 h-5 text-yellow-400" />
            <h2 className="text-lg font-bold">
              {isPt ? "Calendário Econômico Global" : "Global Economic Calendar"}
            </h2>
          </div>
          <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
            {loading ? (
              <div className="flex items-center justify-center py-10">
                <div className="w-8 h-8 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : calendar.length > 0 ? (
              calendar.slice(0, 10).map((event, i) => (
                <div
                  key={i}
                  className={cn(
                    "p-4 rounded-xl bg-white/5 border-l-4",
                    event.importance === "HIGH" ? "border-red-500" : "border-yellow-500"
                  )}
                >
                  <div className="flex justify-between items-start gap-4">
                    <p className="font-medium text-sm">{event.event || "Unknown"}</p>
                    <span className="text-xs text-white/50 whitespace-nowrap">
                      {event.date !== "TBD" ? new Date(event.date + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "TBD"} {event.time || ""}
                    </span>
                  </div>
                  {(event.estimate || event.previous) && (
                    <p className="text-xs text-white/40 mt-2">
                      {event.estimate && `Est: ${event.estimate}`}
                      {event.previous && ` | Prev: ${event.previous}`}
                    </p>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center py-10 text-white/40">
                <Calendar className="w-8 h-8 mx-auto mb-2" />
                <p>No upcoming events</p>
              </div>
            )}
          </div>
        </div>

        {/* Top Gainers */}
        <div className="glass-card rounded-2xl p-6 animate-in fade-in slide-in-from-bottom-4 duration-500" style={{ animationDelay: '0.3s' }}>
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
            <TrendingUp className="w-5 h-5 text-green-400" />
            <h2 className="text-lg font-bold">{isPt ? "Maiores Altas (24h)" : "Top Gainers (24h)"}</h2>
          </div>
          <div className="space-y-3">
            {gainers.length > 0 ? (
              gainers.map((coin, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                  <div className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold">
                      {i + 1}
                    </div>
                    <div>
                      <p className="font-medium text-sm">{coin.name}</p>
                      <p className="text-xs text-white/50">{coin.symbol}</p>
                    </div>
                  </div>
                  <span className="text-green-400 font-bold">
                    +{coin.percent_change_24h?.toFixed(2) || 0}%
                  </span>
                </div>
              ))
            ) : (
              <div className="text-center py-6 text-white/40">No data</div>
            )}
          </div>
        </div>

        {/* Top Losers */}
        <div className="glass-card rounded-2xl p-6 animate-in fade-in slide-in-from-bottom-4 duration-500" style={{ animationDelay: '0.4s' }}>
          <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
            <TrendingDown className="w-5 h-5 text-red-400" />
            <h2 className="text-lg font-bold">{isPt ? "Maiores Baixas (24h)" : "Top Losers (24h)"}</h2>
          </div>
          <div className="space-y-3">
            {losers.length > 0 ? (
              losers.map((coin, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                  <div className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold">
                      {i + 1}
                    </div>
                    <div>
                      <p className="font-medium text-sm">{coin.name}</p>
                      <p className="text-xs text-white/50">{coin.symbol}</p>
                    </div>
                  </div>
                  <span className="text-red-400 font-bold">
                    {coin.percent_change_24h?.toFixed(2) || 0}%
                  </span>
                </div>
              ))
            ) : (
              <div className="text-center py-6 text-white/40">No data</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
