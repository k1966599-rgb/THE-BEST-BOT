from src.elliott_wave_engine.wave_structure import WavePattern, WaveRuleResult
from src.elliott_wave_engine.rules import zigzag_wave_b_retrace_rule

def validate_zigzag_wave(engine, pattern: WavePattern):
    """
    Validates a 3-wave pattern against the rules and guidelines of a Zigzag wave.
    """
    if len(pattern.points) != 4:
        return

    p0, pA, pB, _ = pattern.points
    is_bearish = pA.price < p0.price

    # --- Rule 1: Wave B cannot retrace more than 100% of Wave A ---
    # This is a fundamental rule for all corrective patterns.
    rule1_passed = (pB.price < p0.price) if is_bearish else (pB.price > p0.price)
    pattern.rules_results.append(WaveRuleResult(
        name="Rule: B not beyond A start",
        passed=rule1_passed,
        details=f"Wave B ({pB.price:.2f}) did not retrace beyond the start of Wave A ({p0.price:.2f})."
    ))

    # --- Guideline: Wave B Retracement (user-specified) ---
    # Per user request, check if Wave B retraces between 38.2% and 61.8% of Wave A.
    # This is a guideline, not a strict rule.
    pattern.guidelines_results.append(zigzag_wave_b_retrace_rule(pattern.points))
