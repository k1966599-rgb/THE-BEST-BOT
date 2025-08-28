import datetime
import asyncio
import json
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, Application

from src.background_scanner import run_scanner
from src.strategies.h4_strategy import h4_long_term_strategy
from src.strategies.m15_strategy import m15_scalp_strategy
from src.strategies.m5_strategy import m5_scalp_strategy
from src.strategies.m3_strategy import m3_scalp_strategy
from src.trading.trade_proposer import propose_trade
from src.bot_interface.formatters import format_elliott_wave_report, format_trade_alert

BOT_NAME = "Elliott Wave Bot"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the main menu."""
    if 'user_id' not in context.bot_data:
        context.bot_data['user_id'] = update.effective_chat.id
    is_running = context.bot_data.get('is_running', False)
    status_text = "الحالة: 🟢 يعمل" if is_running else "الحالة: 🔴 متوقف"
    keyboard = [
        [InlineKeyboardButton("🟢 تشغيل البوت", callback_data='start_bot'), InlineKeyboardButton("🔴 ايقاف البوت", callback_data='stop_bot')],
        [InlineKeyboardButton("📊 تحليل موجي", callback_data='wave_analysis_menu')],
        [InlineKeyboardButton("📈 الصفقات النشطة", callback_data='active_trades'), InlineKeyboardButton("📋 الاحصائيات", callback_data='statistics')]
    ]
    text = f"**{BOT_NAME}**\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{status_text}\n\nاختر احد الأوامر:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    else:
        await update.message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

async def show_symbol_selection_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays a menu to select a symbol for analysis."""
    popular_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
    keyboard = [[InlineKeyboardButton(s, callback_data=f'select_symbol_{s}') for s in popular_symbols[i:i+2]] for i in range(0, len(popular_symbols), 2)]
    keyboard.append([InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')])
    await update.callback_query.edit_message_text(text="اختر العملة للتحليل:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_timeframe_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str) -> None:
    """Displays the timeframe options for the selected symbol."""
    keyboard = [
        [InlineKeyboardButton("بحث عن صفقة طويلة المدى (4h)", callback_data=f'run_strategy_h4_{symbol}')],
        [InlineKeyboardButton("بحث عن صفقة مضاربة (15m)", callback_data=f'run_strategy_m15_{symbol}')],
        [InlineKeyboardButton("بحث عن صفقة مضاربة (5m)", callback_data=f'run_strategy_m5_{symbol}')],
        [InlineKeyboardButton("بحث عن صفقة مضاربة (3m)", callback_data=f'run_strategy_m3_{symbol}')],
        [InlineKeyboardButton("رجوع (اختيار العملة) ⬅️", callback_data='wave_analysis_menu')]
    ]
    await update.callback_query.edit_message_text(text=f"اختر الإطار الزمني لتحليل **{symbol}**:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

def _run_strategy_sync(strategy_func, symbol):
    """Synchronous wrapper for the blocking strategy call."""
    return strategy_func(symbol)

async def _create_and_send_analysis_report(update: Update, context: ContextTypes.DEFAULT_TYPE, strategy_func, symbol: str, interval_str: str):
    """
    Runs the heavy analysis in a separate thread and sends the results when complete.
    """
    try:
        # Run the blocking analysis in a thread
        scenarios, data_with_indicators = await asyncio.to_thread(_run_strategy_sync, strategy_func, symbol)

        if not scenarios:
            response_text = f"لم يتم العثور على أي أنماط موجية لـ **{symbol}** حالياً على فريم {interval_str}."
        else:
            wave_report = format_elliott_wave_report(symbol, interval_str, scenarios)
            trade_signal = propose_trade(scenarios, interval_str, data_with_indicators)
            if trade_signal:
                trade_alert = format_trade_alert(trade_signal, interval_str, symbol, scenarios)
                response_text = f"{wave_report}\n\n{trade_alert}"
            else:
                response_text = f"{wave_report}\n\n*لا توجد فرصة تداول واضحة بناءً على الأنماط الحالية.*"
    except Exception as e:
        response_text = f"حدث خطأ فادح أثناء تحليل {symbol}. يرجى مراجعة السجل."
        print(f"Error during manual analysis for {symbol} on {interval_str}:")
        traceback.print_exc()

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response_text, parse_mode='Markdown')


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    # --- Menu Navigation ---
    if data == 'main_menu':
        await start(update, context)
        return
    if data == 'wave_analysis_menu':
        await show_symbol_selection_menu(update, context)
        return
    if data.startswith('select_symbol_'):
        symbol = data.split('_')[2]
        await show_timeframe_menu(update, context, symbol)
        return

    # --- Bot State Control ---
    if data == 'start_bot':
        if not context.bot_data.get('is_running', False):
            context.bot_data['is_running'] = True
            save_bot_state(True)
            print("Scanner start requested. It will begin on the next bot restart or cycle.")
        await start(update, context)
        return
    if data == 'stop_bot':
        if context.bot_data.get('is_running', False):
            context.bot_data['is_running'] = False
            save_bot_state(False)
            print("Scanner stop requested. Please restart the bot to ensure the scanner is stopped.")
        await start(update, context)
        return

    # --- Strategy Execution ---
    if data.startswith('run_strategy_'):
        try:
            parts = data.split('_')
            strategy_key, symbol = parts[2], parts[3]
            strategy_map = {'h4': (h4_long_term_strategy, "4h"), 'm15': (m15_scalp_strategy, "15m"), 'm5': (m5_scalp_strategy, "5m"), 'm3': (m3_scalp_strategy, "3m")}

            if strategy_key in strategy_map:
                strategy_func, interval_str = strategy_map[strategy_key]
                # Acknowledge immediately
                await query.edit_message_text(text=f"طلبك لتحليل {symbol} على فريم {interval_str} قيد المعالجة... سأرسل النتائج في رسالة جديدة عند اكتمالها.")
                # Schedule the heavy lifting to run in the background
                asyncio.create_task(_create_and_send_analysis_report(update, context, strategy_func, symbol, interval_str))
            else:
                await query.edit_message_text(text="استراتيجية غير معروفة.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')]]))
        except IndexError:
            await query.edit_message_text(text="خطأ في تحليل أمر الاستراتيجية.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')]]))
        return

    # --- Placeholder Buttons ---
    response_map = {'active_trades': "📈 **الصفقات النشطة**\n\n(هذه الميزة قيد التطوير)", 'statistics': "📋 **الاحصائيات**\n\n(هذه الميزة قيد التطوير)"}
    if data in response_map:
        await query.edit_message_text(text=response_map[data], parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("رجوع ⬅️", callback_data='main_menu')]]))

# --- State Persistence ---
STATE_FILE = ".bot_state.json"
def save_bot_state(is_running: bool):
    with open(STATE_FILE, "w") as f: json.dump({"is_running": is_running}, f)
def load_bot_state() -> bool:
    try:
        with open(STATE_FILE, "r") as f: return json.load(f).get("is_running", False)
    except (FileNotFoundError, json.JSONDecodeError): return False
