from ..wave_structure import WavePattern, WaveRuleResult
from ..indicators.volume import analyze_wave_volume
from ..indicators.momentum import calculate_rsi

def validate_impulse_wave(engine, pattern: WavePattern):
    """
    Validates a 5-point pattern against the cardinal rules of an Elliott Impulse Wave.
    """
    if len(pattern.points) != 6:
        return

    p0, p1, p2, p3, p4, p5 = pattern.points
    is_bullish = p1.price > p0.price

    # --- Rule 1: Wave 2 cannot retrace more than 100% of Wave 1 ---
    rule1_passed = (p2.price > p0.price) if is_bullish else (p2.price < p0.price)
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 1: Wave 2 Retracement",
        passed=rule1_passed,
        details=f"P2 ({p2.price:.2f}) vs P0 ({p0.price:.2f})"
    ))

    # --- Rule 2: Wave 3 is never the shortest impulse wave ---
    len1 = abs(p1.price - p0.price)
    len3 = abs(p3.price - p2.price)
    len5 = abs(p5.price - p4.price)
    rule2_passed = len3 > len1 or len3 > len5
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 2: Wave 3 Length",
        passed=rule2_passed,
        details=f"W3({len3:.2f}) vs W1({len1:.2f}), W5({len5:.2f})"
    ))

    # --- Rule 3: Wave 4 does not overlap Wave 1 ---
    rule3_passed = (p4.price > p1.price) if is_bullish else (p4.price < p1.price)
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 3: Wave 4 Overlap",
        passed=rule3_passed,
        details=f"P4 ({p4.price:.2f}) vs P1 ({p1.price:.2f})"
    ))

def score_impulse_wave_guidelines(engine, pattern: WavePattern):
    """
    Scores an impulse wave based on common guidelines (e.g., extensions, alternations).
    """
    if len(pattern.points) != 6:
        return

    p0, p1, p2, p3, p4, p5 = pattern.points
    is_bullish = p1.price > p0.price
    len1 = abs(p1.price - p0.price)
    len3 = abs(p3.price - p2.price)

    # --- Guideline: Wave 3 Extension ---
    is_extended = len3 > len1 and len3 > abs(p5.price - p4.price)
    ratio = len3 / len1 if len1 > 0 else 0
    guideline1_passed = is_extended and (1.5 < ratio < 1.7)
    pattern.guidelines_results.append(WaveRuleResult(
        name="Guideline: W3 Extension",
        passed=guideline1_passed,
        details=f"Wave 3 extended to {ratio:.2f} of Wave 1."
    ))

    # --- Guideline: Wave 2 Retracement ---
    retrace_ratio = abs(p2.price - p1.price) / len1 if len1 > 0 else 0
    guideline2_passed = (0.5 < retrace_ratio < 0.65)
    pattern.guidelines_results.append(WaveRuleResult(
        name="Guideline: W2 Retrace",
        passed=guideline2_passed,
        details=f"Wave 2 retraced {retrace_ratio:.2f} of Wave 1."
    ))
