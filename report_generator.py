from datetime import datetime
import requests

def get_coingecko_price(symbol: str) -> float:
    """Fetches the current price from CoinGecko for verification."""
    try:
        # Simple mapping for common symbols
        base_currency = symbol.split('/')[0].lower()
        id_map = {
            'btc': 'bitcoin', 'eth': 'ethereum', 'sol': 'solana',
            'xrp': 'ripple', 'doge': 'dogecoin', 'ada': 'cardano'
        }
        coin_id = id_map.get(base_currency)
        if not coin_id: return None

        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data[coin_id]['usd']
    except Exception as e:
        print(f"Could not fetch price from CoinGecko: {e}")
        return None

def generate_full_report(symbol: str, exchange: str, ranked_results: list) -> str:
    """
    Generates the final, complex, multi-timeframe report with all user feedback incorporated.
    """
    if not ranked_results or not ranked_results[0]['success']:
        return f"❌ تعذر إنشاء تقرير لـ {symbol}."

    all_results_map = {res['bot'].final_recommendation['timeframe']: res['bot'] for res in ranked_results if res['success']}
    if not all_results_map:
        return f"❌ فشلت جميع التحليلات لـ {symbol}."

    current_price_exchange = list(all_results_map.values())[0].final_recommendation['current_price']
    coingecko_price = get_coingecko_price(symbol)

    # --- HEADER ---
    report = (
        f"╔═══════════════════════════════════════════════════╗\n"
        f"║           💎 تحليل فني شامل - {symbol} 💎           ║\n"
        f"║              📊 منصة {exchange.upper()} Exchange 📊               ║\n"
        f"╚═══════════════════════════════════════════════════╝\n\n"
        f"🕐 **التوقيت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"💰 **السعر الحالي ({exchange.upper()}):** ${current_price_exchange:,.2f}\n"
    )
    if coingecko_price:
        report += f"🌍 **السعر العالمي (CoinGecko):** ${coingecko_price:,.2f}\n"

    # --- TIMEFRAME SECTIONS ---
    timeframe_groups = {
        "🏗️ **استثمار طويل المدى** (1D - 4H - 1H) 🏗️": ['1d', '4h', '1h'],
        "⚡ **تداول قصير المدى** (30M - 15M) ⚡": ['30m', '15m'],
        "🔥 **مضاربة سريعة** (5M - 3M - 1M) 🔥": ['5m', '3m', '1m']
    }

    for title, timeframes in timeframe_groups.items():
        group_results = [res for tf, res in all_results_map.items() if tf in timeframes]
        if not group_results: continue

        report += f"\n\n{title}\n"
        sorted_group = sorted(group_results, key=lambda x: (abs(x.final_recommendation.get('total_score',0))), reverse=True)

        for i, bot_instance in enumerate(sorted_group):
            rec = bot_instance.final_recommendation
            analysis = bot_instance.analysis_results
            timeframe = rec['timeframe']
            priority_icon = ["🥇", "🥈", "🥉"][i] if i < 3 else "🔹"

            report += f"\n{priority_icon} **فريم {timeframe.upper()}** - الأولوية {i+1}\n"
            report += "┌─────────────────────────────────────────────────┐\n"

            tm = analysis.get('trade_management', {})
            sr = analysis.get('support_resistance', {})

            report += f"│ 📊 قوة الإشارة: {rec.get('confidence', 0)}% | {rec.get('main_action', '')}\n"
            report += f"│ 🎯 نقطة الدخول: ${tm.get('entry_price', rec.get('current_price', 0)):,.2f}\n"

            demand = sr.get('primary_demand_zone')
            supply = sr.get('primary_supply_zone')
            report += f"│ 🟢 منطقة الطلب: ${demand['start']:,.2f} - ${demand['end']:,.2f}\n" if demand else "│ 🟢 منطقة الطلب: غير محددة\n"
            report += f"│ 🔴 منطقة العرض: ${supply['start']:,.2f} - ${supply['end']:,.2f}\n" if supply else "│ 🔴 منطقة العرض: غير محددة\n"
            report += f"│ 🛑 وقف الخسارة: ${tm.get('stop_loss', 0):,.2f}\n"
            report += f"│ 🎯 الهدف الأول: ${tm.get('profit_target', 0):,.2f}\n"
            report += "└─────────────────────────────────────────────────┘"

    # --- EXECUTIVE SUMMARY ---
    report += "\n\n🏆 **الملخص التنفيذي للاستراتيجية** 🏆\n\n"
    best_bot = list(all_results_map.values())[0]
    best_rec = best_bot.final_recommendation
    best_tm = best_bot.analysis_results.get('trade_management', {})

    report += f"✅ **التوصية المثلى (من فريم {best_rec['timeframe']}):**\n"
    report += f"   📊 {best_rec['main_action']} بقوة {best_rec['confidence']}%\n"
    report += f"   🎯 دخول: ${best_tm.get('entry_price', 0):,.2f}\n"
    report += f"   🛑 وقف خسارة: ${best_tm.get('stop_loss', 0):,.2f}\n"
    report += f"   🚀 أهداف: ${best_tm.get('profit_target', 0):,.2f}\n"

    return report
