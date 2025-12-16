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
ENABLE_TELEGRAM = os.environ.get("ENABLE_TELEGRAM", "true").lower() == "true"
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_IDS = os.environ.get("TELEGRAM_ADMIN_IDS", "").split(",")

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


class TelegramBot:
    """Simple Telegram bot with 3 main buttons"""
    
    def __init__(self):
        self.running = False
        self.bot = None
        self._thread = None
        
    def start(self):
        """Start bot in background thread"""
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
        """Async main for telegram bot"""
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
        
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Handlers
        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("status", self._cmd_status))
        app.add_handler(CommandHandler("panic", self._cmd_panic))
        app.add_handler(CallbackQueryHandler(self._handle_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        self.running = True
        print("[TG] Bot running")
        
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        
        # Keep running
        while self.running:
            await asyncio.sleep(1)
        
        await app.stop()
    
    async def _cmd_start(self, update, context):
        """Handle /start command - show persistent keyboard"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
        
        # Inline buttons for toggle actions
        inline_keyboard = [
            [
                InlineKeyboardButton("🤖 IA: ON/OFF", callback_data="toggle_ai"),
                InlineKeyboardButton("🚨 PANIC", callback_data="panic")
            ]
        ]
        inline_markup = InlineKeyboardMarkup(inline_keyboard)
        
        # PERSISTENT reply keyboard (always visible)
        reply_keyboard = [
            ["📊 Resumo", "💬 Chat"],
            ["📰 Notícias", "📅 Calendário"],
            ["📈 Status", "🔍 Scan"]
        ]
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, 
            resize_keyboard=True,  # Smaller buttons
            is_persistent=True     # Always visible
        )
        
        await update.message.reply_text(
            "🚀 *Hyperliquid AI Bot*\n\n"
            f"IA: {'✅ ON' if _bot_state['ai_enabled'] else '❌ OFF'}\n\n"
            "Use os botões abaixo para navegar:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        # Also send inline buttons for toggle
        await update.message.reply_text(
            "⚡ Ações rápidas:",
            reply_markup=inline_markup
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
        
        # Account
        text += "💰 *Conta:*\n"
        text += f"  Equity: ${state.get('equity', 0):.2f}\n"
        text += f"  Buying Power: ${state.get('buying_power', 0):.0f}\n"
        text += f"  IA: {'✅ ON' if _bot_state['ai_enabled'] else '❌ OFF'}\n\n"
        
        # Positions
        positions = state.get("positions", {})
        if positions:
            text += "📈 *Posições:*\n"
            for sym, pos in positions.items():
                pnl = pos.get("unrealized_pnl", 0)
                pnl_emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                safe_sym = escape_md(sym)
                text += f"  {safe_sym}: {pos.get('side')} ${pos.get('size', 0):.4f} | PnL: {pnl_emoji} ${pnl:.2f}\n"
        else:
            text += "📈 *Posições:* Nenhuma\n"
        
        # Trigger status
        triggers = state.get('trigger_status', 'N/A')
        text += f"\n🎯 *Triggers:*\n{escape_md(triggers)}\n"
        
        # Scan info with visibility
        scan_info = _bot_state.get("scan_info", {})
        scanned = scan_info.get("scanned", 0)
        total = scan_info.get("total", 0)
        symbols_list = scan_info.get("symbols", [])
        if scanned and total:
            text += f"\n🔍 *Scan:* {scanned}/{total} symbols\n"
        
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
        
        # Handle keyboard button presses (not in chat mode required)
        if "📊 resumo" in user_text_lower or user_text_lower == "resumo":
            await self._send_full_summary_text(update)
            return
        
        if "📰 notícias" in user_text_lower or user_text_lower in ["noticias", "news"]:
            await self._send_news(update)
            return
            
        if "📅 calendário" in user_text_lower or user_text_lower in ["calendario", "calendar"]:
            await self._send_calendar(update)
            return
            
        if "📈 status" in user_text_lower or user_text_lower == "status":
            await self._cmd_status(update, context)
            return
            
        if "🔍 scan" in user_text_lower or user_text_lower == "scan":
            await self._send_scan(update)
            return
            
        if "💬 chat" in user_text_lower:
            _bot_state["chat_mode"] = True
            await update.message.reply_text(
                "💬 *Modo Chat Ativado*\n\n"
                "Pergunte qualquer coisa sobre o mercado ou suas operações.\n"
                "Digite 'sair' para desativar.",
                parse_mode="Markdown"
            )
            return
        
        # Check if user wants to exit chat mode
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
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Você É o trading bot. Responda em PRIMEIRA PESSOA. Diga 'Eu tenho', 'Eu pretendo', 'Minha estratégia'. Seja direto e assertivo, sem rodeios. Max 2 parágrafos."},
                        {"role": "user", "content": context}
                    ],
                    max_tokens=300,
                    temperature=0.7
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
        """Send full summary as reply (for keyboard button)"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        state = _bot_state.get("last_summary", {})
        scan = _bot_state.get("last_scan", [])
        
        text = "📊 *RESUMO COMPLETO*\n\n"
        text += f"💰 Equity: ${state.get('equity', 0):.2f}\n"
        text += f"📈 Buying Power: ${state.get('buying_power', 0):.0f}\n"
        text += f"🤖 IA: {'✅ ON' if _bot_state['ai_enabled'] else '❌ OFF'}\n\n"
        
        # Positions
        positions = state.get("positions", {})
        if positions:
            text += "📈 *Posições:*\n"
            for sym, pos in positions.items():
                pnl = pos.get("unrealized_pnl", 0)
                emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
                text += f"  {sym}: {pos.get('side')} | PnL: {emoji} ${pnl:.2f}\n"
        
        # Top 5 scan
        if scan:
            text += "\n📡 *Top 5:*\n"
            for s in scan[:5]:
                text += f"  {s['symbol']}: {s['score']} | {s.get('trend', '?')}\n"
        
        # Try to get external data
        try:
            from data_sources import get_fear_greed
            fg = get_fear_greed()
            if fg.get("value"):
                text += f"\n😱 Fear & Greed: {fg['value']} ({fg.get('classification', '')})\n"
        except:
            pass
        
        await update.message.reply_text(text, parse_mode="Markdown")
    
    async def _send_news(self, update):
        """Send latest crypto news"""
        await update.message.reply_text("📰 Buscando notícias...")
        
        try:
            from data_sources import get_cryptopanic_news
            news = get_cryptopanic_news()
            
            if news.get("error"):
                await update.message.reply_text(f"❌ {news['error']}")
                return
            
            headlines = news.get("headlines", [])
            if not headlines:
                await update.message.reply_text("📰 Nenhuma notícia encontrada")
                return
            
            text = "📰 *TOP NOTÍCIAS*\n\n"
            for i, headline in enumerate(headlines[:8], 1):
                safe_title = escape_md(headline.get('title', '')[:80])
                source = headline.get('source', '')
                text += f"{i}. {safe_title}\n   _{source}_\n\n"
            
            await update.message.reply_text(text, parse_mode="Markdown")
            
        except Exception as e:
            await update.message.reply_text(f"❌ Erro ao buscar notícias: {str(e)[:100]}")
    
    async def _send_calendar(self, update):
        """Send economic calendar"""
        await update.message.reply_text("📅 Buscando calendário econômico...")
        
        try:
            import httpx
            
            # Try to get from Forex Factory or similar free API
            # Using a free endpoint
            url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
            
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
                events = resp.json()
            
            if not events:
                await update.message.reply_text("📅 Nenhum evento encontrado")
                return
            
            # Filter high impact events
            high_impact = [e for e in events if e.get("impact", "").lower() in ["high", "medium"]][:10]
            
            text = "📅 *CALENDÁRIO ECONÔMICO*\n\n"
            for event in high_impact:
                date = event.get("date", "")[:10]
                time_str = event.get("time", "")
                title = escape_md(event.get("title", "")[:40])
                currency = event.get("country", "")
                impact = "🔴" if event.get("impact") == "High" else "🟡"
                
                text += f"{impact} *{currency}* {time_str}\n   {title}\n\n"
            
            if not high_impact:
                text += "Nenhum evento de alto impacto hoje."
            
            await update.message.reply_text(text, parse_mode="Markdown")
            
        except Exception as e:
            print(f"[TG][CALENDAR] Error: {e}")
            await update.message.reply_text(f"❌ Erro ao buscar calendário: {str(e)[:100]}")
    
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


def start_telegram_bot():
    """Start telegram bot if enabled"""
    bot = get_telegram_bot()
    if bot:
        bot.start()


def update_telegram_state(state: Dict[str, Any]):
    """Update telegram with latest engine state"""
    _bot_state["last_summary"] = {
        "equity": state.get("equity", 0),
        "buying_power": state.get("buying_power", 0),
        "positions_count": state.get("positions_count", 0),
        "positions": state.get("positions", {}),
        "trigger_status": state.get("trigger_status", ""),
        "holding_symbol": state.get("holding_symbol", None)
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
    briefs = state.get("symbol_briefs", {})
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
