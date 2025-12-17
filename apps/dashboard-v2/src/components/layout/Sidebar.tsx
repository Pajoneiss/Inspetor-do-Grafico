'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    LayoutDashboard,
    TrendingUp,
    Briefcase,
    FileText,
    Bot,
    Activity
} from 'lucide-react';

const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard, href: '/' },
    { id: 'analytics', label: 'Analytics', icon: TrendingUp, href: '/analytics' },
    { id: 'positions', label: 'Positions', icon: Briefcase, href: '/positions' },
    { id: 'logs', label: 'Logs', icon: FileText, href: '/logs' },
    { id: 'ai', label: 'AI', icon: Bot, href: '/ai' },
];

export function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="sidebar-logo">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-green)] flex items-center justify-center">
                        <Activity className="w-5 h-5 text-[var(--bg-primary)]" />
                    </div>
                    <div>
                        <h1 className="text-lg font-bold text-[var(--text-primary)]">
                            Engine V0
                        </h1>
                        <p className="text-xs text-[var(--text-muted)]">Dashboard v2.0</p>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav className="sidebar-nav">
                {navItems.map((item) => {
                    const isActive = pathname === item.href ||
                        (item.href !== '/' && pathname.startsWith(item.href));
                    const Icon = item.icon;

                    return (
                        <Link
                            key={item.id}
                            href={item.href}
                            className={`sidebar-item ${isActive ? 'active' : ''}`}
                        >
                            <Icon className="w-5 h-5" />
                            <span>{item.label}</span>
                        </Link>
                    );
                })}
            </nav>

            {/* Bot Status */}
            <div className="p-4 border-t border-[var(--border)]">
                <div className="flex items-center gap-3 p-3 rounded-xl bg-[var(--bg-card)]">
                    <div className="status-dot" />
                    <div>
                        <p className="text-xs font-medium text-[var(--text-primary)]">Bot Running</p>
                        <p className="text-[10px] text-[var(--text-muted)]">GLOBAL_IA Mode</p>
                    </div>
                </div>
            </div>
        </aside>
    );
}
