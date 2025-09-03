#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 البوت الشامل للتحليل الفني (يعمل مع CCXT)

أمثلة للاستخدام:
  python run_bot.py BTC/USDT          # تحليل عملة واحدة
  python run_bot.py --watchlist       # تحليل قائمة المراقبة
  python run_bot.py --top20           # تحليل أفضل 20 عملة
"""

import sys
import os
import argparse
from datetime import datetime
import json
import time

# إضافة المجلد الحالي للمسار لضمان عمل الاستيراد
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from main_bot import ComprehensiveTradingBot
    from config import get_config, WATCHLIST
except ImportError as e:
    print(f"❌ خطأ في استيراد الوحدات: {e}")
    print("تأكد من وجود 'main_bot.py' و 'config.py' في نفس المجلد.")
    sys.exit(1)

def create_output_folder(config: dict):
    """إنشاء مجلد المخرجات إذا لم يكن موجودًا"""
    output_folder = config['output']['OUTPUT_FOLDER']
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    return output_folder

def analyze_single_symbol(symbol: str, config: dict, save_to_file: bool = True) -> dict:
    """تحليل رمز واحد"""
    print(f"\n🔍 تحليل الرمز: {symbol}")
    print("="*50)

    try:
        bot = ComprehensiveTradingBot(symbol=symbol, config=config)
        report = bot.run_complete_analysis()

        # حفظ التقرير
        if save_to_file and config['output']['SAVE_TXT']:
            output_folder = create_output_folder(config)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # استبدال الشرطة المائلة في اسم الملف
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
    """تحليل عملات متعددة"""
    print(f"🔍 تحليل {len(symbols)} رمز...")
    results = []
    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] معالجة {symbol}...")
        result = analyze_single_symbol(symbol, config, save_to_file=save)
        results.append(result)
        if i < len(symbols):
            print("⏳ انتظار 3 ثوانٍ...")
            time.sleep(3)
    return results

def generate_summary_report(results: list) -> str:
    """إنتاج تقرير ملخص"""
    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]
    summary = f"""
 ملخص التحليل
==============
- التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- إجمالي العملات: {len(results)}
- نجح: {len(successful_results)}
- فشل: {len(failed_results)}
"""
    if successful_results:
        summary += "\n--- النتائج الناجحة ---\n"
        for res in successful_results:
            summary += f"- {res['symbol']}: {res['report']}\n"
    if failed_results:
        summary += "\n--- النتائج الفاشلة ---\n"
        for res in failed_results:
            summary += f"- {res['symbol']}: {res['error']}\n"
    return summary

def main():
    parser = argparse.ArgumentParser(description='🤖 البوت الشامل للتحليل الفني (CCXT)')
    parser.add_argument('symbols', nargs='*', help='رموز العملات للتحليل (e.g., BTC/USDT ETH/USDT)')
    parser.add_argument('--watchlist', action='store_true', help='تحليل قائمة المراقبة من config.py')
    parser.add_argument('--top20', action='store_true', help='تحليل أفضل 20 عملة من المنصة المحددة')
    parser.add_argument('--no-save', action='store_true', help='عدم حفظ التقارير في ملفات')

    args = parser.parse_args()
    config = get_config()
    symbols_to_analyze = []

    if args.top20:
        print("📋 سيتم تحليل أفضل 20 عملة...")
        try:
            temp_bot = ComprehensiveTradingBot(symbol="", config=config)
            symbols_to_analyze = temp_bot.get_top_usdt_coins(20)
        except Exception as e:
            print(f"❌ فشل في جلب قائمة أفضل العملات: {e}")
            sys.exit(1)
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

    start_time = datetime.now()

    try:
        if len(symbols_to_analyze) == 1:
            result = analyze_single_symbol(symbols_to_analyze[0], config, not args.no_save)
            if result['success']:
                print(f"\n{result['report']}")
        else:
            results = analyze_multiple_symbols(symbols_to_analyze, config, not args.no_save)
            summary = generate_summary_report(results)
            print(f"\n{summary}")

    except KeyboardInterrupt:
        print("\n⏹️ تم إيقاف التحليل.")
        sys.exit(0)

    execution_time = datetime.now() - start_time
    print(f"\n⏱️ وقت التنفيذ: {execution_time}")
    print("🎉 تم انتهاء التشغيل!")

if __name__ == "__main__":
    main()
