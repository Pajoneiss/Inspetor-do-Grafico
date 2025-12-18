// Latest AI Trade Analysis Card Component
// Insert this in the Overview section of page.tsx

{/* Latest AI Trade Analysis - WOW Feature */ }
<GlassCard className="lg:col-span-3 border border-purple-500/20" delay={0.35}>
    <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-purple-500/20 text-purple-400 neon-glow">
                <BrainCircuit className="w-6 h-6" />
            </div>
            <div>
                <h3 className="text-xl font-bold tracking-tight">Latest AI Trade Analysis</h3>
                <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-widest mt-1">Detailed Strategy Breakdown</p>
            </div>
        </div>
        <button className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-all text-xs font-bold uppercase tracking-wider">
            View All
        </button>
    </div>

    {tradeLog ? (
        <div className="space-y-6">
            {/* Trade Header */}
            <div className="flex items-center justify-between p-4 rounded-2xl bg-gradient-to-r from-purple-500/10 to-primary/10 border border-white/10">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center font-bold text-lg">
                        {tradeLog.symbol?.substring(0, 2) || 'BTC'}
                    </div>
                    <div>
                        <h4 className="text-lg font-bold">{tradeLog.symbol} {tradeLog.side}</h4>
                        <p className="text-xs text-muted-foreground font-bold">@ ${tradeLog.entry_price?.toLocaleString() || '0'}</p>
                    </div>
                </div>
                <div className="text-right">
                    <p className="text-xs text-muted-foreground font-bold uppercase tracking-widest">Setup Quality</p>
                    <div className="flex items-center gap-2 mt-1">
                        <div className="h-2 w-24 bg-white/10 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${(tradeLog.strategy?.setup_quality || 0) * 10}%` }}
                                className="h-full bg-gradient-to-r from-primary to-purple-500 neon-glow"
                            />
                        </div>
                        <span className="text-sm font-bold text-primary">{tradeLog.strategy?.setup_quality || 0}/10</span>
                    </div>
                </div>
            </div>

            {/* Strategy */}
            <div>
                <div className="flex items-center gap-2 mb-3">
                    <Target className="w-4 h-4 text-primary" />
                    <h5 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Strategy</h5>
                </div>
                <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                    <p className="text-xs font-bold text-primary mb-1">{tradeLog.strategy?.name || 'N/A'} • {tradeLog.strategy?.timeframe || 'N/A'}</p>
                    <p className="text-sm text-white/80 leading-relaxed">{tradeLog.entry_rationale || 'No rationale provided'}</p>
                </div>
            </div>

            {/* Confluence Factors */}
            {tradeLog.strategy?.confluence_factors && (
                <div>
                    <div className="flex items-center gap-2 mb-3">
                        <Shield className="w-4 h-4 text-primary" />
                        <h5 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Confluence ({tradeLog.strategy.confluence_factors.length} factors)</h5>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {tradeLog.strategy.confluence_factors.map((factor, i) => (
                            <div key={i} className="flex items-start gap-2 p-2 rounded-lg bg-white/5">
                                <span className="text-primary text-xs mt-0.5">✓</span>
                                <span className="text-xs text-white/70">{factor}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Risk Management */}
            <div>
                <div className="flex items-center gap-2 mb-3">
                    <Activity className="w-4 h-4 text-secondary" />
                    <h5 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Risk Management</h5>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {/* Stop Loss */}
                    <div className="p-3 rounded-xl bg-secondary/10 border border-secondary/20">
                        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1">Stop Loss</p>
                        <p className="text-lg font-bold text-secondary">${tradeLog.risk_management?.stop_loss?.toLocaleString() || '0'}</p>
                        <p className="text-xs text-white/60 mt-1">{tradeLog.risk_management?.stop_loss_reason || 'N/A'}</p>
                    </div>

                    {/* TP1 */}
                    <div className="p-3 rounded-xl bg-primary/10 border border-primary/20">
                        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1">Take Profit 1 ({tradeLog.risk_management?.tp1_size_pct || 0}%)</p>
                        <p className="text-lg font-bold text-primary">${tradeLog.risk_management?.take_profit_1?.toLocaleString() || '0'}</p>
                        <p className="text-xs text-white/60 mt-1">{tradeLog.risk_management?.tp1_reason || 'N/A'}</p>
                    </div>

                    {/* TP2 */}
                    <div className="p-3 rounded-xl bg-primary/10 border border-primary/20">
                        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1">Take Profit 2 ({tradeLog.risk_management?.tp2_size_pct || 0}%)</p>
                        <p className="text-lg font-bold text-primary">${tradeLog.risk_management?.take_profit_2?.toLocaleString() || '0'}</p>
                        <p className="text-xs text-white/60 mt-1">{tradeLog.risk_management?.tp2_reason || 'N/A'}</p>
                    </div>

                    {/* Risk */}
                    <div className="p-3 rounded-xl bg-white/5 border border-white/10">
                        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-1">Risk</p>
                        <p className="text-lg font-bold">${tradeLog.risk_management?.risk_usd?.toFixed(2) || '0'}</p>
                        <p className="text-xs text-white/60 mt-1">{tradeLog.risk_management?.risk_pct?.toFixed(2) || '0'}% of equity</p>
                    </div>
                </div>
            </div>

            {/* Breakeven & Trailing */}
            {(tradeLog.risk_management?.breakeven_plan?.enabled || tradeLog.risk_management?.trailing_stop?.enabled) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {tradeLog.risk_management?.breakeven_plan?.enabled && (
                        <div className="p-3 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
                            <div className="flex items-center gap-2 mb-2">
                                <ChevronRight className="w-4 h-4 text-yellow-500" />
                                <p className="text-xs font-bold uppercase tracking-widest text-yellow-500">Breakeven Plan</p>
                            </div>
                            <p className="text-sm text-white/80">Move to ${tradeLog.risk_management.breakeven_plan.move_to?.toLocaleString() || '0'}</p>
                            <p className="text-xs text-white/60 mt-1">{tradeLog.risk_management.breakeven_plan.trigger || 'N/A'}</p>
                        </div>
                    )}

                    {tradeLog.risk_management?.trailing_stop?.enabled && (
                        <div className="p-3 rounded-xl bg-blue-500/10 border border-blue-500/20">
                            <div className="flex items-center gap-2 mb-2">
                                <Activity className="w-4 h-4 text-blue-400" />
                                <p className="text-xs font-bold uppercase tracking-widest text-blue-400">Trailing Stop</p>
                            </div>
                            <p className="text-sm text-white/80">{tradeLog.risk_management.trailing_stop.distance || 'N/A'}</p>
                            <p className="text-xs text-white/60 mt-1">{tradeLog.risk_management.trailing_stop.activation || 'N/A'}</p>
                        </div>
                    )}
                </div>
            )}

            {/* AI Notes */}
            {tradeLog.ai_notes && (
                <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
                    <div className="flex items-center gap-2 mb-2">
                        <BrainCircuit className="w-4 h-4 text-purple-400" />
                        <p className="text-xs font-bold uppercase tracking-widest text-purple-400">AI Notes</p>
                    </div>
                    <p className="text-sm text-white/80 italic leading-relaxed">"{tradeLog.ai_notes}"</p>
                </div>
            )}

            {/* Confidence */}
            <div className="flex items-center justify-between p-4 rounded-xl bg-gradient-to-r from-white/5 to-primary/5 border border-white/10">
                <div>
                    <p className="text-xs font-bold text-muted-foreground uppercase tracking-widest mb-1">AI Confidence</p>
                    <p className="text-2xl font-bold text-primary">{((tradeLog.confidence || 0) * 100).toFixed(0)}%</p>
                </div>
                <div className="text-right max-w-md">
                    <p className="text-xs text-white/60">{tradeLog.expected_outcome || 'No outcome prediction'}</p>
                </div>
            </div>
        </div>
    ) : (
        <div className="h-64 flex flex-col items-center justify-center opacity-20">
            <BrainCircuit className="w-16 h-16 mb-4 animate-pulse" />
            <p className="text-sm font-bold uppercase tracking-widest">No trade logs yet</p>
        </div>
    )}
</GlassCard>
