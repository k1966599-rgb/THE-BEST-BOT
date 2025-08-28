from ..wave_structure import WavePattern, WaveRuleResult

def validate_zigzag_wave(engine, pattern: WavePattern):
    """
    Validates a 3-point pattern against the rules of an Elliott Zigzag Wave.
    A Zigzag is a 3-wave (A-B-C) corrective pattern.
    """
    if len(pattern.points) != 4:
        return

    p0, pA, pB, pC = pattern.points
    is_bearish = pA.price < p0.price

    # --- Rule 1: Wave B cannot retrace more than 100% of Wave A ---
    rule1_passed = (pB.price < p0.price) if is_bearish else (pB.price > p0.price)
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 1: Wave B Retracement",
        passed=rule1_passed,
        details=f"Wave B ({pB.price:.2f}) did not retrace beyond the start of Wave A ({p0.price:.2f})."
    ))

    # --- Rule 2: Wave C must move beyond the end of Wave A ---
    rule2_passed = (pC.price < pA.price) if is_bearish else (pC.price > pA.price)
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 2: Wave C Extension",
        passed=rule2_passed,
        details=f"Wave C ({pC.price:.2f}) moved beyond the end of Wave A ({pA.price:.2f})."
    ))

    # --- Guidelines ---
    lenA = abs(pA.price - p0.price)
    retraceB = abs(pB.price - pA.price)
    retrace_ratio = retraceB / lenA if lenA > 0 else 0
    guideline1_passed = retrace_ratio < 0.62
    pattern.guidelines_results.append(WaveRuleResult(
        name="Guideline: Wave B is shallow",
        passed=guideline1_passed,
        details=f"Wave B retraced {retrace_ratio:.2%} of Wave A."
    ))

    lenC = abs(pC.price - pB.price)
    equality_ratio = lenC / lenA if lenA > 0 else 0
    guideline2_passed = 0.7 < equality_ratio < 1.3
    pattern.guidelines_results.append(WaveRuleResult(
        name="Guideline: Wave C equals Wave A",
        passed=guideline2_passed,
        details=f"Wave C is {equality_ratio:.2f} times the length of Wave A."
    ))
