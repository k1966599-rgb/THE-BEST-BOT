import logging
from typing import List, Dict, Any, Generator
from ..core.wave_structure import WavePoint, WavePattern, WaveRuleResult

def _get_wave_length(p1: WavePoint, p2: WavePoint) -> float:
    return abs(p2.price - p1.price)

def diagonal_wave_4_overlap_rule(points: List[WavePoint]) -> WaveRuleResult:
    p1, p4 = points[1], points[4]
    is_bullish = p1.price > points[0].price
    passed = (p4.price < p1.price) if is_bullish else (p4.price > p1.price)
    return WaveRuleResult("Rule: Diagonal W4 Overlap W1", passed, f"W4 end({p4.price:.2f}) vs W1 end({p1.price:.2f})")

def diagonal_converging_rule(points: List[WavePoint]) -> WaveRuleResult:
    len1 = _get_wave_length(points[0], points[1]); len3 = _get_wave_length(points[2], points[3]); len5 = _get_wave_length(points[4], points[5])
    passed = len3 < len1 and len5 < len3
    return WaveRuleResult("Guideline: Converging Shape", passed, f"W1:{len1:.2f}>W3:{len3:.2f}>W5:{len5:.2f}")

def validate_diagonal_wave(engine, pattern: WavePattern):
    if len(pattern.points) != 6: return

    from .impulse import wave_3_shortest_rule, wave_2_retrace_rule

    rules_to_check = [diagonal_wave_4_overlap_rule, wave_3_shortest_rule, wave_2_retrace_rule]
    for rule_func in rules_to_check:
        result = rule_func(pattern.points)
        pattern.rules_results.append(result)
        if not result.passed:
            logging.debug(f"Diagonal pattern failed: {result.name} - {result.details}")
            return

    pattern.guidelines_results.append(diagonal_converging_rule(pattern.points))

def generate_diagonal_waves(pivots: List[Dict[str, Any]]) -> Generator[WavePattern, None, None]:
    if len(pivots) < 6: return
    for i in range(len(pivots) - 5):
        p = pivots[i:i+6]
        is_bullish = p[0]['type']=='L' and p[1]['type']=='H' and p[2]['type']=='L' and p[3]['type']=='H' and p[4]['type']=='L' and p[5]['type']=='H'
        is_bearish = p[0]['type']=='H' and p[1]['type']=='L' and p[2]['type']=='H' and p[3]['type']=='L' and p[4]['type']=='H' and p[5]['type']=='L'
        if is_bullish or is_bearish:
            points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
            yield WavePattern(pattern_type="Bullish Diagonal" if is_bullish else "Bearish Diagonal", points=points)
