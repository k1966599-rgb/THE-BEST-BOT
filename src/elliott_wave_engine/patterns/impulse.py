import pandas as pd
import logging
from typing import List, Dict, Any, Generator
from ..core.wave_structure import WavePoint, WavePattern, WaveRuleResult

# --- Helper Functions ---

def _get_wave_length(p1: WavePoint, p2: WavePoint) -> float:
    """Calculates the vertical price distance of a wave."""
    return abs(p2.price - p1.price)

# --- Impulse Rules ---

def wave_2_retrace_rule(points: List[WavePoint]) -> WaveRuleResult:
    p0, p1, p2 = points[0], points[1], points[2]
    is_bullish = p1.price > p0.price
    passed = (p2.price > p0.price) if is_bullish else (p2.price < p0.price)
    return WaveRuleResult("Wave 2 Retracement < 100%", passed, f"W2 end({p2.price:.2f}) vs W1 start({p0.price:.2f})")

def wave_4_overlap_rule(points: List[WavePoint]) -> WaveRuleResult:
    p1, p4 = points[1], points[4]
    is_bullish = p1.price > points[0].price
    passed = (p4.price > p1.price) if is_bullish else (p4.price < p1.price)
    return WaveRuleResult("Wave 4 No Overlap", passed, f"W4 end({p4.price:.2f}) vs W1 end({p1.price:.2f})")

def wave_3_shortest_rule(points: List[WavePoint]) -> WaveRuleResult:
    len1 = _get_wave_length(points[0], points[1])
    len3 = _get_wave_length(points[2], points[3])
    len5 = _get_wave_length(points[4], points[5])
    passed = not (len3 < len1 and len3 < len5)
    return WaveRuleResult("Wave 3 Not Shortest", passed, f"W1:{len1:.2f}, W3:{len3:.2f}, W5:{len5:.2f}")

# --- Impulse Guidelines ---

def wave_3_extension_rule(points: List[WavePoint]) -> WaveRuleResult:
    len1 = _get_wave_length(points[0], points[1])
    len3 = _get_wave_length(points[2], points[3])
    len5 = _get_wave_length(points[4], points[5])
    passed = (len3 > len1 and len3 > len5)
    return WaveRuleResult("Guideline: W3 Extension", passed, f"W3:{len3:.2f} > W1,W5")

def wave_5_divergence_rule(points: List[WavePoint], data: pd.DataFrame) -> WaveRuleResult:
    if 'rsi' not in data.columns: return WaveRuleResult("Wave 5 Divergence", False, "RSI not found")
    p3_price, p5_price = points[3].price, points[5].price
    p3_time, p5_time = points[3].time, points[5].time
    is_bullish = p5_price > p3_price
    rsi_p3 = data.loc[p3_time]['rsi']
    rsi_p5 = data.loc[p5_time]['rsi']
    passed = (is_bullish and rsi_p5 < rsi_p3) or (not is_bullish and rsi_p5 > rsi_p3)
    return WaveRuleResult("Guideline: W5 Divergence", passed, f"Price:{'HH' if is_bullish else 'LL'}, RSI:{'LH' if rsi_p5 < rsi_p3 else 'HL'}")

# --- Impulse Validator ---

def validate_impulse_wave(engine, pattern: WavePattern):
    rules_to_check = [
        wave_2_retrace_rule,
        wave_4_overlap_rule,
        wave_3_shortest_rule
    ]
    for rule_func in rules_to_check:
        result = rule_func(pattern.points)
        pattern.rules_results.append(result)
        if not result.passed:
            logging.debug(f"Impulse pattern failed validation. Rule: {result.name}, Details: {result.details}")
            # Stop validation if a cardinal rule fails
            return

    # Add guidelines if all rules passed
    guidelines_to_check = [
        wave_3_extension_rule,
        wave_5_divergence_rule,
    ]
    for guideline_func in guidelines_to_check:
        # Guidelines need engine data
        if "data" in guideline_func.__code__.co_varnames:
            result = guideline_func(pattern.points, engine.data)
        else:
            result = guideline_func(pattern.points)
        pattern.guidelines_results.append(result)

# --- Impulse Generator ---

def generate_impulse_waves(pivots: List[Dict[str, Any]]) -> Generator[WavePattern, None, None]:
    if len(pivots) < 6: return
    for i in range(len(pivots) - 5):
        p = pivots[i:i+6]
        is_bullish = p[0]['type']=='L' and p[1]['type']=='H' and p[2]['type']=='L' and p[3]['type']=='H' and p[4]['type']=='L' and p[5]['type']=='H'
        is_bearish = p[0]['type']=='H' and p[1]['type']=='L' and p[2]['type']=='H' and p[3]['type']=='L' and p[4]['type']=='H' and p[5]['type']=='L'

        if is_bullish or is_bearish:
            points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
            pattern_type = "Bullish Impulse" if is_bullish else "Bearish Impulse"
            yield WavePattern(pattern_type=pattern_type, points=points)
