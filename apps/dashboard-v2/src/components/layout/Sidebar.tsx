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

interface SidebarProps {
    activePage?: string;
}

export default function Sidebar({ activePage }: SidebarProps = {}) {
    const pathname = usePathname();

    return (
        <aside className="sidebar">
            {/* Logo */}
            <div className="sidebar-logo">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-[var(--accent-cyan)] to-[var(--accent-green)] flex items-center justify-center">
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
                            className={`sidebar-item group ${isActive ? 'active shadow-[0_0_20px_rgba(0,229,255,0.15)] bg-white/5' : ''} !rounded-none`}
                        >
                            <Icon className={`w-5 h-5 transition-transform duration-300 group-hover:scale-110 ${isActive ? 'text-[var(--accent-cyan)]' : ''}`} />
                            <span className={isActive ? 'font-bold' : ''}>{item.label}</span>
                            {isActive && (
                                <div className="ml-auto w-1 h-4 rounded-full bg-[var(--accent-cyan)] shadow-[0_0_10px_var(--accent-cyan)]" />
                            )}
                        </Link>
                    );
                })}
            </nav>

            {/* Bot Status */}
            <div className="p-4 mt-auto border-t border-[var(--border)]">
                <div className="flex items-center gap-3 p-6 glass glass-hover">
                    <div className="relative">
                        <div className="status-dot" />
                        <div className="absolute inset-0 status-dot blur-sm opacity-50" />
                    </div>
                    <div>
                        <p className="text-[11px] font-bold text-[var(--text-primary)] tracking-tight">Active Engine</p>
                        <p className="text-[10px] font-medium text-[var(--accent-green)] opacity-80 uppercase tracking-wider">Operational</p>
                    </div>
                </div>
            </div>
        </aside>
    );
}
