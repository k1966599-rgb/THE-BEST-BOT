import sys
import os
import argparse
from datetime import datetime
import time
import copy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from main_bot import ComprehensiveTradingBot
    from config import get_config, WATCHLIST
    from telegram_sender import send_telegram_message
except ImportError as e:
    print(f"❌ خطأ في استيراد الوحدات: {e}")
    sys.exit(1)

def run_analysis_for_timeframe(symbol: str, timeframe: str, config: dict) -> dict:
    """Runs the complete analysis for a single symbol on a specific timeframe."""
    print(f"--- ⏳ تحليل {symbol} على فريم {timeframe} ---")
    timeframe_config = copy.deepcopy(config)
    timeframe_config['trading']['INTERVAL'] = timeframe
    try:
        bot = ComprehensiveTradingBot(symbol=symbol, config=timeframe_config)
        report = bot.run_complete_analysis()
        bot.final_recommendation['timeframe'] = timeframe
        return {'success': True, 'result': bot.final_recommendation, 'report': report}
    except Exception as e:
        return {'success': False, 'timeframe': timeframe, 'error': str(e)}

def rank_opportunities(results: list) -> list:
    """Ranks analysis results from different timeframes."""
    for res in results:
        if res['success']:
            rec = res['result']
            signal_multiplier = 0.5 if 'انتظار' in rec.get('main_action', '') else 1.0
            rank_score = abs(rec.get('total_score', 0)) * (rec.get('confidence', 0) / 100) * signal_multiplier
            res['rank_score'] = rank_score
        else:
            res['rank_score'] = -1
    return sorted(results, key=lambda x: x['rank_score'], reverse=True)

def format_report_for_display(symbol: str, ranked_results: list) -> str:
    """Formats the final report string with the best timeframe and a summary of others."""
    if not ranked_results or not ranked_results[0]['success']:
        return f"\n❌ لم يتم العثور على فرص تداول واضحة لـ {symbol}"

    best_result = ranked_results[0]
    best_report = best_result['report']
    full_report = f"🏆 **أفضل فرصة لـ {symbol} على فريم {best_result['result']['timeframe']}** 🏆\n"
    full_report += best_report
    if len(ranked_results) > 1:
        full_report += "\n\n--- **ملخص باقي الفريمات** ---\n"
        for res in ranked_results[1:]:
            if res['success']:
                rec = res['result']
                full_report += f"- **فريم {rec['timeframe']}**: {rec['main_action']} (النتيجة: {rec['total_score']:+})\n"
            else:
                full_report += f"- **فريم {res['timeframe']}**: فشل التحليل\n"
    return full_report

def get_ranked_analysis_for_symbol(symbol: str, config: dict) -> str:
    """
    This is the main callable function that performs multi-timeframe analysis
    for a single symbol and returns a formatted report string.
    """
    timeframes = config['trading'].get('TIMEFRAMES_TO_ANALYZE', ['1d'])
    print(f"📊 تحليل {symbol} على {len(timeframes)} فريمات زمنية...")
    all_timeframe_results = []
    for timeframe in timeframes:
        result = run_analysis_for_timeframe(symbol, timeframe, config)
        all_timeframe_results.append(result)
        time.sleep(1)

    ranked_results = rank_opportunities(all_timeframe_results)
    final_report = format_report_for_display(symbol, ranked_results)
    return final_report

def main():
    parser = argparse.ArgumentParser(description='🤖 البوت الشامل للتحليل الفني (CCXT)')
    parser.add_argument('symbols', nargs='*', help='رموز العملات للتحليل (e.g., BTC/USDT)')
    parser.add_argument('--watchlist', action='store_true', help='تحليل قائمة المراقبة')
    parser.add_argument('--top20', action='store_true', help='تحليل أفضل 20 عملة')
    parser.add_argument('--period', type=str, default=None, help="تحديد فترة البيانات (e.g., '1y', '6mo')")
    args = parser.parse_args()
    config = get_config()

    if args.period: config['trading']['PERIOD'] = args.period

    symbols_to_analyze = []
    if args.top20:
        print("📋 سيتم تحليل أفضل 20 عملة...")
        # A temporary bot instance is needed to fetch the list
        temp_bot = ComprehensiveTradingBot(symbol="", config=config)
        symbols_to_analyze = temp_bot.get_top_usdt_coins(20)
    elif args.watchlist:
        symbols_to_analyze = WATCHLIST
    elif args.symbols:
        symbols_to_analyze = [s.upper() for s in args.symbols]
    else:
        symbols_to_analyze = [config['trading']['DEFAULT_SYMBOL']]

    if not symbols_to_analyze:
        sys.exit("❌ لم يتم تحديد عملات للتحليل.")

    for symbol in symbols_to_analyze:
        final_report = get_ranked_analysis_for_symbol(symbol, config)
        print(final_report)
        send_telegram_message(final_report) # Send the final report to Telegram
        if len(symbols_to_analyze) > 1:
            time.sleep(5)

if __name__ == "__main__":
    main()
