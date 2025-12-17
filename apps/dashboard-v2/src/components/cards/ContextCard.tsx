'use client'
import React, { useState } from 'react'
import { ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

interface ContextCardProps {
    market?: any
    scanner?: any[]
    aiThinking?: any
    loading?: boolean
}

const TabButton = ({ active, label, onClick }: { active: boolean, label: string, onClick: () => void }) => (
    <button
        onClick={onClick}
        className={`px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider transition-all border-b-2 ${active ? 'border-accent-cyan text-accent-cyan bg-accent-cyan/5' : 'border-transparent text-text-muted hover:text-text-secondary'
            }`}
    >
        {label}
    </button>
)

export default function ContextCard({ market, scanner, aiThinking, loading }: ContextCardProps) {
    const [activeTab, setActiveTab] = useState<'sentiment' | 'scanner' | 'ai'>('sentiment')

    const fearGreed = market?.fear_greed || 50
    const sentimentColor = fearGreed > 70 ? '#00ff88' : fearGreed < 30 ? '#ff3b69' : '#00e5ff'

    const getSentimentLabel = (v: number) => {
        if (v >= 75) return 'Extreme Greed'
        if (v >= 55) return 'Greed'
        if (v >= 45) return 'Neutral'
        if (v >= 25) return 'Fear'
        return 'Extreme Fear'
    }

    const renderSentiment = () => (
        <div className="flex flex-col items-center py-4">
            <div className="w-32 h-20 relative">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={[{ value: fearGreed }, { value: 100 - fearGreed }]}
                            cx="50%"
                            cy="100%"
                            innerRadius={40}
                            outerRadius={60}
                            startAngle={180}
                            endAngle={0}
                            dataKey="value"
                            stroke="none"
                        >
                            <Cell fill={sentimentColor} opacity={0.8} />
                            <Cell fill="#1a1a1a" />
                        </Pie>
                    </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
                    <span className="text-2xl font-black text-text-primary leading-none">{fearGreed}</span>
                    <span className="text-[8px] text-text-muted font-bold uppercase mt-1 tracking-tighter">Fear & Greed</span>
                </div>
            </div>
            <div className="mt-2 text-xs font-bold" style={{ color: sentimentColor }}>
                {getSentimentLabel(fearGreed)}
            </div>
        </div>
    )

    const renderScanner = () => {
        const top5 = scanner?.filter(s => s.score > 60).sort((a, b) => b.score - a.score).slice(0, 5) || []
        const bottom3 = scanner?.filter(s => s.score < 40).sort((a, b) => a.score - b.score).slice(0, 3) || []

        return (
            <div className="space-y-3 py-2">
                <div>
                    <div className="text-[9px] font-bold text-profit uppercase mb-1 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-profit animate-pulse" /> Top Bullish
                    </div>
                    <div className="flex flex-wrap gap-1">
                        {top5.length ? top5.map(s => (
                            <span key={s.symbol} className="px-1.5 py-0.5 bg-profit/10 border border-profit/20 rounded text-[10px] font-bold text-profit">
                                {s.symbol} <span className="opacity-60 text-[8px] ml-0.5">{s.score}</span>
                            </span>
                        )) : <span className="text-[10px] text-text-muted">No signals</span>}
                    </div>
                </div>
                <div>
                    <div className="text-[9px] font-bold text-loss uppercase mb-1 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-loss" /> Top Bearish
                    </div>
                    <div className="flex flex-wrap gap-1">
                        {bottom3.length ? bottom3.map(s => (
                            <span key={s.symbol} className="px-1.5 py-0.5 bg-loss/10 border border-loss/20 rounded text-[10px] font-bold text-loss">
                                {s.symbol} <span className="opacity-60 text-[8px] ml-0.5">{s.score}</span>
                            </span>
                        )) : <span className="text-[10px] text-text-muted">No signals</span>}
                    </div>
                </div>
            </div>
        )
    }

    const renderAI = () => (
        <div className="py-2 space-y-2">
            <div className="bg-dark-bg/50 border border-dark-border p-2 rounded-lg">
                <div className="text-[9px] font-bold text-accent-cyan uppercase mb-1">Latest Decision</div>
                <div className="text-xs text-text-primary font-medium leading-tight">
                    {aiThinking?.objective || 'Analyzing current market regime...'}
                </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
                <div className="bg-dark-bg/30 p-2 rounded border border-dark-border/50">
                    <div className="text-[8px] font-bold text-text-muted uppercase mb-0.5">Confidence</div>
                    <div className="text-sm font-bold text-text-primary">{(aiThinking?.confidence || 0.85 * 100).toFixed(0)}%</div>
                </div>
                <div className="bg-dark-bg/30 p-2 rounded border border-dark-border/50">
                    <div className="text-[8px] font-bold text-text-muted uppercase mb-0.5">Regime</div>
                    <div className="text-sm font-bold text-accent-cyan">{aiThinking?.tags?.regime || 'Trending'}</div>
                </div>
            </div>
            <div className="text-[10px] text-text-muted italic leading-snug">
                Next review: {(aiThinking?.next_check || '3m 42s')}
            </div>
        </div>
    )

    return (
        <div className="bg-dark-card rounded-xl border border-dark-border flex flex-col h-full overflow-hidden">
            <div className="flex border-b border-dark-border bg-dark-bg/30">
                <TabButton active={activeTab === 'sentiment'} label="Sentiment" onClick={() => setActiveTab('sentiment')} />
                <TabButton active={activeTab === 'scanner'} label="Scanner" onClick={() => setActiveTab('scanner')} />
                <TabButton active={activeTab === 'ai'} label="AI Insight" onClick={() => setActiveTab('ai')} />
            </div>
            <div className="p-4 flex-1">
                {loading ? (
                    <div className="h-full flex flex-col gap-4 animate-pulse">
                        <div className="h-4 w-1/2 bg-dark-border rounded" />
                        <div className="h-20 w-full bg-dark-border rounded" />
                        <div className="h-10 w-full bg-dark-border rounded" />
                    </div>
                ) : (
                    <>
                        {activeTab === 'sentiment' && renderSentiment()}
                        {activeTab === 'scanner' && renderScanner()}
                        {activeTab === 'ai' && renderAI()}
                    </>
                )}
            </div>
        </div>
    )
}
