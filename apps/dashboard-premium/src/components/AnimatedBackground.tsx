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

interface Particle {
    x: number;
    y: number;
    speed: number;
    direction: 'horizontal' | 'vertical';
    length: number;
    color: string;
    opacity: number;
}

interface Root {
    x: number;
    y: number;
    segments: { x: number, y: number }[];
    maxSegments: number;
    growSpeed: number;
    color: string;
    complete: boolean;
}

export default function AnimatedBackground() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const coinsRef = useRef<Coin[]>([]);
    const particlesRef = useRef<Particle[]>([]);
    const rootsRef = useRef<Root[]>([]);
    const animationFrameRef = useRef<number>();

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        // --- COINS ---
        const initCoins = () => {
            const coins: Coin[] = [];
            const coinCount = Math.floor((window.innerWidth * window.innerHeight) / 15000);
            for (let i = 0; i < coinCount; i++) {
                coins.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    size: 20 + Math.random() * 30,
                    speed: 0.2 + Math.random() * 0.5,
                    rotation: Math.random() * Math.PI * 2,
                    rotationSpeed: (Math.random() - 0.5) * 0.02,
                    type: 'btc' // User requested only BTC
                });
            }
            coinsRef.current = coins;
        };
        initCoins();

        // --- ENERGY PARTICLES ---
        const spawnParticle = () => {
            if (Math.random() > 0.1) return; // limit spawn rate
            const axis = Math.random() > 0.5 ? 'horizontal' : 'vertical';
            particlesRef.current.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                speed: 2 + Math.random() * 3,
                direction: axis,
                length: 20 + Math.random() * 50,
                color: '#00FF41',
                opacity: 0.5 + Math.random() * 0.5
            });
        };

        // --- ROOTS "ENRAIZADAS" ---
        const spawnRoot = () => {
            if (rootsRef.current.length > 5) return;
            if (Math.random() > 0.02) return;
            rootsRef.current.push({
                x: Math.random() * canvas.width,
                y: canvas.height,
                segments: [{ x: Math.random() * canvas.width, y: canvas.height }],
                maxSegments: 20 + Math.random() * 30,
                growSpeed: 1, // frame count
                color: '#00FF41',
                complete: false
            });
        };

        // DRAW COINS
        const drawBTC = (ctx: CanvasRenderingContext2D, x: number, y: number, size: number, rotation: number) => {
            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(rotation);
            ctx.fillStyle = 'rgba(247, 147, 26, 0.15)';
            ctx.font = `bold ${size}px "Courier New", monospace`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText('₿', 0, 0);
            ctx.restore();
        };

        // ETH drawing removed as requested

        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // 1. Draw Roots (Bottom "Enraizadas")
            spawnRoot();
            rootsRef.current.forEach((root, idx) => {
                if (!root.complete && Math.random() > 0.5) {
                    const last = root.segments[root.segments.length - 1];
                    // Move mostly up, slightly random x
                    const newX = last.x + (Math.random() - 0.5) * 20;
                    const newY = last.y - (Math.random() * 20);
                    root.segments.push({ x: newX, y: newY });
                    if (root.segments.length >= root.maxSegments || newY < 0) {
                        root.complete = true;
                    }
                }

                ctx.beginPath();
                ctx.strokeStyle = `rgba(0, 255, 65, 0.1)`;
                ctx.lineWidth = 2;
                if (root.segments.length > 0) {
                    ctx.moveTo(root.segments[0].x, root.segments[0].y);
                    root.segments.forEach(p => ctx.lineTo(p.x, p.y));
                }
                ctx.stroke();

                // Draw glowing tip
                if (root.segments.length > 0) {
                    const tip = root.segments[root.segments.length - 1];
                    ctx.fillStyle = '#00FF41';
                    ctx.fillRect(tip.x - 2, tip.y - 2, 4, 4);
                }

                if (root.complete) {
                    // Fade out logic could be here, or remove
                    if (Math.random() > 0.99) rootsRef.current.splice(idx, 1);
                }
            });

            // 2. Draw Energy Particles (Network Flow)
            spawnParticle();
            for (let i = particlesRef.current.length - 1; i >= 0; i--) {
                const p = particlesRef.current[i];
                if (p.direction === 'horizontal') p.x += p.speed;
                else p.y += p.speed;

                if (p.x > canvas.width || p.y > canvas.height) {
                    particlesRef.current.splice(i, 1);
                    continue;
                }

                ctx.fillStyle = `rgba(0, 255, 65, ${p.opacity * 0.5})`;
                if (p.direction === 'horizontal') {
                    ctx.fillRect(p.x, p.y, p.length, 2);
                } else {
                    ctx.fillRect(p.x, p.y, 2, p.length);
                }
            }

            // 3. Draw Coins
            coinsRef.current.forEach(coin => {
                coin.y -= coin.speed;
                coin.rotation += coin.rotationSpeed;
                if (coin.y + coin.size < 0) {
                    coin.y = canvas.height + coin.size;
                    coin.x = Math.random() * canvas.width;
                }
                if (coin.type === 'btc') drawBTC(ctx, coin.x, coin.y, coin.size, coin.rotation);
            });

            animationFrameRef.current = requestAnimationFrame(animate);
        };

        animate();

        return () => {
            window.removeEventListener('resize', resizeCanvas);
            if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="fixed inset-0 pointer-events-none z-[-1]"
            style={{ background: 'transparent' }}
        />
    );
}
