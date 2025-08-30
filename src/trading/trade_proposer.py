import pandas as pd
from typing import Dict, Any, Optional

# Import the new trading logic calculators
from src.trading.risk_management import calculate_impulsive_trade, calculate_corrective_trade, calculate_post_correction_trade

def define_trade_setup(analysis_result: Dict[str, Any], historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Takes the analysis result from the V2 engine and calls the appropriate
    trade calculation function.
    """
    if not analysis_result or not analysis_result.get('best_pattern'):
        return None

    best_pattern = analysis_result['best_pattern']
    pattern_type = best_pattern.get('type', '').lower()

    trade_setup = None

    # --- Dispatcher Logic ---
    if 'impulse' in pattern_type:
        trade_setup = calculate_impulsive_trade(best_pattern, historical_data)

    # If we see a bullish corrective pattern, trade the reversal
    elif 'abc' in pattern_type and best_pattern.get('direction') == 'bullish':
        trade_setup = calculate_post_correction_trade(best_pattern, historical_data)

    # --- Return Results ---
    if trade_setup:
        return trade_setup
    else:
        return {
            "type": "Analysis",
            "reason": f"تم رصد نمط ({pattern_type}) لكن لا توجد قاعدة تداول له حاليًا.",
            "details": f"النمط يحتوي على {len(best_pattern.get('points', []))} نقطة."
        }
