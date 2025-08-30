import asyncio
import datetime
import traceback
import pandas as pd
import os
from telegram.ext import Application
from typing import Dict, Any, List, Optional

from src.utils.config_loader import load_config
from src.bot_interface.formatters import format_trade_alert
from src.analysis_manager import AnalysisManager
from src.trading import state_manager, trade_manager, trade_logger
from src.trading.state_manager import load_notification_state, save_notification_state
from src.data.bybit_client import BybitClient
from src.learning_system import TradingLearningSystem

# --- Constants are now loaded inside the scanner loop to ensure they are fresh ---


# --- Scoring for aggregated notifications ---
COMPLETENESS_SCORES = {
    "ACCEPT": 100,
    "STAGE_PASSED:SETUP_GENERATED": 90,
    "DEFER": 80,
    "STAGE_PASSED:ALIGN_15m": 70,
    "STAGE_PASSED:ALIGN_1h": 60,
    "STAGE_PASSED:4h": 50,
}


def find_new_setups_sync(symbol: str) -> List[Dict[str, Any]]:
    """Uses the AnalysisManager to perform a full hierarchical analysis for a single symbol."""
    manager = AnalysisManager(symbol)
    manager.run_hierarchical_analysis()

    # For ACCEPT/DEFER, we add a timestamp.
    if manager.context.get("final_decision") in ["ACCEPT", "DEFER"]:
        manager.context['first_seen_timestamp'] = datetime.datetime.now().isoformat()

    # Return the context if any analysis was actually performed.
    # The main loop will handle routing based on the final_decision.
    if manager.context and manager.context.get("decision_path"):
        return [manager.context]

    return []

