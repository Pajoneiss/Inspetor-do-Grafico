"use client";

import React, { useState } from 'react';
import { Book, GraduationCap, ArrowRight, Globe, Lock, Brain, TrendingUp, Activity, Heart, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';


const GlassCard = ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div className={cn(
        "glass-card p-6 overflow-hidden relative group transition-all duration-300 hover:-translate-y-1 hover:border-primary/30",
        className
    )}>
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        <div className="relative z-10">{children}</div>
    </div>
);

const CHAPTERS = [
    {
        id: 1,
        title_pt: "Os Fundamentos Clássicos",
        title_en: "Classical Fundamentals",
        desc_pt: "Dow, Elliott e Wyckoff: A base centenária dos mercados.",
        desc_en: "Dow, Elliott, and Wyckoff: The century-old market foundation.",
        icon: Book,
        file_pt: "01_FUNDAMENTOS_CLASSICOS.md",
        file_en: "01_CLASSICAL_FUNDAMENTALS.md",
        color: "text-blue-400"
    },
    {
        id: 2,
        title_pt: "Price Action Avançado",
        title_en: "Advanced Price Action",
        desc_pt: "Lendo a linguagem pura das velas e padrões gráficos.",
        desc_en: "Reading the pure language of candles and chart patterns.",
        icon: TrendingUp,
        file_pt: "02_PRICE_ACTION_AVANCADO.md",
        file_en: "02_ADVANCED_PRICE_ACTION.md",
        color: "text-green-400"
    },
    {
        id: 3,
        title_pt: "Smart Money Concepts (SMC)",
        title_en: "Smart Money Concepts (SMC)",
        desc_pt: "O segredo institucional: Order Blocks, FVG e Liquidez.",
        desc_en: "Institutional secrets: Order Blocks, FVG, and Liquidity.",
        icon: Lock,
        file_pt: "03_SMART_MONEY_CONCEPTS.md",
        file_en: "03_SMART_MONEY_CONCEPTS.md",
        color: "text-purple-400"
    },
    {
        id: 4,
        title_pt: "Ferramentas Matemáticas",
        title_en: "Mathematical Tools",
        desc_pt: "Fibonacci, RSI e a geometria do lucro.",
        desc_en: "Fibonacci, RSI, and the geometry of profit.",
        icon: Activity,
        file_pt: "04_FERRAMENTAS_MATEMATICAS.md",
        file_en: "04_MATHEMATICAL_TOOLS.md",
        color: "text-yellow-400"
    },
    {
        id: 5,
        title_pt: "Mente Blindada & Gestão",
        title_en: "Bulletproof Mind & Management",
        desc_pt: "Psicologia e Risco: Onde o jogo é ganho.",
        desc_en: "Psychology and Risk: Where the game is won.",
        icon: Shield,
        file_pt: "05_GESTAO_RISCO_PSICOLOGIA.md",
        file_en: "05_PSYCHOLOGY_RISK.md",
        color: "text-red-400"
    },
    {
        id: 6,
        title_pt: "Trader Atleta - Lifestyle",
        title_en: "Trader Athlete - Lifestyle",
        desc_pt: "Sono, dopamina e a biologia da alta performance.",
        desc_en: "Sleep, dopamine, and the biology of peak performance.",
        icon: Heart,
        file_pt: "06_LIFESTYLE_SAUDE.md",
        file_en: "06_LIFESTYLE_HEALTH.md",
        color: "text-pink-400"
    },
    {
        id: 7,
        title_pt: "A Revolução Inspetor",
        title_en: "The Inspetor Revolution",
        desc_pt: "IA + Humano: O futuro do trading híbrido.",
        desc_en: "AI + Human: The future of hybrid trading.",
        icon: Brain,
        file_pt: "07_A_REVOLUCAO_INSPETOR.md",
        file_en: "07_THE_INSPETOR_REVOLUTION.md",
        color: "text-cyan-400"
    },
    {
        id: 8,
        title_pt: "Modalidades e Perfis",
        title_en: "Modalities & Profiles",
        desc_pt: "Scalp vs Swing vs Hodl: Quem é você no mercado?",
        desc_en: "Scalp vs Swing vs Hodl: Who are you in the market?",
        icon: GraduationCap,
        file_pt: "08_MODALIDADES_ESTILOS.md",
        file_en: "08_MODALITIES_STYLES.md",
        color: "text-indigo-400"
    },
    {
        id: 9,
        title_pt: "Cripto & Segurança",
        title_en: "Crypto & Security",
        desc_pt: "DeFi, Blockchain e como não ser hackeado (Keys).",
        desc_en: "DeFi, Blockchain and how to filter attacks.",
        icon: Shield,
        file_pt: "09_ECOSSISTEMA_CRIPTO_SEGURANCA.md",
        file_en: "09_CRYPTO_ECOSYSTEM_SECURITY.md",
        color: "text-orange-400"
    }
];

