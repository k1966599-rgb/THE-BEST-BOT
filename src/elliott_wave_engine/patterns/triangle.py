import logging
from typing import List, Dict, Any, Generator
from ..core.wave_structure import WavePoint, WavePattern, WaveRuleResult

def validate_triangle_wave(engine, pattern: WavePattern):
    if len(pattern.points) != 6: return

    pA, pB, pC, pD, pE = pattern.points[1], pattern.points[2], pattern.points[3], pattern.points[4], pattern.points[5]
    is_bullish_contraction = pD.price > pB.price and pC.price < pA.price
    is_bearish_contraction = pD.price < pB.price and pC.price > pA.price
    converging = is_bullish_contraction or is_bearish_contraction

    result1 = WaveRuleResult("قاعدة: خطوط اتجاه متقاربة", converging, f"A:{pA.price:.2f},B:{pB.price:.2f},C:{pC.price:.2f},D:{pD.price:.2f}")
    pattern.rules_results.append(result1)
    if not result1.passed:
        logging.debug(f"Triangle pattern failed: {result1.name} - {result1.details}")
        return

    rule_e_vs_c = pE.price < pC.price if is_bullish_contraction else pE.price > pC.price
    result2 = WaveRuleResult("قاعدة: E لا تتجاوز C", rule_e_vs_c, f"P_E({pE.price:.2f}) vs P_C({pC.price:.2f})")
    pattern.rules_results.append(result2)
    if not result2.passed:
        logging.debug(f"Triangle pattern failed: {result2.name} - {result2.details}")
        return

def generate_triangle_waves(pivots: List[Dict[str, Any]]) -> Generator[WavePattern, None, None]:
    if len(pivots) < 6: return
    for i in range(len(pivots) - 5):
        p = pivots[i:i+6]
        is_bullish = p[0]['type'] == 'L'
        alternating = all(p[j]['type'] != p[j+1]['type'] for j in range(len(p)-1))
        if alternating:
            points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
            yield WavePattern(pattern_type="Bullish Triangle" if is_bullish else "Bearish Triangle", points=points)
