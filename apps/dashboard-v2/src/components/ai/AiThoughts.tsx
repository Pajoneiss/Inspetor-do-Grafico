'use client';

import { useState, useEffect } from 'react';
import { Brain, TrendingUp, TrendingDown, Filter, CheckCircle, XCircle, Clock } from 'lucide-react';

interface AiThought {
    id: string;
    timestamp: string;
    symbols: string[];
    summary: string;
    confidence: number;
    actions: {
        type: string;
        symbol: string;
        status: 'executed' | 'skipped' | 'blocked';
        reason?: string;
    }[];
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

// Mock data for development
const MOCK_THOUGHTS: AiThought[] = [
    {
        id: '1',
        timestamp: new Date(Date.now() - 120000).toISOString(),
        symbols: ['BTC', 'ETH'],
        summary: 'Both positions have SL and TP set. Market is showing strong bearish signals with no clear edge for new trades.',
        confidence: 0.80,
        actions: [
            { type: 'HOLD', symbol: 'ALL', status: 'executed', reason: 'positions managed, waiting for edge' }
        ]
    },
    {
        id: '2',
        timestamp: new Date(Date.now() - 300000).toISOString(),
        symbols: ['BTC'],
        summary: 'BTC position lacks a stop loss. Setting SL to manage risk.',
        confidence: 0.85,
        actions: [
            { type: 'SET_STOP_LOSS', symbol: 'BTC', status: 'executed' }
        ]
    },
    {
        id: '3',
        timestamp: new Date(Date.now() - 600000).toISOString(),
        symbols: ['ETH'],
        summary: 'ETH showing weakness. Maintaining long with defined risk parameters.',
        confidence: 0.70,
        actions: [
            { type: 'HOLD', symbol: 'ETH', status: 'skipped', reason: 'confidence below threshold' }
        ]
    }
];

export function AiThoughts() {
    const [thoughts, setThoughts] = useState<AiThought[]>(MOCK_THOUGHTS);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'decisions' | 'holds'>('all');
    const [minConfidence, setMinConfidence] = useState(0);

    useEffect(() => {
        const fetchThoughts = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/ai/thoughts?limit=50`);
                if (res.ok) {
                    const json = await res.json();
                    // Only update if we got actual data, otherwise keep mock
                    if (json.ok && json.data && json.data.length > 0) {
                        setThoughts(json.data);
                    }
                }
            } catch (err) {
                console.log('[AiThoughts] Using mock data');
            }
            setLoading(false);
        };

        fetchThoughts();
        const interval = setInterval(fetchThoughts, 10000);
        return () => clearInterval(interval);
    }, []);

    const formatTimeAgo = (timestamp: string) => {
        const seconds = Math.max(0, Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000));
        if (seconds < 60) return `${seconds}s ago`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        return `${Math.floor(seconds / 3600)}h ago`;
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'executed':
                return <CheckCircle className="w-3 h-3 text-[var(--profit)]" />;
            case 'blocked':
                return <XCircle className="w-3 h-3 text-[var(--loss)]" />;
            default:
                return <Clock className="w-3 h-3 text-[var(--text-muted)]" />;
        }
    };

    const filteredThoughts = thoughts.filter(t => {
        if (t.confidence < minConfidence) return false;
        if (filter === 'decisions') return t.actions.some(a => a.type !== 'HOLD');
        if (filter === 'holds') return t.actions.every(a => a.type === 'HOLD');
        return true;
    });

    if (loading) {
        return (
            <div className="card">
                <div className="skeleton h-6 w-48 mb-4" />
                <div className="space-y-4">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="skeleton h-24 w-full" />
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="card">
            <div className="card-header border-b border-[var(--border)] pb-4">
                <div className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-[var(--accent-green)]" />
                    <span className="font-semibold">AI Thoughts Feed</span>
                    <span className="badge badge-live text-[10px]">LIVE</span>
                </div>

                {/* Filters */}
                <div className="flex items-center gap-2">
                    <Filter className="w-4 h-4 text-[var(--text-muted)]" />
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value as any)}
                        className="bg-[var(--bg-primary)] border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)]"
                    >
                        <option value="all">All</option>
                        <option value="decisions">Decisions Only</option>
                        <option value="holds">Holds Only</option>
                    </select>
                    <select
                        value={minConfidence}
                        onChange={(e) => setMinConfidence(Number(e.target.value))}
                        className="bg-[var(--bg-primary)] border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--text-secondary)]"
                    >
                        <option value={0}>Conf: Any</option>
                        <option value={0.5}>Conf: ≥50%</option>
                        <option value={0.7}>Conf: ≥70%</option>
                        <option value={0.8}>Conf: ≥80%</option>
                    </select>
                </div>
            </div>

            {/* Thoughts List */}
            <div className="space-y-4 mt-4 max-h-[500px] overflow-y-auto pr-2">
                {filteredThoughts.length === 0 ? (
                    <div className="text-center py-8 text-[var(--text-muted)]">
                        No thoughts match your filters
                    </div>
                ) : (
                    filteredThoughts.map((thought) => (
                        <div key={thought.id} className="p-4 bg-[var(--bg-primary)] border border-[var(--border)]">
                            {/* Header */}
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <Clock className="w-3 h-3 text-[var(--text-muted)]" />
                                    <span className="text-xs text-[var(--text-muted)]">
                                        {formatTimeAgo(thought.timestamp)}
                                    </span>
                                    {thought.symbols.map(s => (
                                        <span key={s} className="badge bg-[var(--bg-card)] text-[var(--text-secondary)] text-[10px]">
                                            {s}
                                        </span>
                                    ))}
                                </div>
                                <div className="flex items-center gap-1">
                                    <span className={`text-xs font-medium ${thought.confidence >= 0.8 ? 'text-[var(--profit)]' :
                                        thought.confidence >= 0.6 ? 'text-[var(--accent-cyan)]' :
                                            'text-[var(--text-muted)]'
                                        }`}>
                                        {Math.round(thought.confidence * 100)}%
                                    </span>
                                </div>
                            </div>

                            {/* Summary */}
                            <p className="text-sm text-[var(--text-secondary)] mb-3">
                                {thought.summary}
                            </p>

                            {/* Actions */}
                            <div className="space-y-1">
                                {thought.actions.map((action, i) => (
                                    <div key={i} className="flex items-center gap-2 text-xs">
                                        {getStatusIcon(action.status)}
                                        <span className={`font-medium ${action.status === 'executed' ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)]'
                                            }`}>
                                            {action.type}
                                        </span>
                                        <span className="text-[var(--text-muted)]">{action.symbol}</span>
                                        {action.reason && (
                                            <span className="text-[var(--text-muted)]">— {action.reason}</span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
