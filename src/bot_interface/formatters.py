from typing import List
from src.elliott_wave_engine.wave_structure import WaveScenario, WavePattern

def _format_single_pattern(pattern: WavePattern) -> List[str]:
    """Formats a single wave pattern into a list of report lines."""
    lines = [f"\n--- {pattern.pattern_type} ---"]
    lines.append(f"**الثقة:** {pattern.confidence_score:.1f}%")

    header = f"`{'الموجة':<7}| {'نقطة البداية':<12} | {'نقطة النهاية':<12} | {'التغيير':<10}`"
    separator = f"`-------+--------------+--------------+-----------`"
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
        start_price_str = f"${p_start.price:,.2f}"
        end_price_str = f"${p_end.price:,.2f}"
        change = p_end.price - p_start.price
        change_pct = (change / p_start.price) * 100 if p_start.price != 0 else 0
        change_str = f"{change_pct:+.2f}%"
        row = f"`{label:<7}| {start_price_str:<12} | {end_price_str:<12} | {change_str:<10}`"
        lines.append(row)

    lines.append("\n**قواعد النمط:**")
    for rule in pattern.rules_results:
        status = "✅" if rule.passed else "❌"
        lines.append(f"  {status} {rule.name}")

    lines.append("\n**إرشادات النمط:**")
    for guideline in pattern.guideline_results:
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

    # The first scenario is the primary one
    primary_scenario = scenarios[0]
    report_lines = [f"**-- التحليل الأساسي لـ {symbol} ({interval_str}) --**"]
    report_lines.extend(_format_single_pattern(primary_scenario.primary_pattern))

    # Add alternate scenarios
    alternate_scenarios = scenarios[1:3] # Show up to 2 alternates
    if alternate_scenarios:
        report_lines.append("\n\n**-- سيناريوهات بديلة --**")
        for i, scenario in enumerate(alternate_scenarios):
            pattern = scenario.primary_pattern
            report_lines.append(f"{i+1}. {pattern.pattern_type} (الثقة: {pattern.confidence_score:.1f}%)")

    return "\n".join(report_lines)


from src.utils.config_loader import config

def format_trade_alert(trade_signal: dict, interval_str: str, symbol: str, scenarios: List[WaveScenario]) -> str:
    """
    Formats a trade signal or an analysis event into a concise alert message.
    """
    # Handle analysis-only events (e.g., bearish patterns)
    if trade_signal.get('type') == "Analysis":
        pattern = trade_signal.get('pattern')
        details = trade_signal.get('details', 'تم رصد نمط هام.')

        # If the full pattern is provided, format it
        if pattern:
            report_lines = [f"**-- تحليل سياق لـ {symbol} ({interval_str}) --**"]
            report_lines.extend(_format_single_pattern(pattern))
            report_lines.append(f"\n**ملاحظة:** {details}")
            return "\n".join(report_lines)
        # Fallback for simple analysis messages
        else:
            reason = trade_signal.get('reason', 'تحليل سياق')
            return (
                f"**⚠️ تنبيه تحليلي ⚠️**\n\n"
                f"**الإطار الزمني:** {interval_str}\n"
                f"**السبب:** {reason}\n"
                f"**ملاحظة:** {details}"
            )

    # Format a standard trade proposal
    entry_price = trade_signal['entry']
    stop_loss_price = trade_signal['stop_loss']
    position_size = trade_signal.get('position_size') # Use .get() for safety

    sl_percentage = abs((stop_loss_price - entry_price) / entry_price) * 100

    targets_text_lines = []
    for i, target_price in enumerate(trade_signal['targets']):
        tp_percentage = abs((target_price - entry_price) / entry_price) * 100
        targets_text_lines.append(
            f"  - الهدف {i+1}: ${target_price:,.2f} (+{tp_percentage:.1f}%)"
        )
    targets_text = "\n".join(targets_text_lines)

    # --- Build Position Sizing Text ---
    position_size_text = ""
    if position_size:
        asset = symbol.replace("USDT", "") # e.g., BTC, ETH
        account_size = config.get('risk', {}).get('account_size', 'N/A')
        risk_percentage = config.get('risk', {}).get('risk_per_trade', 0) * 100

        position_size_text = (
            f"\n**إدارة المخاطر (بناءً على إعداداتك):**\n"
            f"- حجم الحساب: ${account_size:,.2f}\n"
            f"- نسبة المخاطرة: {risk_percentage:.1f}%\n"
            f"- **حجم الصفقة المقترح:** {position_size:.4f} {asset}\n"
        )

    # --- Build Alternate Scenarios Text ---
    alternate_scenarios_text = ""
    alternate_scenarios = scenarios[1:2] # Show one alternate
    if alternate_scenarios:
        alt_pattern = alternate_scenarios[0].primary_pattern
        alternate_scenarios_text = (
            f"\n\n**سيناريو بديل:** {alt_pattern.pattern_type} (ثقة: {alt_pattern.confidence_score:.1f}%)"
        )

    alert_text = (
        f"**🚨 تنبيه فرصة تداول جديدة! 🚨**\n\n"
        f"**العملة:** {symbol}\n"
        f"**الإطار الزمني:** {interval_str}\n"
        f"**السبب:** {trade_signal['reason']}\n"
        f"**نوع الصفقة:** {trade_signal['type']}\n\n"
        f"**سعر الدخول المقترح:** ${entry_price:,.2f}\n"
        f"**وقف الخسارة:** ${stop_loss_price:,.2f} (-{sl_percentage:.1f}%)\n"
        f"**الأهداف:**\n{targets_text}"
        f"{position_size_text}"
        f"{alternate_scenarios_text}"
    )
    return alert_text
