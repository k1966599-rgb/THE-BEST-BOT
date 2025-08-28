from src.elliott_wave_engine.wave_structure import WavePattern, WaveRuleResult
from src.elliott_wave_engine.rules import flat_wave_b_retrace_rule

def validate_flat_wave(engine, pattern: WavePattern):
    """
    Validates a 3-wave pattern against the rules of an Elliott Flat Wave.
    """
    if len(pattern.points) != 4:
        return

    # --- Rule 1: Wave B must retrace at least 90% of Wave A (user-specified) ---
    pattern.add_rule_result(flat_wave_b_retrace_rule(pattern.points))

    # You can add other rules for flats here as needed, for example,
    # ensuring Wave C doesn't go excessively far, etc.
    # For now, we only implement the key rule requested by the user.
    pA, pB, pC = pattern.points[1], pattern.points[2], pattern.points[3]
    lenB = abs(pB.price - pA.price)
    lenC = abs(pC.price - pB.price)
    len_ratio_c_b = lenC / lenB if lenB > 0 else 0
    rule2_passed = len_ratio_c_b < 1.618 # Usually not excessively long
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 2: Wave C Length",
        passed=rule2_passed,
        details=f"Wave C length is {len_ratio_c_b:.2%} of Wave B."
    ))
