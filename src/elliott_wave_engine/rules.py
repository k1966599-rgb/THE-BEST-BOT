from src.elliott_wave_engine.wave_structure import WavePoint, WaveRuleResult
from typing import List

def _get_wave_length(p1: WavePoint, p2: WavePoint) -> float:
    """Calculates the vertical price distance of a wave."""
    return abs(p2.price - p1.price)

def wave_2_retrace_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Rule: Wave 2 cannot retrace more than 100% of Wave 1."""
    p0, p1, p2 = points[0], points[1], points[2]
    is_bullish = p1.price > p0.price

    passed = (p2.price > p0.price) if is_bullish else (p2.price < p0.price)

    return WaveRuleResult(
        name="Wave 2 Retracement < 100%",
        passed=passed,
        details=f"Wave 2 low/high ({p2.price:.2f}) vs Wave 1 start ({p0.price:.2f})."
    )

def wave_4_overlap_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Rule: Wave 4 cannot overlap with the price territory of Wave 1."""
    p1, p4 = points[1], points[4]
    is_bullish = p1.price > points[0].price

    passed = (p4.price > p1.price) if is_bullish else (p4.price < p1.price)

    return WaveRuleResult(
        name="Wave 4 No Overlap",
        passed=passed,
        details=f"Wave 4 low/high ({p4.price:.2f}) vs Wave 1 high/low ({p1.price:.2f})."
    )

def wave_3_shortest_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Rule: Wave 3 cannot be the shortest of the three impulse waves (1, 3, 5)."""
    len1 = _get_wave_length(points[0], points[1])
    len3 = _get_wave_length(points[2], points[3])
    len5 = _get_wave_length(points[4], points[5])

    passed = not (len3 < len1 and len3 < len5)

    return WaveRuleResult(
        name="Wave 3 Not Shortest",
        passed=passed,
        details=f"Lengths W1:{len1:.2f}, W3:{len3:.2f}, W5:{len5:.2f}."
    )

def wave_3_extension_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Guideline: Wave 3 is often the longest impulse wave."""
    len1 = _get_wave_length(points[0], points[1])
    len3 = _get_wave_length(points[2], points[3])
    len5 = _get_wave_length(points[4], points[5])

    passed = (len3 > len1 and len3 > len5)

    return WaveRuleResult(
        name="Wave 3 Extension",
        passed=passed,
        details=f"W3 length {len3:.2f} vs W1 {len1:.2f}, W5 {len5:.2f}."
    )

def wave_4_retrace_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Guideline: Wave 4 often retraces between 23.6% and 50% of Wave 3."""
    len3 = _get_wave_length(points[2], points[3])
    retrace4 = _get_wave_length(points[3], points[4])
    ratio = retrace4 / len3 if len3 > 0 else 0

    passed = 0.236 < ratio < 0.5

    return WaveRuleResult(
        name="Wave 4 Retracement",
        passed=passed,
        details=f"W4 retraced {ratio:.1%} of W3."
    )
