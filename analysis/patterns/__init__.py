import pandas as pd
from typing import Dict, List

from .ascending_triangle import check_ascending_triangle
from .double_bottom import check_double_bottom
from .bull_flag import check_bull_flag
from .bear_flag import check_bear_flag
# Import other pattern checkers here as they are created

def check_all_patterns(df: pd.DataFrame, config: dict, highs: List[Dict], lows: List[Dict], current_price: float, price_tolerance: float) -> List[Dict]:
    """
    Runs all individual pattern checkers and aggregates the results.
    """
    all_patterns = []

    # Call each pattern checker and extend the list
    all_patterns.extend(check_ascending_triangle(df, config, highs, lows, current_price, price_tolerance))
    all_patterns.extend(check_double_bottom(df, config, highs, lows, current_price, price_tolerance))
    all_patterns.extend(check_bull_flag(df, config, highs, lows, current_price, price_tolerance))
    all_patterns.extend(check_bear_flag(df, config, highs, lows, current_price, price_tolerance))
    # Extend with other checkers here

    return all_patterns
