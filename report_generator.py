from datetime import datetime

def generate_full_report(symbol: str, exchange: str, ranked_results: list) -> str:
    """
    Generates the final, polished, multi-timeframe report.
    """
    if not ranked_results or not any(r['success'] for r in ranked_results):
        return f"❌ تعذر إنشاء تقرير لـ {symbol}."

    all_results_map = {res['bot'].final_recommendation['timeframe']: res['bot'] for res in ranked_results if res['success']}
    if not all_results_map:
        return f"❌ لا توجد بيانات ناجحة لإنشاء تقرير لـ {symbol}."

    # --- HEADER ---
    best_bot_instance = next(res['bot'] for res in ranked_results if res['success'])
    current_price = best_bot_instance.final_recommendation['current_price']

    report = (
        f"╔═══════════════════════════════════════════════════╗\n"
        f"║           💎 تحليل فني شامل - {symbol} 💎           ║\n"
        f"║              📊 منصة {exchange.upper()} Exchange 📊               ║\n"
        f"╚═══════════════════════════════════════════════════╝\n\n"
        f"🕐 **التوقيت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"💰 **السعر الحالي:** ${current_price:,.2f}\n"
    )

    # --- TIMEFRAME SECTIONS ---
    timeframe_groups = {
        "🏗️ **استثمار طويل المدى** (1D - 4H - 1H) 🏗️": ['1d', '4h', '1h'],
        "⚡ **تداول قصير المدى** (30M - 15M) ⚡": ['30m', '15m'],
        "🔥 **مضاربة سريعة** (5M - 3M - 1M) 🔥": ['5m', '3m', '1m']
    }

    for title, timeframes in timeframe_groups.items():
        group_results = [bot for tf, bot in all_results_map.items() if tf in timeframes]
        if not group_results: continue

        report += f"\n\n{title}\n"
        sorted_group = sorted(group_results, key=lambda x: abs(x.final_recommendation.get('total_score', 0)), reverse=True)

        for i, bot in enumerate(sorted_group):
            rec, analysis = bot.final_recommendation, bot.analysis_results
            priority_icon = ["🥇", "🥈", "🥉"][i] if i < 3 else "🔹"

            report += f"\n{priority_icon} **فريم {rec['timeframe'].upper()}** - الأولوية {i+1}\n"
            report += "┌─────────────────────────────────────────────────┐\n"

            tm = analysis.get('trade_management', {})
            sr = analysis.get('support_resistance', {})
            patterns = analysis.get('patterns', {})
            fib = analysis.get('fibonacci', {})
            indicators = analysis.get('indicators', {})
            demand, supply = sr.get('primary_demand_zone'), sr.get('primary_supply_zone')

            report += f"│ 📊 قوة الإشارة: {rec.get('confidence', 0)}% | {rec.get('main_action', '')}\n"
            report += f"│ 🎯 نقطة الدخول: ${tm.get('entry_price', rec.get('current_price', 0)):,.2f}\n"
            report += f"│ 🟢 منطقة الطلب: ${demand['start']:,.2f} - ${demand['end']:,.2f}\n" if demand else "│ 🟢 منطقة الطلب: غير محددة\n"
            report += f"│ 🔴 منطقة العرض: ${supply['start']:,.2f} - ${supply['end']:,.2f}\n" if supply else "│ 🔴 منطقة العرض: غير محددة\n"
            report += "│\n"
            report += f"│ 🏛️ **النماذج:** " + (f"{patterns['found_patterns'][0]['name']} - {patterns['found_patterns'][0]['status']}" if patterns.get('found_patterns') else "لا يوجد") + "\n"
            report += "│\n"
            report += f"│ 🌊 **فيبوناتشي:** " + (f"{fib['retracement_levels'][1]['level']} @ ${fib['retracement_levels'][1]['price']:.2f}" if fib.get('retracement_levels') and len(fib['retracement_levels']) > 1 else "N/A") + "\n"
            report += "│\n"
            report += f"│ 📊 **RSI:** {indicators.get('rsi', 0):.1f} | **MACD:** {'Bullish' if indicators.get('macd_is_bullish') else 'Bearish'}\n"
            report += f"│ 🛑 وقف الخسارة: ${tm.get('stop_loss', 0):,.2f}\n"
            report += f"│ 🎯 الهدف الأول: ${tm.get('profit_target', 0):,.2f}\n"
            report += "└─────────────────────────────────────────────────┘"

    # --- EXECUTIVE SUMMARY ---
    report += "\n\n🏆 **الملخص التنفيذي للاستراتيجية** 🏆\n"
    best_bot = sorted([b for b in all_results_map.values()], key=lambda x: x.final_recommendation.get('rank_score', 0), reverse=True)[0]
    best_rec, best_tm = best_bot.final_recommendation, best_bot.analysis_results.get('trade_management', {})

    report += f"\n✅ **التوصية المثلى (من فريم {best_rec['timeframe']}):**\n"
    report += f"   📊 {best_rec['main_action']} بقوة {best_rec['confidence']}%\n"
    report += f"   🎯 دخول: ${best_tm.get('entry_price', 0):,.2f}\n"
    report += f"   🛑 وقف خسارة: ${best_tm.get('stop_loss', 0):,.2f}\n"
    report += f"   🚀 أهداف: ${best_tm.get('profit_target', 0):,.2f}\n"
    report += "\n*📝 التحليل مبني على الاستراتيجية الشاملة - ليس نصيحة استثمارية*"

    return report
