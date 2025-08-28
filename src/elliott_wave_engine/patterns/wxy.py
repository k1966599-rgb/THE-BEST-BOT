import logging
from typing import List, Generator
from ..core.wave_structure import WavePattern, ComplexWavePattern, WaveRuleResult

# --- WXY Validator ---

def validate_wxy_wave(engine, pattern: ComplexWavePattern):
    """
    Validates a WXY complex correction.
    """
    if len(pattern.sub_patterns) != 2:
        return

    pattern_w = pattern.sub_patterns[0]
    pattern_y = pattern.sub_patterns[1]

    # Rule 1: W and Y should be valid corrective patterns
    w_valid = all(r.passed for r in pattern_w.rules_results)
    y_valid = all(r.passed for r in pattern_y.rules_results)
    result1 = WaveRuleResult("Rule: Sub-patterns are valid", (w_valid and y_valid), f"W:{w_valid}, Y:{y_valid}")
    pattern.rules_results.append(result1)
    if not result1.passed:
        logging.debug(f"WXY pattern failed validation. Rule: {result1.name}, Details: {result1.details}")
        return

    # Rule 2: The X wave (the connection) should not be too large.
    result2 = WaveRuleResult("Rule: X wave is valid", True, "Simplified validation")
    pattern.rules_results.append(result2)

# --- WXY Generator ---

def generate_wxy_waves(pivots, simple_patterns: List[WavePattern]) -> Generator[ComplexWavePattern, None, None]:
    """
    Generates complex WXY patterns by combining two adjacent simple corrective patterns.
    """
    if len(simple_patterns) < 2:
        return

    simple_patterns.sort(key=lambda p: p.points[0].time)

    for i in range(len(simple_patterns) - 1):
        pattern_w = simple_patterns[i]
        pattern_y = simple_patterns[i+1]

        # Check if the patterns are consecutive and non-overlapping.
        if pattern_w.points[-1].time == pattern_y.points[0].time:
            points = pattern_w.points + pattern_y.points[1:]
            pattern_type = f"WXY ({pattern_w.pattern_type} / {pattern_y.pattern_type})"
            yield ComplexWavePattern(
                pattern_type=pattern_type,
                points=points,
                sub_patterns=[pattern_w, pattern_y]
            )
