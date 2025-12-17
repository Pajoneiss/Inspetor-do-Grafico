'use client';

import { Wallet, Globe, Clock, RefreshCw } from 'lucide-react';

interface HeaderProps {
    wallet?: string;
    network?: string;
    isLive?: boolean;
    lastUpdate?: number;
}

export function Header({
    wallet = '0x...04bA24',
    network = 'mainnet',
    isLive = true,
    lastUpdate
}: HeaderProps) {
    const formatTimeAgo = (ms?: number) => {
        if (!ms) return '-';
        const seconds = Math.max(0, Math.floor((Date.now() - ms) / 1000));
        if (seconds < 60) return `${seconds}s ago`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        return `${Math.floor(seconds / 3600)}h ago`;
    };

    return (
        <header className="header">
            {/* Left: Wallet Info */}
            <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-green)] flex items-center justify-center">
                        <Wallet className="w-4 h-4 text-[var(--bg-primary)]" />
                    </div>
                    <div>
                        <p className="text-sm font-medium text-[var(--text-primary)]">{wallet}</p>
                        <div className="flex items-center gap-1">
                            <Globe className="w-3 h-3 text-[var(--text-muted)]" />
                            <p className="text-[10px] text-[var(--text-muted)] uppercase">{network}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Right: Status Badges */}
            <div className="flex items-center gap-3">
                {/* Last Update */}
                <div className="flex items-center gap-2 text-[var(--text-muted)]">
                    <Clock className="w-4 h-4" />
                    <span className="text-xs">{formatTimeAgo(lastUpdate)}</span>
                </div>

                {/* Refresh Indicator */}
                <button className="p-2 rounded-lg hover:bg-[var(--bg-card)] transition-colors">
                    <RefreshCw className="w-4 h-4 text-[var(--text-muted)]" />
                </button>

                {/* Live/Paper Badge */}
                <span className={`badge ${isLive ? 'badge-live' : 'badge-paper'}`}>
                    {isLive ? 'LIVE' : 'PAPER'}
                </span>

                {/* Mode Badge */}
                <span className="badge badge-cyan">
                    GLOBAL_IA
                </span>
            </div>
        </header>
    );
}
