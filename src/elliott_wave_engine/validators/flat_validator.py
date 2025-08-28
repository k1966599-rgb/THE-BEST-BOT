from ..wave_structure import WavePattern, WaveRuleResult

def validate_flat_wave(engine, pattern: WavePattern):
    """
    Validates a 3-point pattern against the rules of an Elliott Flat Wave.
    """
    if len(pattern.points) != 4:
        return

    p0, pA, pB, pC = pattern.points
    lenA = abs(pA.price - p0.price)

    # --- Rule 1: Wave B must retrace at least 61.8% of Wave A ---
    retraceB_price = abs(pB.price - pA.price)
    retrace_ratio = retraceB_price / lenA if lenA > 0 else 0
    rule1_passed = retrace_ratio > 0.618
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 1: Wave B Deep Retracement",
        passed=rule1_passed,
        details=f"Wave B retraced {retrace_ratio:.2%} of Wave A."
    ))

    # --- Rule 2: Wave C is generally no longer than Wave B ---
    lenB = abs(pB.price - pA.price)
    lenC = abs(pC.price - pB.price)
    len_ratio_c_b = lenC / lenB if lenB > 0 else 0
    rule2_passed = len_ratio_c_b < 1.618 # Usually not excessively long
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 2: Wave C Length",
        passed=rule2_passed,
        details=f"Wave C length is {len_ratio_c_b:.2%} of Wave B."
    ))

    # --- Guidelines ---
    guideline1_passed = retrace_ratio > 0.9
    pattern.guidelines_results.append(WaveRuleResult(
        name="Guideline: Wave B is nearly 100% retrace",
        passed=guideline1_passed,
        details=f"Wave B retraced {retrace_ratio:.2%} of Wave A."
    ))