def get_analysis_notification(context: Dict[str, Any], notification_state: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """
    Analyzes the decision path of a setup and returns a notification object if a new stage has been reached.
    This is a pure function that does not have side effects.
    """
    decision_path = context.get('decision_path', [])
    symbol = context.get('symbol')

    stage_messages = {
        "STAGE_PASSED:4h": f"📈 **فرصة محتملة | {symbol} | 4H**\nتم رصد نمط مبدئي على فريم الأربع ساعات. جاري البحث عن تأكيد...",
        "STAGE_PASSED:ALIGN_1h": f"✅ **تأكيد مبدئي | {symbol} | 1H**\nتم العثور على توافق مع فريم الساعة. جاري تحليل فريم 15 دقيقة...",
        "STAGE_PASSED:ALIGN_15m": f"✅ **تأكيد متقدم | {symbol} | 15M**\nتم العثور على توافق مع فريم 15 دقيقة. جاري فحص شروط الدخول...",
        "STAGE_PASSED:SETUP_GENERATED": f"⏳ **تجهيز الصفقة | {symbol}**\nتم تحديد معلمات الصفقة بنجاح. في انتظار إشارة الدخول النهائية..."
    }

    latest_stage = None
    for stage in reversed(decision_path):
        if stage in stage_messages:
            latest_stage = stage
            break

    if not latest_stage:
        return None

    try:
        start_time = context['4h_scenarios'][0].start_point.time
        opportunity_key = f"{symbol}_{start_time}"
    except (KeyError, IndexError):
        opportunity_key = f"{symbol}_unknown"

    last_notified_stage = notification_state.get(opportunity_key)

    if latest_stage != last_notified_stage:
        return {
            "message": stage_messages[latest_stage],
            "score": COMPLETENESS_SCORES.get(latest_stage, 0),
            "opportunity_key": opportunity_key,
            "stage": latest_stage
        }

    return None


async def handle_trade_update(app: Application, user_id: int, event: Dict[str, Any], trade: Dict[str, Any], learning_system: TradingLearningSystem):
    """Handles events from the trade manager, sends alerts, updates state, and logs completed trades."""
    event_type = event.get('event')
    symbol = event.get('symbol')
    trade_id = trade.get('id')
    message_id = trade.get('telegram_message_id')
    alert_text = ""
    if event_type == 'TP1_HIT':
        alert_text = (f"✅ **الهدف الأول تحقق | {symbol}** ✅\n"
                      f"**الإجراء الموصى به:** نقل وقف الخسارة إلى نقطة الدخول لتأمين الصفقة.")
        trade['stop_loss'] = event.get('new_stop_loss')
        trade['status'] = 'RISK_FREE'
        if 'hit_targets_indices' not in trade: trade['hit_targets_indices'] = []
        trade['hit_targets_indices'].append(event.get('target_index'))
        state_manager.update_trade(trade)
    elif event_type == 'TP_HIT':
        target_index = event.get('target_index', 0)
        alert_text = f"✅ **هدف جديد تحقق | {symbol}** (الهدف رقم {target_index + 1}) ✅"
        if 'hit_targets_indices' not in trade: trade['hit_targets_indices'] = []
        trade['hit_targets_indices'].append(target_index)
        if len(trade['hit_targets_indices']) == len(trade['targets']):
            trade['status'] = 'CLOSED_TP'
            alert_text += "\nاكتملت جميع أهداف الصفقة بنجاح!"
            trade_logger.log_trade(trade, 'TP_FINAL_HIT')
            learning_system.log_closed_trade(trade, event) # New learning system log
            state_manager.remove_trade(trade_id)
        else:
            state_manager.update_trade(trade)
    elif event_type == 'SL_HIT':
        alert_text = f"❌ **تم ضرب وقف الخسارة | {symbol}** ❌"
        trade['status'] = 'CLOSED_SL'
        trade_logger.log_trade(trade, 'SL_HIT')
        learning_system.log_closed_trade(trade, event) # New learning system log
        state_manager.remove_trade(trade_id)
    if alert_text:
        await app.bot.send_message(chat_id=user_id, text=alert_text, parse_mode='Markdown')
    if message_id and not trade.get('status', '').startswith('CLOSED'):
        try:
            updated_alert_text = format_trade_alert(trade, "15m", symbol, [])
            await app.bot.edit_message_text(chat_id=user_id, message_id=message_id, text=updated_alert_text, parse_mode='Markdown')
        except Exception as e:
            print(f"Could not edit message {message_id} for trade {trade_id}: {e}")

async def monitor_active_trades(app: Application, user_id: int, learning_system: TradingLearningSystem):
    """Loads active trades, checks their status, and handles updates."""
    active_trades = state_manager.load_active_trades()
    if not active_trades: return
    print(f"--- Monitoring {len(active_trades)} active trade(s) ---")
    client = BybitClient()
    for trade in active_trades:
        symbol = trade.get('symbol')
        if not symbol or trade.get('status', '').startswith('CLOSED'): continue
        price_str = client.get_market_price(symbol)
        if not price_str: continue
        try:
            current_price = float(price_str)
        except (ValueError, TypeError):
            continue
        update_event = trade_manager.manage_active_trade(trade, current_price)
        if update_event:
            await handle_trade_update(app, user_id, update_event, trade, learning_system)

def get_today_trade_count() -> int:
    """Counts how many trades were sent today."""
    # To be accurate, this should count trades logged with 'SENT' outcome.
    if not os.path.exists(trade_logger.LOG_FILE): return 0
    try:
        df = pd.read_csv(trade_logger.LOG_FILE)
        df['log_timestamp'] = pd.to_datetime(df['log_timestamp'])
        today_sent_trades = df[(df['log_timestamp'].dt.date == datetime.date.today()) & (df['outcome'] == 'SENT')]
        return len(today_sent_trades)
    except Exception as e:
        print(f"Error reading trade history: {e}")
        return 0

def cleanup_expired_deferred_setups(max_age_hours: int):
    """Loads deferred setups and removes any that are older than the configured max age."""
    now = datetime.datetime.now()
    setups_to_keep = []
    for setup_obj in state_manager.load_deferred_setups():
        first_seen = datetime.datetime.fromisoformat(setup_obj['first_seen_timestamp'])
        age_hours = (now - first_seen).total_seconds() / 3600
        if age_hours < max_age_hours:
            setups_to_keep.append(setup_obj)
        else:
            print(f"INFO: Expired deferred setup for {setup_obj['setup']['symbol']} removed.")
    state_manager.save_deferred_setups(setups_to_keep)

async def run_scanner(app: Application):
    """The main background task."""
    print("Background scanner started.")
    learning_system = TradingLearningSystem()
    # Symbols to scan are now loaded inside the loop to allow for dynamic updates.

    while True:
        try:
            # Reload config at the start of each cycle to get the latest settings
            current_config = load_config()
            if not current_config:
                print("ERROR: Could not load config.yaml, skipping cycle.")
                await asyncio.sleep(60)
                continue

            # --- Load fresh constants from config for this cycle ---
            scanner_config = current_config.get('scanner', {})
            trading_rules = current_config.get('trading_rules', {})

            symbols_to_scan = scanner_config.get('symbols_to_scan', [])
            notify_on_no_setups = scanner_config.get('notify_on_no_setups', False)
            scan_interval_seconds = scanner_config.get('interval_seconds', 900)

            max_trades_per_day = trading_rules.get('max_trades_per_day', 3)
            max_opportunity_age_hours = trading_rules.get('max_opportunity_age_hours', 24)

            print(f"\n[{datetime.datetime.now()}] --- Running new scan cycle for symbols: {symbols_to_scan} ---")
            user_id = current_config.get('telegram', {}).get('chat_id')
            if not user_id:
                print("User ID not found in config.yaml, skipping cycle.")
                await asyncio.sleep(10)
                continue

            # --- Part 1: Cleanup Expired Opportunities ---
            cleanup_expired_deferred_setups(max_opportunity_age_hours)

            # --- Part 2: Find New Trade Setups ---
            todays_trades = get_today_trade_count()
            if todays_trades >= max_trades_per_day:
                print(f"Daily trade limit of {max_trades_per_day} reached. Skipping new trade search.")
            else:
                # This block handles finding setups and sending notifications.
                all_found_setups = []
                notifications_to_send = []
                sent_trade_this_cycle = False

                for symbol in symbols_to_scan:
                    setups = await asyncio.to_thread(find_new_setups_sync, symbol)
                    if setups:
                        all_found_setups.extend(setups)

                if all_found_setups:
                    notification_state = load_notification_state()
                    deferred_setups = state_manager.load_deferred_setups()
                    deferred_keys = {f"{s['setup']['symbol']}-{s['setup']['pattern_type']}-{s['setup']['reason']}" for s in deferred_setups}

                    for context in all_found_setups:
                        trade_setup = context.get("final_trade_setup")
                        decision = context.get("final_decision")

                        if decision == "ACCEPT" and get_today_trade_count() < MAX_TRADES_PER_DAY:
                            sent_trade_this_cycle = True
                            symbol = context.get("symbol")
                            alert_text = format_trade_alert(trade_setup, "multi-tf", symbol, [])
                            sent_message = await app.bot.send_message(chat_id=user_id, text=alert_text, parse_mode='Markdown')
                            trade_setup['telegram_message_id'] = sent_message.message_id
                            trade_setup['status'] = 'ACTIVE'
                            state_manager.add_trade(trade_setup)
                            trade_logger.log_trade(trade_setup, 'SENT')
                            print(f"SUCCESS: Saved new active trade for {symbol}")

                        elif decision == "DEFER":
                            setup_key = f"{trade_setup['symbol']}-{trade_setup['pattern_type']}-{trade_setup['reason']}"
                            if setup_key not in deferred_keys:
                                state_manager.save_deferred_setups(deferred_setups + [context])
                                info_text = (f"⏳ **فرصة قيد المراقبة | {trade_setup.get('symbol')}**\n"
                                             f"**النمط:** `{trade_setup.get('pattern_type')}`\n"
                                             f"**الحالة:** {context['decision_path'][-1]}")
                                notifications_to_send.append({"message": info_text, "score": COMPLETENESS_SCORES["DEFER"]})

                        else:  # REJECT case for progressive notifications
                            notification = get_analysis_notification(context, notification_state)
                            if notification:
                                notifications_to_send.append(notification)
                                notification_state[notification['opportunity_key']] = notification['stage']

                    save_notification_state(notification_state)

                # Now, decide what message to send based on what we found.
                if notifications_to_send:
                    notifications_to_send.sort(key=lambda x: x.get('score', 0), reverse=True)
                    header = f"**ملخص فرص التداول ({datetime.datetime.now().strftime('%H:%M')})**\n"
                    header += "====================\n\n"
                    body = "\n\n---\n\n".join([item['message'] for item in notifications_to_send])
                    final_message = header + body
                    await app.bot.send_message(chat_id=user_id, text=final_message, parse_mode='Markdown')

                elif not sent_trade_this_cycle:
                    # Only send "no setups" if no summary was sent AND no individual trades were sent.
                    print("Scan cycle complete. No new notifications to send.")
                    if notify_on_no_setups:
                        await app.bot.send_message(chat_id=user_id, text="✅ دورة فحص مكتملة. لم يتم رصد أي فرص جديدة حاليًا.")

            # --- Part 3: Monitor Existing Active Trades ---
            await monitor_active_trades(app, user_id, learning_system)

            print(f"--- Scan cycle complete. Waiting {scan_interval_seconds} seconds. ---")
            await asyncio.sleep(scan_interval_seconds)

        except asyncio.CancelledError:
            print("Background scanner stopped.")
            break
        except Exception as e:
            print(f"An error occurred in the main scanner loop: {e}")
            traceback.print_exc()
            await asyncio.sleep(60)
