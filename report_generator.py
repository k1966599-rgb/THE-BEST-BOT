from datetime import datetime
from typing import Dict, List, Any

def format_timeframe_analysis(result: Dict[str, Any], current_price: float, priority: int) -> str:
    """Formats the detailed analysis for a single timeframe using HTML."""
    bot = result.get('bot')
    if not bot:
        return ""

    rec = bot.final_recommendation or {}
    analysis = bot.analysis_results or {}
    tm = analysis.get('trade_management', {}) or {}
    sr = analysis.get('support_resistance', {}) or {}
    fib = analysis.get('fibonacci', {}) or {}
    indicators = analysis.get('indicators', {}) or {}

    timeframe = rec.get('timeframe', 'N/A')
    signal_strength = rec.get('confidence', 0)
    action = rec.get('main_action', 'انتظار')
    rsi = indicators.get('rsi', 0.0)
    macd_status = "إيجابي" if indicators.get('macd_is_bullish') else "سلبي"

    demand_zones_text = ""
    all_demands = sr.get('all_demand_zones', [])
    if all_demands:
        high_demand = next((z for z in all_demands if z.get('strength_text') == "عالية"), None)
        very_high_demand = next((z for z in all_demands if z.get('strength_text') == "عالية جداً"), None)
        if very_high_demand:
            demand_zones_text += f"- <b>دعم عالي جداً:</b> <code>${very_high_demand.get('end', 0):,.2f}</code> (المسافة: <code>${very_high_demand.get('distance', 0):,.2f}</code>)\n"
        if high_demand:
             demand_zones_text += f"- <b>منطقة طلب عالية:</b> <code>${high_demand.get('start', 0):,.2f} - ${high_demand.get('end', 0):,.2f}</code>\n"
    if not demand_zones_text:
        demand_zones_text = "- <i>غير محددة حالياً</i>\n"

    supply_zones_text = ""
    all_supplies = sr.get('all_supply_zones', [])
    if all_supplies:
        weak_supply = next((z for z in all_supplies if z.get('strength_text') == "ضعيفة"), None)
        if weak_supply:
            supply_zones_text += f"- <b>مقاومة ضعيفة:</b> <code>${weak_supply.get('start', 0):,.2f}</code> (المسافة: <code>${weak_supply.get('distance', 0):,.2f}</code>)\n"
    if not supply_zones_text:
        supply_zones_text = "- <i>غير محددة حالياً</i>\n"

    fib_text = ""
    fib_levels = fib.get('retracement_levels', [])
    if fib_levels:
        fib_23 = next((f for f in fib_levels if f.get('level') == '23.6%'), None)
        fib_38 = next((f for f in fib_levels if f.get('level') == '38.2%'), None)
        if fib_23 and fib_23.get('price', 0) < current_price:
            fib_text += f"- <b>23.6%:</b> <code>${fib_23.get('price', 0):,.2f}</code> (دعم فني)\n"
        if fib_38 and fib_38.get('price', 0) < current_price:
             fib_text += f"- السعر يحتفظ بمستوى <b>38.2%</b> كدعم\n"
    if not fib_text:
        fib_text = "<i>لا توجد مستويات فيبوناتشي مؤثرة حالياً</i>\n"

    positive_indicators = []
    if all_demands and any(d.get('end', 0) < current_price for d in all_demands):
        positive_indicators.append("✅ السعر قريب من منطقة دعم قوية")
    if fib_levels:
        fib_38_support = next((f for f in fib_levels if f.get('level') == '38.2%' and f.get('price', 0) < current_price), None)
        if fib_38_support:
            positive_indicators.append("✅ مستوى فيبوناتشي 38.2% يحتفظ كدعم")
    pos_indicators_text = "\n".join(positive_indicators) if positive_indicators else "❌ لا توجد مؤشرات إيجابية واضحة حالياً"

    bullish_prob, neutral_prob, bearish_prob = 40, 35, 25
    if "شراء" in action:
        bullish_prob, neutral_prob, bearish_prob = 60, 25, 15

    stop_loss = tm.get('stop_loss', 0)
    target1 = tm.get('profit_target', 0)

    priority_icons = ["🥇", "🥈", "🥉"]
    icon = priority_icons[priority] if priority < len(priority_icons) else "🔹"
    action_icon = "🚀" if "شراء" in action else "📈" if "انتظار" in action else "📉"

    report = f"""
<pre>---</pre>
<b>{icon} فريم {timeframe} - الأولوية الـ{priority+1}</b>

<b>📈 المعطيات الأساسية</b>
- <b>قوة الإشارة:</b> {signal_strength}% | {action} {action_icon}
- <b>نقطة الدخول:</b> <code>${tm.get('entry_price', 0):,.2f}</code>
- <b>مستوى RSI:</b> {rsi:.1f}
- <b>مؤشر MACD:</b> {macd_status}

<b>🎯 المستويات الحرجة</b>
<b>🟢 مناطق الطلب والدعوم:</b>
{demand_zones_text}
<b>🔴 مناطق العرض والمقاومات:</b>
{supply_zones_text}
<b>🌊 مستويات فيبوناتشي:</b>
{fib_text}
<b>📊 المؤشرات الفنية الإيجابية ({len(positive_indicators)}/12):</b>
{pos_indicators_text}

<b>🎯 أهداف وإدارة المخاطر:</b>
- <b>وقف الخسارة:</b> <code>${stop_loss:,.2f}</code>
- <b>الهدف الأول:</b> <code>${target1:,.2f}</code>

<b>📋 السيناريوهات المحتملة:</b>

<b>🚀 السيناريو الصاعد (احتمال {bullish_prob}%):</b>
- <b>الهدف التالي:</b> <code>${target1:,.2f}</code>
- إمكانية الوصول لمنطقة <code>${(target1 * 1.02):,.2f}</code>

<b>⚡ السيناريو المحايد (احتمال {neutral_prob}%):</b>
- تداول عرضي لمدة 4-8 ساعات
- انتظار كسر واضح لأحد الحدود

<b>📉 السيناريو الهابط (احتمال {bearish_prob}%):</b>
- في حال كسر دعم <code>${(stop_loss*1.01):,.2f}</code>:
- <b>الهدف الأول:</b> <code>${stop_loss:,.2f}</code> (وقف الخسارة)

<b>📝 ملخص الفريم {timeframe}:</b>
<i>{rec.get('summary', 'لا يوجد ملخص')}</i>
"""
    return report

