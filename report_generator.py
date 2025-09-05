from datetime import datetime
from typing import Dict, List, Any

def _format_scenarios(p: Dict, trend_analysis: Dict) -> str:
    if not p: return ""
    name = p.get('name', '')
    base_confidence = p.get('confidence', 60)
    is_trending = trend_analysis.get('is_trending', False)

    # Adjust probability based on trend confirmation
    if is_trending:
        primary_prob = min(base_confidence + 10, 85) # Cap at 85%
    else:
        primary_prob = base_confidence - 5

    neutral_prob = 15
    counter_prob = 100 - primary_prob - neutral_prob

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
    patterns_section = _format_patterns_for_timeframe(patterns_data)
    sr_section = _format_sr(analysis.get('support_resistance', {}), rec.get('current_price', 0))

    found_patterns = patterns_data.get('found_patterns', [])
    # Pass trend analysis data to the scenarios function
    scenarios_section = _format_scenarios(found_patterns[0] if found_patterns else None, trends_data)

    goals_section = f"""
<b>🎯 أهداف وإدارة المخاطر:</b>
- <b>وقف الخسارة:</b> <code>${tm.get('stop_loss', 0):,.2f}</code>
- <b>الهدف الأول:</b> <code>${tm.get('profit_target', 0):,.2f}</code>
"""
    if found_patterns:
        goals_section += f"- <b>الهدف من النموذج:</b> <code>${found_patterns[0].get('calculated_target', 0):,.2f}</code>"

    return main_data + "\n" + patterns_section + "\n<b>🎯 المستويات الحرجة</b>\n" + sr_section + goals_section + scenarios_section

# ... (rest of the file is unchanged)
def _format_executive_summary(ranked_results: list, current_price: float) -> str:
    if not ranked_results: return ""
    best_bot = ranked_results[0].get('bot')
    rec, tm = best_bot.final_recommendation, best_bot.analysis_results.get('trade_management', {})
    
    summary_text = f"""
---
<b>🏆 الملخص التنفيذي الشامل</b>

<b>✅ التوصية الرئيسية:</b>
<b>{rec.get('main_action', '')}</b> 🚀 بقوة {rec.get('confidence', 0)}% (حسب أفضل فريم)
- <b>الدخول:</b> <code>${tm.get('entry_price', current_price):,.2f}</code>
- <b>وقف الخسارة:</b> <code>${tm.get('stop_loss', 0):,.2f}</code>  
- <b>الهدف الأول:</b> <code>${tm.get('profit_target', 0):,.2f}</code>
"""
    summary_text += "\n<b>🎯 الاستراتيجية الموصى بها:</b>\n"
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
