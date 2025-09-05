from datetime import datetime
from typing import Dict, List
from positive_indicators_generator import generate_positive_indicators
from config import TRADING_CONFIG

def format_critical_levels(sr_analysis: Dict, current_price: float) -> str:
    """Formats the 'Critical Price Levels' section using the new detailed S/R data."""
    report = "📍 **مستويات السعر الحرجة:**\n"
    supply_zones = sr_analysis.get('all_supply_zones', [])
    demand_zones = sr_analysis.get('all_demand_zones', [])

    report += f"   🔺 **فوق السعر الحالي (${current_price:,.2f}):**\n"
    if not supply_zones:
        report += "      (لا توجد مقاومات واضحة)\n"
    else:
        for zone in supply_zones[:3]:
            report += f"      🔴 مقاومة {zone.get('strength_text', '')}: ${zone.get('start', 0):,.2f} (المسافة: ${zone.get('distance', 0):,.2f})\n"

    report += f"   🔻 **تحت السعر الحالي (${current_price:,.2f}):**\n"
    if not demand_zones:
        report += "      (لا توجد دعوم واضحة)\n"
    else:
        for zone in demand_zones[:3]:
            report += f"      🟢 دعم {zone.get('strength_text', '')}: ${zone.get('end', 0):,.2f} (المسافة: ${zone.get('distance', 0):,.2f})\n"
    return report

def format_positive_indicators(analysis_results: Dict, current_price: float) -> str:
    """Formats the 'Positive Indicators' list by calling the generator."""
    indicators = generate_positive_indicators(analysis_results, current_price)
    report = f"📈 **المؤشرات الإيجابية:** ({len(indicators)}/7)\n"
    if not indicators:
        report += "      (لا توجد مؤشرات إيجابية واضحة حالياً)\n"
    else:
        for indicator in indicators:
            report += f"      {indicator}\n"
    return report

def generate_executive_summary(ranked_results: list, current_price: float) -> str:
    """Generates the final executive summary by analyzing data across all timeframes."""
    summary = "\n\n🏆 **الملخص التنفيذي للاستراتيجية** 🏆\n"
    best_result = ranked_results[0] if ranked_results else None
    if best_result:
        rec = best_result['bot'].final_recommendation
        tm = best_result['bot'].analysis_results.get('trade_management', {})
        summary += f"\n✅ **التوصية المثلى** (من فريم {rec.get('timeframe', 'N/A')}):\n"
        summary += f"   📊 {rec.get('main_action', '')} بقوة {rec.get('confidence', 0)}%\n"
        summary += f"   🎯 دخول: ${tm.get('entry_price', 0):,.2f}\n"
        summary += f"   🛑 وقف خسارة: ${tm.get('stop_loss', 0):,.2f}\n"
        summary += f"   🚀 أهداف: ${tm.get('profit_target', 0):,.2f}\n"

    summary += "\n🎯 **التوصية الإستراتيجية الشاملة:**\n"
    long_term_tfs = TRADING_CONFIG.get('TIMEFRAME_GROUPS', {}).get('long', [])
    long_term_scores = [res['bot'].final_recommendation.get('total_score', 0) for res in ranked_results if res.get('success') and res['bot'].final_recommendation.get('timeframe') in long_term_tfs]
    avg_long_score = sum(long_term_scores) / len(long_term_scores) if long_term_scores else 0
    if avg_long_score >= 5: summary += "   - الفريمات الطويلة تظهر اتجاه صاعد متوسط إلى قوي.\n"
    elif avg_long_score <= -5: summary += "   - الفريمات الطويلة تظهر اتجاه هابط متوسط إلى قوي.\n"
    else: summary += "   - الفريمات الطويلة تظهر اتجاه محايد أو متذبذب.\n"
    summary += "   - إدارة المخاطر ضرورية مع مراقبة مستويات الدعم والمقاومة.\n"

    summary += "\n📊 **توزيع قوة المستويات حسب المسافة من السعر الحالي:**\n"
    all_supports = [z for res in ranked_results if res.get('success') for z in res['bot'].analysis_results.get('support_resistance', {}).get('all_demand_zones', [])]
    all_resistances = [z for res in ranked_results if res.get('success') for z in res['bot'].analysis_results.get('support_resistance', {}).get('all_supply_zones', [])]

    strong_resistances = [r for r in all_resistances if r.get('strength_text') in ["قوية", "عالية جداً"]]
    strong_supports = [s for s in all_supports if s.get('strength_text') in ["قوية", "عالية جداً"]]

    closest_strong_resistance = min(strong_resistances, key=lambda x: x.get('distance', float('inf')), default=None)
    closest_strong_support = min(strong_supports, key=lambda x: x.get('distance', float('inf')), default=None)

    if closest_strong_resistance: summary += f"   🔴 أقرب مقاومة قوية: ${closest_strong_resistance.get('start', 0):,.2f}\n"
    if closest_strong_support: summary += f"   🟢 أقرب دعم قوي: ${closest_strong_support.get('end', 0):,.2f}\n"

    return summary

