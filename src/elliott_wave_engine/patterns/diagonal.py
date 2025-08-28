import logging
from typing import List, Dict, Any, Generator
from ..core.wave_structure import WavePoint, WavePattern, WaveRuleResult

# --- Helper Functions ---

def _get_wave_length(p1: WavePoint, p2: WavePoint) -> float:
    """Calculates the vertical price distance of a wave."""
    return abs(p2.price - p1.price)

# --- Diagonal Rules & Guidelines ---

def diagonal_wave_4_overlap_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Rule: In a Diagonal, Wave 4 MUST overlap with Wave 1."""
    p1, p4 = points[1], points[4]
    is_bullish = p1.price > points[0].price
    passed = (p4.price < p1.price) if is_bullish else (p4.price > p1.price)
    return WaveRuleResult("Rule: Diagonal W4 Overlap W1", passed, f"W4 end({p4.price:.2f}) vs W1 end({p1.price:.2f})")

def diagonal_converging_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Guideline: In a contracting diagonal, waves get smaller."""
    len1 = _get_wave_length(points[0], points[1])
    len3 = _get_wave_length(points[2], points[3])
    len5 = _get_wave_length(points[4], points[5])
    passed = len3 < len1 and len5 < len3
    return WaveRuleResult("Guideline: Converging Shape", passed, f"W1:{len1:.2f} > W3:{len3:.2f} > W5:{len5:.2f}")

# --- Diagonal Validator ---

def validate_diagonal_wave(engine, pattern: WavePattern):
    if len(pattern.points) != 6: return

    # Import shared rules from impulse to avoid code duplication
    from .impulse import wave_3_shortest_rule, wave_2_retrace_rule

    rules_to_check = {
        "Diagonal W4 Overlap": diagonal_wave_4_overlap_rule,
        "Wave 3 Not Shortest": wave_3_shortest_rule,
        "Wave 2 Retracement": wave_2_retrace_rule
    }

    for name, rule_func in rules_to_check.items():
        result = rule_func(pattern.points)
        pattern.rules_results.append(result)
        if not result.passed:
            logging.debug(f"Diagonal pattern failed validation. Rule: {result.name}, Details: {result.details}")
            return

    # Guidelines
    pattern.guidelines_results.append(diagonal_converging_rule(pattern.points))

# --- Diagonal Generator ---

def generate_diagonal_waves(pivots: List[Dict[str, Any]]) -> Generator[WavePattern, None, None]:
    if len(pivots) < 6: return
    for i in range(len(pivots) - 5):
        p = pivots[i:i+6]
        is_bullish = p[0]['type']=='L' and p[1]['type']=='H' and p[2]['type']=='L' and p[3]['type']=='H' and p[4]['type']=='L' and p[5]['type']=='H'
        is_bearish = p[0]['type']=='H' and p[1]['type']=='L' and p[2]['type']=='H' and p[3]['type']=='L' and p[4]['type']=='H' and p[5]['type']=='L'

        if is_bullish or is_bearish:
            points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
            pattern_type = "Bullish Diagonal" if is_bullish else "Bearish Diagonal"
            yield WavePattern(pattern_type=pattern_type, points=points)
