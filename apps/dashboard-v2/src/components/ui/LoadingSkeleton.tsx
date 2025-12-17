'use client'

export default function LoadingSkeleton({ variant = 'default', className = '' }: { variant?: 'default' | 'chart' | 'card' | 'text', className?: string }) {
    const variants = {
        default: 'h-8 w-full',
        chart: 'h-64 w-full',
        card: 'h-32 w-full',
        text: 'h-4 w-3/4'
    }

    return (
        <div className={`${variants[variant]} ${className} bg-gradient-to-r from-[var(--glass-bg)] via-[var(--glass-border)] to-[var(--glass-bg)] bg-[length:200%_100%] animate-shimmer rounded-lg`} />
    )
}
