'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, AlertTriangle } from 'lucide-react';

interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
}

const COMMAND_PATTERNS = [
    /\b(buy|sell|long|short|open|close|cancel|execute)\b/i,
    /\b(comprar|vender|abrir|fechar|cancelar|executar)\b/i,
    /\b(trade|order|position)\s+(open|close|cancel)/i,
    /\b(close\s+all|fechar\s+tudo|reverter)\b/i
];

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export function AiChat() {
    const [messages, setMessages] = useState<Message[]>([
        {
            id: '1',
            role: 'assistant',
            content: 'Olá! Sou o assistente de leitura do Engine V0. Posso responder perguntas sobre posições, performance, e estratégia. **Nota: Este chat é apenas para consultas. Comandos de trading devem ser enviados pelo Telegram.**',
            timestamp: new Date()
        }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const isCommand = (text: string): boolean => {
        return COMMAND_PATTERNS.some(pattern => pattern.test(text));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMessage = input.trim();
        setInput('');
        setError(null);

        // Check for commands (CLIENT-SIDE BLOCKING)
        if (isCommand(userMessage)) {
            setError('⚠️ Comandos de trading são permitidos somente no Telegram.');
            return;
        }

        // Add user message
        const newUserMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: userMessage,
            timestamp: new Date()
        };
        setMessages(prev => [...prev, newUserMessage]);
        setLoading(true);

        try {
            const res = await fetch(`${API_BASE}/api/ai/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: userMessage })
            });

            const json = await res.json();

            if (!res.ok) {
                throw new Error(json.error || 'Failed to get response');
            }

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: json.answer || json.response || 'Sem resposta disponível.',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, assistantMessage]);
        } catch (err: any) {
            setError(err.message || 'Erro ao consultar AI');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card h-[600px] flex flex-col">
            <div className="card-header border-b border-[var(--border)] pb-4">
                <div className="flex items-center gap-2">
                    <Bot className="w-5 h-5 text-[var(--accent-cyan)]" />
                    <span className="font-semibold">AI Chat</span>
                    <span className="badge badge-cyan text-[10px]">READ-ONLY</span>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        {msg.role === 'assistant' && (
                            <div className="w-8 h-8 rounded-full bg-[var(--accent-cyan-bg)] flex items-center justify-center flex-shrink-0">
                                <Bot className="w-4 h-4 text-[var(--accent-cyan)]" />
                            </div>
                        )}
                        <div
                            className={`max-w-[80%] p-3 rounded-xl ${msg.role === 'user'
                                    ? 'bg-[var(--accent-cyan)] text-[var(--bg-primary)]'
                                    : 'bg-[var(--bg-primary)]'
                                }`}
                        >
                            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                            <p className={`text-[10px] mt-1 ${msg.role === 'user' ? 'text-[var(--bg-secondary)]' : 'text-[var(--text-muted)]'
                                }`}>
                                {msg.timestamp.toLocaleTimeString()}
                            </p>
                        </div>
                        {msg.role === 'user' && (
                            <div className="w-8 h-8 rounded-full bg-[var(--accent-green-bg)] flex items-center justify-center flex-shrink-0">
                                <User className="w-4 h-4 text-[var(--accent-green)]" />
                            </div>
                        )}
                    </div>
                ))}
                {loading && (
                    <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-full bg-[var(--accent-cyan-bg)] flex items-center justify-center">
                            <div className="spinner" />
                        </div>
                        <div className="bg-[var(--bg-primary)] p-3 rounded-xl">
                            <p className="text-sm text-[var(--text-muted)]">Pensando...</p>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Error Banner */}
            {error && (
                <div className="mx-4 mb-2 p-3 rounded-lg bg-[var(--accent-red-bg)] flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-[var(--loss)]" />
                    <span className="text-sm text-[var(--loss)]">{error}</span>
                </div>
            )}

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-4 border-t border-[var(--border)]">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Faça uma pergunta sobre o bot..."
                        className="flex-1 bg-[var(--bg-primary)] border border-[var(--border)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-cyan)]"
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        disabled={loading || !input.trim()}
                        className="p-3 rounded-xl bg-[var(--accent-cyan)] text-[var(--bg-primary)] hover:opacity-90 disabled:opacity-50 transition-opacity"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
                <p className="text-[10px] text-[var(--text-muted)] mt-2 text-center">
                    📖 Este chat é apenas para perguntas. Comandos devem ser enviados pelo Telegram.
                </p>
            </form>
        </div>
    );
}
