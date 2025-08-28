from typing import List, Dict, Any, Generator
from ..wave_structure import WavePoint, WavePattern

def generate_diagonal_waves(pivots: List[Dict[str, Any]]) -> Generator[WavePattern, None, None]:
    if len(pivots) < 6: return
    for i in range(len(pivots) - 5):
        p = pivots[i:i+6]
        if (p[0]['type'] == 'L' and p[1]['type'] == 'H' and p[2]['type'] == 'L' and p[3]['type'] == 'H' and p[4]['type'] == 'L' and p[5]['type'] == 'H'):
            yield WavePattern(pattern_type="Bullish Diagonal", points=[WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p])
        elif (p[0]['type'] == 'H' and p[1]['type'] == 'L' and p[2]['type'] == 'H' and p[3]['type'] == 'L' and p[4]['type'] == 'H' and p[5]['type'] == 'L'):
            yield WavePattern(pattern_type="Bearish Diagonal", points=[WavePoint(x['time'], x['price'], x['type'], x['idx']) for x in p])
