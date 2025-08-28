import logging
from typing import List, Dict, Any, Generator
from ..core.wave_structure import WavePoint, WavePattern, WaveRuleResult

def _get_wave_length(p1: WavePoint, p2: WavePoint) -> float:
    return abs(p2.price - p1.price)

def flat_wave_b_retrace_rule(points: List[WavePoint]) -> WaveRuleResult:
    len_a = _get_wave_length(points[0], points[1])
    retrace_b = _get_wave_length(points[1], points[2])
    ratio = retrace_b / len_a if len_a > 0 else 0
    passed = ratio >= 0.9
    return WaveRuleResult("Rule: Flat B Retracement > 90%", passed, f"Wave B retraced {ratio:.1%} of Wave A.")

def validate_flat_wave(engine, pattern: WavePattern):
    if len(pattern.points) != 4: return

    result1 = flat_wave_b_retrace_rule(pattern.points)
    pattern.rules_results.append(result1)
    if not result1.passed:
        logging.debug(f"Flat pattern failed: {result1.name} - {result1.details}")
        return

    pA, pB, pC = pattern.points[1], pattern.points[2], pattern.points[3]
    lenB = _get_wave_length(pA, pB)
    lenC = _get_wave_length(pB, pC)
    len_ratio_c_b = lenC / lenB if lenB > 0 else 0
    rule2_passed = len_ratio_c_b < 1.618
    result2 = WaveRuleResult("Rule: Wave C Length", rule2_passed, f"Wave C length is {len_ratio_c_b:.2%} of Wave B.")
    pattern.rules_results.append(result2)
    if not result2.passed:
        logging.debug(f"Flat pattern failed: {result2.name} - {result2.details}")
        return

def generate_flat_waves(pivots: List[Dict[str, Any]]) -> Generator[WavePattern, None, None]:
    if len(pivots) < 4: return
    for i in range(len(pivots) - 3):
        p = pivots[i:i+4]
        is_bullish = p[0]['type'] == 'L' and p[1]['type'] == 'H' and p[2]['type'] == 'L' and p[3]['type'] == 'H'
        is_bearish = p[0]['type'] == 'H' and p[1]['type'] == 'L' and p[2]['type'] == 'H' and p[3]['type'] == 'L'
        if is_bullish or is_bearish:
            points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
            yield WavePattern(pattern_type="Bullish Flat" if is_bullish else "Bearish Flat", points=points)
