'use client';

import { Wallet, Globe, Clock, RefreshCw } from 'lucide-react';

interface HeaderProps {
    wallet?: string;
    network?: string;
    isLive?: boolean;
    lastUpdate?: Date | number;
    onRefresh?: () => void;
}

export default function Header({
    wallet = '0x...04bA24',
    network = 'mainnet',
    isLive = true,
    lastUpdate,
    onRefresh
}: HeaderProps) {
    const formatTimeAgo = (update?: Date | number) => {
        if (!update) return '0s ago';
        const ms = update instanceof Date ? update.getTime() : update;
        const seconds = Math.max(0, Math.floor((Date.now() - ms) / 1000));
        if (seconds < 60) return `${seconds}s ago`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        return `${Math.floor(seconds / 3600)}h ago`;
    };

    return (
        <header className="px-8 py-6 flex justify-between items-center border-b border-white/5 bg-[#040608]/50 backdrop-blur-xl sticky top-0 z-50">
            {/* Left: Wallet Info */}
            <div className="flex items-center gap-6">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[var(--color-accent-cyan)] to-[var(--color-accent-green)] flex items-center justify-center shadow-lg shadow-cyan-500/20">
                        <Wallet className="w-5 h-5 text-[#040608]" />
                    </div>
                    <div>
                        <p className="text-xs font-black text-[var(--color-text-muted)] uppercase tracking-widest opacity-60">Fleet Commander</p>
                        <p className="text-sm font-black text-[var(--color-text-primary)] tracking-tight">{wallet}</p>
                    </div>
                </div>
            </div>

            {/* Right: Status Badges */}
            <div className="flex items-center gap-4">
                {/* Last Update */}
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/5">
                    <Clock className="w-3.5 h-3.5 text-[var(--color-accent-cyan)] animate-pulse" />
                    <span className="text-[10px] font-black text-[var(--color-text-primary)] tracking-widest">{formatTimeAgo(lastUpdate).toUpperCase()}</span>
                </div>

                {/* Refresh Button */}
                <button
                    onClick={onRefresh}
                    className="p-2 rounded-xl glass glass-hover group"
                >
                    <RefreshCw className="w-4 h-4 text-[var(--color-text-muted)] group-hover:text-[var(--color-accent-cyan)] transition-colors group-hover:rotate-180 duration-500" />
                </button>

                {/* Live/Paper Badge */}
                <span className={`badge ${isLive ? 'badge-live' : 'badge-paper'} px-4 py-1.5 rounded-full font-black tracking-[0.2em] shadow-lg`}>
                    {isLive ? 'LIVE CORE' : 'PAPER SIM'}
                </span>

                {/* Mode Badge */}
                <span className="badge badge-cyan px-4 py-1.5 rounded-full font-black tracking-[0.2em] shadow-lg neon-glow-cyan bg-cyan-500/10 border-cyan-500/20">
                    GLOBAL_IA
                </span>
            </div>
        </header>
    );
}