def generate_full_report(symbol: str, exchange: str, ranked_results: list) -> str:
    """Generates the new, detailed, multi-timeframe report based on the user's template."""
    if not ranked_results or not any(r.get('success') for r in ranked_results):
        return f"❌ تعذر إنشاء تقرير لـ {symbol}."

    all_results_map = {res['bot'].final_recommendation['timeframe']: res for res in ranked_results if res.get('success')}
    if not all_results_map:
        return f"❌ لا توجد بيانات ناجحة لإنشاء تقرير لـ {symbol}."

    best_bot_result = next(res for res in ranked_results if res.get('success'))
    current_price = best_bot_result['bot'].final_recommendation['current_price']

    report = f"💎 تحليل فني شامل - {symbol.replace('/', '-')} 💎\n📊 منصة {exchange.upper()} Exchange 📊\n\n"
    report += f"🕐 **التوقيت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n💰 **السعر الحالي:** ${current_price:,.2f}\n"

    timeframe_titles = {
        "long": "🏗️ استثمار طويل المدى (1D - 4H - 1H) 🏗️",
        "medium": "⚡️ تداول قصير المدى (30M - 15M) ⚡️",
        "short": "🔥 مضاربة سريعة (5M - 3M - 1M) 🔥"
    }

    timeframe_groups = TRADING_CONFIG.get('TIMEFRAME_GROUPS', {})

    # Iterate through the defined groups to maintain order
    for group_key, group_timeframes in timeframe_groups.items():
        group_results = [res for tf, res in all_results_map.items() if tf in group_timeframes]
        if not group_results: continue

        sorted_group = sorted(group_results, key=lambda x: x.get('rank_score', 0), reverse=True)
        report += f"\n\n{timeframe_titles.get(group_key, 'تحليل مخصص')}\n"

        for i, result in enumerate(sorted_group):
            bot = result['bot']
            rec = bot.final_recommendation
            analysis = bot.analysis_results
            priority_icon = ["🥇", "🥈", "🥉"][i] if i < 3 else "🔹"

            report += f"\n{priority_icon} **فريم {rec['timeframe'].upper()} - الأولوية {i+1}**\n"

            tm = analysis.get('trade_management', {})
            sr = analysis.get('support_resistance', {})
            patterns = analysis.get('patterns', {})
            fib = analysis.get('fibonacci', {})
            indicators = analysis.get('indicators', {})

            demand = sr.get('primary_demand_zone')
            supply = sr.get('primary_supply_zone')
            pattern_name = patterns.get('found_patterns', [{}])[0].get('name', "لا يوجد")
            rsi_val = indicators.get('rsi', 0)
            macd_status = "إيجابي" if indicators.get('macd_is_bullish') else "سلبي"
            closest_fib = min(fib.get('retracement_levels', []), key=lambda x: abs(x['price'] - current_price), default={})
            fib_text = f"{closest_fib.get('level', 'N/A')} @ ${closest_fib.get('price', 0):.2f}" if closest_fib else "N/A"

            report += f"📊 قوة الإشارة: {rec.get('confidence', 0)}% | {rec.get('main_action', '')}\n"
            report += f"🎯 نقطة الدخول: ${tm.get('entry_price', current_price):,.2f}\n"
            report += f"🟢 منطقة الطلب: ${demand['start']:,.2f} - ${demand['end']:,.2f}\n" if demand else "🟢 منطقة الطلب: غير محددة\n"
            report += f"🔴 منطقة العرض: ${supply['start']:,.2f} - ${supply['end']:,.2f}\n" if supply else "🔴 منطقة العرض: غير محددة\n\n"
            report += f"🏛️ النموذج الكلاسيكي: {pattern_name}\n"

            report += format_positive_indicators(analysis, current_price)
            report += format_critical_levels(sr, current_price)

            report += f"\n🌊 فيبوناتشي: {fib_text}\n"
            report += f"📊 RSI: {rsi_val:.1f} | MACD: {macd_status}\n"
            report += f"🛑 وقف الخسارة: ${tm.get('stop_loss', 0):,.2f}\n"
            report += f"🎯 الهدف الأول: ${tm.get('profit_target', 0):,.2f}\n"

    report += generate_executive_summary(ranked_results, current_price)
    report += "\n\n*📝 التحليل مبني على الاستراتيجية الشاملة - ليس نصيحة استثمارية*"

    return report
