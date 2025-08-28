from ..wave_structure import WavePattern, WaveRuleResult

def validate_diagonal_wave(engine, pattern: WavePattern):
    """
    Validates a 5-point pattern against the rules of an Elliott Diagonal Wave.
    """
    if len(pattern.points) != 6:
        return

    p0, p1, p2, p3, p4, p5 = pattern.points
    is_bullish = p1.price > p0.price

    # --- Rule 1: Wave 4 must overlap with Wave 1 ---
    rule1_passed = (p4.price < p1.price) if is_bullish else (p4.price > p1.price)
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 1: Wave 4 Overlap",
        passed=rule1_passed,
        details=f"P4 ({p4.price:.2f}) vs P1 ({p1.price:.2f})"
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

    # --- Rule 3: Must form a converging wedge (for contracting diagonal) ---
    rule3_passed = (len3 < len1) and (len5 < len3)
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 3: Converging Wedge Shape",
        passed=rule3_passed,
        details=f"W1({len1:.2f}) > W3({len3:.2f}) > W5({len5:.2f})"
    ))

    # --- Rule 4: Wave 2 does not retrace more than 100% of Wave 1 ---
    rule4_passed = (p2.price > p0.price) if is_bullish else (p2.price < p0.price)
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 4: Wave 2 Retracement",
        passed=rule4_passed,
        details=f"P2 ({p2.price:.2f}) vs P0 ({p0.price:.2f})"
    ))
