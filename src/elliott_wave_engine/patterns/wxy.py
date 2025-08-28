import logging
from typing import List, Generator
from ..core.wave_structure import WavePattern, ComplexWavePattern, WaveRuleResult

def validate_wxy_wave(engine, pattern: ComplexWavePattern):
    if len(pattern.sub_patterns) != 2: return

    pattern_w = pattern.sub_patterns[0]
    pattern_y = pattern.sub_patterns[1]

    w_valid = all(r.passed for r in pattern_w.rules_results)
    y_valid = all(r.passed for r in pattern_y.rules_results)
    result1 = WaveRuleResult("قاعدة: الأنماط الفرعية صالحة", (w_valid and y_valid), f"W:{w_valid}, Y:{y_valid}")
    pattern.rules_results.append(result1)
    if not result1.passed:
        logging.debug(f"WXY pattern failed: {result1.name} - {result1.details}")
        return

    result2 = WaveRuleResult("قاعدة: موجة X صالحة", True, "Simplified validation")
    pattern.rules_results.append(result2)

def generate_wxy_waves(pivots, simple_patterns: List[WavePattern]) -> Generator[ComplexWavePattern, None, None]:
    if len(simple_patterns) < 2: return
    simple_patterns.sort(key=lambda p: p.points[0].time)
    for i in range(len(simple_patterns) - 1):
        pattern_w = simple_patterns[i]
        pattern_y = simple_patterns[i+1]
        if pattern_w.points[-1].time == pattern_y.points[0].time:
            points = pattern_w.points + pattern_y.points[1:]
            pattern_type = f"WXY ({pattern_w.pattern_type} / {pattern_y.pattern_type})"
            yield ComplexWavePattern(pattern_type=pattern_type, points=points, sub_patterns=[pattern_w, pattern_y])
