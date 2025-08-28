from typing import List, Dict, Any, Generator
from ..wave_structure import WavePoint, WavePattern

def generate_flat_waves(pivots: List[Dict[str, Any]]) -> Generator[WavePattern, None, None]:
    """
    Generates all possible 3-wave flat patterns from a list of pivots.
    A flat wave is defined by 4 pivots (points 0, A, B, C).
    Its shape is the same as a zigzag, the difference is in the validation rules.
    """
    if len(pivots) < 4:
        return

    for i in range(len(pivots) - 3):
        p = pivots[i:i+4]

        # Bearish Flat (correcting an uptrend) has a H-L-H-L pivot sequence
        if (p[0]['type'] == 'H' and p[1]['type'] == 'L' and
            p[2]['type'] == 'H' and p[3]['type'] == 'L'):
            points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
            yield WavePattern(pattern_type="Bearish Flat", points=points)

        # Bullish Flat (correcting a downtrend) has a L-H-L-H pivot sequence
        elif (p[0]['type'] == 'L' and p[1]['type'] == 'H' and
              p[2]['type'] == 'L' and p[3]['type'] == 'H'):
            points = [WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p]
            yield WavePattern(pattern_type="Bullish Flat", points=points)
