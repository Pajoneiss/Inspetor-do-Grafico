"use client";

import React, { useEffect, useRef } from 'react';

interface Coin {
    x: number;
    y: number;
    size: number;
    speed: number;
    rotation: number;
    rotationSpeed: number;
    type: 'btc' | 'eth';
}

export default function AnimatedBackground() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const coinsRef = useRef<Coin[]>([]);
    const animationFrameRef = useRef<number>();

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Set canvas size
        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        // Initialize coins
        const initCoins = () => {
            const coins: Coin[] = [];
            const coinCount = Math.floor((window.innerWidth * window.innerHeight) / 15000); // Density control

            for (let i = 0; i < coinCount; i++) {
                coins.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    size: 20 + Math.random() * 30, // 20-50px
                    speed: 0.2 + Math.random() * 0.5, // Slow floating
                    rotation: Math.random() * Math.PI * 2,
                    rotationSpeed: (Math.random() - 0.5) * 0.02,
                    type: Math.random() > 0.5 ? 'btc' : 'eth'
                });
            }
            coinsRef.current = coins;
        };
        initCoins();

        // Draw BTC symbol
        const drawBTC = (ctx: CanvasRenderingContext2D, x: number, y: number, size: number, rotation: number) => {
            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(rotation);

            // Bitcoin symbol (₿)
            ctx.fillStyle = 'rgba(247, 147, 26, 0.15)'; // Bitcoin orange with low opacity
            ctx.font = `bold ${size}px Arial`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('₿', 0, 0);

            ctx.restore();
        };

        // Draw ETH symbol
        const drawETH = (ctx: CanvasRenderingContext2D, x: number, y: number, size: number, rotation: number) => {
            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(rotation);

            // Ethereum symbol (Ξ)
            ctx.fillStyle = 'rgba(98, 126, 234, 0.15)'; // Ethereum blue with low opacity
            ctx.font = `bold ${size}px Arial`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('Ξ', 0, 0);

            ctx.restore();
        };

        // Animation loop
        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            coinsRef.current.forEach(coin => {
                // Update position
                coin.y -= coin.speed;
                coin.rotation += coin.rotationSpeed;

                // Reset coin if it goes off screen
                if (coin.y + coin.size < 0) {
                    coin.y = canvas.height + coin.size;
                    coin.x = Math.random() * canvas.width;
                }

                // Draw coin
                if (coin.type === 'btc') {
                    drawBTC(ctx, coin.x, coin.y, coin.size, coin.rotation);
                } else {
                    drawETH(ctx, coin.x, coin.y, coin.size, coin.rotation);
                }
            });

            animationFrameRef.current = requestAnimationFrame(animate);
        };

        animate();

        return () => {
            window.removeEventListener('resize', resizeCanvas);
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current);
            }
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 pointer-events-none z-0"
            style={{ background: 'transparent' }}
        />
    );
}
