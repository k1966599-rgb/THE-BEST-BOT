from typing import List, Dict, Any, Generator
from ..wave_structure import WavePoint, WavePattern

def generate_zigzag_waves(pivots: List[Dict[str, Any]]) -> Generator[WavePattern, None, None]:
    """
    Generates all possible 3-wave zigzag patterns from a list of pivots.
    A zigzag wave is defined by 4 pivots (points 0, A, B, C).
    """
    if len(pivots) < 4:
        return

    for i in range(len(pivots) - 3):
        p = pivots[i:i+4]

        # Bearish Zigzag (correcting an uptrend) has a H-L-H-L pivot sequence
        if (p[0]['type'] == 'H' and p[1]['type'] == 'L' and
            p[2]['type'] == 'H' and p[3]['type'] == 'L'):
            # Basic check: B wave (p2) must be lower than start of A (p0)
            if p[2]['price'] < p[0]['price']:
                points = [WavePoint(x['time'], x['price'], x['type']) for x in p]
                yield WavePattern(pattern_type="زجزاج هابط", points=points)

        # Bullish Zigzag (correcting a downtrend) has a L-H-L-H pivot sequence
        elif (p[0]['type'] == 'L' and p[1]['type'] == 'H' and
              p[2]['type'] == 'L' and p[3]['type'] == 'H'):
            # Basic check: B wave (p2) must be higher than start of A (p0)
            if p[2]['price'] > p[0]['price']:
                points = [WavePoint(x['time'], x['price'], x['type']) for x in p]
                yield WavePattern(pattern_type="زجزاج صاعد", points=points)
