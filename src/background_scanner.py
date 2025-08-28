import asyncio
import datetime
import traceback
from telegram.ext import Application
from typing import Dict, Any, List

from src.utils.config_loader import config
from src.bot_interface.formatters import format_trade_alert
from src.analysis_manager import AnalysisManager
from src.trading import state_manager, trade_manager # Updated import
from src.data.bybit_client import BybitClient

SCAN_INTERVAL_SECONDS = config.get('scanner', {}).get('interval_seconds', 900)

def find_new_setups_sync(symbol: str) -> List[Dict[str, Any]]:
    """
    Uses the AnalysisManager to perform a full hierarchical analysis for a single symbol.
    """
    manager = AnalysisManager(symbol)
    manager.run_hierarchical_analysis()

    if manager.context.get("final_decision") in ["ACCEPT", "DEFER"]:
        return [manager.context]
    return []

async def handle_trade_update(app: Application, user_id: int, event: Dict[str, Any], trade: Dict[str, Any]):
    """
    Handles events from the trade manager, sends alerts, updates state, and edits the original message.
    """
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
        alert_text = f"✅ **هدف جديد تحقق | {symbol}** ✅"

        if 'hit_targets_indices' not in trade: trade['hit_targets_indices'] = []
        trade['hit_targets_indices'].append(event.get('target_index'))
        state_manager.update_trade(trade)

    elif event_type == 'SL_HIT':
        alert_text = f"❌ **تم ضرب وقف الخسارة | {symbol}** ❌"
        trade['status'] = 'CLOSED_SL'
        state_manager.update_trade(trade)

    # Send a new, brief notification about the update
    if alert_text:
        await app.bot.send_message(chat_id=user_id, text=alert_text, parse_mode='Markdown')

    # Now, edit the original message to reflect the new state
    if message_id and trade.get('status') != 'CLOSED_SL':
        try:
            # We need the original scenarios to re-format the alert.
            # This is a limitation; for now, we pass an empty list.
            # A future improvement would be to save scenarios with the trade state.
            updated_alert_text = format_trade_alert(trade, "15m", symbol, [])
            await app.bot.edit_message_text(chat_id=user_id, message_id=message_id, text=updated_alert_text, parse_mode='Markdown')
        except Exception as e:
            print(f"Could not edit message {message_id} for trade {trade_id}: {e}")

async def monitor_active_trades(app: Application, user_id: int):
    """
    Loads active trades, checks their status using the trade_manager, and handles updates.
    """
    active_trades = state_manager.load_active_trades()
    if not active_trades: return

    print(f"--- Monitoring {len(active_trades)} active trade(s) ---")
    client = BybitClient()

    for trade in active_trades:
        symbol = trade.get('symbol')
        if not symbol or trade.get('status') == 'CLOSED_SL': continue

        price_str = client.get_market_price(symbol)
        if not price_str: continue

        try:
            current_price = float(price_str)
        except (ValueError, TypeError):
            continue

        # Use the new trade_manager to check for events
        update_event = trade_manager.manage_active_trade(trade, current_price)
        if update_event:
            await handle_trade_update(app, user_id, update_event, trade)

async def run_scanner(app: Application):
    """
    The main background task that finds new trades and monitors active ones.
    """
    print("Background scanner started.")
    symbols_to_scan = config['symbols_to_scan']
    print(f"Scanner will analyze the following symbols: {symbols_to_scan}")

    while True:
        try:
            print(f"\n[{datetime.datetime.now()}] --- Running new scan cycle ---")
            user_id = app.bot_data.get('user_id')
            if not user_id:
                print("User ID not found, skipping scan cycle.")
                await asyncio.sleep(10)
                continue

            # --- Part 1: Find New Trade Setups ---
            all_found_setups = []
            for symbol in symbols_to_scan:
                setups = await asyncio.to_thread(find_new_setups_sync, symbol)
                if setups:
                    all_found_setups.extend(setups)

            if all_found_setups:
                info_alerts_text = []
                for context in all_found_setups:
                    if context.get("final_decision") == "ACCEPT":
                        trade_setup = context.get("final_trade_setup")
                        symbol = context.get("symbol")
                        scenarios = context.get("15m_scenarios", [])
                        alert_text = format_trade_alert(trade_setup, "15m", symbol, scenarios)
                        sent_message = await app.bot.send_message(chat_id=user_id, text=alert_text, parse_mode='Markdown')

                        trade_setup['telegram_message_id'] = sent_message.message_id
                        trade_setup['status'] = 'ACTIVE'
                        state_manager.add_trade(trade_setup)
                        print(f"SUCCESS: Saved new active trade for {symbol} with ID {trade_setup['id']}")
                    elif context.get("final_decision") == "DEFER":
                        trade_setup = context.get("final_trade_setup")
                        info_text = (f"⏳ **فرصة قيد المراقبة | {context.get('symbol')}**\n"
                                     f"**النمط:** `{trade_setup.get('pattern_type')}`\n"
                                     f"**الحالة:** {context['decision_path'][-1]}")
                        info_alerts_text.append(info_text)

                if info_alerts_text:
                    final_info_message = "⏳ **فرص قيد المراقبة** ⏳\n\n" + "\n\n---\n\n".join(info_alerts_text)
                    await app.bot.send_message(chat_id=user_id, text=final_info_message, parse_mode='Markdown')
            else:
                print("Scan cycle complete. No new setups found.")

            # --- Part 2: Monitor Existing Active Trades ---
            await monitor_active_trades(app, user_id)

            print(f"--- Scan cycle complete. Waiting {SCAN_INTERVAL_SECONDS} seconds. ---")
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)

        except asyncio.CancelledError:
            print("Background scanner stopped.")
            break
        except Exception as e:
            print(f"An error occurred in the main scanner loop: {e}")
            traceback.print_exc()
            await asyncio.sleep(60)
