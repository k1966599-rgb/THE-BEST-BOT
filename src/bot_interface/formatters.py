import math
from typing import List
from src.elliott_wave_engine.core.wave_structure import WaveScenario, WavePattern
from src.utils.config_loader import load_config

def _get_dynamic_price_format(price: float) -> str:
    """
    Determines the number of decimal places to use for formatting based on the price.
    Uses more precision for lower-priced assets.
    """
    if price <= 0: return ",.2f"
    if price >= 100: return ",.2f" # e.g., 12345.67
    if price >= 1: return ",.3f"   # e.g., 2.345

    # For prices < 1, use log10 to find the first significant digit
    num_zeros = math.floor(abs(math.log10(price)))
    # Add 2-3 extra digits of precision
    decimals = num_zeros + 3
    return f",.{decimals}f"

def _format_single_pattern(pattern: WavePattern) -> List[str]:
    """Formats a single wave pattern into a list of report lines."""
    lines = [f"\n--- {pattern.pattern_type} ---"]
    lines.append(f"**الثقة:** {pattern.confidence_score:.1f}%")

    header = f"`{'الموجة':<7}| {'نقطة البداية':<18} | {'نقطة النهاية':<18} | {'التغيير':<10}`"
    separator = f"`-------+--------------------+--------------------+-----------`"
    lines.append("\n" + header)
    lines.append(separator)

    wave_labels = []
    if "Impulse" in pattern.pattern_type or "Diagonal" in pattern.pattern_type:
        wave_labels = ["الموجة 1", "الموجة 2", "الموجة 3", "الموجة 4", "الموجة 5"]
    elif "Zigzag" in pattern.pattern_type or "Flat" in pattern.pattern_type:
        wave_labels = ["الموجة A", "الموجة B", "الموجة C"]
    elif "Triangle" in pattern.pattern_type:
        wave_labels = ["الموجة A", "الموجة B", "الموجة C", "الموجة D", "الموجة E"]

    for i, label in enumerate(wave_labels):
        if i + 1 >= len(pattern.points): break
        p_start, p_end = pattern.points[i], pattern.points[i+1]

        price_format = _get_dynamic_price_format(p_start.price)

        # Format date as DD-Mon (e.g., 07-Apr)
        start_date_str = p_start.time.strftime('%d-%b')
        end_date_str = p_end.time.strftime('%d-%b')

        start_point_str = f"{start_date_str} ${p_start.price:{price_format}}"
        end_point_str = f"{end_date_str} ${p_end.price:{price_format}}"

        change = p_end.price - p_start.price
        change_pct = (change / p_start.price) * 100 if p_start.price != 0 else 0
        change_str = f"{change_pct:+.2f}%"
        row = f"`{label:<7}| {start_point_str:<18} | {end_point_str:<18} | {change_str:<10}`"
        lines.append(row)

    lines.append("\n**قواعد النمط:**")
    for rule in pattern.rules_results:
        status = "✅" if rule.passed else "❌"
        lines.append(f"  {status} {rule.name}")

    lines.append("\n**إرشادات النمط:**")
    for guideline in pattern.guidelines_results:
        status = "👍" if guideline.passed else "👎"
        lines.append(f"  {status} {guideline.name} ({guideline.details})")

    return lines

def format_elliott_wave_report(symbol: str, interval_str: str, scenarios: List[WaveScenario]) -> str:
    """
    Formats a list of wave scenarios into a detailed report, showing the primary
    scenario in full and summarizing alternates.
    """
    if not scenarios:
        return f"**-- التحليل الموجي لـ {symbol} ({interval_str}) --**\n\nلم يتم العثور على أي أنماط موجية واضحة حالياً."

    primary_scenario = scenarios[0]
    report_lines = [f"**-- التحليل الأساسي لـ {symbol} ({interval_str}) --**"]
    report_lines.extend(_format_single_pattern(primary_scenario.primary_pattern))

    alternate_scenarios = scenarios[1:3]
    if alternate_scenarios:
        report_lines.append("\n\n**-- سيناريوهات بديلة --**")
        for i, scenario in enumerate(alternate_scenarios):
            pattern = scenario.primary_pattern
            report_lines.append(f"{i+1}. {pattern.pattern_type} (الثقة: {pattern.confidence_score:.1f}%)")

    return "\n".join(report_lines)

