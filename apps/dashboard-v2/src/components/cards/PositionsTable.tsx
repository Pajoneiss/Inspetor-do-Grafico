'use client';

interface Position {
    symbol: string;
    side: 'LONG' | 'SHORT';
    size: number;
    entryPrice: number;
    markPrice: number;
    unrealizedPnl: number;
    roe: number;
    liquidationPrice?: number;
    stopLoss?: number;
    takeProfit?: number;
    breakeven?: 'INACTIVE' | 'ARMED' | 'TRIGGERED' | 'EXECUTED';
}

interface PositionsTableProps {
    positions: Position[];
    loading?: boolean;
}

export function PositionsTable({ positions, loading = false }: PositionsTableProps) {
    if (loading) {
        return (
            <div className="card">
                <div className="card-header">
                    <span className="card-title">Open Positions</span>
                </div>
                <div className="space-y-3">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="skeleton h-12 w-full" />
                    ))}
                </div>
            </div>
        );
    }

    const formatCurrency = (value: number, decimals = 2) =>
        new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: decimals
        }).format(value);

    const formatPnl = (value: number) => {
        const formatted = formatCurrency(Math.abs(value));
        return value >= 0 ? `+${formatted}` : `-${formatted}`;
    };

    const formatRoe = (value: number) => {
        const sign = value >= 0 ? '+' : '';
        return `${sign}${value.toFixed(1)}%`;
    };

    const getBadgeClass = (status?: string) => {
        switch (status) {
            case 'ARMED': return 'badge-cyan';
            case 'TRIGGERED': return 'bg-[var(--accent-yellow-bg)] text-[var(--accent-yellow)]';
            case 'EXECUTED': return 'badge-live';
            default: return 'bg-[var(--bg-primary)] text-[var(--text-muted)]';
        }
    };

    return (
        <div className="card">
            <div className="card-header">
                <span className="card-title">Open Positions</span>
                <span className="text-xs text-[var(--text-muted)]">{positions.length} active</span>
            </div>

            {positions.length === 0 ? (
                <div className="py-8 text-center text-[var(--text-muted)]">
                    No open positions
                </div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Symbol</th>
                                <th>Side</th>
                                <th>Size</th>
                                <th>Entry</th>
                                <th>Mark</th>
                                <th>uPnL</th>
                                <th>ROE</th>
                                <th>SL / TP</th>
                                <th>BE</th>
                            </tr>
                        </thead>
                        <tbody>
                            {positions.map((pos) => (
                                <tr key={pos.symbol}>
                                    <td className="font-medium">{pos.symbol}</td>
                                    <td>
                                        <span className={`badge ${pos.side === 'LONG' ? 'badge-live' : 'badge-error'}`}>
                                            {pos.side}
                                        </span>
                                    </td>
                                    <td>{pos.size.toFixed(4)}</td>
                                    <td>{formatCurrency(pos.entryPrice)}</td>
                                    <td>{formatCurrency(pos.markPrice)}</td>
                                    <td className={pos.unrealizedPnl >= 0 ? 'profit' : 'loss'}>
                                        {formatPnl(pos.unrealizedPnl)}
                                    </td>
                                    <td className={pos.roe >= 0 ? 'profit' : 'loss'}>
                                        {formatRoe(pos.roe)}
                                    </td>
                                    <td className="text-[var(--text-muted)] text-xs">
                                        {pos.stopLoss ? formatCurrency(pos.stopLoss, 0) : '-'} / {pos.takeProfit ? formatCurrency(pos.takeProfit, 0) : '-'}
                                    </td>
                                    <td>
                                        <span className={`badge text-[10px] ${getBadgeClass(pos.breakeven)}`}>
                                            {pos.breakeven || 'N/A'}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
