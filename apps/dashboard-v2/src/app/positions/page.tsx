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
                        <div className="space-y-4">
                            {positions.map((position, index) => (
                                <div key={index} className="card hover:border-[var(--accent-cyan)] transition-colors">
                                    <div className="flex items-center justify-between">
                                        {/* Symbol & Side */}
                                        <div className="flex items-center gap-4">
                                            <div className="flex items-center gap-2">
                                                <span className="text-xl font-bold text-[var(--text-primary)]">{position.symbol}</span>
                                                <span className={`badge ${position.side === 'LONG' ? 'badge-green' : 'badge-red'}`}>
                                                    {position.side}
                                                </span>
                                                <span className="badge badge-outline">{position.leverage}x</span>
                                            </div>
                                        </div>

                                        {/* P&L */}
                                        <div className="text-right">
                                            <p className={`text-xl font-bold ${position.unrealizedPnl >= 0 ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'}`}>
                                                {position.unrealizedPnl >= 0 ? '+' : ''}${position.unrealizedPnl.toFixed(2)}
                                            </p>
                                            <p className={`text-sm ${position.roe >= 0 ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'}`}>
                                                {position.roe >= 0 ? '+' : ''}{position.roe.toFixed(2)}% ROE
                                            </p>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mt-4 pt-4 border-t border-[var(--border)]">
                                        <div>
                                            <p className="text-xs text-[var(--text-muted)]">Size</p>
                                            <p className="text-sm font-medium text-[var(--text-primary)]">{position.size}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-[var(--text-muted)]">Entry</p>
                                            <p className="text-sm font-medium text-[var(--text-primary)]">${formatPrice(position.entryPrice)}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-[var(--text-muted)]">Mark</p>
                                            <p className="text-sm font-medium text-[var(--text-primary)]">${formatPrice(position.markPrice)}</p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-[var(--text-muted)]">Stop Loss</p>
                                            <p className="text-sm font-medium text-[var(--accent-red)]">
                                                {position.stopLoss ? `$${formatPrice(position.stopLoss)}` : '—'}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-[var(--text-muted)]">Take Profit</p>
                                            <p className="text-sm font-medium text-[var(--accent-green)]">
                                                {position.takeProfit ? `$${formatPrice(position.takeProfit)}` : '—'}
                                            </p>
                                        </div>
                                        <div>
                                            <p className="text-xs text-[var(--text-muted)]">Liq. Price</p>
                                            <p className="text-sm font-medium text-[var(--accent-orange)]">
                                                {position.liquidationPrice ? `$${formatPrice(position.liquidationPrice)}` : '—'}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Mini Chart */}
                                    <div className="mt-4 pt-4 border-t border-[var(--border)]">
                                        <PositionMiniChart
                                            symbol={position.symbol}
                                            entryPrice={position.entryPrice}
                                            markPrice={position.markPrice}
                                            side={position.side}
                                            roe={position.roe}
                                        />
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
