from datetime import datetime
from typing import Dict, List, Any

def _format_scenarios(p: Dict, trend_analysis: Dict) -> str:
    if not p: return ""
    name = p.get('name', '')
    primary_prob = p.get('confidence', 60)
    neutral_prob = 15
    counter_prob = 100 - primary_prob - neutral_prob
    if counter_prob < 0:
        counter_prob = 5
        neutral_prob = 100 - primary_prob - counter_prob

    res_line = p.get('resistance_line', p.get('neckline', 0))
    sup_line = p.get('support_line', p.get('neckline', 0))
    if sup_line == 0: sup_line = p.get('support_line_start', 0)
    target = p.get('calculated_target', 0)
    secondary_target = target * 1.02 # 2% higher
    stop_loss_level = sup_line * 0.99 # 1% below support

    text = "\n<b>📋 السيناريوهات المحتملة:</b>\n\n"
    # Bullish Scenarios
    if "مثلث صاعد" in name or "علم صاعد" in name or "قاع مزدوج" in name:
        text += f"<h4>🚀 السيناريو الصاعد (احتمال {primary_prob}%):</h4>"
        text += f"كسر مقاومة النموذج عند <code>${res_line:,.2f}</code>:\n"
        text += f"- الهدف الفوري: <code>${target:,.2f}</code> (هدف النموذج)\n"
        text += f"- محطة ثانية: <code>${secondary_target:,.2f}</code>\n\n"

        text += f"<h4>⚡️ السيناريو المحايد (احتمال {neutral_prob}%):</h4>"
        text += "البقاء داخل النموذج:\n- تداول عرضي وانتظار كسر واضح.\n\n"

        text += f"<h4>📉 السيناريو الهابط (احتمال {counter_prob}%):</h4>"
        text += f"كسر خط الدعم للنموذج:\n- إلغاء النموذج الإيجابي\n- الهدف: <code>${stop_loss_level:,.2f}</code> (وقف الخسارة)\n"
    # Bearish Scenarios
    elif "قمة مزدوجة" in name or "رأس وكتفين" in name:
        text += f"<h4>📉 السيناريو الهابط (احتمال {primary_prob}%):</h4>"
        text += f"كسر دعم النموذج عند <code>${sup_line:,.2f}</code>:\n"
        text += f"- الهدف الفوري: <code>${target:,.2f}</code> (هدف النموذج)\n"
        text += f"- محطة ثانية: <code>${target * 0.98:,.2f}</code>\n\n"

        text += f"<h4>⚡️ السيناريو المحايد (احتمال {neutral_prob}%):</h4>"
        text += "البقاء داخل النموذج:\n- تداول عرضي وانتظار كسر واضح.\n\n"

        text += f"<h4>🚀 السيناريو الصاعد (احتمال {counter_prob}%):</h4>"
        text += f"كسر خط المقاومة للنموذج:\n- إلغاء النموذج السلبي\n- الهدف: <code>${res_line * 1.01:,.2f}</code>\n"
    else:
        return ""
    return text

def _format_patterns_for_timeframe(analysis: Dict) -> str:
    # ... (code is unchanged)
    patterns = analysis.get('found_patterns', [])
    if not patterns: return "<b>🔍 النموذج الكلاسيكي المكتشف</b>\n- <i>لم يتم العثور على نموذج واضح.</i>"
    p = patterns[0]
    name = p.get('name', 'N/A')
    confidence = p.get('confidence', 0)
    details = f"- **نمط:** {'إيجابي' if ('صاعد' in name or 'قاع' in name) else 'سلبي'} - احتمالية نجاح {confidence}%\n"
    if 'neckline' in p: details += f"- **خط العنق:** <code>${p['neckline']:,.2f}</code>\n"
    if 'resistance_line' in p: details += f"- **خط المقاومة:** <code>${p['resistance_line']:,.2f}</code>\n"
    sup_line = p.get('support_line', p.get('support_line_start', 0))
    if sup_line > 0: details += f"- **خط الدعم:** <code>${sup_line:,.2f}</code>\n"
    details += f"- **الهدف المحسوب:** <code>${p.get('calculated_target', 0):,.2f}</code>"
    return f"<b>🔍 النموذج الكلاسيكي المكتشف</b>\n<b>{name}</b>\n{details}"


