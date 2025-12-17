'use client';

import { useState } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import { AiChat } from '@/components/ai/AiChat';
import { AiThoughts } from '@/components/ai/AiThoughts';

export default function AiPage() {
    const [activeTab, setActiveTab] = useState<'chat' | 'thoughts'>('thoughts');

    return (
        <div className="min-h-screen flex">
            <Sidebar />

            <main className="main-content">
                <Header
                    wallet="0x...04bA24"
                    network="mainnet"
                    isLive={true}
                    lastUpdate={Date.now()}
                />

                <div className="p-6">
                    {/* Tab Navigation */}
                    <div className="flex gap-2 mb-6">
                        <button
                            onClick={() => setActiveTab('thoughts')}
                            className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${activeTab === 'thoughts'
                                ? 'bg-[var(--accent-green-bg)] text-[var(--accent-green)] border border-[var(--accent-green)]/30'
                                : 'bg-[var(--bg-card)] text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)]'
                                }`}
                        >
                            AI Thoughts Feed
                        </button>
                        <button
                            onClick={() => setActiveTab('chat')}
                            className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors ${activeTab === 'chat'
                                ? 'bg-[var(--accent-cyan-bg)] text-[var(--accent-cyan)] border border-[var(--accent-cyan)]/30'
                                : 'bg-[var(--bg-card)] text-[var(--text-secondary)] hover:bg-[var(--bg-card-hover)]'
                                }`}
                        >
                            AI Chat (Q&A)
                        </button>
                    </div>

                    {/* Content */}
                    {activeTab === 'thoughts' ? <AiThoughts /> : <AiChat />}
                </div>
            </main>
        </div>
    );
}
