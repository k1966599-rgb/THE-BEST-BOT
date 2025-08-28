import pandas as pd
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

def wave_3_momentum_rule(points: List[WavePoint], data: pd.DataFrame) -> WaveRuleResult:
    """Guideline: Wave 3 should have the highest momentum (RSI)."""
    if 'rsi' not in data.columns:
        return WaveRuleResult("Wave 3 Strong Momentum", False, "RSI data not available.")

    p1_time, p3_time, p5_time = points[1].time, points[3].time, points[5].time

    # Get RSI values at the peaks of waves 1, 3, and 5
    rsi_at_p1 = data.loc[p1_time]['rsi']
    rsi_at_p3 = data.loc[p3_time]['rsi']
    rsi_at_p5 = data.loc[p5_time]['rsi']

    passed = rsi_at_p3 > rsi_at_p1 and rsi_at_p3 > rsi_at_p5

    return WaveRuleResult(
        name="Wave 3 Strong Momentum",
        passed=passed,
        details=f"RSI at P3 ({rsi_at_p3:.1f}) vs P1 ({rsi_at_p1:.1f}) and P5 ({rsi_at_p5:.1f})."
    )

def wave_5_divergence_rule(points: List[WavePoint], data: pd.DataFrame) -> WaveRuleResult:
    """Guideline: Wave 5 should show momentum divergence against Wave 3."""
    if 'rsi' not in data.columns:
        return WaveRuleResult("Wave 5 Divergence", False, "RSI data not available.")

    p3_price, p5_price = points[3].price, points[5].price
    p3_time, p5_time = points[3].time, points[5].time
    is_bullish_price = p5_price > p3_price

    rsi_at_p3 = data.loc[p3_time]['rsi']
    rsi_at_p5 = data.loc[p5_time]['rsi']

    # Bullish divergence: Higher high in price, lower high in RSI
    divergence_passed = (is_bullish_price and rsi_at_p5 < rsi_at_p3)

    # Note: Bearish divergence is not checked here as the trade proposer
    # currently only handles bullish scenarios. This can be expanded later.

    return WaveRuleResult(
        name="Wave 5 Divergence",
        passed=divergence_passed,
        details=f"Price P3->P5 {'rose' if is_bullish_price else 'fell'}, RSI P3->P5 {'fell' if rsi_at_p5 < rsi_at_p3 else 'rose'}."
    )

# --- Rules for Corrective Waves ---

def zigzag_wave_b_retrace_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Guideline: In a Zigzag, Wave B typically retraces 38.2% to 61.8% of Wave A."""
    len_a = _get_wave_length(points[0], points[1])
    retrace_b = _get_wave_length(points[1], points[2])
    ratio = retrace_b / len_a if len_a > 0 else 0

    passed = 0.382 < ratio < 0.618

    return WaveRuleResult(
        name="Zigzag B Retracement",
        passed=passed,
        details=f"Wave B retraced {ratio:.1%} of Wave A."
    )

# --- Advanced Rules & Guidelines ---

def rule_of_alternation(points: List[WavePoint]) -> WaveRuleResult:
    """Guideline: Wave 2 and Wave 4 should alternate in complexity (sharp vs. sideways)."""
    len_1 = _get_wave_length(points[0], points[1])
    retrace_2 = _get_wave_length(points[1], points[2])
    ratio_2 = retrace_2 / len_1 if len_1 > 0 else 0

    len_3 = _get_wave_length(points[2], points[3])
    retrace_4 = _get_wave_length(points[3], points[4])
    ratio_4 = retrace_4 / len_3 if len_3 > 0 else 0

    # Define "sharp" vs "sideways" based on retracement depth
    # Sharp correction (like a Zigzag) is typically deep, > 50%
    w2_is_sharp = ratio_2 > 0.5
    # Sideways correction (like a Flat) is typically shallow, < 50% (often < 38.2%)
    w4_is_sideways = ratio_4 < 0.5

    # Alternation holds if one is sharp and the other is sideways
    alternation_passed = (w2_is_sharp and w4_is_sideways) or (not w2_is_sharp and not w4_is_sideways)

    return WaveRuleResult(
        name="Guideline: Alternation",
        passed=alternation_passed,
        details=f"W2 retrace: {ratio_2:.1%}, W4 retrace: {ratio_4:.1%}"
    )

def wave_2_4_time_similarity_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Guideline: Wave 2 and 4 should be similar in time duration."""
    # Duration is calculated by the difference in candle indices
    duration_2 = points[2].idx - points[1].idx
    duration_4 = points[4].idx - points[3].idx

    if duration_2 == 0 or duration_4 == 0:
        return WaveRuleResult("Guideline: Time Similarity", False, "Could not calculate wave duration.")

    # Check if the shorter wave is at least 61.8% of the longer wave
    ratio = min(duration_2, duration_4) / max(duration_2, duration_4)
    passed = ratio > 0.618

    return WaveRuleResult(
        name="Guideline: Time Similarity",
        passed=passed,
        details=f"W2 duration: {duration_2} candles, W4 duration: {duration_4} candles."
    )

# --- Rules for Diagonal Waves ---

def diagonal_wave_4_overlap_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Rule: In a Diagonal, Wave 4 MUST overlap with Wave 1."""
    p1, p4 = points[1], points[4]
    is_bullish = p1.price > points[0].price

    # For a bullish diagonal, the low of wave 4 must be below the high of wave 1.
    passed = (p4.price < p1.price) if is_bullish else (p4.price > p1.price)

    return WaveRuleResult(
        name="Diagonal W4 Overlap W1",
        passed=passed,
        details=f"Wave 4 end ({p4.price:.2f}) vs Wave 1 end ({p1.price:.2f})."
    )

def diagonal_converging_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Guideline: In a contracting diagonal, waves get smaller."""
    len1 = _get_wave_length(points[0], points[1])
    len3 = _get_wave_length(points[2], points[3])
    len5 = _get_wave_length(points[4], points[5])

    # Check if each successive impulse wave is smaller than the last
    passed = len3 < len1 and len5 < len3

    return WaveRuleResult(
        name="Guideline: Converging Shape",
        passed=passed,
        details=f"Lengths W1:{len1:.2f}, W3:{len3:.2f}, W5:{len5:.2f}."
    )

def wave_5_truncation_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Guideline: Checks for a truncated 5th wave."""
    p3, p5 = points[3], points[5]
    is_bullish = p3.price > points[2].price

    # For a bullish impulse, truncation occurs if P5 does not exceed P3.
    # For a bearish impulse, truncation occurs if P5 does not go below P3.
    truncation_detected = (is_bullish and p5.price < p3.price) or \
                          (not is_bullish and p5.price > p3.price)

    return WaveRuleResult(
        name="Guideline: 5th Wave Truncation",
        passed=truncation_detected,
        details=f"P5 ({p5.price:.2f}) failed to exceed P3 ({p3.price:.2f})."
    )

def flat_wave_b_retrace_rule(points: List[WavePoint]) -> WaveRuleResult:
    """Rule: In a Flat, Wave B must retrace at least 90% of Wave A."""
    len_a = _get_wave_length(points[0], points[1])
    retrace_b = _get_wave_length(points[1], points[2])
    ratio = retrace_b / len_a if len_a > 0 else 0

    passed = ratio >= 0.9

    return WaveRuleResult(
        name="Flat B Retracement > 90%",
        passed=passed,
        details=f"Wave B retraced {ratio:.1%} of Wave A."
    )
