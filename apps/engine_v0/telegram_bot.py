"""
Telegram Bot Module for Hyperliquid AI Bot
v11.0 MVP - 3 buttons + chat + summary
"""
import os
import asyncio
import threading
from datetime import datetime
from typing import Optional, Dict, Any, List

# Feature flag
from config import (
    ENABLE_TELEGRAM,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_ADMIN_IDS,
    TG_CHAT_MODEL,
    AI_TEMPERATURE
)

# Runtime state (shared with engine)
_bot_state = {
    "ai_enabled": True,
    "last_summary": None,
    "last_scan": None,
    "chat_mode": False
}


def get_bot_state() -> Dict[str, Any]:
    """Get current bot state for telegram display"""
    return _bot_state


def update_bot_state(key: str, value: Any):
    """Update bot state from engine"""
    _bot_state[key] = value


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return str(user_id) in TELEGRAM_ADMIN_IDS or not TELEGRAM_ADMIN_IDS[0]  # Allow all if not configured


def escape_md(text: str) -> str:
    """Escape markdown v1 special chars"""
    return str(text).replace("_", "\\_").replace("*", "\\*").replace("`", "\\`").replace("[", "\\[")


def get_test_trade_request() -> Optional[Dict[str, Any]]:
    """Get pending test trade request from Telegram"""
    return _bot_state.get("test_trade_request")


def clear_test_trade_request():
    """Clear test trade request after processing"""
    if "test_trade_request" in _bot_state:
        del _bot_state["test_trade_request"]


def send_test_trade_result(chat_id: int, result_text: str):
    """Send test trade result back to Telegram user"""
    _bot_state["test_trade_result"] = {
        "chat_id": chat_id,
        "text": result_text
    }