def _format_sr(analysis: Dict, current_price: float) -> str:
    # ... (code is unchanged)
    demand_zones = analysis.get('all_demand_zones', [])
    supply_zones = analysis.get('all_supply_zones', [])
    demand_text = ""
    if demand_zones:
        for z in demand_zones[:2]:
            demand_text += f"- منطقة طلب {z.get('strength_text', 'عادية')}: <code>${z.get('start', 0):,.2f} - ${z.get('end', 0):,.2f}</code>\n"
    else: demand_text = "- <i>لا توجد مناطق طلب واضحة.</i>\n"
    supply_text = ""
    if supply_zones:
        z = supply_zones[0]
        supply_text += f"- منطقة عرض {z.get('strength_text', 'عادية')}: <code>${z.get('start', 0):,.2f} - ${z.get('end', 0):,.2f}</code>\n"
    else: supply_text = "- <i>لا توجد مناطق عرض واضحة.</i>\n"
    return f"<b>🟢 مناطق الطلب والدعوم:</b>\n{demand_text}\n<b>🔴 مناطق العرض والمقاومات:</b>\n{supply_text}"


def _format_timeframe_analysis(result: Dict, priority: int) -> str:
    bot = result.get('bot')
    if not bot: return ""
    rec = bot.final_recommendation
    analysis = bot.analysis_results
    tm = analysis.get('trade_management', {})
    indicators = analysis.get('indicators', {})
    patterns_data = analysis.get('patterns', {})
    trends_data = analysis.get('trends', {})
    fib_data = analysis.get('fibonacci', {})
    sr_data = analysis.get('support_resistance', {})
    current_price = rec.get('current_price', 0)

    timeframe_map = {"1d": "يومي", "4h": "4 ساعات", "1h": "1 ساعة", "30m": "30 دقيقة", "15m": "15 دقيقة", "5m": "5 دقائق", "3m": "3 دقائق", "1m": "دقيقة"}
    timeframe_name = timeframe_map.get(rec.get('timeframe', 'N/A'), rec.get('timeframe', 'N/A'))
    priority_icons = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]
    icon = priority_icons[priority] if priority < len(priority_icons) else "🔹"

    # --- Section 1: Basic Data ---
    main_data = f"""
---
<b>{icon} فريم {timeframe_name} - الأولوية الـ{priority+1}</b>
<b>📈 المعطيات الأساسية</b>
- <b>قوة الإشارة:</b> {rec.get('confidence', 0)}% | {rec.get('main_action', '')}
- <b>نقطة الدخول:</b> <code>${current_price:,.2f}</code>
- <b>مستوى RSI:</b> {indicators.get('rsi', 0.0):.1f}
- <b>مؤشر MACD:</b> {'إيجابي' if indicators.get('macd_is_bullish') else 'سلبي'}
"""

    # --- Section 2: Patterns ---
    patterns_section = _format_patterns_for_timeframe(patterns_data)

    # --- Section 3: Critical Levels (S/R and Fibonacci) ---
    sr_section = _format_sr(sr_data, current_price)

    fib_section = "<b>🌊 مستويات فيبوناتشي:</b>\n"
    retracement_levels = fib_data.get('retracement_levels', [])
    if retracement_levels:
        for level in retracement_levels:
            # Highlight the most relevant fib level acting as support/resistance
            price_diff = abs(level['price'] - current_price) / current_price
            if price_diff < 0.02: # If price is within 2% of the level
                fib_section += f"- <b>{level['level']}: <code>${level['price']:,.2f}</code> (مستوى حالي مهم)</b>\n"
            else:
                fib_section += f"- {level['level']}: <code>${level['price']:,.2f}</code>\n"
    else:
        fib_section += "- <i>لم يتم تحديد مستويات فيبوناتشي.</i>\n"

    critical_levels_section = f"\n<b>🎯 المستويات الحرجة</b>\n{sr_section}{fib_section}"

    # --- Section 4: Positive Indicators ---
    positive_indicators = indicators.get('positive_indicators', [])
    indicators_section = f"\n<b>📊 المؤشرات الفنية الإيجابية ({len(positive_indicators)}/12):</b>\n"
    if positive_indicators:
        for indicator in positive_indicators[:3]: # Show top 3
            indicators_section += f"✅ {indicator}\n"
    else:
        indicators_section += "<i>لا توجد مؤشرات إيجابية قوية حالياً.</i>\n"

    # --- Section 5: Risk Management ---
    found_patterns = patterns_data.get('found_patterns', [])
    first_pattern = found_patterns[0] if found_patterns else None

    goals_section = "\n<b>🎯 أهداف وإدارة المخاطر:</b>\n"
    stop_loss = tm.get('stop_loss', 0)
    if stop_loss > 0:
        goals_section += f"- <b>وقف الخسارة:</b> <code>${stop_loss:,.2f}</code>\n"
        goals_section += f"- <b>الهدف الأول:</b> <code>${tm.get('profit_target', 0):,.2f}</code>\n"
    elif tm.get('conditional_stop_loss', 0) > 0:
        goals_section += f"<i>- 💡 <b>فكرة تداول مشروطة:</b> {tm.get('trade_idea_name', '')}</i>\n"
        entry_label = "الدخول فوق" if "اختراق" in tm.get('trade_idea_name', '') else "الدخول تحت"
        goals_section += f"- <b>{entry_label}:</b> <code>${tm.get('conditional_entry', 0):,.2f}</code>\n"
        goals_section += f"- <b>وقف الخسارة المشروط:</b> <code>${tm.get('conditional_stop_loss', 0):,.2f}</code>\n"
        goals_section += f"- <b>الهدف المشروط:</b> <code>${tm.get('conditional_profit_target', 0):,.2f}</code>\n"

    if first_pattern and 'الهدف من النموذج' not in goals_section:
        goals_section += f"- <b>الهدف من النموذج:</b> <code>${first_pattern.get('calculated_target', 0):,.2f}</code>"

    # --- Section 6: Scenarios ---
    scenarios_section = _format_scenarios(first_pattern, trends_data)

    return main_data + "\n" + patterns_section + critical_levels_section + indicators_section + goals_section + scenarios_section

