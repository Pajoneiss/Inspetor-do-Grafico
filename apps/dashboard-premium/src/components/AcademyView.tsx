"use client";

import React, { useState } from 'react';
import { Book, GraduationCap, ArrowRight, Globe, Lock, Brain, TrendingUp, Activity, Heart, Shield, AlertTriangle, Flag } from 'lucide-react';
import { cn } from '@/lib/utils';


const GlassCard = ({ children, className }: { children: React.ReactNode; className?: string }) => (
    <div className={cn(
        "relative overflow-hidden rounded-xl border border-white/10 bg-black/40 backdrop-blur-md shadow-xl",
        className
    )}>
        <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
        {children}
    </div>
);

const CHAPTERS = [
    {
        id: 0,
        title_pt: "A Verdade Brutal",
        title_en: "The Brutal Truth",
        desc_pt: "Leia antes de começar. O filtro dos fracos.",
        desc_en: "Read before starting. The filter for the weak.",
        icon: AlertTriangle,
        file_pt: "00_PREFACIO_A_VERDADE.md",
        file_en: "00_THE_BRUTAL_TRUTH.md",
        color: "text-red-500"
    },
    {
        id: 1,
        title_pt: "Fundamentos Clássicos",
        title_en: "Classical Fundamentals",
        desc_pt: "Dow, Elliott e Wyckoff: A base de tudo.",
        desc_en: "Dow, Elliott and Wyckoff: The foundation.",
        icon: Book,
        file_pt: "01_FUNDAMENTOS_CLASSICOS.md",
        file_en: "01_CLASSICAL_FUNDAMENTALS.md",
        color: "text-blue-400"
    },
    {
        id: 2,
        title_pt: "Price Action Avançado",
        title_en: "Advanced Price Action",
        desc_pt: "Candles, Padrões e a psicologia do pavio.",
        desc_en: "Candles, Patterns and wick psychology.",
        icon: Activity,
        file_pt: "02_PRICE_ACTION_AVANCADO.md",
        file_en: "02_ADVANCED_PRICE_ACTION.md",
        color: "text-green-400"
    },
    {
        id: 3,
        title_pt: "Smart Money Concepts",
        title_en: "Smart Money Concepts",
        desc_pt: "Rastreando os Grandes Players (SMC).",
        desc_en: "Tracking Big Players (SMC).",
        icon: Lock,
        file_pt: "03_SMART_MONEY_CONCEPTS.md",
        file_en: "03_SMART_MONEY_CONCEPTS.md",
        color: "text-purple-400"
    },
    {
        id: 4,
        title_pt: "Ferramentas Matemáticas",
        title_en: "Mathematical Tools",
        desc_pt: "Fibonacci, Médias e Indicadores Reais.",
        desc_en: "Fibonacci, Averages and Real Indicators.",
        icon: TrendingUp,
        file_pt: "04_FERRAMENTAS_MATEMATICAS.md",
        file_en: "04_MATHEMATICAL_TOOLS.md",
        color: "text-yellow-400"
    },
    {
        id: 5,
        title_pt: "Psicologia & Risco",
        title_en: "Psychology & Risk",
        desc_pt: "Como não quebrar a banca e a mente.",
        desc_en: "How not to blow your account and mind.",
        icon: Brain,
        file_pt: "05_GESTAO_RISCO_PSICOLOGIA.md",
        file_en: "05_PSYCHOLOGY_RISK.md",
        color: "text-red-400"
    },
    {
        id: 6,
        title_pt: "Lifestyle & Saúde",
        title_en: "Lifestyle & Health",
        desc_pt: "O corpo do trader de alta performance.",
        desc_en: "The high performance trader's body.",
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
        title_pt: "O Mapa dos Ativos",
        title_en: "The Asset Map",
        desc_pt: "Ações, FIIs, Derivativos e Perfis de Risco.",
        desc_en: "Stocks, REITs, Derivatives and Risk Profiles.",
        icon: GraduationCap,
        file_pt: "08_MODALIDADES_ESTILOS.md",
        file_en: "08_MODALITIES_STYLES.md",
        color: "text-indigo-400"
    },
    {
        id: 9,
        title_pt: "Tecnologia Cripto & Segurança",
        title_en: "Crypto Tech & Security",
        desc_pt: "Blockchain, Layers, Tokenomics e Defesa.",
        desc_en: "Blockchain, Layers, Tokenomics and Defense.",
        icon: Shield,
        file_pt: "09_ECOSSISTEMA_CRIPTO_SEGURANCA.md",
        file_en: "09_CRYPTO_ECOSYSTEM_SECURITY.md",
        color: "text-orange-400"
    },
    {
        id: 10,
        title_pt: "Macroeconomia & Fundamentos",
        title_en: "Macro & Fundamentals",
        desc_pt: "Juros, Inflação e Ciclos Econômicos.",
        desc_en: "Rates, Inflation and Economic Cycles.",
        icon: Globe,
        file_pt: "10_ANALISE_FUNDAMENTALISTA_MACRO.md",
        file_en: "10_FUNDAMENTAL_ANALYSIS_MACRO.md",
        color: "text-emerald-400"
    },
    {
        id: 11,
        title_pt: "História dos Crashes",
        title_en: "History of Crashes",
        desc_pt: "Tulipas, 1929, 2008 e Lendas do Mercado.",
        desc_en: "Tulips, 1929, 2008 and Market Legends.",
        icon: Activity,
        file_pt: "11_HISTORIA_CRASHES.md",
        file_en: "11_HISTORY_CRASHES.md",
        color: "text-rose-400"
    },
    {
        id: 12,
        title_pt: "O Mapa Final",
        title_en: "The Final Map",
        desc_pt: "A conexão total. O sistema unificado.",
        desc_en: "The total connection. The unified system.",
        icon: Activity,
        file_pt: "12_MAPA_FINAL.md",
        file_en: "12_THE_FINAL_MAP.md",
        color: "text-rose-400"
    },
    {
        id: 13,
        title_pt: "O Legado Final",
        title_en: "The Final Legacy",
        desc_pt: "O manifesto. Pensar em décadas.",
        desc_en: "The manifesto. Thinking in decades.",
        icon: Flag,
        file_pt: "13_LEGADO_FINAL.md",
        file_en: "13_FINAL_LEGACY.md",
        color: "text-gold-400"
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