const REPO_URL = "https://github.com/Pajoneiss/Inspetor-do-Grafico/blob/main/docs/ebook";

export default function AcademyView() {
    const [lang, setLang] = useState<'pt' | 'en'>('pt');

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">

            {/* Header Banner */}
            <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-black to-slate-900 p-8 shadow-2xl">
                <div className="absolute top-0 right-0 p-8 opacity-10">
                    <GraduationCap className="w-64 h-64 text-primary" />
                </div>

                <div className="relative z-10 max-w-2xl">
                    <div className="flex items-center gap-3 mb-4">
                        <span className="px-3 py-1 rounded-full bg-primary/20 text-primary text-xs font-bold uppercase tracking-widest border border-primary/20">
                            New
                        </span>
                        <span className="text-white/40 text-xs font-mono uppercase tracking-widest">v1.0.0</span>
                    </div>

                    <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-4 text-transparent bg-clip-text bg-gradient-to-r from-white to-white/50">
                        {lang === 'pt' ? 'Inspetor Academy' : 'Inspector Academy'}
                    </h1>

                    <p className="text-lg text-muted-foreground leading-relaxed mb-8">
                        {lang === 'pt'
                            ? 'A "Bíblia do Trader Moderno". Um curso completo de 7 módulos cobrindo do zero ao institucional, integrando Teoria de Dow, SMC e IA.'
                            : 'The "Modern Trader Bible". A complete 7-module course covering from zero to institutional level, integrating Dow Theory, SMC, and AI.'}
                    </p>

                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setLang(lang === 'pt' ? 'en' : 'pt')}
                            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                        >
                            <Globe className="w-4 h-4 text-primary" />
                            <span className="text-sm font-semibold">{lang === 'pt' ? 'English' : 'Português'}</span>
                        </button>
                        <a
                            href={`${REPO_URL}/${lang}/README.md`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 px-6 py-2 rounded-xl bg-primary text-black font-bold hover:opacity-90 transition-opacity"
                        >
                            {lang === 'pt' ? 'Ler Introdução' : 'Read Introduction'}
                            <ArrowRight className="w-4 h-4" />
                        </a>
                    </div>
                </div>
            </div>

            {/* Grid of Chapters */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {CHAPTERS.map((chapter) => (
                    <a
                        key={chapter.id}
                        href={`${REPO_URL}/${lang}/${lang === 'pt' ? chapter.file_pt : chapter.file_en}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block h-full"
                    >
                        <GlassCard className="h-full flex flex-col justify-between hover:scale-[1.02] transition-transform cursor-pointer">
                            <div>
                                <div className="flex items-start justify-between mb-6">
                                    <div className={cn("p-3 rounded-2xl bg-white/5 border border-white/5", chapter.color)}>
                                        <chapter.icon className="w-6 h-6" />
                                    </div>
                                    <span className="text-[10px] font-bold text-white/20 uppercase tracking-[0.2em]">
                                        {lang === 'pt' ? `Capítulo 0${chapter.id}` : `Chapter 0${chapter.id}`}
                                    </span>
                                </div>

                                <h3 className="text-xl font-bold mb-3 leading-tight group-hover:text-primary transition-colors">
                                    {lang === 'pt' ? chapter.title_pt : chapter.title_en}
                                </h3>

                                <p className="text-sm text-muted-foreground leading-relaxed">
                                    {lang === 'pt' ? chapter.desc_pt : chapter.desc_en}
                                </p>
                            </div>

                            <div className="mt-8 pt-6 border-t border-white/5 flex items-center justify-between">
                                <span className="text-xs font-mono text-white/30 group-hover:text-white/60 transition-colors">
                                    Read.md
                                </span>
                                <ArrowRight className="w-4 h-4 text-white/30 -translate-x-2 opacity-0 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                            </div>
                        </GlassCard>
                    </a>
                ))}
            </div>

        </div>
    );
}