def format_trade_alert(trade_signal: dict, interval_str: str, symbol: str, scenarios: List[WaveScenario]) -> str:
    """
    Formats a trade signal or an analysis event into a concise alert message.
    """
    config = load_config()
    if trade_signal.get('type') == "Analysis":
        pattern = trade_signal.get('pattern')
        details = trade_signal.get('details', 'تم رصد نمط هام.')

        if pattern:
            report_lines = [f"**-- تحليل سياق لـ {symbol} ({interval_str}) --**"]
            report_lines.extend(_format_single_pattern(pattern))
            report_lines.append(f"\n**ملاحظة:** {details}")
            return "\n".join(report_lines)
        else:
            reason = trade_signal.get('reason', 'تحليل سياق')
            return (f"**⚠️ تنبيه تحليلي ⚠️**\n\n"
                    f"**الإطار الزمني:** {interval_str}\n"
                    f"**السبب:** {reason}\n"
                    f"**ملاحظة:** {details}")

    entry_price = trade_signal['entry'] # This is the specific 61.8% level
    entry_zone = trade_signal.get('entry_zone') # This is the (top, bottom) tuple
    stop_loss_price = trade_signal['stop_loss']
    position_size = trade_signal.get('position_size')

    sl_percentage = abs((stop_loss_price - entry_price) / entry_price) * 100

    # Use dynamic formatting for all prices in the alert
    entry_format = _get_dynamic_price_format(entry_price)
    sl_format = _get_dynamic_price_format(stop_loss_price)

    entry_text = ""
    if entry_zone:
        zone_top_format = _get_dynamic_price_format(entry_zone[0])
        zone_bottom_format = _get_dynamic_price_format(entry_zone[1])
        entry_text = (
            f"**منطقة الدخول (Fib 50-61.8%):** بين `${entry_zone[0]:{zone_top_format}}` و `${entry_zone[1]:{zone_bottom_format}}`\n"
            f"**نقطة الدخول الحالية:** `${entry_price:{entry_format}}`\n"
        )
    else:
        entry_text = f"**سعر الدخول المقترح:** ${entry_price:{entry_format}}\n"


    targets_text_lines = []
    hit_targets_indices = trade_signal.get('hit_targets_indices', [])
    for i, target_price in enumerate(trade_signal['targets']):
        is_hit = "✅" if i in hit_targets_indices else ""
        tp_percentage = abs((target_price - entry_price) / entry_price) * 100
        tp_format = _get_dynamic_price_format(target_price)
        targets_text_lines.append(
            f"  - الهدف {i+1}: ${target_price:{tp_format}} (+{tp_percentage:.1f}%) {is_hit}"
        )
    targets_text = "\n".join(targets_text_lines)

    position_size_text = ""
    if position_size:
        asset = symbol.replace("USDT", "")
        account_size = config.get('risk', {}).get('account_size', 'N/A')
        risk_percentage = config.get('risk', {}).get('risk_per_trade', 0) * 100
        position_size_text = (
            f"\n**إدارة المخاطر (بناءً على إعداداتك):**\n"
            f"- حجم الحساب: ${account_size:,.2f}\n"
            f"- نسبة المخاطرة: {risk_percentage:.1f}%\n"
            f"- **حجم الصفقة المقترح:** {position_size:.4f} {asset}\n"
        )

    alternate_scenarios_text = ""
    if scenarios and len(scenarios) > 1:
        alt_pattern = scenarios[1].primary_pattern
        alternate_scenarios_text = (
            f"\n\n**سيناريو بديل:** {alt_pattern.pattern_type} (ثقة: {alt_pattern.confidence_score:.1f}%)"
        )

    # --- NEW: R:R and Confidence Score ---
    rr_ratio = trade_signal.get('rr_ratio')
    confidence_score = trade_signal.get('confidence_score')

    rr_text = f"⚖️ **R:R Ratio:** {rr_ratio:.2f}" if rr_ratio is not None else ""
    confidence_text = f"📈 **الثقة:** {confidence_score:.0f}%" if confidence_score is not None else ""

    alert_text = (
        f"💎 **صفقة جاهزة | {symbol} | {interval_str}** 💎\n\n"
        f"**النمط:** `{trade_signal.get('pattern_type', 'N/A')}`\n"
        f"**السبب:** {trade_signal.get('reason', 'N/A')}\n"
        f"{rr_text}\n"
        f"{confidence_text}\n\n"
        f"{entry_text}"
        f"**وقف الخسارة:** `${stop_loss_price:{sl_format}}` (`-{sl_percentage:.1f}%`)\n"
        f"**الأهداف:**\n{targets_text}"
        f"{position_size_text}"
        f"{alternate_scenarios_text}"
    )
    return alert_text
