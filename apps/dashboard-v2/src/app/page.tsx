'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import { AccountValueCard } from '@/components/cards/AccountValueCard';
import { RiskMonitorCard } from '@/components/cards/RiskMonitorCard';
import { PositionsTable } from '@/components/cards/PositionsTable';
import { ScanSignalsCard } from '@/components/cards/ScanSignalsCard';
import { EquityCurve } from '@/components/charts/EquityCurve';

// API Base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

// Mock data for development
const MOCK_DATA = {
  account: {
    equity: 35.11,
    buyingPower: 1404,
    unrealizedPnl: -0.45,
    realizedPnl24h: 2.34,
    fees24h: 0.12,
    funding24h: 0.08
  },
  risk: {
    marginUsage: 24.5,
    liquidationBuffer: 65.2,
    totalExposure: 142.50,
    openPositions: 2,
    errorCount: 0
  },
  positions: [
    {
      symbol: 'BTC',
      side: 'SHORT' as const,
      size: 0.00826,
      entryPrice: 87783.60,
      markPrice: 86277.50,
      unrealizedPnl: 12.44,
      roe: 15.2,
      liquidationPrice: 95000,
      stopLoss: 86364,
      takeProfit: 85000,
      breakeven: 'ARMED' as const
    },
    {
      symbol: 'ETH',
      side: 'LONG' as const,
      size: 0.01,
      entryPrice: 2955.30,
      markPrice: 2945.20,
      unrealizedPnl: -0.10,
      roe: -0.34,
      stopLoss: 2900,
      takeProfit: 3100,
      breakeven: 'INACTIVE' as const
    }
  ],
  scan: {
    top: [
      { symbol: 'BTC', score: 85, bias: 'BULLISH' as const, reason: 'Strong momentum' },
      { symbol: 'ETH', score: 85, bias: 'BULLISH' as const, reason: 'Trend continuation' },
      { symbol: 'SOL', score: 85, bias: 'BULLISH' as const, reason: 'Volume surge' },
      { symbol: 'DOGE', score: 65, bias: 'NEUTRAL' as const, reason: 'Consolidating' },
      { symbol: 'XRP', score: 65, bias: 'NEUTRAL' as const, reason: 'Range bound' }
    ],
    bottom: [
      { symbol: 'ADA', score: 25, bias: 'BEARISH' as const, reason: 'Weak structure' },
      { symbol: 'LINK', score: 25, bias: 'BEARISH' as const, reason: 'No momentum' },
      { symbol: 'ARB', score: 25, bias: 'BEARISH' as const, reason: 'Breakdown risk' }
    ]
  },
  chart: [
    { time: '00:00', value: 32 },
    { time: '04:00', value: 33.5 },
    { time: '08:00', value: 34.2 },
    { time: '12:00', value: 33.8 },
    { time: '16:00', value: 35.5 },
    { time: '20:00', value: 34.8 },
    { time: 'Now', value: 35.11 }
  ]
};

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<number>(Date.now());
  const [data, setData] = useState(MOCK_DATA);

  // Fetch data from API
  const fetchData = async () => {
    try {
      // Fetch all endpoints in parallel
      const [statusRes, positionsRes, marketRes] = await Promise.all([
        fetch(`${API_BASE}/api/status`).catch(() => null),
        fetch(`${API_BASE}/api/positions`).catch(() => null),
        fetch(`${API_BASE}/api/market`).catch(() => null)
      ]);

      const statusJson = statusRes?.ok ? await statusRes.json() : null;
      const positionsJson = positionsRes?.ok ? await positionsRes.json() : null;
      const marketJson = marketRes?.ok ? await marketRes.json() : null;

      setData(prev => {
        const newData = { ...prev };

        // Update account data
        if (statusJson?.ok && statusJson.data) {
          newData.account = {
            equity: statusJson.data.equity || prev.account.equity,
            buyingPower: statusJson.data.buying_power || prev.account.buyingPower,
            unrealizedPnl: statusJson.data.unrealized_pnl || prev.account.unrealizedPnl,
            realizedPnl24h: statusJson.data.pnl_24h || prev.account.realizedPnl24h,
            fees24h: statusJson.data.fees_24h || prev.account.fees24h,
            funding24h: statusJson.data.funding_24h || prev.account.funding24h
          };
          newData.risk = {
            marginUsage: statusJson.data.margin_usage || prev.risk.marginUsage,
            liquidationBuffer: statusJson.data.liq_buffer || prev.risk.liquidationBuffer,
            totalExposure: statusJson.data.total_exposure || prev.risk.totalExposure,
            openPositions: statusJson.data.positions_count || prev.risk.openPositions,
            errorCount: 0
          };
          setLastUpdate(statusJson.data.server_time_ms || Date.now());
        }

        // Update positions
        if (positionsJson?.ok && positionsJson.data) {
          newData.positions = positionsJson.data.map((p: Record<string, unknown>) => ({
            symbol: (p.symbol || p.coin || '') as string,
            side: ((p.side as string)?.toUpperCase() === 'LONG' || (p.szi as number) > 0) ? 'LONG' : 'SHORT',
            size: Math.abs((p.size as number) || (p.szi as number) || 0),
            entryPrice: (p.entry_price as number) || (p.entryPx as number) || 0,
            markPrice: (p.mark_price as number) || (p.markPx as number) || 0,
            unrealizedPnl: (p.unrealized_pnl as number) || (p.unrealizedPnl as number) || 0,
            roe: (p.pnl_pct as number) || (p.returnOnEquity as number) || 0,
            stopLoss: (p.stop_loss as number) || undefined,
            takeProfit: (p.take_profit as number) || undefined,
            breakeven: (p.stop_loss && (p.stop_loss as number) >= ((p.entry_price as number) || 0)) ? 'ARMED' : 'INACTIVE'
          }));
          newData.risk.openPositions = positionsJson.data.length;
        }

        // Update market/scan data
        if (marketJson?.ok && marketJson.data) {
          const topSymbols = marketJson.data.top_symbols || [];
          if (topSymbols.length > 0) {
            newData.scan.top = topSymbols.slice(0, 5).map((s: string, i: number) => ({
              symbol: s,
              score: 85 - (i * 5),
              bias: 'BULLISH' as const,
              reason: 'High score'
            }));
          }
        }

        return newData;
      });
    } catch (err) {
      console.log('[Dashboard] API fetch error, using mock data');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="main-content">
        {/* Header */}
        <Header
          wallet="0x...04bA24"
          network="mainnet"
          isLive={true}
          lastUpdate={lastUpdate}
        />

        {/* Dashboard Content */}
        <div className="p-6">
          {/* Top Row: Account + Risk */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="lg:col-span-2">
              <AccountValueCard
                equity={data.account.equity}
                buyingPower={data.account.buyingPower}
                unrealizedPnl={data.account.unrealizedPnl}
                realizedPnl24h={data.account.realizedPnl24h}
                fees24h={data.account.fees24h}
                funding24h={data.account.funding24h}
                loading={loading}
              />
            </div>
            <RiskMonitorCard
              marginUsage={data.risk.marginUsage}
              liquidationBuffer={data.risk.liquidationBuffer}
              totalExposure={data.risk.totalExposure}
              openPositions={data.risk.openPositions}
              errorCount={data.risk.errorCount}
              loading={loading}
            />
          </div>

          {/* Chart Row */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="lg:col-span-2">
              <EquityCurve
                data={data.chart}
                loading={loading}
              />
            </div>
            <ScanSignalsCard
              topSignals={data.scan.top}
              bottomSignals={data.scan.bottom}
              totalScanned={11}
              loading={loading}
            />
          </div>

          {/* Positions Table */}
          <PositionsTable
            positions={data.positions}
            loading={loading}
          />
        </div>
      </main>
    </div>
  );
}
