import numpy as np
from typing import Dict, List
from .utils import calculate_dynamic_confidence

def check_ascending_triangle(df: 'pd.DataFrame', config: dict, highs: List[Dict], lows: List[Dict], current_price: float, price_tolerance: float) -> List[Dict]:
    """
    Checks for the Ascending Triangle bullish pattern.
    """
    patterns = []
    if len(highs) < 2 or len(lows) < 2:
        return patterns

    # Find a flat resistance line
    last_high_price = highs[-1]['price']
    resistance_highs = [h for h in highs if abs(h['price'] - last_high_price) / last_high_price < price_tolerance]

    if len(resistance_highs) < 2:
        return patterns

    resistance_line_price = np.mean([h['price'] for h in resistance_highs])

    # Find a series of higher lows
    higher_lows = []
    for i in range(len(lows) - 1):
        if lows[i+1]['price'] > lows[i]['price']:
            if not higher_lows or lows[i]['price'] > higher_lows[-1]['price']:
                 higher_lows.append(lows[i])
    if len(lows) > 0 and (not higher_lows or lows[-1]['price'] > higher_lows[-1]['price']):
        higher_lows.append(lows[-1])

    if len(higher_lows) < 2:
        return patterns

    # Ensure the last low is below the resistance
    if higher_lows[-1]['price'] > resistance_line_price:
        return patterns

    height = resistance_line_price - higher_lows[0]['price']
    if height <= 0: return patterns

    confidence = _calculate_dynamic_confidence(df, config, base_confidence=70, is_bullish=True)

    patterns.append({
        'name': 'مثلث صاعد (Ascending Triangle)',
        'status': 'مكتمل ✅' if current_price > resistance_line_price else 'قيد التكوين 🟡',
        'resistance_line': resistance_line_price,
        'support_line_start': higher_lows[0]['price'],
        'support_line': higher_lows[-1]['price'],  # Use the last higher low for a tighter S/L
        'calculated_target': resistance_line_price + height,
        'confidence': confidence
    })
    return patterns
