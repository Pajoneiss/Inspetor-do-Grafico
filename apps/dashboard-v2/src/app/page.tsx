'use client';

import { useState, useEffect } from 'react';

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<{
    equity: number;
    positions: number;
    pnlToday: number;
    mode: string;
  } | null>(null);

  useEffect(() => {
    // Simulate loading - Replace with actual API call
    const timer = setTimeout(() => {
      setData({
        equity: 1250.75,
        positions: 2,
        pnlToday: 45.23,
        mode: 'GLOBAL_IA'
      });
      setLoading(false);
    }, 1500);

    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-[var(--accent-cyan)]" />
          <p className="text-[var(--text-muted)] text-sm">Conectando ao bot...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-56 bg-[var(--card-bg)] border-r border-[var(--card-border)] flex flex-col z-50">
        {/* Logo */}
        <div className="p-6 border-b border-[var(--card-border)]">
          <h1 className="text-xl font-bold gradient-text">
            🔍 Inspetor
          </h1>
          <p className="text-xs text-[var(--text-muted)] mt-1">Dashboard v2.0</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {[
            { id: 'overview', label: 'Overview', icon: '📊', active: true },
            { id: 'analytics', label: 'Analytics', icon: '📈' },
            { id: 'positions', label: 'Positions', icon: '💼' },
            { id: 'logs', label: 'Logs', icon: '📋' },
            { id: 'ai', label: 'AI', icon: '🤖' },
          ].map((item) => (
            <button
              key={item.id}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200
                ${item.active
                  ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/20'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--card-border)]/50 hover:text-[var(--text-primary)]'
                }`}
            >
              <span className="text-base">{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Bot Status */}
        <div className="p-4 border-t border-[var(--card-border)]">
          <div className="flex items-center gap-3 px-4 py-3 bg-[var(--card-border)]/30 rounded-xl">
            <div className="relative">
              <div className="w-2.5 h-2.5 rounded-full bg-[var(--accent-green)] animate-pulse" />
            </div>
            <div>
              <p className="text-xs font-medium text-[var(--text-primary)]">Bot Running</p>
              <p className="text-[10px] text-[var(--text-muted)]">{data?.mode || 'GLOBAL_IA'}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="ml-56 flex-1">
        {/* Header */}
        <header className="sticky top-0 z-40 bg-[var(--background)]/80 backdrop-blur-lg border-b border-[var(--card-border)]">
          <div className="flex items-center justify-between px-6 py-3">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-green)] flex items-center justify-center text-xs font-bold text-[var(--background)]">
                  HL
                </div>
                <div>
                  <p className="text-sm font-medium text-[var(--text-primary)]">0x...abcd</p>
                  <p className="text-[10px] text-[var(--text-muted)] uppercase">mainnet</p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-[var(--accent-green-bg)] text-[var(--accent-green)] border border-[var(--accent-green)]/30">
                LIVE
              </span>
              <span className="px-3 py-1 rounded-full text-xs font-medium bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/30">
                {data?.mode}
              </span>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <div className="p-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="glass-card p-4">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide">Equity</p>
              <p className="text-2xl font-bold text-[var(--text-primary)]">${data?.equity.toFixed(2)}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide">Positions</p>
              <p className="text-2xl font-bold text-[var(--text-primary)]">{data?.positions}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide">PnL Today</p>
              <p className={`text-2xl font-bold ${data?.pnlToday && data.pnlToday >= 0 ? 'text-[var(--profit)]' : 'text-[var(--loss)]'}`}>
                ${data?.pnlToday.toFixed(2)}
              </p>
            </div>
            <div className="glass-card p-4">
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide">Mode</p>
              <p className="text-2xl font-bold text-[var(--accent-cyan)]">{data?.mode}</p>
            </div>
          </div>

          {/* Placeholder for Chart */}
          <div className="glass-card p-6 mb-6">
            <h2 className="text-lg font-bold text-[var(--text-primary)] mb-4">Equity Chart</h2>
            <div className="h-64 flex items-center justify-center text-[var(--text-muted)]">
              📈 Chart coming soon...
            </div>
          </div>

          {/* Footer */}
          <footer className="text-center text-xs text-[var(--text-muted)] border-t border-[var(--card-border)] pt-4">
            Inspetor do Gráfico v2.0 | Dashboard Premium Dark Theme
          </footer>
        </div>
      </main>
    </div>
  );
}
