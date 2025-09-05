import re
from datetime import datetime
from typing import Dict, List, Any

def escape_markdown_v2(text: str) -> str:
    """Escapes characters for Telegram's MarkdownV2 parser."""
    if not isinstance(text, str):
        text = str(text)
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def format_timeframe_analysis(result: Dict[str, Any], current_price: float, priority: int) -> str:
    """Formats the detailed analysis for a single timeframe."""
    bot = result.get('bot')
    if not bot:
        return ""

    rec = bot.final_recommendation
    analysis = bot.analysis_results
    tm = analysis.get('trade_management', {})
    sr = analysis.get('support_resistance', {})
    fib = analysis.get('fibonacci', {})
    indicators = analysis.get('indicators', {})

    timeframe = rec.get('timeframe', 'N/A')
    signal_strength = rec.get('confidence', 0)
    action = rec.get('main_action', 'انتظار')
    entry_point = tm.get('entry_price', current_price)
    rsi = indicators.get('rsi', 0.0)
    macd_status = "إيجابي" if indicators.get('macd_is_bullish') else "سلبي"

    # --- Critical Levels ---
    demand_zones_text = ""
    all_demands = sr.get('all_demand_zones', [])
    if all_demands:
        high_demand = next((z for z in all_demands if z.get('strength_text') == "عالية"), None)
        very_high_demand = next((z for z in all_demands if z.get('strength_text') == "عالية جداً"), None)
        if very_high_demand:
            demand_zones_text += f"- *دعم عالي جداً:* `${very_high_demand['end']:,.2f}` \\(المسافة: `${very_high_demand['distance']:,.2f}`\\)\n"
        if high_demand:
             demand_zones_text += f"- *منطقة طلب عالية:* `${high_demand['start']:,.2f} - ${high_demand['end']:,.2f}`\n"
    if not demand_zones_text:
        demand_zones_text = "- *غير محددة حالياً*\n"

    supply_zones_text = ""
    all_supplies = sr.get('all_supply_zones', [])
    if all_supplies:
        weak_supply = next((z for z in all_supplies if z.get('strength_text') == "ضعيفة"), None)
        if weak_supply:
            supply_zones_text += f"- *مقاومة ضعيفة:* `${weak_supply['start']:,.2f}` \\(المسافة: `${weak_supply['distance']:,.2f}`\\)\n"
    if not supply_zones_text:
        supply_zones_text = "- *غير محددة حالياً*\n"

    # --- Fibonacci Levels ---
    fib_text = ""
    fib_levels = fib.get('retracement_levels', [])
    if fib_levels:
        fib_23 = next((f for f in fib_levels if f['level'] == '23.6%'), None)
        fib_38 = next((f for f in fib_levels if f['level'] == '38.2%'), None)
        if fib_23 and fib_23['price'] < current_price:
            fib_text += f"- *23\\.6%:* `${fib_23['price']:,.2f}` \\(دعم فني\\)\n"
        if fib_38 and fib_38['price'] < current_price:
             fib_text += f"- السعر يحتفظ بمستوى *38\\.2%* كدعم\n"
    if not fib_text:
        fib_text = "لا توجد مستويات فيبوناتشي مؤثرة حالياً\n"

    # --- Positive Indicators ---
    # This is a simplified version; a more complex mapping can be done.
    positive_indicators = []
    if any(d['end'] < current_price for d in all_demands):
        positive_indicators.append("✅ السعر قريب من منطقة دعم قوية")
    if fib_38 and fib_38['price'] < current_price:
        positive_indicators.append("✅ مستوى فيبوناتشي 38\\.2% يحتفظ كدعم")

    pos_indicators_text = "\n".join(positive_indicators) if positive_indicators else "❌ لا توجد مؤشرات إيجابية واضحة حالياً"

    # --- Scenarios (Simplified Logic) ---
    bullish_prob, neutral_prob, bearish_prob = 40, 35, 25 # Default
    if "شراء" in action:
        bullish_prob = 60
        neutral_prob = 25
        bearish_prob = 15

    # --- Stop Loss & Targets ---
    stop_loss = tm.get('stop_loss', 0)
    target1 = tm.get('profit_target', 0)

    # --- Icons ---
    priority_icons = ["🥇", "🥈", "🥉"]
    icon = priority_icons[priority] if priority < len(priority_icons) else "🔹"

    action_icon = "🚀" if "شراء" in action else "📈" if "انتظار" in action else "📉"

    # --- Build Report ---
    report = f"""
---

## {icon} فريم {escape_markdown_v2(timeframe)} \\- الأولوية الـ{priority+1}

### 📈 المعطيات الأساسية
- *قوة الإشارة:* {signal_strength}% \\| {escape_markdown_v2(action)} {action_icon}
- *نقطة الدخول:* `${entry_point:,.2f}`
- *مستوى RSI:* {rsi:.1f}
- *مؤشر MACD:* {escape_markdown_v2(macd_status)}

### 🎯 المستويات الحرجة
#### 🟢 مناطق الطلب والدعوم:
{demand_zones_text}
#### 🔴 مناطق العرض والمقاومات:
{supply_zones_text}
#### 🌊 مستويات فيبوناتشي:
{fib_text}

### 📊 المؤشرات الفنية الإيجابية ({len(positive_indicators)}/12):
{pos_indicators_text}

### 🎯 أهداف وإدارة المخاطر:
- *وقف الخسارة:* `${stop_loss:,.2f}`
- *الهدف الأول:* `${target1:,.2f}`

### 📋 السيناريوهات المحتملة:

#### 🚀 السيناريو الصاعد (احتمال {bullish_prob}%):
- *الهدف التالي:* `${target1:,.2f}`
- إمكانية الوصول لمنطقة `${(target1 * 1.02):,.2f}`

#### ⚡ السيناريو المحايد (احتمال {neutral_prob}%):
- تداول عرضي لمدة 4\\-8 ساعات
- انتظار كسر واضح لأحد الحدود

#### 📉 السيناريو الهابط (احتمال {bearish_prob}%):
- في حال كسر دعم `${(stop_loss*1.01):,.2f}`:
- *الهدف الأول:* `${stop_loss:,.2f}` \\(وقف الخسارة\\)

### 📝 ملخص الفريم {escape_markdown_v2(timeframe)}:
{escape_markdown_v2(rec.get('summary', 'لا يوجد ملخص'))}
"""
    return report

