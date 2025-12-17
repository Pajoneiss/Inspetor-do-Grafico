'use client';

import { useState, useEffect } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';

interface LogEntry {
    id: string;
    timestamp: string;
    level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
    category: string;
    message: string;
}

interface ActionLog {
    timestamp: string;
    type: string;
    symbol?: string;
    side?: string;
    reason?: string;
    confidence?: number;
    summary?: string;
}

export default function LogsPage() {
    const [actions, setActions] = useState<ActionLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
    const [filter, setFilter] = useState<'all' | 'trades' | 'holds'>('all');

    const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const response = await fetch(`${API_BASE}/api/actions?limit=50`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.ok && data.data) {
                        setActions(data.data);
                    }
                }
                setLastUpdate(new Date());
            } catch (error) {
                console.error('Failed to fetch logs:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchLogs();
        const interval = setInterval(fetchLogs, 10000);
        return () => clearInterval(interval);
    }, [API_BASE]);

    const filteredActions = actions.filter(action => {
        if (filter === 'all') return true;
        if (filter === 'trades') return action.type !== 'HOLD' && action.type !== 'NO_TRADE';
        if (filter === 'holds') return action.type === 'HOLD' || action.type === 'NO_TRADE';
        return true;
    });

    const getActionIcon = (type: string) => {
        switch (type) {
            case 'BUY':
            case 'LONG':
                return '🟢';
            case 'SELL':
            case 'SHORT':
                return '🔴';
            case 'HOLD':
            case 'NO_TRADE':
                return '⏸️';
            case 'SET_SL':
                return '🛡️';
            case 'SET_TP':
                return '🎯';
            case 'CLOSE':
                return '❌';
            default:
                return '📋';
        }
    };

    const getActionBadgeClass = (type: string) => {
        switch (type) {
            case 'BUY':
            case 'LONG':
                return 'badge-green';
            case 'SELL':
            case 'SHORT':
                return 'badge-red';
            case 'HOLD':
            case 'NO_TRADE':
                return 'badge-outline';
            default:
                return 'badge-cyan';
        }
    };

    const formatTime = (timestamp: string) => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    const formatDate = (timestamp: string) => {
        const date = new Date(timestamp);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
        });
    };

    return (
        <div className="min-h-screen flex">
            <Sidebar activePage="logs" />
            <main className="main-content">
                <Header lastUpdate={lastUpdate} onRefresh={() => window.location.reload()} />

                <div className="p-6">
                    <div className="mb-6 flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-bold text-[var(--text-primary)]">Activity Logs</h1>
                            <p className="text-sm text-[var(--text-muted)]">
                                AI decisions and trading activity
                            </p>
                        </div>

                        {/* Filter buttons */}
                        <div className="flex items-center gap-2 bg-[var(--bg-tertiary)] rounded-lg p-1">
                            {(['all', 'trades', 'holds'] as const).map((f) => (
                                <button
                                    key={f}
                                    onClick={() => setFilter(f)}
                                    className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${filter === f
                                        ? 'bg-[var(--accent-cyan)] text-[var(--bg-primary)]'
                                        : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                                        }`}
                                >
                                    {f.charAt(0).toUpperCase() + f.slice(1)}
                                </button>
                            ))}
                        </div>
                    </div>

                    {loading ? (
                        <div className="card">
                            <div className="space-y-3">
                                {[...Array(10)].map((_, i) => (
                                    <div key={i} className="skeleton h-16 w-full rounded-lg"></div>
                                ))}
                            </div>
                        </div>
                    ) : filteredActions.length > 0 ? (
                        <div className="card">
                            <div className="space-y-2">
                                {filteredActions.map((action, index) => (
                                    <div
                                        key={index}
                                        className="p-4 rounded-lg bg-[var(--bg-tertiary)] hover:bg-[var(--bg-card)] transition-colors border border-transparent hover:border-[var(--border)]"
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-start gap-3">
                                                <span className="text-xl">{getActionIcon(action.type)}</span>
                                                <div>
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className={`badge ${getActionBadgeClass(action.type)}`}>
                                                            {action.type}
                                                        </span>
                                                        {action.symbol && (
                                                            <span className="text-sm font-medium text-[var(--text-primary)]">
                                                                {action.symbol}
                                                            </span>
                                                        )}
                                                        {action.side && (
                                                            <span className={`text-xs ${action.side === 'LONG' ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'}`}>
                                                                {action.side}
                                                            </span>
                                                        )}
                                                        {action.confidence !== undefined && (
                                                            <span className="text-xs text-[var(--text-muted)]">
                                                                {(action.confidence * 100).toFixed(0)}% conf
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-sm text-[var(--text-secondary)]">
                                                        {action.summary || action.reason || 'No details available'}
                                                    </p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-xs text-[var(--text-muted)]">{formatDate(action.timestamp)}</p>
                                                <p className="text-xs text-[var(--text-muted)]">{formatTime(action.timestamp)}</p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="card text-center py-12">
                            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-[var(--bg-tertiary)] flex items-center justify-center">
                                <span className="text-2xl">📝</span>
                            </div>
                            <h3 className="text-lg font-medium text-[var(--text-primary)] mb-2">No Logs Available</h3>
                            <p className="text-sm text-[var(--text-muted)]">
                                Activity logs will appear here as the bot makes decisions.
                            </p>
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
