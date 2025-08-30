import pandas as pd
from typing import List, Dict, Any, Optional
from src.trading.risk_management import calculate_trade_parameters
from src.elliott_wave_engine.core.wave_structure import WaveScenario

def define_trade_setup(scenarios: List[WaveScenario], historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Identifies the best wave scenario and calculates a potential trade setup.

    This function now acts as a high-level orchestrator, delegating all complex
    calculations to the `risk_management` module. Its main responsibilities are:
    1. Select the most confident wave scenario.
    2. Call the appropriate calculator for the identified pattern.
    3. Return the calculated trade setup or an analysis message.
    """
    if not scenarios:
        return None

    # We base the trade proposal on the most confident scenario identified by the engine.
    most_confident_scenario = scenarios[0]
    primary_pattern = most_confident_scenario.primary_pattern

    # Delegate all calculation logic to the specialized function
    trade_setup = calculate_trade_parameters(primary_pattern, historical_data)

    if trade_setup:
        # The setup is valid and meets all criteria (e.g., R:R ratio)
        return trade_setup
    else:
        # If no valid trade setup could be calculated, return a contextual analysis message.
        # This helps in debugging and understanding why a trade was not proposed.
        pattern_type = primary_pattern.pattern_type
        return {
            "type": "Analysis",
            "reason": f"تم رصد نمط ({pattern_type}) لكنه لم يستوفِ شروط الصفقة.",
            "details": "قد يكون السبب نسبة مخاطرة/عائد غير كافية، أو أن النمط غير مكتمل."
        }
