from typing import List, Dict, Any, Generator
from ..wave_structure import WavePoint, WavePattern

def generate_triangle_waves(pivots: List[Dict[str, Any]]) -> Generator[WavePattern, None, None]:
    """
    Generates all possible 5-wave triangle patterns from a list of pivots.
    A triangle is defined by 6 pivots (0, A, B, C, D, E).
    The basic shape is the same as an impulse, the difference is in the validation.
    """
    if len(pivots) < 6:
        return

    for i in range(len(pivots) - 5):
        p = pivots[i:i+6]

        # Bearish Triangle (starts with a down move, A)
        if (p[0]['type'] == 'H' and p[1]['type'] == 'L' and p[2]['type'] == 'H' and
            p[3]['type'] == 'L' and p[4]['type'] == 'H' and p[5]['type'] == 'L'):
            points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
            yield WavePattern(pattern_type="Bearish Triangle", points=points)

        # Bullish Triangle (starts with an up move, A)
        elif (p[0]['type'] == 'L' and p[1]['type'] == 'H' and p[2]['type'] == 'L' and
              p[3]['type'] == 'H' and p[4]['type'] == 'L' and p[5]['type'] == 'H'):
            points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
            yield WavePattern(pattern_type="Bullish Triangle", points=points)
