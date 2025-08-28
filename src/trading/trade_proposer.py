import pandas as pd
from typing import List, Dict, Any, Optional
from src.trading.risk_management import calculate_fibonacci_trade_parameters
from src.elliott_wave_engine.core.wave_structure import WaveScenario

def define_trade_setup(scenarios: List[WaveScenario], historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Defines an ideal trade setup based on Fibonacci analysis of a wave pattern.
    It does NOT check the current price; it only defines the setup parameters.
    """
    if not scenarios:
        return None

    # We only propose a trade based on the primary pattern of the most confident scenario.
    primary_pattern = scenarios[0].primary_pattern
    pattern_type_lower = primary_pattern.pattern_type.lower()

    # --- Main Logic: Check for Bullish Patterns to Define a Setup ---
    # As per user request, we are only defining setups for spot (long trades).
    if "bullish" in pattern_type_lower or "up" in pattern_type_lower:

        # All the complex calculation is now in one place.
        trade_setup = calculate_fibonacci_trade_parameters(primary_pattern, historical_data)

        if not trade_setup:
            return None # The pattern was not suitable for a fib-based trade.

        # Add pattern context to the trade setup
        trade_setup['type'] = "LONG"
        trade_setup['pattern_type'] = primary_pattern.pattern_type
        # Overwrite the generic reason with a more specific one if needed
        trade_setup['reason'] = f"نمط {primary_pattern.pattern_type} مع انتظار تصحيح فيبوناتشي."

        return trade_setup

    # --- Contextual Logic: Identify other patterns but do not trade ---
    elif "bearish" in pattern_type_lower or "down" in pattern_type_lower:
        return {
            "type": "Analysis",
            "reason": f"تم رصد نمط هابط ({primary_pattern.pattern_type}).",
            "details": "لن يتم اقتراح صفقة بيع حسب الإعدادات."
        }

    elif "triangle" in pattern_type_lower or "flat" in pattern_type_lower:
        return {
            "type": "Analysis",
            "reason": f"تم رصد نمط تصحيحي جانبي ({primary_pattern.pattern_type}).",
            "details": "هذه الأنماط تشير إلى فترة حيرة في السوق."
        }

    # If the pattern is not one of the recognized types, ignore it for now.
    return None
