import pandas as pd
from typing import List, Dict, Any, Optional
from src.trading.risk_management import calculate_impulsive_trade, calculate_corrective_trade
from src.elliott_wave_engine.core.wave_structure import WaveScenario

def define_trade_setup(scenarios: List[WaveScenario], historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Analyzes the most confident wave scenario and calls the appropriate
    trade calculation function based on the pattern's type and stage.

    This now implements the user's detailed trading logic:
    - Trade wave 3 or 5 during an impulse.
    - Trade the ABC correction after a completed 5-wave impulse.
    """
    if not scenarios:
        return None

    most_confident_scenario = scenarios[0]
    primary_pattern = most_confident_scenario.primary_pattern
    pattern_type = primary_pattern.pattern_type.lower()
    num_points = len(primary_pattern.points)

    trade_setup = None

    # --- Dispatcher Logic ---

    # If we see a bullish impulse that is still developing (3 or 5 points)
    if 'bullish impulse' in pattern_type and (num_points == 3 or num_points == 5):
        trade_setup = calculate_impulsive_trade(primary_pattern, historical_data)

    # If we see a completed bullish impulse (6 points), look for a short/corrective trade
    elif 'bullish impulse' in pattern_type and num_points >= 6:
        trade_setup = calculate_corrective_trade(primary_pattern, historical_data)

    # (Future) Add logic for bearish impulses to propose long/corrective trades
    # elif 'bearish impulse' in pattern_type and ...

    # (Future) Add logic for trading after corrective patterns like Zigzag
    # elif 'zigzag' in pattern_type and ...

    # --- Return Results ---
    if trade_setup:
        return trade_setup
    else:
        # Return an analysis message if no valid trade setup could be generated
        return {
            "type": "Analysis",
            "reason": f"تم رصد نمط ({primary_pattern.pattern_type}) لكنه ليس في مرحلة قابلة للتداول حاليًا.",
            "details": f"النمط يحتوي على {num_points} نقطة. لا توجد قاعدة تداول لهذه المرحلة."
        }
