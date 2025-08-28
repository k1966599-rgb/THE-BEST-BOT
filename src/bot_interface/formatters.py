from typing import List
from src.analysis.wave_structure import BaseWavePattern

def format_elliott_wave_report(symbol: str, interval_str: str, patterns: List[BaseWavePattern]) -> str:
    """
    Formats a list of found wave patterns into a detailed, table-like report.
    """
    report_lines = [f"**-- التحليل الموجي لـ {symbol} ({interval_str}) --**"]

    if not patterns:
        report_lines.append("\nلم يتم العثور على أي أنماط موجية واضحة حالياً.")
        return "\n".join(report_lines)

    for pattern in patterns:
        report_lines.append(f"\n--- {pattern.pattern_type} ---")
        report_lines.append(f"**الثقة:** {pattern.confidence_score:.1f}%")

        # Using code blocks for a clean, table-like layout
        header = f"`{'الموجة':<7}| {'نقطة البداية':<12} | {'نقطة النهاية':<12} | {'التغيير':<10}`"
        separator = f"`-------+--------------+--------------+-----------`"
        report_lines.append("\n" + header)
        report_lines.append(separator)

        # Determine wave labels based on pattern type
        wave_labels = []
        if "دافع" in pattern.pattern_type or "قطرية" in pattern.pattern_type: # Impulse or Diagonal
            wave_labels = ["الموجة 1", "الموجة 2", "الموجة 3", "الموجة 4", "الموجة 5"]
        elif "زجزاج" in pattern.pattern_type or "مسطحة" in pattern.pattern_type: # Zigzag or Flat
            wave_labels = ["الموجة A", "الموجة B", "الموجة C"]
        elif "مثلث" in pattern.pattern_type: # Triangle
            wave_labels = ["الموجة A", "الموجة B", "الموجة C", "الموجة D", "الموجة E"]

        for i, label in enumerate(wave_labels):
            if i + 1 >= len(pattern.points): break

            p_start = pattern.points[i]
            p_end = pattern.points[i+1]

            start_price_str = f"${p_start.price:,.2f}"
            end_price_str = f"${p_end.price:,.2f}"

            change = p_end.price - p_start.price
            change_pct = (change / p_start.price) * 100 if p_start.price != 0 else 0
            change_str = f"{change_pct:+.2f}%"

            row = f"`{label:<7}| {start_price_str:<12} | {end_price_str:<12} | {change_str:<10}`"
            report_lines.append(row)

        report_lines.append("\n**قواعد النمط:**")
        for rule in pattern.rules_results:
            status = "✅" if rule.passed else "❌"
            report_lines.append(f"  {status} {rule.name}")

    return "\n".join(report_lines)


from src.utils.config_loader import config

def format_trade_alert(trade_signal: dict, interval_str: str) -> str:
    """
    Formats a trade signal into a concise alert message, including position size.
    """
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
        # Extract symbol from the reason text, e.g., "Potential Bullish Impulse on BTCUSDT"
        symbol = trade_signal['reason'].split(' ')[-2]
        asset = symbol.replace("USDT", "") # e.g., BTC, ETH

        account_size = config.get('risk', {}).get('account_size', 'N/A')
        risk_percentage = config.get('risk', {}).get('risk_per_trade', 0) * 100

        position_size_text = (
            f"\n**إدارة المخاطر (بناءً على إعداداتك):**\n"
            f"- حجم الحساب: ${account_size:,.2f}\n"
            f"- نسبة المخاطرة: {risk_percentage:.1f}%\n"
            f"- **حجم الصفقة المقترح:** {position_size:.4f} {asset}\n"
        )

    alert_text = (
        f"**🚨 تنبيه فرصة تداول جديدة! 🚨**\n\n"
        f"**الإطار الزمني:** {interval_str}\n"
        f"**السبب:** {trade_signal['reason']}\n"
        f"**نوع الصفقة:** {trade_signal['type']}\n\n"
        f"**سعر الدخول المقترح:** ${entry_price:,.2f}\n"
        f"**وقف الخسارة:** ${stop_loss_price:,.2f} (-{sl_percentage:.1f}%)\n"
        f"**الأهداف:**\n{targets_text}"
        f"{position_size_text}" # Append the position sizing text
    )
    return alert_text
