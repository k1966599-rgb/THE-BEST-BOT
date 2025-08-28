import pandas as pd
from typing import List, Dict, Any, Optional
from src.trading.risk_management import calculate_smart_sl_tp, calculate_zigzag_trade
from src.elliott_wave_engine.core.wave_structure import WaveScenario

def propose_trade(scenarios: List[WaveScenario], timeframe: str, historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Analyzes the most likely wave scenario to propose a trade with SL/TP.
    """
    if not scenarios:
        return None

    # We only propose a trade based on the primary pattern of the most confident scenario.
    primary_pattern = scenarios[0].primary_pattern

    # Refactored logic to determine trade type. This anticipates more
    # descriptive pattern types from the completed engine.
    pattern_type_lower = primary_pattern.pattern_type.lower()

    # Determine trade type and handle bearish patterns for context only
    if "bullish" in pattern_type_lower or "up" in pattern_type_lower:
        trade_type = "LONG"
        # Only LONG trades will proceed to SL/TP calculation.
        trade_params = calculate_smart_sl_tp(primary_pattern, timeframe, historical_data)
        if not trade_params:
            return None
        trade_params['reason'] = f"نمط {primary_pattern.pattern_type} محتمل."
        trade_params['type'] = trade_type
        return trade_params

    elif "bearish" in pattern_type_lower or "down" in pattern_type_lower:
        # Per user request, identify bearish patterns for context but do not propose a trade.
        # We pass the pattern back so the formatter can display its details.
        return {
            "type": "Analysis",
            "pattern": primary_pattern,
            "reason": f"تم رصد نمط هابط ({primary_pattern.pattern_type}).",
            "details": "التداول على الهابط معطل في الإعدادات."
        }
    elif "zigzag" in pattern_type_lower:
        # For Bullish Zigzags, we can propose a trend-following trade.
        if "bullish" in pattern_type_lower:
            trade_type = "LONG"
            trade_params = calculate_zigzag_trade(primary_pattern, timeframe, historical_data)
            if not trade_params:
                return None
            trade_params['reason'] = f"نهاية نمط تصحيحي من نوع {primary_pattern.pattern_type}."
            trade_params['type'] = trade_type
            return trade_params
        else: # For Bearish Zigzags, provide context only.
            return {
                "type": "Analysis",
                "reason": f"قد يكون النمط التصحيحي ({primary_pattern.pattern_type}) قد اكتمل.",
                "details": "قد يشير هذا إلى استئناف محتمل للاتجاه الرئيسي."
            }
    elif "flat" in pattern_type_lower:
        # Flats are also corrective, but we will only analyze them for now.
        return {
            "type": "Analysis",
            "reason": f"قد يكون النمط التصحيحي ({primary_pattern.pattern_type}) قد اكتمل.",
            "details": "قد يشير هذا إلى استئناف محتمل للاتجاه الرئيسي."
        }
    else:
        # If the pattern is not one of the recognized types, ignore it.
        return None
