from typing import List, Dict, Any, Optional
from src.trading.risk_management import calculate_smart_sl_tp
from src.analysis.wave_structure import BaseWavePattern

def propose_trade(patterns: List[BaseWavePattern], timeframe: str) -> Optional[Dict[str, Any]]:
    """
    Analyzes the most likely wave pattern to propose a trade with SL/TP.
    """
    if not patterns:
        return None

    # For now, we only analyze the first (most confident) pattern.
    primary_pattern = patterns[0]

    # Refactored logic to determine trade type. This anticipates more
    # descriptive pattern types from the completed engine.
    pattern_type_lower = primary_pattern.pattern_type.lower()

    # Per user request, only propose LONG (BUY) trades for SPOT.
    if "bullish" in pattern_type_lower or "up" in pattern_type_lower:
        trade_type = "LONG"
    else:
        # If the pattern is not clearly bullish, ignore it and propose no trade.
        return None

    # Only LONG trades will proceed past this point.
    trade_params = calculate_smart_sl_tp(primary_pattern, timeframe)

    if not trade_params:
        return None

    # Augment the trade params with more context
    trade_params['reason'] = f"Potential {primary_pattern.pattern_type} pattern detected."
    trade_params['type'] = trade_type

    return trade_params
