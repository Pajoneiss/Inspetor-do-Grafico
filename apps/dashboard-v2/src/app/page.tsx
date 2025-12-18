'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import MetricStrip from '@/components/layout/MetricStrip';
import EquityChart from '@/components/charts/EquityChart';
import ContextCard from '@/components/cards/ContextCard';
import PositionsTable from '@/components/positions/PositionsTable';
import CMCMarketOverview from '@/components/cards/CMCMarketOverview';
import TrendingCoins from '@/components/cards/TrendingCoins';
import GainersLosers from '@/components/cards/GainersLosers';

// API Base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<number>(Date.now());
  const [data, setData] = useState<any>({
    account: {
      equity: 0,
      buyingPower: 0,
      unrealized_pnl: 0,
      pnl_pct: 0,
      realizedPnl24h: 0,
      leverage: 1,
      marginUsage: 0,
      openPositions: 0
    },
    positions: [],
    market: {
      fear_greed: 50
    },
    scanner: [],
    aiThinking: null,
    chart: []
  });

  // Fetch data from API
  const fetchData = async () => {
    try {
      const [statusRes, positionsRes, marketRes, aiRes, chartRes] = await Promise.all([
        fetch(`${API_BASE}/api/status`).catch(() => null),
        fetch(`${API_BASE}/api/positions`).catch(() => null),
        fetch(`${API_BASE}/api/market`).catch(() => null),
        fetch(`${API_BASE}/api/ai/current-thinking`).catch(() => null),
        fetch(`${API_BASE}/api/pnl/history`).catch(() => null)
      ]);

      const statusJson = statusRes?.ok ? await statusRes.json() : null;
      const positionsJson = positionsRes?.ok ? await positionsRes.json() : null;
      const marketJson = marketRes?.ok ? await marketRes.json() : null;
      const aiJson = aiRes?.ok ? await aiRes.json() : null;
      const chartJson = chartRes?.ok ? await chartRes.json() : null;

      setData((prev: any) => {
        const newData = { ...prev };

        if (statusJson?.ok && statusJson.data) {
          newData.account = {
            equity: statusJson.data.equity || 0,
            buyingPower: statusJson.data.buying_power || 0,
            unrealized_pnl: statusJson.data.unrealized_pnl || 0,
            pnl_pct: statusJson.data.unrealized_pnl_pct || 0,
            realizedPnl24h: statusJson.data.pnl_24h || 0,
            leverage: statusJson.data.leverage || 1,
            marginUsage: statusJson.data.margin_usage || 0,
            openPositions: statusJson.data.positions_count || 0
          };
          setLastUpdate(statusJson.data.server_time_ms || Date.now());
        }

        if (positionsJson?.ok && positionsJson.data) {
          newData.positions = positionsJson.data.map((p: any) => ({
            symbol: p.symbol || p.coin || '',
            side: ((p.side as string)?.toUpperCase() === 'LONG' || (p.szi as number) > 0) ? 'LONG' : 'SHORT',
            size: Math.abs(p.size || p.szi || 0),
            entryPrice: p.entry_price || p.entryPx || 0,
            markPrice: p.mark_price || p.markPx || 0,
            unrealizedPnl: p.unrealized_pnl || p.unrealizedPnl || 0,
            roe: p.pnl_pct || p.returnOnEquity || 0,
            leverage: p.leverage || 1,
            stopLoss: p.stop_loss || undefined,
            takeProfit: p.take_profit || undefined
          }));
        }

        if (marketJson?.ok && marketJson.data) {
          newData.market = { fear_greed: marketJson.data.fear_greed || 50 };
          newData.scanner = (marketJson.data.scanner || []).map((s: any) => ({
            symbol: s.symbol,
            score: s.score || 50,
            reason: s.reason || ''
          }));
        }

        if (aiJson?.ok && aiJson.data) {
          newData.aiThinking = aiJson.data;
        }

        if (chartJson?.ok && chartJson.data) {
          newData.chart = chartJson.data.map((p: any) => ({
            time: p.time || p.ts || '',
            value: p.value || p.equity_usd || 0
          }));
        }

        return newData;
      });
    } catch (err) {
      console.error('[Dashboard] API fetch error:', err);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex bg-dark-bg text-text-primary">
      <Sidebar />
      <main className="main-content flex-1">
        <Header
          wallet="0x...04bA24"
          network="mainnet"
          isLive={true}
          lastUpdate={lastUpdate}
        />

        <div className="px-6 py-4 space-y-4">
          {/* KPI Strip */}
          <MetricStrip account={data.account} loading={loading} />

          {/* Top Row: CMC Market Overview + Trending - FIXED LAYOUT */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-1 min-h-[300px]">
              <CMCMarketOverview />
            </div>
            <div className="lg:col-span-2 min-h-[300px]">
              <TrendingCoins />
            </div>
          </div>

          {/* Middle Row: Chart & Context */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            <div className="lg:col-span-8">
              <EquityChart data={data.chart} loading={loading} />
            </div>
            <div className="lg:col-span-4">
              <ContextCard
                market={data.market}
                scanner={data.scanner}
                aiThinking={data.aiThinking}
                loading={loading}
              />
            </div>
          </div>

          {/* Gainers/Losers Row */}
          <div className="w-full">
            <GainersLosers />
          </div>

          {/* Bottom Row: Positions */}
          <div className="w-full">
            <PositionsTable positions={data.positions} loading={loading} />
          </div>
        </div>
      </main>
    </div>
  );
}

