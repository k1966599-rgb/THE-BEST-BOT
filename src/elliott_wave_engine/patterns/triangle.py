import logging
from typing import List, Dict, Any, Generator
from ..core.wave_structure import WavePoint, WavePattern, WaveRuleResult

# --- Triangle Validator ---

def validate_triangle_wave(engine, pattern: WavePattern):
    """
    Validates a 5-point pattern against the rules of an Elliott Triangle Wave.
    """
    if len(pattern.points) != 6:
        return

    p0, pA, pB, pC, pD, pE = pattern.points
    is_bullish_contraction = pD.price > pB.price and pC.price < pA.price
    is_bearish_contraction = pD.price < pB.price and pC.price > pA.price
    converging = is_bullish_contraction or is_bearish_contraction

    result1 = WaveRuleResult("Rule: Converging Trendlines", converging, f"A:{pA.price:.2f}, B:{pB.price:.2f}, C:{pC.price:.2f}, D:{pD.price:.2f}")
    pattern.rules_results.append(result1)
    if not result1.passed:
        logging.debug(f"Triangle pattern failed validation. Rule: {result1.name}, Details: {result1.details}")
        return

    rule_e_vs_c = pE.price < pC.price if is_bullish_contraction else pE.price > pC.price
    result2 = WaveRuleResult("Rule: E does not exceed C", rule_e_vs_c, f"P_E({pE.price:.2f}) vs P_C({pC.price:.2f})")
    pattern.rules_results.append(result2)
    if not result2.passed:
        logging.debug(f"Triangle pattern failed validation. Rule: {result2.name}, Details: {result2.details}")
        return


# --- Triangle Generator ---

def generate_triangle_waves(pivots: List[Dict[str, Any]]) -> Generator[WavePattern, None, None]:
    """
    Generates all possible 5-wave triangle patterns from a list of pivots.
    """
    if len(pivots) < 6:
        return

    for i in range(len(pivots) - 5):
        p = pivots[i:i+6]

        is_bullish = p[0]['type'] == 'L'
        is_bearish = p[0]['type'] == 'H'

        # A triangle is a 5-wave pattern (A-B-C-D-E) with 6 pivots
        # It must have alternating pivot types
        alternating = (p[0]['type'] != p[1]['type'] and
                       p[1]['type'] != p[2]['type'] and
                       p[2]['type'] != p[3]['type'] and
                       p[3]['type'] != p[4]['type'] and
                       p[4]['type'] != p[5]['type'])

        if alternating:
            points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
            pattern_type = "Bullish Triangle" if is_bullish else "Bearish Triangle"
            yield WavePattern(pattern_type=pattern_type, points=points)
