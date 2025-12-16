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
        """Handle /start command"""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [
                InlineKeyboardButton("🤖 IA: ON/OFF", callback_data="toggle_ai"),
                InlineKeyboardButton("💬 Chat", callback_data="chat_mode")
            ],
            [
                InlineKeyboardButton("📊 Resumo Completo", callback_data="full_summary")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🚀 *Hyperliquid AI Bot*\n\n"
            f"IA: {'✅ ON' if _bot_state['ai_enabled'] else '❌ OFF'}\n"
            "Escolha uma opção:",
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
    
def escape_md(text: str) -> str:
    """Escape markdown v1 special chars"""
    return str(text).replace("_", "\\_").replace("*", "\\*").replace("`", "\\`").replace("[", "\\[")

class TelegramBot:
    # ... (keeps existing init and other methods)

    # ... (keeps _cmd_start, _cmd_status, etc. - we fix _send_full_summary below)

    async def _send_full_summary(self, query):
        """Send full summary with all info"""
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
        
        # Scan
        if scan:
            text += "\n📡 *Top 5 Score:*\n"
            for s in scan[:5]:
                sym = escape_md(s['symbol'])
                score = s['score']
                trend = escape_md(s.get('trend', '?'))
                reason = escape_md(s.get('reason', ''))
                text += f"  {sym}: {score} | {trend} | {reason}\n"
        
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
        """Handle free text messages (chat mode)"""
        if not _bot_state.get("chat_mode"):
            return
            
        user_text = update.message.text.lower()
        
        # Simple intent detection
        if any(cmd in user_text for cmd in ["abrir long", "comprar", "buy"]):
            # Extract symbol
            for sym in ["btc", "eth", "sol", "doge", "xrp"]:
                if sym in user_text:
                    await update.message.reply_text(
                        f"🎯 Comando detectado: LONG {sym.upper()}\n"
                        "⚠️ Funcionalidade em desenvolvimento"
                    )
                    return
            await update.message.reply_text("❓ Qual símbolo? Ex: 'abrir long em BTC'")
            
        elif any(cmd in user_text for cmd in ["abrir short", "vender", "sell"]):
            for sym in ["btc", "eth", "sol", "doge", "xrp"]:
                if sym in user_text:
                    await update.message.reply_text(
                        f"🎯 Comando detectado: SHORT {sym.upper()}\n"
                        "⚠️ Funcionalidade em desenvolvimento"
                    )
                    return
            await update.message.reply_text("❓ Qual símbolo? Ex: 'abrir short em ETH'")
            
        elif any(cmd in user_text for cmd in ["fechar tudo", "fechar todas", "close all"]):
            await update.message.reply_text(
                "🚨 Comando: FECHAR TODAS\n"
                "Use /panic para confirmar"
            )
            
        else:
            # Generic response (placeholder for LLM chat)
            await update.message.reply_text(
                "🤖 Recebi sua mensagem.\n"
                "Chat com IA em desenvolvimento.\n\n"
                "Comandos suportados:\n"
                "• 'abrir long em BTC'\n"
                "• 'abrir short em ETH'\n"
                "• 'fechar todas'\n"
                "• /status\n"
                "• /panic"
            )
    
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
        "trigger_status": state.get("trigger_status", "")
    }
    
    # Update scan
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