def generate_executive_summary(ranked_results: list, current_price: float) -> str:
    if not ranked_results:
        return ""

    best_result = ranked_results[0]['bot']
    rec = best_result.final_recommendation
    tm = best_result.analysis_results.get('trade_management', {})

    # Extract targets from different timeframes for a richer summary
    long_term_target = 0
    for r in ranked_results:
        if r['bot'].final_recommendation.get('timeframe') == '1d':
            long_term_target = r['bot'].analysis_results.get('trade_management', {}).get('profit_target', 0)

    report = f"""
---

## 🏆 الملخص التنفيذي الشامل

### ✅ التوصية الرئيسية:
**{escape_markdown_v2(rec.get('main_action', ''))}** 🚀 بقوة {rec.get('confidence', 0)}% \\(حسب فريم {escape_markdown_v2(rec.get('timeframe', 'N/A'))}\\)
- *الدخول:* `${tm.get('entry_price', current_price):,.2f}`
- *وقف الخسارة:* `${tm.get('stop_loss', 0):,.2f}`
- *الهدف الأول:* `${tm.get('profit_target', 0):,.2f}`
- *الهدف المتوسط:* `${long_term_target:,.2f}`

### 🚨 نقاط المراقبة الحرجة:
- *📈 للصعود:* كسر وإغلاق فوق `${tm.get('profit_target', 0):,.2f}`
- *📉 للهبوط:* كسر دعم `${tm.get('stop_loss', 0):,.2f}`
"""
    return report

def generate_quick_trade_plan(ranked_results: list, current_price: float) -> str:
    if not ranked_results:
        return ""

    best_result = ranked_results[0]['bot']
    rec = best_result.final_recommendation
    tm = best_result.analysis_results.get('trade_management', {})

    risk_reward_ratio = (tm.get('profit_target', 0) - tm.get('entry_price', 1)) / (tm.get('entry_price', 1) - tm.get('stop_loss', 1)) if (tm.get('entry_price', 1) - tm.get('stop_loss', 1)) != 0 else 0

    report = f"""
---

## ⚡ خطة التداول السريعة \\- فريم {escape_markdown_v2(rec.get('timeframe', 'N/A'))} \\(الأفضل حالياً\\)

### 🎯 القرار السريع:
**🟢 {escape_markdown_v2(rec.get('main_action', ''))} الآن** \\- إشارة قوية {rec.get('confidence', 0)}%

### 📊 بيانات التنفيذ الفورية:
- *💰 الدخول:* `${tm.get('entry_price', current_price):,.2f}` \\(السعر الحالي\\)
- *🛑 وقف الخسارة:* `${tm.get('stop_loss', 0):,.2f}`
- *🎯 الهدف السريع:* `${tm.get('profit_target', 0):,.2f}`
- *📈 نسبة المخاطرة للربح:* {risk_reward_ratio:.2f}:1
"""
    return report

def generate_final_report_text(symbol: str, analysis_type: str, ranked_results: list) -> str:
    """
    Generates the comprehensive, user-specified technical analysis report.
    """
    if not ranked_results or not any(r.get('success') for r in ranked_results):
        return f"❌ تعذر إنشاء تقرير لـ {symbol}\\."

    successful_results = [r for r in ranked_results if r.get('success')]
    if not successful_results:
        return f"❌ لا توجد بيانات ناجحة لإنشاء تقرير لـ {symbol}\\."

    # Use the first successful result to get exchange and current price
    first_result = successful_results[0]['bot']
    exchange = first_result.config['trading'].get('EXCHANGE_ID', 'OKX')
    current_price = first_result.final_recommendation.get('current_price', 0)

    # --- Main Info ---
    symbol_formatted = escape_markdown_v2(symbol.replace("/", "\\-"))
    current_time = escape_markdown_v2(datetime.now().strftime("%Y\\-%m\\-%d | %H:%M:%S"))

    report = f"""# 💎 تحليل فني شامل \\- {symbol_formatted} 💎

## 📊 معلومات عامة
- *المنصة:* {escape_markdown_v2(exchange)} Exchange
- *التاريخ والوقت:* {current_time}
- *السعر الحالي:* `${current_price:,.2f}`
- *نوع التحليل:* {escape_markdown_v2(analysis_type)}
"""

    # --- Timeframe Analysis ---
    for i, result in enumerate(successful_results):
        report += format_timeframe_analysis(result, current_price, priority=i)

    # --- Summaries ---
    report += generate_executive_summary(successful_results, current_price)
    report += generate_quick_trade_plan(successful_results, current_price)

    # --- Disclaimer ---
    report += """
---

## 📝 إخلاء المسؤولية

هذا التحليل مبني على الاستراتيجية الفنية الشاملة للترندات والقنوات السعرية والمؤشرات الفنية والنماذج الكلاسيكية ومستويات فيبوناتشي ومناطق العرض والطلب والدعوم والمقاومات\\. **ليس نصيحة استثمارية** ويجب إجراء البحث الخاص قبل اتخاذ أي قرارات مالية\\.
"""
    return report
