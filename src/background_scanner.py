import asyncio
import datetime
import traceback
from telegram.ext import Application

from src.utils.config_loader import config
from src.data.bybit_client import BybitClient
from src.analysis.support_resistance import find_supply_demand_zones
from src.strategies.h4_strategy import h4_long_term_strategy
from src.strategies.m15_strategy import m15_scalp_strategy
from src.strategies.m5_strategy import m5_scalp_strategy
from src.strategies.m3_strategy import m3_scalp_strategy
from src.trading.trade_proposer import propose_trade
from src.bot_interface.formatters import format_trade_alert

LOWER_TIMEFRAME_STRATEGIES = [
    (m15_scalp_strategy, "15m"),
    (m5_scalp_strategy, "5m"),
    (m3_scalp_strategy, "3m"),
]

SCAN_INTERVAL_SECONDS = 900

async def run_scanner(app: Application):
    """
    The main background task that uses Multi-Timeframe Analysis.
    """
    print("Background scanner started.")
    last_alerted_pattern_time = {}
    client = BybitClient()
    symbols_to_scan = config['symbols_to_scan']
    print(f"Scanner will analyze the following symbols: {symbols_to_scan}")

    while True:
        try:
            print(f"[{datetime.datetime.now()}] Running new automatic scan cycle...")
            user_id = app.bot_data.get('user_id')
            alert_sent_in_cycle = False

            for symbol in symbols_to_scan:
                print(f"--- Analyzing {symbol} ---")

                # 1. Get High-Timeframe (HTF) context
                htf_data = client.get_historical_data(symbol, "240")
                if htf_data is None or htf_data.empty:
                    print(f"  - Could not fetch HTF data for {symbol}. Skipping.")
                    continue

                htf_zones = find_supply_demand_zones(htf_data)
                current_price = htf_data['close'].iloc[-1]

                print(f"  - Current price: {current_price:.2f}. Found {len(htf_zones)} HTF zones.")

                # 2. Check if price is near a HTF demand zone
                is_near_htf_demand = False
                for zone in htf_zones:
                    if zone['type'] == 'demand' and (zone['bottom'] * 0.995 < current_price < zone['top'] * 1.005):
                        is_near_htf_demand = True
                        print(f"  - Price is near HTF demand zone: {zone['bottom']:.2f} - {zone['top']:.2f}")
                        break

                if not is_near_htf_demand:
                    print(f"  - Price is not near any HTF demand zone. Skipping lower timeframe analysis.")
                    continue

                # 3. If near HTF demand, scan lower timeframes for entries
                print(f"  - Price near HTF demand. Scanning lower timeframes for entry patterns...")
                for strategy_func, timeframe in LOWER_TIMEFRAME_STRATEGIES:
                    # This logic remains the same as before
                    try:
                        # Unpack the new return tuple (scenarios, data)
                        loose_scenarios, _ = strategy_func(symbol, strict=False)
                        if loose_scenarios:
                            # We only care about the primary pattern of the top scenario for alerts
                            latest_primary_pattern = loose_scenarios[0].primary_pattern
                            latest_pattern_timestamp = latest_primary_pattern.points[-1].time
                            alert_key = f"{symbol}-{timeframe}"

                            if last_alerted_pattern_time.get(alert_key) != latest_pattern_timestamp:
                                if user_id:
                                    initial_alert = f"⚠️ فرصة محتملة على {symbol} إطار {timeframe} (عند منطقة طلب 4 ساعات)"
                                    await app.bot.send_message(chat_id=user_id, text=initial_alert)

                                # Rerun with strict=True to get clean scenarios and the final data with indicators
                                strict_scenarios, data_with_indicators = strategy_func(symbol, strict=True)
                                if strict_scenarios:
                                    # We still propose trades based on the single most likely scenario
                                    trade_signal = propose_trade(strict_scenarios, timeframe, data_with_indicators)
                                    if trade_signal:
                                        # The formatter will now handle displaying alternate scenarios
                                        alert_text = format_trade_alert(trade_signal, timeframe, strict_scenarios)
                                        await app.bot.send_message(chat_id=user_id, text=alert_text, parse_mode='Markdown')
                                        last_alerted_pattern_time[alert_key] = latest_pattern_timestamp
                                        alert_sent_in_cycle = True
                    except Exception as e:
                        print(f"    - ERROR during LTF scan on {symbol}/{timeframe}: {e}")
                        traceback.print_exc()

            if user_id and not alert_sent_in_cycle:
                await app.bot.send_message(chat_id=user_id, text=f"✅ اكتمل الفحص. لا توجد فرص جديدة.", disable_notification=True)

            print("Scan cycle complete.")
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)

        except asyncio.CancelledError:
            print("Background scanner stopped.")
            break
        except Exception as e:
            print(f"An error occurred in the main scanner loop: {e}")
            traceback.print_exc()
            await asyncio.sleep(60)
