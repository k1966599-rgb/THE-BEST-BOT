from datetime import datetime
from typing import Dict, List, Any

def _format_scenarios(p: Dict, trend_analysis: Dict) -> str:
    if not p: return ""
    name = p.get('name', '')

    # The confidence score is now fully dynamic from classic_patterns.py
    primary_prob = p.get('confidence', 60)

    # Set a smaller, fixed neutral probability
    neutral_prob = 10

    # Counter probability is the remainder
    counter_prob = 100 - primary_prob - neutral_prob

    # Ensure counter_prob is not negative if confidence is very high
    if counter_prob < 0:
        counter_prob = 5
        neutral_prob = 100 - primary_prob - counter_prob

    res_line = p.get('resistance_line', p.get('neckline', 0))
    sup_line = p.get('support_line', p.get('neckline', 0))
    if sup_line == 0: sup_line = p.get('support_line_start', 0)
    target = p.get('calculated_target', 0)

    text = "\n<b>📋 السيناريوهات المحتملة:</b>\n"
    if "مثلث صاعد" in name or "علم صاعد" in name or "قاع مزدوج" in name: # Bullish Scenarios
        text += f"🚀 <b>السيناريو الصاعد (احتمال {primary_prob}%):</b> كسر المقاومة عند <code>${res_line:,.2f}</code> سيؤدي إلى هدف <code>${target:,.2f}</code>.\n"
        text += f"⚡ <b>السيناريو المحايد (احتمال {neutral_prob}%):</b> التداول العرضي بين الدعم والمقاومة.\n"
        text += f"📉 <b>السيناريو الهابط (احتمال {counter_prob}%):</b> كسر الدعم عند <code>${sup_line:,.2f}</code> يلغي النموذج الإيجابي.\n"
    elif "قمة مزدوجة" in name or "رأس وكتفين" in name: # Bearish Scenarios
        text += f"📉 <b>السيناريو الهابط (احتمال {primary_prob}%):</b> كسر الدعم عند <code>${sup_line:,.2f}</code> سيؤدي إلى هدف <code>${target:,.2f}</code>.\n"
        text += f"⚡ <b>السيناريو المحايد (احتمال {neutral_prob}%):</b> التداول العرضي بين الدعم والمقاومة.\n"
        text += f"🚀 <b>السيناريو الصاعد (احتمال {counter_prob}%):</b> اختراق المقاومة عند <code>${res_line:,.2f}</code> يلغي النموذج السلبي.\n"
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
    rec, analysis = bot.final_recommendation, bot.analysis_results
    tm, indicators, patterns_data, trends_data = analysis.get('trade_management', {}), analysis.get('indicators', {}), analysis.get('patterns', {}), analysis.get('trends', {})

    timeframe_map = {"1d": "يومي", "4h": "4 ساعات", "1h": "1 ساعة", "30m": "30 دقيقة", "15m": "15 دقيقة", "5m": "5 دقائق", "3m": "3 دقائق", "1m": "دقيقة"}
    timeframe_name = timeframe_map.get(rec.get('timeframe', 'N/A'), rec.get('timeframe', 'N/A'))
    priority_icons = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]
    icon = priority_icons[priority] if priority < len(priority_icons) else "🔹"

    main_data = f"""
---
<b>{icon} فريم {timeframe_name} - الأولوية الـ{priority+1}</b>
<b>📈 المعطيات الأساسية</b>
- <b>قوة الإشارة:</b> {rec.get('confidence', 0)}% | {rec.get('main_action', '')}
"""
    # Add Divergence Information
    rsi_div = indicators.get('rsi_divergence')
    macd_div = indicators.get('macd_divergence')
    if rsi_div or macd_div:
        main_data += "<b>⚠️ إشارات انعكاس (Divergence):</b>\n"
        if rsi_div:
            main_data += f"- <b>RSI:</b> {rsi_div.get('type', '')}\n"
        if macd_div:
            main_data += f"- <b>MACD:</b> {macd_div.get('type', '')}\n"

    patterns_section = _format_patterns_for_timeframe(patterns_data)
    sr_section = _format_sr(analysis.get('support_resistance', {}), rec.get('current_price', 0))

    found_patterns = patterns_data.get('found_patterns', [])
    # Safely get the first pattern, or None if the list is empty
    first_pattern = found_patterns[0] if found_patterns else None

    # Pass trend analysis data to the scenarios function
    scenarios_section = _format_scenarios(first_pattern, trends_data)

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
    else:
        goals_section += "- <b>وقف الخسارة:</b> <code>$0.00</code>\n"
        goals_section += "- <b>الهدف الأول:</b> <code>$0.00</code>\n"

    if first_pattern and 'الهدف من النموذج' not in goals_section:
        goals_section += f"- <b>الهدف من النموذج:</b> <code>${first_pattern.get('calculated_target', 0):,.2f}</code>"

    return main_data + "\n" + patterns_section + "\n<b>🎯 المستويات الحرجة</b>\n" + sr_section + goals_section + scenarios_section