# ... (rest of the file is unchanged)
def _format_executive_summary(ranked_results: list, current_price: float) -> str:
    if not ranked_results: return ""

    # --- Part 1: Main Recommendation ---
    best_bot = ranked_results[0].get('bot')
    rec = best_bot.final_recommendation
    tm = best_bot.analysis_results.get('trade_management', {})
    
    summary_text = f"""
---
<b>🏆 الملخص التنفيذي الشامل</b>

<b>✅ التوصية الرئيسية:</b>
<b>{rec.get('main_action', '')}</b> بقوة {rec.get('confidence', 0)}% (حسب أفضل فريم: {rec.get('timeframe')})
- <b>الدخول:</b> <code>${current_price:,.2f}</code>
- <b>وقف الخسارة:</b> <code>${tm.get('stop_loss', 0):,.2f}</code>  
- <b>الهدف الأول:</b> <code>${tm.get('profit_target', 0):,.2f}</code>
"""

    # --- Part 2: Classic Patterns Analysis ---
    summary_text += "\n<b>🔍 تحليل النماذج الكلاسيكية:</b>\n"
    timeframe_map = {"1d": "يومي", "4h": "4 ساعات", "1h": "1 ساعة"}
    for r in ranked_results:
        p_data = r['bot'].analysis_results.get('patterns', {})
        tf = r['bot'].final_recommendation.get('timeframe')
        if p_data.get('found_patterns'):
            p = p_data['found_patterns'][0]
            tf_name = timeframe_map.get(tf, tf)
            res_line = p.get('resistance_line', p.get('neckline'))

            summary_text += f"<h4>فريم {tf_name} - {p.get('name', '')}:</h4>"
            summary_text += f"- قوة النموذج: عالية ({p.get('confidence', 0)}% نجاح)\n"
            summary_text += f"- الإجراء: مراقبة كسر <code>${res_line:,.2f}</code>\n"

    # --- Part 3: Recommended Strategy ---
    summary_text += "\n<b>🎯 الاستراتيجية الموصى بها:</b>\n"
    for r in ranked_results:
        p_data = r['bot'].analysis_results.get('patterns', {})
        tf = r['bot'].final_recommendation.get('timeframe')
        if p_data.get('found_patterns'):
            p = p_data['found_patterns'][0]
            tf_name = timeframe_map.get(tf, tf)
            res_line = p.get('resistance_line', p.get('neckline'))
            target = p.get('calculated_target', 0)

            if tf in ['1h', '30m', '15m', '5m', '3m', '1m']:
                summary_text += f"<h4>للمتداولين قصيري المدى ({tf_name}):</h4>"
                summary_text += f"- النموذج المستهدف: {p.get('name', '')}\n"
                summary_text += f"- نقطة الدخول: عند كسر <code>${res_line:,.2f}</code>\n"
                summary_text += f"- الهدف: <code>${target:,.2f}</code>\n"

            if tf in ['4h', '1d']:
                summary_text += f"<h4>للمستثمرين متوسطي/طويلي المدى ({tf_name}):</h4>"
                summary_text += f"- النموذج المستهدف: {p.get('name', '')}\n"
                summary_text += f"- استراتيجية: تجميع عند كسر <code>${res_line:,.2f}</code>\n"
                summary_text += f"- الهدف النهائي: <code>${target:,.2f}</code>\n"

    # --- Part 4: Critical Monitoring Points ---
    summary_text += "\n<b>🚨 نقاط المراقبة الحرجة للنماذج:</b>\n"
    critical_points_up = ""
    critical_points_down = ""
    for r in ranked_results:
        p_data = r['bot'].analysis_results.get('patterns', {})
        tf = r['bot'].final_recommendation.get('timeframe')
        if p_data.get('found_patterns'):
            p = p_data['found_patterns'][0]
            res_line = p.get('resistance_line', p.get('neckline'))
            sup_line = p.get('support_line', p.get('neckline', p.get('support_line_start', 0)))
            if res_line: critical_points_up += f"- <b>فريم {tf}:</b> كسر <code>${res_line:,.2f}</code> (مقاومة النموذج)\n"
            if sup_line: critical_points_down += f"- <b>فريم {tf}:</b> كسر <code>${sup_line:,.2f}</code> (دعم النموذج)\n"

    if critical_points_up: summary_text += "<h4>📈 للصعود:</h4>\n" + critical_points_up
    if critical_points_down: summary_text += "<h4>📉 للهبوط:</h4>\n" + critical_points_down

    return summary_text

