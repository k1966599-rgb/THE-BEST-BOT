#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 البوت الشامل للتحليل الفني (يعمل مع CCXT)
"""
import sys
import os
import argparse
from datetime import datetime
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from main_bot import ComprehensiveTradingBot
    from config import get_config, WATCHLIST
except ImportError as e:
    print(f"❌ خطأ في استيراد الوحدات: {e}")
    sys.exit(1)

def create_output_folder(config: dict):
    output_folder = config['output']['OUTPUT_FOLDER']
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    return output_folder

def analyze_single_symbol(symbol: str, config: dict, save_to_file: bool = True) -> dict:
    print(f"\n🔍 تحليل الرمز: {symbol}")
    print("="*50)
    try:
        bot = ComprehensiveTradingBot(symbol=symbol, config=config)
        report = bot.run_complete_analysis()
        if save_to_file and config['output']['SAVE_TXT']:
            output_folder = create_output_folder(config)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_symbol_name = symbol.replace('/', '_')
            txt_filename = os.path.join(output_folder, f"{safe_symbol_name}_report_{timestamp}.txt")
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"💾 تم حفظ التقرير النصي: {txt_filename}")
        return {'symbol': symbol, 'success': True, 'report': report}
    except Exception as e:
        error_msg = f"❌ خطأ في تحليل {symbol}: {e}"
        print(error_msg)
        return {'symbol': symbol, 'success': False, 'error': str(e)}

def analyze_multiple_symbols(symbols: list, config: dict, save: bool) -> list:
    results = []
    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] معالجة {symbol}...")
        result = analyze_single_symbol(symbol, config, save_to_file=save)
        results.append(result)
        if i < len(symbols):
            time.sleep(3)
    return results

def generate_summary_report(results: list) -> str:
    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]
    summary = f"ملخص التحليل - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    summary += f"نجح: {len(successful_results)} | فشل: {len(failed_results)}\n"
    for res in successful_results:
        try:
            # Extract the main recommendation line from the report
            report_line = next(line for line in res.get('report', '').split('\n') if 'التوصية النهائية' in line)
            summary += f"- {res['symbol']}: {report_line.strip()}\n"
        except StopIteration:
            summary += f"- {res['symbol']}: تعذر استخلاص التقرير.\n"
    return summary

def main():
    parser = argparse.ArgumentParser(description='🤖 البوت الشامل للتحليل الفني (CCXT)')
    parser.add_argument('symbols', nargs='*', help='رموز العملات للتحليل (e.g., BTC/USDT)')
    parser.add_argument('--watchlist', action='store_true', help='تحليل قائمة المراقبة')
    parser.add_argument('--top20', action='store_true', help='تحليل أفضل 20 عملة')
    parser.add_argument('--no-save', action='store_true', help='عدم حفظ التقارير')
    parser.add_argument('--period', type=str, default=None, help="تحديد فترة البيانات (e.g., '1y', '6mo')")
    parser.add_argument('--interval', type=str, default=None, help="تحديد الفاصل الزمني (e.g., '1d', '4h')")
    args = parser.parse_args()
    config = get_config()

    if args.period: config['trading']['PERIOD'] = args.period
    if args.interval: config['trading']['INTERVAL'] = args.interval

    symbols_to_analyze = []
    if args.top20:
        print("📋 سيتم تحليل أفضل 20 عملة...")
        temp_bot = ComprehensiveTradingBot(symbol="", config=config)
        symbols_to_analyze = temp_bot.get_top_usdt_coins(20)
    elif args.watchlist:
        symbols_to_analyze = WATCHLIST
    elif args.symbols:
        symbols_to_analyze = [s.upper() for s in args.symbols]
    else:
        symbols_to_analyze = [config['trading']['DEFAULT_SYMBOL']]

    if not symbols_to_analyze:
        print("❌ لم يتم تحديد عملات للتحليل.")
        sys.exit(1)

    print(f"📊 سيتم تحليل {len(symbols_to_analyze)} رمز من منصة {config['trading']['EXCHANGE_ID']}")

    if len(symbols_to_analyze) == 1:
        result = analyze_single_symbol(symbols_to_analyze[0], config, not args.no_save)
        print(f"\n{result.get('report', 'لا يوجد تقرير')}")
    else:
        results = analyze_multiple_symbols(symbols_to_analyze, config, not args.no_save)
        summary = generate_summary_report(results)
        print(f"\n{summary}")

if __name__ == "__main__":
    main()
