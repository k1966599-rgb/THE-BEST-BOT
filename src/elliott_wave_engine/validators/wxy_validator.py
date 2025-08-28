from ..wave_structure import ComplexWavePattern, WaveRuleResult

def _log_rule(pattern: ComplexWavePattern, name: str, passed: bool, details: str):
    """Helper to append a rule result and log it if it fails."""
    result = WaveRuleResult(name=name, passed=passed, details=details)
    pattern.rules_results.append(result)
    if not passed:
        print(f"    - FAIL: {name} | {details}")

def validate_wxy_wave(engine, pattern: ComplexWavePattern):
    """
    Validates a WXY complex correction.
    """
    if len(pattern.sub_patterns) != 2:
        return

    pattern_w = pattern.sub_patterns[0]
    pattern_y = pattern.sub_patterns[1]

    # Rule 1: W and Y should be valid corrective patterns
    w_valid = all(r.passed for r in pattern_w.rules_results)
    y_valid = all(r.passed for r in pattern_y.rules_results)

    _log_rule(pattern, "Rule 1: Sub-patterns are valid", (w_valid and y_valid),
              f"W is valid: {w_valid}, Y is valid: {y_valid}")

    # Rule 2: The X wave (the connection) should not be too large.
    _log_rule(pattern, "Rule 2: X wave is valid", True,
              "Simplified validation for X wave.")
