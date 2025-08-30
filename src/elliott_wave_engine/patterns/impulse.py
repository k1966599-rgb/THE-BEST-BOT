import pandas as pd
import logging
from typing import List, Dict, Any, Generator
from ..core.wave_structure import WavePoint, WavePattern, WaveRuleResult

# --- Helper Functions ---
def _get_wave_length(p1: WavePoint, p2: WavePoint) -> float:
    return abs(p2.price - p1.price)

# --- Impulse Rules (Applicable based on number of points) ---
def wave_2_retrace_rule(points: List[WavePoint]) -> WaveRuleResult:
    p0, p1, p2 = points[0], points[1], points[2]
    is_bullish = p1.price > p0.price
    passed = (p2.price > p0.price) if is_bullish else (p2.price < p0.price)
    return WaveRuleResult("الموجة 2 لم تتجاوز 100% من 1", passed, f"W2 end({p2.price:.2f}) vs W1 start({p0.price:.2f})")

def wave_4_overlap_rule(points: List[WavePoint]) -> WaveRuleResult:
    p1, p4 = points[1], points[4]
    is_bullish = p1.price > points[0].price
    passed = (p4.price > p1.price) if is_bullish else (p4.price < p1.price)
    return WaveRuleResult("الموجة 4 لا تتداخل مع 1", passed, f"W4 end({p4.price:.2f}) vs W1 end({p1.price:.2f})")

def wave_3_shortest_rule(points: List[WavePoint]) -> WaveRuleResult:
    len1 = _get_wave_length(points[0], points[1])
    len3 = _get_wave_length(points[2], points[3])
    len5 = _get_wave_length(points[4], points[5])
    passed = not (len3 < len1 and len3 < len5)
    return WaveRuleResult("الموجة 3 ليست الأقصر", passed, f"W1:{len1:.2f}, W3:{len3:.2f}, W5:{len5:.2f}")

# --- Impulse Validator (Now handles partial patterns) ---
def validate_impulse_wave(engine, pattern: WavePattern):
    num_points = len(pattern.points)

    # Apply rules based on the number of points available
    if num_points >= 3:
        pattern.add_rule_result(wave_2_retrace_rule(pattern.points))
    if num_points >= 5:
        pattern.add_rule_result(wave_4_overlap_rule(pattern.points))
    if num_points >= 6:
        pattern.add_rule_result(wave_3_shortest_rule(pattern.points))

    # Future: Add guideline checks here as well, e.g., for divergence after wave 5
    # For now, we focus on making the generation work.

# --- Impulse Generator (Rewritten for Flexibility) ---
def generate_impulse_waves(pivots: List[Dict[str, Any]]) -> Generator[WavePattern, None, None]:
    """
    Generates impulse wave patterns of various lengths (3, 4, 5, 6 points)
    to identify both developing and completed waves.
    """
    # A 1-2 wave needs at least 3 pivots
    if len(pivots) < 3:
        return

    for i in range(len(pivots) - 2):
        # --- Check for developing Wave 1-2 (3 points) ---
        p = pivots[i:i+3]
        is_bullish_1_2 = p[0]['type'] == 'L' and p[1]['type'] == 'H' and p[2]['type'] == 'L'
        is_bearish_1_2 = p[0]['type'] == 'H' and p[1]['type'] == 'L' and p[2]['type'] == 'H'

        if is_bullish_1_2 or is_bearish_1_2:
            points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
            yield WavePattern(pattern_type="Bullish Impulse" if is_bullish_1_2 else "Bearish Impulse", points=points)

        # --- Check for developing Wave 1-2-3-4 (5 points) ---
        if i + 4 < len(pivots):
            p = pivots[i:i+5]
            is_bullish_1_4 = p[0]['type']=='L' and p[1]['type']=='H' and p[2]['type']=='L' and p[3]['type']=='H' and p[4]['type']=='L'
            is_bearish_1_4 = p[0]['type']=='H' and p[1]['type']=='L' and p[2]['type']=='H' and p[3]['type']=='L' and p[4]['type']=='H'

            if is_bullish_1_4 or is_bearish_1_4:
                points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
                yield WavePattern(pattern_type="Bullish Impulse" if is_bullish_1_4 else "Bearish Impulse", points=points)

        # --- Check for completed Wave 1-2-3-4-5 (6 points) ---
        if i + 5 < len(pivots):
            p = pivots[i:i+6]
            is_bullish_1_5 = p[0]['type']=='L' and p[1]['type']=='H' and p[2]['type']=='L' and p[3]['type']=='H' and p[4]['type']=='L' and p[5]['type']=='H'
            is_bearish_1_5 = p[0]['type']=='H' and p[1]['type']=='L' and p[2]['type']=='H' and p[3]['type']=='L' and p[4]['type']=='H' and p[5]['type']=='L'

            if is_bullish_1_5 or is_bearish_1_5:
                points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
                yield WavePattern(pattern_type="Bullish Impulse" if is_bullish_1_5 else "Bearish Impulse", points=points)
