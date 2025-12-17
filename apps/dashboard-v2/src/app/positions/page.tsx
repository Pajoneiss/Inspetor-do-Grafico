'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import PositionMiniChart from '@/components/positions/PositionMiniChart';

interface Position {
    symbol: string;
    side: 'LONG' | 'SHORT';
    size: number;
    entryPrice: number;
    markPrice: number;
    unrealizedPnl: number;
    roe: number;
    leverage: number;
    stopLoss?: number;
    takeProfit?: number;
    liquidationPrice?: number;
    marginUsed: number;
}

export default function PositionsPage() {
    const [positions, setPositions] = useState<Position[]>([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

    const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

    useEffect(() => {
        const fetchPositions = async () => {
            try {
                const response = await fetch(`${API_BASE}/api/positions`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.ok && data.data) {
                        setPositions(data.data.map((p: Record<string, unknown>) => ({
                            symbol: (p.symbol || p.coin || '') as string,
                            side: ((p.side as string)?.toUpperCase() === 'LONG' || (p.szi as number) > 0) ? 'LONG' : 'SHORT',
                            size: Math.abs((p.size as number) || (p.szi as number) || 0),
                            entryPrice: (p.entry_price as number) || (p.entryPx as number) || 0,
                            markPrice: (p.mark_price as number) || (p.markPx as number) || 0,
                            unrealizedPnl: (p.unrealized_pnl as number) || (p.unrealizedPnl as number) || 0,
                            roe: (p.pnl_pct as number) || (p.returnOnEquity as number) || 0,
                            leverage: (p.leverage as number) || 1,
                            stopLoss: (p.stop_loss as number) || (p.stopLoss as number) || undefined,
                            takeProfit: (p.take_profit as number) || (p.takeProfit as number) || undefined,
                            liquidationPrice: (p.liquidation_price as number) || (p.liquidationPx as number) || undefined,
                            marginUsed: (p.margin_used as number) || (p.marginUsed as number) || 0,
                        })));
                    }
                }
                setLastUpdate(new Date());
            } catch (error) {
                console.error('Failed to fetch positions:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchPositions();
        const interval = setInterval(fetchPositions, 5000);
        return () => clearInterval(interval);
    }, [API_BASE]);

    const formatPrice = (price: number) => {
        if (price >= 1000) return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        if (price >= 1) return price.toFixed(4);
        return price.toFixed(6);
    };

    return (
        <div className="min-h-screen flex">
            <Sidebar activePage="positions" />
            <main className="main-content">
                <Header lastUpdate={lastUpdate} onRefresh={() => window.location.reload()} />

                <div className="p-6">
                    <div className="mb-6 flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold text-[var(--text-primary)]">Positions</h1>
                            <p className="text-sm text-[var(--text-muted)]">
                                {positions.length} active position{positions.length !== 1 ? 's' : ''}
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="badge badge-cyan">{positions.length} Active</span>
                        </div>
                    </div>

                    {loading ? (
                        <div className="card">
                            <div className="space-y-4">
                                {[...Array(3)].map((_, i) => (
                                    <div key={i} className="skeleton h-20 w-full rounded-lg"></div>
                                ))}
                            </div>
                        </div>
                    ) : positions.length > 0 ? (
                        <div className="grid gap-3">
                            {positions.map((position, index) => (
                                <div key={index} className="card p-4 hover:border-[var(--accent-cyan)] transition-all hover:shadow-lg">
                                    {/* Top Row: Symbol + PnL */}
                                    <div className="flex items-center justify-between mb-3">
                                        <div className="flex items-center gap-2">
                                            <span className="text-lg font-bold text-[var(--text-primary)]">{position.symbol}</span>
                                            <span className={`px-2 py-0.5 rounded text-xs font-semibold ${position.side === 'LONG' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                                {position.side}
                                            </span>
                                            <span className="px-2 py-0.5 rounded text-xs font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                                                {position.leverage}x
                                            </span>
                                        </div>
                                        <div className="text-right">
                                            <p className={`text-lg font-bold ${position.unrealizedPnl >= 0 ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'}`}>
                                                {position.unrealizedPnl >= 0 ? '+' : ''}${position.unrealizedPnl.toFixed(2)}
                                            </p>
                                            <p className={`text-xs ${position.roe >= 0 ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'}`}>
                                                {position.roe >= 0 ? '+' : ''}{position.roe.toFixed(2)}% ROE
                                            </p>
                                        </div>
                                    </div>

                                    {/* Chart */}
                                    <div className="mb-3">
                                        <PositionMiniChart
                                            symbol={position.symbol}
                                            entryPrice={position.entryPrice}
                                            markPrice={position.markPrice}
                                            side={position.side}
                                            roe={position.roe}
                                        />
                                    </div>

                                    {/* Compact Info Grid */}
                                    <div className="grid grid-cols-3 gap-2 text-xs">
                                        <div className="bg-[var(--bg-secondary)] rounded px-2 py-1.5">
                                            <p className="text-[var(--text-muted)] mb-0.5">Entry</p>
                                            <p className="text-[var(--text-primary)] font-medium">${formatPrice(position.entryPrice)}</p>
                                        </div>
                                        <div className="bg-[var(--bg-secondary)] rounded px-2 py-1.5">
                                            <p className="text-[var(--text-muted)] mb-0.5">Mark</p>
                                            <p className="text-[var(--text-primary)] font-medium">${formatPrice(position.markPrice)}</p>
                                        </div>
                                        <div className="bg-[var(--bg-secondary)] rounded px-2 py-1.5">
                                            <p className="text-[var(--text-muted)] mb-0.5">Size</p>
                                            <p className="text-[var(--text-primary)] font-medium">{position.size}</p>
                                        </div>
                                        <div className="bg-[var(--bg-secondary)] rounded px-2 py-1.5">
                                            <p className="text-[var(--text-muted)] mb-0.5">SL</p>
                                            <p className="text-[var(--accent-red)] font-medium">
                                                {position.stopLoss ? `$${formatPrice(position.stopLoss)}` : '—'}
                                            </p>
                                        </div>
                                        <div className="bg-[var(--bg-secondary)] rounded px-2 py-1.5">
                                            <p className="text-[var(--text-muted)] mb-0.5">TP</p>
                                            <p className="text-[var(--accent-green)] font-medium">
                                                {position.takeProfit ? `$${formatPrice(position.takeProfit)}` : '—'}
                                            </p>
                                        </div>
                                        <div className="bg-[var(--bg-secondary)] rounded px-2 py-1.5">
                                            <p className="text-[var(--text-muted)] mb-0.5">Liq</p>
                                            <p className="text-[var(--accent-orange)] font-medium">
                                                {position.liquidationPrice ? `$${formatPrice(position.liquidationPrice)}` : '—'}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="card text-center py-12">
                            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center">
                                <span className="text-2xl">📭</span>
                            </div>
                            <h3 className="text-lg font-medium text-[var(--text-primary)] mb-2">No Open Positions</h3>
                            <p className="text-sm text-[var(--text-muted)]">
                                The bot is monitoring the market. Positions will appear here when trades are opened.
                            </p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
