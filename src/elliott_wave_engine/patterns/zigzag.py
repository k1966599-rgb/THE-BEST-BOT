import logging
from typing import List, Dict, Any, Generator
from ..core.wave_structure import WavePoint, WavePattern, WaveRuleResult

# --- Helper Functions ---

def _get_wave_length(p1: WavePoint, p2: WavePoint) -> float:
    """Calculates the vertical price distance of a wave."""
    return abs(p2.price - p1.price)

# --- Zigzag Rules & Guidelines ---

def zigzag_wave_b_retrace_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Guideline: In a Zigzag, Wave B typically retraces 38.2% to 61.8% of Wave A."""
    len_a = _get_wave_length(points[0], points[1])
    retrace_b = _get_wave_length(points[1], points[2])
    ratio = retrace_b / len_a if len_a > 0 else 0
    passed = 0.382 < ratio < 0.618
    return WaveRuleResult("Guideline: Zigzag B Retracement", passed, f"Wave B retraced {ratio:.1%} of Wave A.")

# --- Zigzag Validator ---

def validate_zigzag_wave(engine, pattern: WavePattern):
    if len(pattern.points) != 4: return

    p0, pA, pB, _ = pattern.points
    is_bearish = pA.price < p0.price

    # Rule: Wave B cannot retrace more than 100% of Wave A.
    rule1_passed = (pB.price < p0.price) if is_bearish else (pB.price > p0.price)
    result = WaveRuleResult("Rule: B not beyond A start", rule1_passed, f"B({pB.price:.2f}) vs A_start({p0.price:.2f})")
    pattern.rules_results.append(result)
    if not result.passed:
        logging.debug(f"Zigzag pattern failed validation. Rule: {result.name}, Details: {result.details}")
        return

    # Guideline: Wave B retracement percentage.
    pattern.guidelines_results.append(zigzag_wave_b_retrace_rule(pattern.points))

# --- Zigzag Generator ---

def generate_zigzag_waves(pivots: List[Dict[str, Any]]) -> Generator[WavePattern, None, None]:
    if len(pivots) < 4: return

    for i in range(len(pivots) - 3):
        p = pivots[i:i+4]
        is_bullish = p[0]['type'] == 'L' and p[1]['type'] == 'H' and p[2]['type'] == 'L' and p[3]['type'] == 'H'
        is_bearish = p[0]['type'] == 'H' and p[1]['type'] == 'L' and p[2]['type'] == 'H' and p[3]['type'] == 'L'

        if is_bullish or is_bearish:
            # Basic check: B wave (p2) must not retrace beyond start of A (p0)
            if (is_bullish and p[2]['price'] > p[0]['price']) or (is_bearish and p[2]['price'] < p[0]['price']):
                points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
                pattern_type = "Bullish Zigzag" if is_bullish else "Bearish Zigzag"
                yield WavePattern(pattern_type=pattern_type, points=points)