def generate_final_report_text(symbol: str, analysis_type: str, ranked_results: list) -> str:
    """Generates the final, detailed, and fully dynamic technical analysis report."""
    if not ranked_results or not any(r.get('success') for r in ranked_results):
        return f"❌ تعذر تحليل {symbol} لجميع الأطر الزمنية المطلوبة."

    successful_results = [r for r in ranked_results if r.get('success')]
    if not successful_results:
        return f"❌ لا توجد بيانات ناجحة لإنشاء تقرير لـ {symbol}."

    first_bot = successful_results[0].get('bot')
    current_price = first_bot.final_recommendation.get('current_price', 0)
    
    report = f"""💎 <b>تحليل فني شامل - {symbol.replace("/", "/")}</b> 💎

📊 <b>معلومات عامة</b>
- <b>المنصة:</b> OKX Exchange
- <b>التاريخ والوقت:</b> {datetime.now().strftime("%Y-%m-%d | %H:%M:%S")}  
- <b>السعر الحالي:</b> <code>${current_price:,.2f}</code>  
- <b>نوع التحليل:</b> {analysis_type}
"""
    canonical_order = ['1d', '4h', '2h', '1h', '30m', '15m', '5m', '3m', '1m']

    def get_sort_key(result):
        timeframe = result['bot'].final_recommendation.get('timeframe', 'N/A')
        return canonical_order.index(timeframe) if timeframe in canonical_order else 99

    sorted_results = sorted(successful_results, key=get_sort_key)

    for i, result in enumerate(sorted_results):
        report += _format_timeframe_analysis(result, priority=i)

    report += _format_executive_summary(sorted_results, current_price)
    
    report += """
---
📝 <b>إخلاء المسؤولية</b>
<i>هذا التحليل مبني على الاستراتيجية الفنية الشاملة. <b>ليس نصيحة استثمارية</b> ويجب إجراء البحث الخاص قبل اتخاذ أي قرارات مالية.</i>
"""
    return report
