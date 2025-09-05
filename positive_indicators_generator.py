from typing import Dict, List

def generate_positive_indicators(analysis_results: Dict, current_price: float) -> List[str]:
    """
    Analyzes the full results dictionary and generates a human-readable list
    of positive (bullish) indicators.

    This is the "rules engine" for the report.
    """
    indicators = []

    # Extract sub-dictionaries for easier access
    indicator_data = analysis_results.get('indicators', {})
    sr_data = analysis_results.get('support_resistance', {})
    pattern_data = analysis_results.get('patterns', {})
    fib_data = analysis_results.get('fibonacci', {})

    # Rule 1: RSI
    rsi_val = indicator_data.get('rsi', 50)
    if rsi_val < 35:
        indicators.append("✅ RSI يقترب من منطقة تشبع البيع")

    # Rule 2: MACD
    if indicator_data.get('macd_is_bullish'):
        indicators.append("✅ MACD يظهر إشارة إيجابية")

    # Rule 3: Support Zones
    # Check if the price is close to a strong demand zone
    demand_zone = sr_data.get('primary_demand_zone')
    if demand_zone:
        distance_to_demand = demand_zone.get('distance', 1)
        if current_price > 0 and (distance_to_demand / current_price) < 0.02:
            indicators.append("✅ السعر قريب من منطقة دعم قوية")

    # Rule 4: Classic Patterns
    found_patterns = pattern_data.get('found_patterns', [])
    if found_patterns:
        # Check for bullish patterns
        bullish_patterns = ['Double Bottom', 'Triangle/Wedge Forming'] # Add more as they are implemented
        for p in found_patterns:
            if p.get('name') in bullish_patterns:
                indicators.append(f"✅ نموذج فني إيجابي: {p.get('name')}")
                break # Add only one pattern indicator

    # Rule 5: Fibonacci Levels
    # Check if price is holding above a key Fibonacci level (e.g., 61.8% or 38.2%)
    retracements = fib_data.get('retracement_levels', [])
    key_fib_levels = ['61.8%', '38.2%']
    for level in retracements:
        if level.get('level') in key_fib_levels and current_price > 0:
            # Check if price is just above this level
            if 0 < (current_price - level.get('price', 0)) / current_price < 0.015:
                 indicators.append(f"✅ مستوى فيبوناتشي {level.get('level')} يحتفظ كدعم")

    # This is a simplified engine. More rules can be added for other indicators
    # like SMA crossovers, volume confirmation, etc.

    return indicators
