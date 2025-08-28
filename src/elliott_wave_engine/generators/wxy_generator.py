from typing import List, Generator
from ..wave_structure import WavePattern, ComplexWavePattern, WavePoint

def generate_wxy_waves(pivots, simple_patterns: List[WavePattern]) -> Generator[ComplexWavePattern, None, None]:
    """
    Generates complex WXY patterns by combining two simple corrective patterns.
    This is a simplified implementation that looks for two adjacent simple correctives.
    """
    if len(simple_patterns) < 2:
        return

    # Sort patterns by their start time to ensure we are combining them in order
    simple_patterns.sort(key=lambda p: p.points[0].time)

    # Optimized: Iterate through adjacent pairs of patterns (O(n) complexity)
    for i in range(len(simple_patterns) - 1):
        pattern_w = simple_patterns[i]
        pattern_y = simple_patterns[i+1]

        # Check if the patterns are consecutive and non-overlapping.
        # The end of W's points should be the start of Y's points.
        if pattern_w.points[-1].time == pattern_y.points[0].time:

            # Combine the points to form the full W-X-Y pattern
            # The structure is W(0,A,B,C) and Y(0,A,B,C).
            # The end of W (point C) is the start of Y (point 0). This point is the X wave.
            points = pattern_w.points + pattern_y.points[1:]

            pattern_type = f"WXY ({pattern_w.pattern_type} / {pattern_y.pattern_type})"

            yield ComplexWavePattern(
                pattern_type=pattern_type,
                points=points,
                sub_patterns=[pattern_w, pattern_y]
            )