# ... (rest of the file is unchanged)
def _analyze_signal_conflict(ranked_results: list) -> str:
    """
    Analyzes conflicts between the main actions ('Buy', 'Sell', 'Wait') of different timeframes.
    """
    if len(ranked_results) < 2:
        return "- لا يوجد سياق كافٍ للمقارنة بين الأطر الزمنية."

    # Define timeframe categories
    long_term_tfs = ['1d', '4h']
    short_term_tfs = ['1h', '30m', '15m', '5m', '3m', '1m']

    # Get the main action for the highest-ranked long-term and short-term timeframes
    long_term_signal = next((r['bot'].final_recommendation.get('main_action', '') for r in ranked_results if r['bot'].final_recommendation.get('timeframe') in long_term_tfs), None)
    short_term_signal = next((r['bot'].final_recommendation.get('main_action', '') for r in ranked_results if r['bot'].final_recommendation.get('timeframe') in short_term_tfs), None)

    if not long_term_signal or not short_term_signal:
        return "- ✅ لا يوجد تعارض واضح في الإشارات بين الأطر الزمنية المختلفة."

    # Analyze conflicts
    is_long_bullish = 'شراء' in long_term_signal
    is_long_bearish = 'بيع' in long_term_signal
    is_short_bullish = 'شراء' in short_term_signal
    is_short_bearish = 'بيع' in short_term_signal

    if is_long_bullish and is_short_bearish:
        return "- 💡 **سياق مهم:** الاتجاه العام على المدى الطويل صاعد، بينما تظهر الأطر القصيرة إشارات ضعف أو جني أرباح. قد يكون هذا مجرد تراجع مؤقت ومناسبة جيدة للشراء من مستويات أقل."
    if is_long_bearish and is_short_bullish:
        return "- 💡 **سياق مهم:** الاتجاه العام على المدى الطويل هابط، بينما تظهر الأطر القصيرة إشارات ارتداد. قد يكون هذا مجرد صعود تصحيحي مؤقت قبل استئناف الهبوط."

    # Check for alignment
    if (is_long_bullish and is_short_bullish) or (is_long_bearish and is_short_bearish):
        return "- ✅ **تأكيد:** الإشارات متوافقة على الأطر الزمنية الطويلة والقصيرة، مما يعزز قوة الاتجاه الحالي."

    return "- ❔ **ملاحظة:** الإشارات محايدة أو غير حاسمة على بعض الأطر الزمنية. يتطلب المزيد من المراقبة."


def _format_executive_summary(ranked_results: list, current_price: float) -> str:
    if not ranked_results: return ""
    best_bot = ranked_results[0].get('bot')
    rec, tm = best_bot.final_recommendation, best_bot.analysis_results.get('trade_management', {})
    
    summary_text = f"""
---
<b>🏆 الملخص التنفيذي الشامل</b>

<b>✅ التوصية الرئيسية:</b>
<b>{rec.get('main_action', '')}</b> 🚀 بقوة {rec.get('confidence', 0)}% (حسب أفضل فريم)
"""
    # Logic to show conditional or actual trade levels in summary
    if tm.get('stop_loss', 0) > 0:
        summary_text += f"""- <b>الدخول:</b> <code>${tm.get('entry_price', current_price):,.2f}</code>
- <b>وقف الخسارة:</b> <code>${tm.get('stop_loss', 0):,.2f}</code>  
- <b>الهدف الأول:</b> <code>${tm.get('profit_target', 0):,.2f}</code>
"""
    elif tm.get('conditional_stop_loss', 0) > 0:
        summary_text += f"""- 💡 <b>فكرة مشروطة:</b> {tm.get('trade_idea_name', '')}
- <b>الدخول عند:</b> <code>${tm.get('conditional_entry', 0):,.2f}</code>
- <b>وقف الخسارة:</b> <code>${tm.get('conditional_stop_loss', 0):,.2f}</code>
- <b>الهدف:</b> <code>${tm.get('conditional_profit_target', 0):,.2f}</code>
"""
    else:
        summary_text += f"""- <b>الدخول:</b> <code>${current_price:,.2f}</code>
- <b>وقف الخسارة:</b> <code>$0.00</code>
- <b>الهدف الأول:</b> <code>$0.00</code>
"""

    summary_text += "\n<b>🎯 السياق الفني:</b>\n"
    summary_text += _analyze_signal_conflict(ranked_results)

    summary_text += "\n\n<b>🎯 الاستراتيجية الموصى بها:</b>\n"
    summary_text += """- **للمدى القصير (فريمات دقائق/ساعة):** التركيز على أهداف الفريمات الأصغر ومراقبة نقاط الكسر لتأكيد النماذج.
- **للمدى الطويل (فريمات 4 ساعات/يومي):** استخدام الفريمات الأصغر لتحديد نقاط دخول دقيقة للنماذج الكبيرة.
"""
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
            if res_line: critical_points_up += f"- **فريم {tf}:** كسر <code>${res_line:,.2f}</code>\n"
            if sup_line: critical_points_down += f"- **فريم {tf}:** كسر <code>${sup_line:,.2f}</code>\n"
    if critical_points_up: summary_text += "📈 **للصعود:**\n" + critical_points_up
    if critical_points_down: summary_text += "📉 **للهبوط:**\n" + critical_points_down

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
