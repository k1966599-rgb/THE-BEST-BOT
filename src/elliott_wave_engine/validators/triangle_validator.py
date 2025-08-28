from ..wave_structure import WavePattern, WaveRuleResult

def validate_triangle_wave(engine, pattern: WavePattern):
    """
    Validates a 5-point pattern against the rules of an Elliott Triangle Wave.
    """
    if len(pattern.points) != 6:
        return

    p0, pA, pB, pC, pD, pE = pattern.points

    # Determine if trendlines are converging
    converging = (pC.price < pA.price and pD.price > pB.price) or \
                 (pC.price > pA.price and pD.price < pB.price)

    if not converging:
        pattern.rules_results.append(WaveRuleResult(name="Rule 0: Converging Trendlines", passed=False, details="Trendlines are not converging."))
        return

    # --- Rule 1: Waves must be contained within converging trendlines ---
    is_bullish_contraction = pD.price > pB.price

    rule1_c_vs_a = pC.price < pA.price if is_bullish_contraction else pC.price > pA.price
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 1a: C does not exceed A",
        passed=rule1_c_vs_a,
        details=f"P_C({pC.price:.2f}) vs P_A({pA.price:.2f})"
    ))

    rule1_d_vs_b = pD.price > pB.price if is_bullish_contraction else pD.price < pB.price
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 1b: D does not exceed B",
        passed=rule1_d_vs_b,
        details=f"P_D({pD.price:.2f}) vs P_B({pB.price:.2f})"
    ))

    rule1_e_vs_c = pE.price < pC.price if is_bullish_contraction else pE.price > pC.price
    pattern.rules_results.append(WaveRuleResult(
        name="Rule 1c: E does not exceed C",
        passed=rule1_e_vs_c,
        details=f"P_E({pE.price:.2f}) vs P_C({pC.price:.2f})"
    ))