class TelegramBot:
    """Simple Telegram bot with 3 main buttons"""
    
    def __init__(self):
        self.running = False
        self.bot = None
        self._thread = None
        
    def start(self):
        """Start bot in background thread"""
        # SINGLE-START GUARD: prevent multiple starts
        if self.running or (self._thread and self._thread.is_alive()):
            print("[TG][WARN] Bot already running, skipping start")
            return
            
        if not ENABLE_TELEGRAM or not TELEGRAM_BOT_TOKEN:
            print("[TG] Telegram disabled or no token")
            return
            
        try:
            from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
            from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
            
            self._thread = threading.Thread(target=self._run_bot, daemon=True)
            self._thread.start()
            print("[TG] Telegram bot starting in background")
        except ImportError as e:
            print(f"[TG][WARN] python-telegram-bot not installed: {e}")
            print("[TG][WARN] Install with: pip install python-telegram-bot")
    
    def _run_bot(self):
        """Run bot event loop"""
        try:
            asyncio.run(self._async_main())
        except Exception as e:
            print(f"[TG][ERROR] Bot crashed: {e}")
    
    async def _async_main(self):
        """Async main for telegram bot with conflict retry"""
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
        import telegram.error
        
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Store app reference for sending messages
        self.app = app
        
        # Register handlers
        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("status", self._cmd_status))
        app.add_handler(CommandHandler("chat", self.chat_handler))
        app.add_handler(CommandHandler("ajuda", self.ajuda_handler))
        app.add_handler(CommandHandler("help", self.ajuda_handler))
        app.add_handler(CommandHandler("test_trade", self._cmd_test_trade))
        app.add_handler(CommandHandler("test", self._cmd_test_trade))
        app.add_handler(CommandHandler("force_trade", self._cmd_test_trade))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        self.running = True
        print("[TG] Bot running")
        
        await app.initialize()
        await app.start()
        
        # Retry loop with exponential backoff for Conflict errors
        retry_delay = 30  # Start with 30s
        max_retry_delay = 300  # Max 5 minutes
        
        while self.running:
            try:
                # KICK STALE SESSIONS: Clear any existing webhook/polling
                try:
                    await app.bot.delete_webhook(drop_pending_updates=True)
                except Exception as e:
                    print(f"[TG][WARN] Clear webhook failed: {e}")
                
                await app.updater.start_polling(drop_pending_updates=True)
                
                # Keep running - reset retry delay on success
                retry_delay = 30
                while self.running:
                    await asyncio.sleep(1)
                    
                    # Check for pending test trade results to send
                    if "test_trade_result" in _bot_state:
                        result = _bot_state["test_trade_result"]
                        try:
                            await app.bot.send_message(
                                chat_id=result["chat_id"],
                                text=result["text"],
                                parse_mode="Markdown"
                            )
                            del _bot_state["test_trade_result"]
                        except Exception as e:
                            print(f"[TG][ERROR] Failed to send test trade result: {e}")
                            del _bot_state["test_trade_result"]  # Clear anyway to avoid spam
                    
            except telegram.error.Conflict as e:
                print(f"[TG][WARN] Conflict error (another instance running?), retrying in {retry_delay}s")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)  # Exponential backoff
                continue
            except Exception as e:
                print(f"[TG][ERROR] Polling error: {e}, retrying in {retry_delay}s")
                await asyncio.sleep(retry_delay)
                continue
        
        await app.stop()
    
    async def _cmd_start(self, update, context):
        """Handle /start command - show persistent keyboard with 4 buttons"""
        from telegram import ReplyKeyboardMarkup
        
        # Check current AI state
        ai_status = "✅ LIGADO" if _bot_state['ai_enabled'] else "❌ DESLIGADO"
        
        # 4 buttons as user requested
        reply_keyboard = [
            [f"🤖 IA: {ai_status}"],
            ["📰 Notícias + Calendário"],
            ["💬 Chat com IA"],
            ["📊 Resumo Completo"]
        ]
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, 
            resize_keyboard=True,
            is_persistent=True
        )
        
        await update.message.reply_text(
            "🚀 *Bot Hyperliquid*\n\n"
            f"🤖 IA: {ai_status}\n\n"
            "Use os botões abaixo:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def _cmd_status(self, update, context):
        """Handle /status command"""
        state = _bot_state.get("last_summary", {})
        
        text = (
            "📊 *Status Atual*\n\n"
            f"💰 Equity: ${state.get('equity', 0):.2f}\n"
            f"📈 Buying Power: ${state.get('buying_power', 0):.0f}\n"
            f"🔢 Posições: {state.get('positions_count', 0)}\n"
            f"🤖 IA: {'✅ ON' if _bot_state['ai_enabled'] else '❌ OFF'}\n"
        )
        
        # Add scan info
        scan = _bot_state.get("last_scan", [])
        if scan:
            text += "\n*Top 5 Score:*\n"
            for s in scan[:5]:
                text += f"  {s['symbol']}: {s['score']} ({s.get('reason', '')})\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    
    async def _cmd_panic(self, update, context):
        """Handle /panic command - emergency close all"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Acesso negado")
            return
        
        keyboard = [[
            InlineKeyboardButton("✅ CONFIRMAR PANIC", callback_data="confirm_panic"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancel")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⚠️ *PANIC MODE*\n\n"
            "Isso vai:\n"
            "1. Desligar a IA\n"
            "2. Fechar TODAS as posições\n\n"
            "Tem certeza?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def _cmd_test_trade(self, update, context):
        """
        Handle /test_trade command - Force AI to analyze and execute test trades
        
        Usage:
        • /test_trade - Analyze all monitored symbols
        • /test_trade BTC ETH SOL - Analyze specific symbols
        • /test_trade 3 - Analyze top 3 symbols by score
        """
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ Apenas admins podem executar test trades")
            return
        
        # Parse command arguments
        args = context.args if context.args else []
        
        # Build symbols list from state (populated by main.py from config.SYMBOL)
        state = _bot_state.get("last_summary", {})
        all_symbols = state.get("symbols", [])
        
        # Safety check: ensure we have symbols configured
        if not all_symbols and not args:
            await update.message.reply_text(
                "❌ Nenhum símbolo configurado no bot.\n"
                "Configure SYMBOL no ambiente ou especifique símbolos: /test_trade BTC ETH",
                parse_mode=None
            )
            return
        
        if not args:
            # No args - use all symbols
            symbols = all_symbols
            mode_desc = f"todos os {len(symbols)} símbolos"
        elif len(args) == 1 and args[0].isdigit():
            # Top N symbols by score
            n = int(args[0])
            scan = _bot_state.get("last_scan", [])
            if scan:
                symbols = [s["symbol"] for s in scan[:n]]
            else:
                symbols = all_symbols[:n] if all_symbols else []
            mode_desc = f"top {n} símbolos"
        else:
            # Specific symbols
            symbols = [s.upper() for s in args]
            mode_desc = f"símbolos específicos: {', '.join(symbols)}"
        
        # Final safety check
        if not symbols:
            await update.message.reply_text(
                "❌ Nenhum símbolo para analisar.\n"
                "Especifique símbolos: /test_trade BTC ETH SOL",
                parse_mode=None
            )
            return
        
        await update.message.reply_text(
            f"🧪 *TEST TRADE INICIADO*\\n\\n"
            f"Modo: {mode_desc}\\n"
            f"Símbolos: {len(symbols)}\\n\\n"
            "⏳ Analisando mercado e executando decisões da IA...\\n\\n"
            "⚠️ Este comando bypassa cooldowns normais",
            parse_mode="Markdown"
        )
        
        # Queue test trade request for main loop
        _bot_state["test_trade_request"] = {
            "symbols": symbols,
            "chat_id": update.effective_chat.id,
            "user_id": update.effective_user.id,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"[TG][TEST_TRADE] Queued test trade for {len(symbols)} symbols by user {update.effective_user.id}")
    
    async def _handle_callback(self, update, context):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "toggle_ai":
            _bot_state["ai_enabled"] = not _bot_state["ai_enabled"]
            status = "✅ ON" if _bot_state["ai_enabled"] else "❌ OFF"
            await query.edit_message_text(f"🤖 IA agora está: {status}")
            print(f"[TG] AI toggled to {_bot_state['ai_enabled']}")
            
        elif data == "chat_mode":
            _bot_state["chat_mode"] = True
            await query.edit_message_text(
                "💬 *Modo Chat Ativado*\n\n"
                "Você pode:\n"
                "• Perguntar qualquer coisa sobre o mercado\n"
                "• Comandar: 'abrir long em BTC', 'fechar todas'\n\n"
                "Digite sua mensagem:",
                parse_mode="Markdown"
            )
            
        elif data == "full_summary":
            await self._send_full_summary(query)
            
        elif data == "confirm_panic":
            if is_admin(update.effective_user.id):
                _bot_state["ai_enabled"] = False
                _bot_state["panic_close_all"] = True
                await query.edit_message_text("🚨 PANIC ATIVADO - IA OFF + Fechando posições...")
                print("[TG][PANIC] Panic mode activated by user")
            
        elif data == "cancel":
            await query.edit_message_text("❌ Cancelado")

    async def _send_full_summary(self, query):
        """Send full summary with all info including external data"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        state = _bot_state.get("last_summary", {})
        scan = _bot_state.get("last_scan", [])
        
        text = "📊 *RESUMO COMPLETO*\n\n"
        
        # Account with buying power bar
        equity = state.get('equity', 0)
        buying_power = state.get('buying_power', 0)
        text += "💰 *CONTA*\n"
        text += f"├ Equity: `${equity:.2f}`\n"
        text += f"├ Buying Power: `${buying_power:.0f}`\n"
        text += f"└ IA: {'✅ LIGADO' if _bot_state['ai_enabled'] else '❌ DESLIGADO'}\n\n"
        
        # Positions with prices and PnL%
        positions = state.get("positions", {})
        if positions:
            text += "📊 *POSIÇÕES*\n"
            for sym, pos in positions.items():
                pnl = pos.get("unrealized_pnl", 0)
                entry = pos.get("entry_price", 0)
                size = pos.get("size", 0)
                side = pos.get('side', '?')
                side_emoji = "🟢" if side == "LONG" else "🔴" if side == "SHORT" else "⚪"
                
                # Calculate PnL %
                pnl_pct = (pnl / (abs(size) * entry * 100)) if entry and size else 0
                pnl_emoji = "📈" if pnl > 0 else "📉" if pnl < 0 else "➖"
                
                safe_sym = escape_md(sym)
                text += f"├ {safe_sym}: {side_emoji} {side} | {pnl_emoji} `${pnl:.2f}` ({pnl_pct:+.2f}%)\n"
        else:
            text += "📊 *POSIÇÕES*\n└ Nenhuma posição aberta\n"
        
        # Triggers with better formatting
        triggers = state.get('trigger_status', '')
        if triggers and triggers != 'N/A':
            text += f"\n🎯 *TRIGGERS*\n{escape_md(triggers)}\n"
        
        # Scan info with visibility
        scan_info = _bot_state.get("scan_info", {})
        scanned = scan_info.get("scanned", 0)
        total = scan_info.get("total", 0)
        symbols_list = scan_info.get("symbols", [])
        if scanned and total:
            text += f"\n🔍 *Scan:* {scanned}/{total} symbols\n"
        
        # MARKET SUMMARY
        try:
            from market_data_fetcher import get_market_data, generate_daily_summary
            macro = get_market_data()
            market_summary = generate_daily_summary()
            
            text += "\n📰 *MERCADO HOJE*\n"
            for line in market_summary.split('\n'):
                text += f"{escape_md(line)}\n"
            
            # Add indices
            sp500 = macro.get("sp500", 0)
            nasdaq = macro.get("nasdaq", 0)
            usd_brl = macro.get("usd_brl", 0)
            
            if sp500 > 0 or nasdaq > 0 or usd_brl > 0:
                text += "\n📊 *Índices:*\n"
                if sp500 > 0:
                    text += f"├ S&P500: `{sp500:.0f}`\n"
                if nasdaq > 0:
                    text += f"├ NASDAQ: `{nasdaq:.0f}`\n"
                if usd_brl > 0:
                    text += f"└ USD/BRL: `R$ {usd_brl:.2f}`\n"
        except Exception as e:
            print(f"[TELEGRAM] Market summary error: {e}")
        
        # Top 5 Score
        if scan:
            text += "\n📡 *Top 5 Score:*\n"
            for s in scan[:5]:
                sym = escape_md(s['symbol'])
                score = s['score']
                trend = escape_md(s.get('trend', '?'))
                reason = escape_md(s.get('reason', ''))
                text += f"  {sym}: {score} | {trend} | {reason}\n"
            
            # Show holding score vs top1 if holding
            holding = state.get("holding_symbol")
            if holding and scan:
                top1 = scan[0]
                holding_score = next((s['score'] for s in scan if s['symbol'] == holding), "?")
                if top1['symbol'] != holding:
                    text += f"\n⚖️ *Holding vs Top1:* {holding}={holding_score} vs {top1['symbol']}={top1['score']}\n"
        
        # PnL Windows (with timeout protection)
        try:
            from pnl_tracker import get_pnl_windows, format_pnl_windows_for_telegram
            
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                pnl_data = await loop.run_in_executor(pool, get_pnl_windows)
            
            pnl_text = format_pnl_windows_for_telegram(pnl_data)
            if pnl_text:
                text += f"\n{escape_md(pnl_text)}\n"
        except Exception as e:
            print(f"[TG][WARN] PnL windows fetch failed: {e}")
        
        # External data (with timeout protection)
        try:
            from data_sources import get_all_external_data, format_external_data_for_telegram
            
            # Run in thread to not block
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                external_data = await loop.run_in_executor(pool, get_all_external_data)
            
            external_text = format_external_data_for_telegram(external_data)
            if external_text and external_text != "(dados externos indisponíveis)":
                text += f"\n{escape_md(external_text)}\n"
        except Exception as e:
            print(f"[TG][WARN] External data fetch failed: {e}")
        
        # Truncate if too long
        if len(text) > 4000:
            text = text[:4000] + "..."
        
        try:
            await query.edit_message_text(text, parse_mode="Markdown")
        except Exception as e:
            print(f"[TG][ERROR] Failed to edit message: {e}")
            # Fallback to plain text if markdown fails
            await query.edit_message_text(text.replace("*", "").replace("_", "").replace("`", ""), parse_mode=None)
    
    async def _handle_message(self, update, context):
        """Handle free text messages (keyboard buttons and chat mode)"""
        user_text = update.message.text
        user_text_lower = user_text.lower()
        user_id = update.effective_user.id
        
        # Handle 4 keyboard buttons
        
        # 1. IA Toggle button
        if "🤖 ia:" in user_text_lower or "ligar" in user_text_lower or "desligar" in user_text_lower:
            _bot_state["ai_enabled"] = not _bot_state.get("ai_enabled", True)
            new_status = "✅ LIGADO" if _bot_state["ai_enabled"] else "❌ DESLIGADO"
            
            # Update keyboard with new status
            from telegram import ReplyKeyboardMarkup
            reply_keyboard = [
                [f"🤖 IA: {new_status}"],
                ["📰 Notícias + Calendário"],
                ["💬 Chat com IA"],
                ["📊 Resumo Completo"]
            ]
            reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, is_persistent=True)
            
            await update.message.reply_text(
                f"🤖 IA agora está: *{new_status}*",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            print(f"[TG] AI toggled to: {new_status}")
            return
        
        # 2. Notícias + Calendário combined
        if "notícias + calendário" in user_text_lower or "noticias" in user_text_lower or "calendário" in user_text_lower:
            await self._send_news_and_calendar(update)
            return
        
        # 3. Chat com IA
        if "💬 chat" in user_text_lower or "chat com ia" in user_text_lower:
            _bot_state["chat_mode"] = True
            await update.message.reply_text(
                "💬 *Modo Chat Ativado*\n\n"
                "Pergunte qualquer coisa:\n"
                "• 'Como está o mercado?'\n"
                "• 'O que você pretende fazer?'\n"
                "• 'Qual sua visão sobre BTC?'\n\n"
                "Digite 'sair' para desativar.",
                parse_mode="Markdown"
            )
            return
        
        # 4. Resumo Completo (includes Status + Scan + Positions)
        if "📊 resumo" in user_text_lower or "resumo completo" in user_text_lower:
            await self._send_full_summary_text(update)
            return
        
        # Exit chat mode
        if user_text_lower == "sair" and _bot_state.get("chat_mode"):
            _bot_state["chat_mode"] = False
            await update.message.reply_text("💬 Chat desativado")
            return
        
        # If not in chat mode and not a button, ignore
        if not _bot_state.get("chat_mode"):
            return
        
        # Rest of chat handling...
        
        # Log incoming chat message
        print(f"[TG][CHAT] user={user_id} text={user_text[:50]}...")
        
        # Intent classification
        intent = self._classify_intent(user_text)
        print(f"[TG][CHAT] intent={intent}")
        
        if intent == "TRADE_COMMAND":
            # Admin check for trade commands
            if not is_admin(user_id):
                await update.message.reply_text("❌ Apenas admins podem executar trades via chat")
                return
            
            # Parse trade command
            action = self._parse_trade_command(user_text)
            if action:
                # Queue for execution (will be picked up by main loop)
                _bot_state["pending_chat_actions"] = _bot_state.get("pending_chat_actions", [])
                _bot_state["pending_chat_actions"].append(action)
                
                await update.message.reply_text(
                    f"🎯 Comando detectado: {action.get('type', 'UNKNOWN')} {action.get('symbol', '')}\n"
                    f"📊 Lado: {action.get('side', '?')}\n"
                    "⏳ Enviado para execução..."
                )
                print(f"[TG][CHAT] actions={action}")
            else:
                await update.message.reply_text("❓ Não entendi o comando. Exemplos:\n• 'abrir long em BTC'\n• 'abrir short em ETH'")
            
        elif intent == "RISK_COMMAND":
            # Admin check for risk commands
            if not is_admin(user_id):
                await update.message.reply_text("❌ Apenas admins podem executar comandos de risco")
                return
            
            # Ask for confirmation with inline keyboard
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = [[
                InlineKeyboardButton("✅ CONFIRMAR", callback_data="confirm_risk_cmd"),
                InlineKeyboardButton("❌ Cancelar", callback_data="cancel")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            _bot_state["pending_risk_cmd"] = user_text
            
            await update.message.reply_text(
                f"⚠️ *Comando de Risco*\n\n"
                f"Você pediu: {user_text}\n\n"
                "Confirma a execução?",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
        elif intent == "QUESTION":
            # Actually call the LLM to answer the question
            try:
                from openai import OpenAI
                import os
                
                api_key = os.environ.get("OPENAI_API_KEY", "")
                if not api_key:
                    await update.message.reply_text("❌ API key não configurada")
                    return
                
                client = OpenAI(api_key=api_key)
                
                # Build context for the question
                state = _bot_state.get("last_summary", {})
                scan = _bot_state.get("last_scan", [])
                positions = state.get("positions", {})
                
                # Build position details
                pos_details = ""
                for sym, pos in positions.items():
                    pos_details += f"  - {sym}: {pos.get('side')} ${pos.get('size', 0)} | PnL ${pos.get('unrealized_pnl', 0):.2f}\n"
                if not pos_details:
                    pos_details = "  Nenhuma posição aberta\n"
                
                context = f"""EU SOU o trading bot. Estou operando agora. Responda na PRIMEIRA PESSOA.

MINHA SITUAÇÃO ATUAL:
- Minha equity: ${state.get('equity', 0):.2f}
- Buying power: ${state.get('buying_power', 0):.0f}

MINHAS POSIÇÕES AGORA:
{pos_details}
MEU SCAN DE MERCADO:
Top 5: {', '.join([f"{s['symbol']}:{s['score']}" for s in scan[:5]])}

O usuário perguntou: {user_text}

Responda como se VOCÊ fosse o bot operando. Diga "Eu estou...", "Minha posição...", "Pretendo...". Seja direto e assertivo."""
                
                await update.message.reply_text("💭 Pensando...")
                
                response = client.chat.completions.create(
                    model=TG_CHAT_MODEL,
                    messages=[
                        {"role": "system", "content": "Você É o trading bot. Responda em PRIMEIRA PESSOA. Diga 'Eu tenho', 'Eu pretendo', 'Minha estratégia'. Seja direto e assertivo, sem rodeios. Max 2 parágrafos."},
                        {"role": "user", "content": context}
                    ],
                    max_tokens=300,
                    temperature=AI_TEMPERATURE
                )
                
                ai_response = response.choices[0].message.content.strip()
                await update.message.reply_text(f"🤖 {ai_response}")
                print(f"[TG][CHAT] AI answered question: {user_text[:50]}...")
                
            except Exception as e:
                print(f"[TG][CHAT][ERROR] {e}")
                await update.message.reply_text(f"❌ Erro ao responder: {str(e)[:100]}")
        
        else:
            # Unknown intent
            await update.message.reply_text(
                "🤖 Recebi sua mensagem.\n\n"
                "Comandos suportados:\n"
                "• 'abrir long em BTC'\n"
                "• 'abrir short em ETH'\n"
                "• 'fechar todas'\n"
                "• /status\n"
                "• /panic"
            )
    
    def _classify_intent(self, text: str) -> str:
        """Classify user intent from message text"""
        text = text.lower()
        
        # Check for symbols first
        symbols = ["btc", "eth", "sol", "doge", "xrp", "ada", "link", "arb", "hype", "bnb", "icp"]
        has_symbol = any(sym in text for sym in symbols)
        
        # Trade commands: require BOTH trade keyword AND symbol
        trade_keywords = ["abrir", "comprar", "vender", "buy", "sell", "long", "short"]
        has_trade_keyword = any(kw in text for kw in trade_keywords)
        
        # Only classify as TRADE_COMMAND if has both keyword AND symbol
        if has_trade_keyword and has_symbol:
            return "TRADE_COMMAND"
        
        # Risk commands
        risk_keywords = ["fechar tudo", "fechar todas", "close all", "liquidar", "panic"]
        if any(kw in text for kw in risk_keywords):
            return "RISK_COMMAND"
        
        # Everything else is a question (let AI handle it)
        return "QUESTION"
    
    def _parse_trade_command(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse trade command into action dict"""
        text = text.lower()
        
        # Determine side
        side = None
        if any(kw in text for kw in ["long", "comprar", "buy"]):
            side = "LONG"
        elif any(kw in text for kw in ["short", "vender", "sell"]):
            side = "SHORT"
        
        if not side:
            return None
        
        # Find symbol
        symbols = ["btc", "eth", "sol", "doge", "xrp", "ada", "link", "arb", "hype", "bnb"]
        symbol = None
        for s in symbols:
            if s in text:
                symbol = s.upper()
                break
        
        if not symbol:
            return None
        
        return {
            "type": "PLACE_ORDER",
            "symbol": symbol,
            "side": side,
            "source": "telegram_chat"
        }
    
    async def _send_full_summary_text(self, update):
        """Send beautiful summary with full market data + AI thoughts + positions details"""
        state = _bot_state.get("last_summary", {})
        
        text = "📊 *RESUMO COMPLETO*\n\n"
        
        # Account section
        text += "💰 *CONTA*\n"
        text += f"├ Equity: ${state.get('equity', 0):.2f}\n"
        text += f"├ Buying Power: ${state.get('buying_power', 0):.0f}\n"
        text += f"└ IA: {'✅ LIGADO' if _bot_state['ai_enabled'] else '❌ DESLIGADO'}\n"
        
        # Positions section - ENHANCED with details
        positions = state.get("positions", {})
        if positions:
            text += "\n📈 *POSIÇÕES*\n"
            for sym, pos in positions.items():
                pnl = pos.get("unrealized_pnl", 0)
                pnl_pct = pos.get("pnl_pct", 0)
                emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                side = pos.get('side', '?')
                
                # Basic info
                text += f"\n{sym}: {side} | {emoji} ${pnl:.2f}\n"
                
                # Detailed info (safely handle missing fields)
                size = pos.get('size', 0)
                entry = pos.get('entry_price', 0)
                mark = pos.get('mark_price', 0)
                lev = pos.get('leverage', 1)
                liq = pos.get('liquidation_price', 0)
                
                if size > 0:
                    # Estimate USD value
                    usd_value = abs(size * mark) if mark > 0 else 0
                    text += f"├ 📊 Size: {abs(size):.4f} {sym} (~${usd_value:.0f})\n"
                
                if entry > 0:
                    text += f"├ 💵 Entry: ${entry:,.2f}\n"
                
                if mark > 0:
                    text += f"├ 📍 Mark: ${mark:,.2f}\n"
                
                if pnl_pct != 0:
                    text += f"├ 📈 PnL: {pnl_pct:+.2f}% (${pnl:.2f})\n"
                
                if lev > 1:
                    text += f"├ ⚡ Leverage: {lev}x\n"
                
                if liq > 0:
                    text += f"├ 💀 Liq: ${liq:,.2f}\n"
                
                # Triggers
                sl = pos.get('stop_loss', 0)
                tp = pos.get('take_profit', 0)
                if sl > 0 or tp > 0:
                    sl_str = f"${sl:,.0f}" if sl > 0 else "None"
                    tp_str = f"${tp:,.0f}" if tp > 0 else "None"
                    text += f"└ 🎯 SL={sl_str} | TP={tp_str}\n"
        else:
            text += "\n📈 *POSIÇÕES:* Nenhuma\n"
        
        # AI Last Decision - NEW
        last_ai = state.get("last_ai_decision", {})
        if last_ai and _bot_state['ai_enabled']:
            text += "\n🤖 *ÚLTIMA DECISÃO IA*\n"
            
            # Timestamp
            import datetime
            ts = last_ai.get("timestamp", "")
            if ts:
                try:
                    dt = datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    now = datetime.datetime.now(datetime.timezone.utc)
                    delta = now - dt
                    mins = int(delta.total_seconds() / 60)
                    if mins < 60:
                        time_str = f"Há {mins} min"
                    else:
                        hours = mins // 60
                        time_str = f"Há {hours}h {mins % 60}m"
                except:
                    time_str = "Recente"
            else:
                time_str = "Recente"
            
            conf = last_ai.get("confidence", 0)
            text += f"⏰ {time_str} | Conf: {conf:.2f}\n\n"
            
            # Summary (escape markdown)
            summary = last_ai.get("summary", "")
            if summary:
                # Limit to 80 chars for Telegram
                if len(summary) > 80:
                    summary = summary[:77] + "..."
                text += f"\"{escape_md(summary)}\"\n"
        
        # Performance Today - NEW
        perf = state.get("performance_today", {})
        if perf and perf.get("trades", 0) > 0:
            text += "\n📊 *PERFORMANCE (Hoje)*\n"
            trades = perf.get("trades", 0)
            win_rate = perf.get("win_rate", 0)
            pnl = perf.get("total_pnl", 0)
            best = perf.get("best_trade", 0)
            
            text += f"Trades: {trades} | Win: {win_rate:.0f}% | PnL: ${pnl:+.2f}\n"
            if best != 0:
                text += f"Best: ${best:+.2f}\n"
        
        # PNL History (24h, 7D, 30D, ALL) - NEW
        pnl_hist = state.get("pnl_history", {})
        if pnl_hist:
            text += "\n💰 *PNL HISTÓRICO*\n"
            
            pnl_24h = pnl_hist.get("24h", 0)
            pnl_7d = pnl_hist.get("7d", 0)
            pnl_30d = pnl_hist.get("30d", 0)
            pnl_all = pnl_hist.get("all", 0)
            
            # Emojis based on positive/negative
            emoji_24h = "🟢" if pnl_24h > 0 else "🔴" if pnl_24h < 0 else "⚪"
            emoji_7d = "🟢" if pnl_7d > 0 else "🔴" if pnl_7d < 0 else "⚪"
            emoji_30d = "🟢" if pnl_30d > 0 else "🔴" if pnl_30d < 0 else "⚪"
            emoji_all = "🟢" if pnl_all > 0 else "🔴" if pnl_all < 0 else "⚪"
            
            text += f"{emoji_24h} 24h: ${pnl_24h:+.2f} | {emoji_7d} 7D: ${pnl_7d:+.2f}\n"
            text += f"{emoji_30d} 30D: ${pnl_30d:+.2f} | {emoji_all} ALL: ${pnl_all:+.2f}\n"
        
        # AI Self-Assessment - NEW
        ai_assessment = state.get("ai_assessment", "")
        if ai_assessment:
            text += "\n🧠 *PENSAMENTO DA IA*\n"
            # Truncate if too long
            if len(ai_assessment) > 120:
                ai_assessment = ai_assessment[:117] + "..."
            text += f"\"{escape_md(ai_assessment)}\"\n"
        
        
        # Top Symbols - NEW
        top_syms = state.get("top_symbols", [])
        if top_syms and len(top_syms) > 0:
            text += "\n🔍 *TOP SÍMBOLOS*\n"
            for i, sym_data in enumerate(top_syms[:4], 1):
                symbol = sym_data.get("symbol", "?")
                score = sym_data.get("score", 0)
                trend = sym_data.get("trend", "")
                
                # Emoji based on trend
                if "BULL" in trend.upper():
                    emoji = "📈"
                elif "BEAR" in trend.upper():
                    emoji = "📉"
                else:
                    emoji = "⚖️"
                
                text += f"{i}. {symbol}: {score:.0f} {emoji}"
                if i < len(top_syms[:4]):
                    text += " | " if i % 2 == 1 else "\n"
            
            if len(top_syms[:4]) % 2 == 1:
                text += "\n"
        
        # Market Data (CMC style) - ENHANCED with NASDAQ/SP500
        try:
            from data_sources import get_fear_greed, fetch_coingecko_global, fetch_macro
            
            text += "\n🌍 *MERCADO GLOBAL*\n"
            
            # CoinGecko data
            market = fetch_coingecko_global()
            if market.get("market_cap") and market.get("market_cap") != "N/A":
                cap = market['market_cap']
                if isinstance(cap, (int, float)):
                    cap_t = cap / 1_000_000_000_000
                    text += f"├ 📊 Market Cap: ${cap_t:.2f}T\n"
            
            if market.get("btc_dominance") and market.get("btc_dominance") != "N/A":
                btc_d = market['btc_dominance']
                if isinstance(btc_d, float):
                    text += f"├ ₿ BTC Dom: {btc_d:.1f}%\n"
            
            if market.get("eth_dominance") and market.get("eth_dominance") != "N/A":
                eth_d = market['eth_dominance']
                if isinstance(eth_d, float):
                    text += f"├ Ξ ETH Dom: {eth_d:.1f}%\n"
            
            if market.get("market_cap_change_24h") and market.get("market_cap_change_24h") != "N/A":
                change = market['market_cap_change_24h']
                if isinstance(change, float):
                    emoji = "📈" if change > 0 else "📉"
                    text += f"├ {emoji} 24h: {change:+.1f}%\n"
            
            # Fear & Greed
            fg = get_fear_greed()
            if fg.get("value") and fg.get("value") != "N/A":
                val = fg['value']
                classification = fg.get('classification', '')
                if val <= 25:
                    fg_emoji = "😱"
                elif val <= 45:
                    fg_emoji = "😨"
                elif val <= 55:
                    fg_emoji = "😐"
                elif val <= 75:
                    fg_emoji = "😊"
                else:
                    fg_emoji = "🤑"
                text += f"├ {fg_emoji} Fear/Greed: {val} ({classification})\n"
            
            # Macro (USD/BRL + NASDAQ + SP500)
            macro = fetch_macro()
            
            # NASDAQ - NEW
            nasdaq = macro.get("nasdaq", 0)
            nasdaq_change = macro.get("nasdaq_change", 0)
            if nasdaq and nasdaq != "N/A" and isinstance(nasdaq, (int, float)):
                nasdaq_emoji = "📈" if nasdaq_change > 0 else "📉" if nasdaq_change < 0 else "➖"
                text += f"├ {nasdaq_emoji} NASDAQ: {nasdaq:,.0f} ({nasdaq_change:+.2f}%)\n"
            
            # SP500 - NEW
            sp500 = macro.get("sp500", 0)
            sp500_change = macro.get("sp500_change", 0)
            if sp500 and sp500 != "N/A" and isinstance(sp500, (int, float)):
                sp500_emoji = "📈" if sp500_change > 0 else "📉" if sp500_change < 0 else "➖"
                text += f"├ {sp500_emoji} S&P 500: {sp500:,.0f} ({sp500_change:+.2f}%)\n"
            
            # USD/BRL
            if macro.get("usd_brl") and macro.get("usd_brl") != "N/A":
                text += f"└ 💵 USD/BRL: R${macro['usd_brl']:.2f}\n"
            else:
                text += "└ 💵 Macro: Carregando...\n"
                
        except Exception as e:
            text += f"\n⚠️ Dados de mercado indisponíveis\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    async def _send_news_and_calendar(self, update):
        """Send combined news + economic calendar in Portuguese"""
        await update.message.reply_text("📰 Buscando notícias e calendário...")
        
        text = ""
        
        # Part 1: Crypto News
        try:
            from data_sources import get_cryptopanic_news
            news = get_cryptopanic_news()
            
            headlines = news.get("headlines", [])
            if headlines:
                text += "📰 *TOP NOTÍCIAS CRYPTO*\n\n"
                for i, headline in enumerate(headlines[:5], 1):
                    safe_title = escape_md(headline.get('title', '')[:70])
                    text += f"{i}. {safe_title}\n\n"
            else:
                text += "📰 *Notícias:* Indisponível\n\n"
        except Exception as e:
            text += f"📰 *Notícias:* Erro ({str(e)[:30]})\n\n"
        
        # Part 2: Economic Calendar (translated to PT)
        try:
            import httpx
            
            url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
            
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                events = resp.json()
            
            # Filter high/medium impact, translate country codes
            country_pt = {
                "USD": "🇺🇸 EUA", "EUR": "🇪🇺 Europa", "GBP": "🇬🇧 Reino Unido",
                "JPY": "🇯🇵 Japão", "CAD": "🇨🇦 Canadá", "AUD": "🇦🇺 Austrália",
                "CHF": "🇨🇭 Suíça", "CNY": "🇨🇳 China", "NZD": "🇳🇿 N.Zelândia",
                "BRL": "🇧🇷 Brasil"
            }
            
            high_impact = [e for e in events if e.get("impact", "").lower() in ["high", "medium"]][:8]
            
            if high_impact:
                text += "📅 *CALENDÁRIO ECONÔMICO*\n\n"
                for event in high_impact:
                    time_str = event.get("time", "")
                    title = escape_md(event.get("title", "")[:35])
                    country = event.get("country", "")
                    country_name = country_pt.get(country, country)
                    impact = "🔴" if event.get("impact") == "High" else "🟡"
                    
                    text += f"{impact} *{country_name}* {time_str}\n   {title}\n\n"
            else:
                text += "📅 *Calendário:* Sem eventos importantes\n"
                
        except Exception as e:
            text += f"📅 *Calendário:* Erro ({str(e)[:30]})\n"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    
    async def _send_news(self, update):
        """Legacy: redirect to combined"""
        await self._send_news_and_calendar(update)
    
    async def _send_calendar(self, update):
        """Legacy: redirect to combined"""
        await self._send_news_and_calendar(update)
    
    async def _send_scan(self, update):
        """Send current market scan"""
        scan = _bot_state.get("last_scan", [])
        
        if not scan:
            await update.message.reply_text("🔍 Scan não disponível ainda")
            return
        
        text = "🔍 *MARKET SCAN*\n\n"
        text += "📊 *Ranking por Score:*\n\n"
        
        for i, s in enumerate(scan, 1):
            score = s.get("score", 0)
            if score >= 70:
                emoji = "🟢"
            elif score >= 50:
                emoji = "🟡"
            else:
                emoji = "🔴"
            
            symbol = s.get("symbol", "?")
            trend = s.get("trend", "?")
            reason = s.get("reason", "")
            
            text += f"{emoji} *{symbol}*: {score} | {trend}\n"
            if reason:
                text += f"   _{escape_md(reason[:50])}_\n"
        
        scan_info = _bot_state.get("scan_info", {})
        text += f"\n📡 Scan: {scan_info.get('scanned', '?')}/{scan_info.get('total', '?')} symbols"
        
        await update.message.reply_text(text, parse_mode="Markdown")

    async def chat_handler(self, update, context):
        """Handler para o comando /chat"""
        # Se o usuário apenas digitou /chat sem argumentos, ativa o modo chat
        if not context.args:
            _bot_state["chat_mode"] = True
            await update.message.reply_text(
                "💬 *Modo Chat Ativado*\n\n"
                "Você agora pode conversar diretamente comigo sem usar comandos.\n"
                "Digite sua mensagem ou 'sair' para encerrar.",
                parse_mode="Markdown"
            )
        else:
            # Se forneceu argumentos, processa como uma pergunta única
            await self._handle_chat_question(update, ' '.join(context.args))

    async def ajuda_handler(self, update, context):
        """Handler para o comando /ajuda /help"""
        text = (
            "❓ *AJUDA - BOT HYPERLIQUID*\n\n"
            "*Comandos:* \n"
            "• /start - Inicia o bot e mostra menu\n"
            "• /status - Mostra equity e posições\n"
            "• /chat - Ativa modo de conversa com IA\n"
            "• /ajuda - Mostra esta mensagem\n"
            "• /panic - (Admin) Fecha tudo e desliga IA\n\n"
            "*Botões do Menu:* \n"
            "• 🤖 IA: ON/OFF - Liga/Desliga trading automático\n"
            "• 📰 Notícias - Resumo das últimas notícias\n"
            "• 📊 Resumo - Status completo do mercado\n"
            "• 💬 Chat - Conversa direta com a IA"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    async def _handle_chat_question(self, update, question):
        """Processa uma pergunta via chat usando LLM (centralizado)"""
        try:
            import openai
            import os
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                await update.message.reply_text("❌ OpenAI API key não configurada")
                return
            
            client = openai.OpenAI(api_key=api_key)
            
            # Get current state for context
            state = _bot_state.get('last_summary', {})
            equity = state.get('equity', 0)
            positions = state.get('positions', {})
            scan = _bot_state.get('last_scan', [])
            
            # Build position details strings
            pos_text = ""
            for sym, pos in positions.items():
                pos_text += f"- {sym}: {pos.get('side')} ${pos.get('size', 0)} | PnL ${pos.get('unrealized_pnl', 0):.2f}\n"
            if not pos_text: pos_text = "Nenhuma\n"

            system_prompt = f"""Você é o " Ladder Labs IA Trader", um bot profissional operando na Hyperliquid.
CONTEXTO ATUAL:
- Equity: ${equity:.2f}
- Posições: {len(positions)}
{pos_text}
- Top 5 Mercado: {', '.join([f"{s['symbol']}:{s['score']}" for s in scan[:5]])}

Responda sempre na PRIMEIRA PESSOA ("Eu", "Meu"). Seja direto, analítico e assertivo. Responda em Português."""

            await update.message.reply_text("💭 Pensando...")

            response = client.chat.completions.create(
                model=os.getenv("AI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=0.7,
                max_tokens=400
            )
            
            answer = response.choices[0].message.content.strip()
            await update.message.reply_text(f"🤖 {answer}")
            
        except Exception as e:
            print(f"[TG][CHAT][ERROR] {e}")
            await update.message.reply_text(f"❌ Erro ao processar pergunta: {str(e)[:50]}...")
    
    def stop(self):
        """Stop the bot"""
        self.running = False


# Singleton instance
_telegram_bot: Optional[TelegramBot] = None


def get_telegram_bot() -> Optional[TelegramBot]:
    """Get or create telegram bot instance"""
    global _telegram_bot
    if _telegram_bot is None and ENABLE_TELEGRAM:
        _telegram_bot = TelegramBot()
    return _telegram_bot


# ============================================================================
# CHAT WITH AI HANDLER (Outside class - avoid scope issues)
# ============================================================================

async def chat_command_handler(update, context):
    """Chat with the AI about its strategy and reasoning"""
    try:
        from telegram import Update
        from telegram.ext import ContextTypes
    except ImportError:
        await update.message.reply_text("❌ Telegram library not available")
        return
    
    if not context.args:
        await update.message.reply_text(
            "💬 *Chat com a IA*\n\n"
            "Usage: `/chat <sua pergunta>`\n\n"
            "Exemplos:\n"
            "• `/chat como você decide leverage?`\n"
            "• `/chat qual seu estilo de trading?`\n"
            "• `/chat por que usa stops largos?`",
            parse_mode="Markdown"
        )
        return
    
    question = ' '.join(context.args)
    
    try:
        import openai
        import os
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            await update.message.reply_text("❌ OpenAI API key not configured")
            return
        
        client = openai.OpenAI(api_key=api_key)
        
        # Get current state for context
        state = _bot_state.get('last_summary', {})
        equity = state.get('equity', 0)
        positions = state.get('positions', {})
        
        system_prompt = f"""You are "Ladder Labs IA Trader", a professional discretionary crypto derivatives trader.

YOUR IDENTITY:
- Professional trader on Hyperliquid mainnet
- Multi-timeframe analysis (1m to 1D)
- Risk-adjusted returns focus
- Dynamic stops: Based on market structure and volatility
- Position sizing: $10-50 notional for small accounts
- Leverage: 1-50x based on conviction (system auto-caps to exchange limits)

CURRENT STATE:
- Equity: ${equity:.2f}
- Open Positions: {len(positions)}

Answer questions about your trading style, reasoning, and strategy.
Be specific, honest, and concise. Respond in Portuguese or English."""

        response = client.chat.completions.create(
            model=os.getenv("AI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        answer = response.choices[0].message.content.strip()
        await update.message.reply_text(f"🤖 {answer}")
        
    except Exception as e:
        print(f"[TG] Chat error: {e}")
        await update.message.reply_text(f"❌ Erro no chat: {str(e)}")


# ============================================================================
# BOT STARTUP
# ============================================================================

def start_telegram_bot():
    """Start telegram bot if enabled"""
    bot = get_telegram_bot()
    if bot:
        bot.start()


def update_telegram_state(state: Dict[str, Any]):
    """Update telegram with latest engine state + NEW enhanced data"""
    
    # Get last AI decision if available
    last_ai_decision = {}
    if "last_decision" in state:
        decision = state["last_decision"]
        last_ai_decision = {
            "timestamp": decision.get("timestamp", ""),
            "confidence": decision.get("confidence", 0),
            "summary": decision.get("summary", "")
        }
    
    # Calculate performance today
    performance_today = {}
    try:
        from trade_journal import get_recent_trades_for_ai
        history = get_recent_trades_for_ai(limit=50)
        
        # Get today's stats from last_24h
        overall = history.get("overall_stats", {})
        recent = history.get("recent_trades", [])
        
        # Filter only today's trades (last 24h is close enough)
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        
        today_trades = []
        for t in recent:
            try:
                entry_time = t.get("entry", {}).get("timestamp", "")
                if entry_time:
                    trade_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                    if trade_time >= cutoff:
                        today_trades.append(t)
            except:
                pass
        
        if today_trades:
            wins = sum(1 for t in today_trades if t.get("win"))
            total = len(today_trades)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            total_pnl = sum(t.get("pnl_usd", 0) for t in today_trades)
            best = max((t.get("pnl_usd", 0) for t in today_trades), default=0)
            
            performance_today = {
                "trades": total,
                "win_rate": round(win_rate, 1),
                "total_pnl": round(total_pnl, 2),
                "best_trade": round(best, 2)
            }
    except Exception as e:
        print(f"[TELEGRAM] Failed to get performance: {e}")
    
    # Get top symbols from scan
    top_symbols = []
    briefs = state.get("symbol_briefs", {})
    if briefs:
        sorted_briefs = sorted(briefs.items(), key=lambda x: x[1].get("score", 0), reverse=True)
        for sym, brief in sorted_briefs[:4]:
            top_symbols.append({
                "symbol": sym,
                "score": brief.get("score", 0),
                "trend": brief.get("trend", "NEUTRAL")
            })
    
    # Enhanced positions with details
    positions_enhanced = {}
    positions = state.get("positions", {})
    for sym, pos in positions.items():
        positions_enhanced[sym] = {
            "side": pos.get("side", "?"),
            "size": pos.get("size", 0),
            "entry_price": pos.get("entry_price", 0),
            "mark_price": pos.get("mark_price", 0),
            "unrealized_pnl": pos.get("unrealized_pnl", 0),
            "pnl_pct": pos.get("pnl_pct", 0),
            "leverage": pos.get("leverage", 1),
            "liquidation_price": pos.get("liquidation_price", 0),
            "stop_loss": pos.get("stop_loss", 0),
            "take_profit": pos.get("take_profit", 0)
        }
    
    
    # Calculate PNL History (24h, 7D, 30D, ALL) - NEW
    pnl_history = {}
    try:
        from pnl_tracker import get_pnl_windows
        pnl_data = get_pnl_windows()
        
        # get_pnl_windows returns dict like:
        # {"24h": {"pnl": 0, "pnl_pct": "N/A"}, "7d": {...}, ...}
        pnl_history = {
            "24h": pnl_data.get("24h", {}).get("pnl", 0),
            "7d": pnl_data.get("7d", {}).get("pnl", 0),
            "30d": pnl_data.get("30d", {}).get("pnl", 0),
            "all": pnl_data.get("allTime", {}).get("pnl", 0)
        }
    except Exception as e:
        print(f"[TELEGRAM] Failed to get PNL history: {e}")
    
    # Generate AI Self-Assessment - NEW
    ai_assessment = ""
    try:
        pnl_24h = pnl_history.get("24h", 0)
        pnl_7d = pnl_history.get("7d", 0)
        trades_today = performance_today.get("trades", 0)
        
        if trades_today > 0:
            # Has trades today - detailed assessment
            win_rate = performance_today.get("win_rate", 0)
            
            # Generate assessment based on performance
            if pnl_24h > 0 and win_rate >= 60:
                ai_assessment = f"Performance sólida hoje: {win_rate:.0f}% win rate, ${pnl_24h:+.2f} em 24h. Estratégias funcionando bem."
            elif pnl_24h > 0:
                ai_assessment = f"Positivo em 24h (${pnl_24h:+.2f}) mas win rate pode melhorar ({win_rate:.0f}%)."
            elif pnl_24h < 0 and win_rate < 50:
                ai_assessment = f"Dia desafiador: ${pnl_24h:.2f} em 24h, {win_rate:.0f}% win rate. Ajustando estratégia."
            elif pnl_7d > 0:
                ai_assessment = f"Curto prazo negativo (${pnl_24h:.2f}) mas 7D positivo (${pnl_7d:+.2f}). Mantendo curso."
            else:
                ai_assessment = f"Analisando mercado. PnL 24h: ${pnl_24h:.2f}, buscando melhores setups."
        else:
            # No trades today - simple status based on position and market
            positions_count = state.get("positions_count", 0)
            
            if positions_count > 0:
                # Has open position
                ai_assessment = "Monitorando posição aberta. Aguardando confirmação de estrutura para próxima ação."
            else:
                # Flat
                ai_assessment = "Flat no momento. Analisando mercado e aguardando setups de alta probabilidade."
                
    except Exception as e:
        print(f"[TELEGRAM] Failed to generate AI assessment: {e}")
    
    # Update state with ALL data
    _bot_state["last_summary"] = {
        # Original fields
        "equity": state.get("equity", 0),
        "buying_power": state.get("buying_power", 0),
        "positions_count": state.get("positions_count", 0),
        "positions": positions_enhanced,  # Enhanced!
        "trigger_status": state.get("trigger_status", ""),
        "holding_symbol": state.get("holding_symbol", None),
        
        # NEW fields
        "last_ai_decision": last_ai_decision,
        "performance_today": performance_today,
        "top_symbols": top_symbols,
        "pnl_history": pnl_history,  # NEW
        "ai_assessment": ai_assessment  # NEW
    }
    
    # Update scan info for visibility
    symbols = state.get("symbols", [])
    _bot_state["scan_info"] = {
        "scanned": len(symbols),
        "total": len(symbols),
        "symbols": symbols,
        "timestamp": state.get("scan_timestamp", "")
    }
    
    # Update scan results
    if briefs:
        scan = []
        for sym, brief in sorted(briefs.items(), key=lambda x: x[1].get("score", 0), reverse=True):
            scan.append({
                "symbol": sym,
                "score": brief.get("score", 0),
                "trend": brief.get("trend", "?"),
                "reason": brief.get("reason", "")
            })
        _bot_state["last_scan"] = scan
def is_ai_enabled() -> bool:
    """Check if AI is enabled (can be toggled via Telegram)"""
    return _bot_state.get("ai_enabled", True)


def should_panic_close() -> bool:
    """Check if panic close was triggered"""
    if _bot_state.get("panic_close_all"):
        _bot_state["panic_close_all"] = False  # Reset flag
        return True
    return False




