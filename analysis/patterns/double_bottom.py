from typing import Dict, List
from .utils import calculate_dynamic_confidence

def check_double_bottom(df: 'pd.DataFrame', config: dict, highs: List[Dict], lows: List[Dict], current_price: float, price_tolerance: float) -> List[Dict]:
    """
    Checks for the Double Bottom bullish reversal pattern.
    """
    patterns = []
    if len(lows) < 2:
        return patterns

    l1, l2 = lows[-2], lows[-1]

    # Check if the two last lows are around the same price level
    if abs(l1['price'] - l2['price']) / l1['price'] < price_tolerance:
        # Find the intervening high (the neckline)
        intervening_highs = [h for h in highs if h['index'] > l1['index'] and h['index'] < l2['index']]
        if intervening_highs:
            neckline_high = max(intervening_highs, key=lambda x: x['price'])
            neckline_price = neckline_high['price']

            # Ensure the bottoms are below the neckline
            if l1['price'] < neckline_price and l2['price'] < neckline_price:
                height = neckline_price - (l1['price'] + l2['price']) / 2
                if height <= 0: return patterns

                confidence = _calculate_dynamic_confidence(df, config, base_confidence=65, is_bullish=True)

                patterns.append({
                    'name': 'قاع مزدوج (Double Bottom)',
                    'status': 'مكتمل ✅' if current_price > neckline_price else 'قيد التكوين 🟡',
                    'neckline': neckline_price,
                    'bottom_1_price': l1['price'],
                    'bottom_2_price': l2['price'],
                    'calculated_target': neckline_price + height,
                    'confidence': confidence
                })
    return patterns