def generate_executive_summary(ranked_results: list, current_price: float) -> str:
    if not ranked_results: return ""
    best_result_bot = ranked_results[0].get('bot')
    if not best_result_bot: return ""

    rec = best_result_bot.final_recommendation or {}
    tm = best_result_bot.analysis_results.get('trade_management', {}) or {}
    long_term_target = 0
    for r in ranked_results:
        bot = r.get('bot')
        if bot and bot.final_recommendation.get('timeframe') == '1d':
            long_term_target = bot.analysis_results.get('trade_management', {}).get('profit_target', 0)

    report = f"""
<pre>---</pre>
<b>🏆 الملخص التنفيذي الشامل 🏆</b>

<b>✅ التوصية الرئيسية:</b>
<b>{rec.get('main_action', '')}</b> 🚀 بقوة {rec.get('confidence', 0)}% (حسب فريم {rec.get('timeframe', 'N/A')})
- <b>الدخول:</b> <code>${tm.get('entry_price', current_price):,.2f}</code>
- <b>وقف الخسارة:</b> <code>${tm.get('stop_loss', 0):,.2f}</code>
- <b>الهدف الأول:</b> <code>${tm.get('profit_target', 0):,.2f}</code>
- <b>الهدف المتوسط:</b> <code>${long_term_target:,.2f}</code>

<b>🚨 نقاط المراقبة الحرجة:</b>
- <b>📈 للصعود:</b> كسر وإغلاق فوق <code>${tm.get('profit_target', 0):,.2f}</code>
- <b>📉 للهبوط:</b> كسر دعم <code>${tm.get('stop_loss', 0):,.2f}</code>
"""
    return report

def generate_quick_trade_plan(ranked_results: list, current_price: float) -> str:
    if not ranked_results: return ""
    best_result_bot = ranked_results[0].get('bot')
    if not best_result_bot: return ""

    rec = best_result_bot.final_recommendation or {}
    tm = best_result_bot.analysis_results.get('trade_management', {}) or {}
    entry = tm.get('entry_price', 0)
    stop = tm.get('stop_loss', 0)
    target = tm.get('profit_target', 0)
    risk_reward_ratio = (target - entry) / (entry - stop) if (entry - stop) != 0 else 0

    report = f"""
<pre>---</pre>
<b>⚡ خطة التداول السريعة - فريم {rec.get('timeframe', 'N/A')} (الأفضل حالياً)</b>

<b>🎯 القرار السريع:</b>
<b>🟢 {rec.get('main_action', '')} الآن</b> - إشارة قوية {rec.get('confidence', 0)}%

<b>📊 بيانات التنفيذ الفورية:</b>
- <b>💰 الدخول:</b> <code>${entry:,.2f}</code> (السعر الحالي)
- <b>🛑 وقف الخسارة:</b> <code>${stop:,.2f}</code>
- <b>🎯 الهدف السريع:</b> <code>${target:,.2f}</code>
- <b>📈 نسبة المخاطرة للربح:</b> {risk_reward_ratio:.2f}:1
"""
    return report

def generate_final_report_text(symbol: str, analysis_type: str, ranked_results: list) -> str:
    if not ranked_results or not any(r.get('success') for r in ranked_results):
        return f"❌ تعذر إنشاء تقرير لـ {symbol}."

    successful_results = [r for r in ranked_results if r.get('success')]
    if not successful_results:
        return f"❌ لا توجد بيانات ناجحة لإنشاء تقرير لـ {symbol}."

    first_result_bot = successful_results[0].get('bot')
    if not first_result_bot:
        return f"❌ خطأ في بيانات التحليل لـ {symbol}."

    exchange = first_result_bot.config.get('trading', {}).get('EXCHANGE_ID', 'OKX')
    current_price = first_result_bot.final_recommendation.get('current_price', 0)

    symbol_formatted = symbol.replace("/", "-")
    current_time = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")

    report = f"""<b>💎 تحليل فني شامل - {symbol_formatted} 💎</b>

<b>📊 معلومات عامة</b>
- <b>المنصة:</b> {exchange} Exchange
- <b>التاريخ والوقت:</b> {current_time}
- <b>السعر الحالي:</b> <code>${current_price:,.2f}</code>
- <b>نوع التحليل:</b> {analysis_type}
"""

    for i, result in enumerate(successful_results):
        report += format_timeframe_analysis(result, current_price, priority=i)

    report += generate_executive_summary(successful_results, current_price)
    report += generate_quick_trade_plan(successful_results, current_price)

    report += """
<pre>---</pre>
<b>📝 إخلاء المسؤولية</b>

<i>هذا التحليل مبني على الاستراتيجية الفنية الشاملة للترندات والقنوات السعرية والمؤشرات الفنية والنماذج الكلاسيكية ومستويات فيبوناتشي ومناطق العرض والطلب والدعوم والمقاومات. <b>ليس نصيحة استثمارية</b> ويجب إجراء البحث الخاص قبل اتخاذ أي قرارات مالية.</i>
"""
    return report
