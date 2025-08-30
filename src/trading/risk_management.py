import pandas as pd
import pandas_ta as ta
from typing import Dict, Any, Optional, List, Tuple
from src.elliott_wave_engine.core.wave_structure import WavePattern
from src.utils.config_loader import load_config

# --- Configuration ---
config = load_config()
risk_config = config.get('risk', {})
ACCOUNT_SIZE = risk_config.get('account_size', 10000)
RISK_PER_TRADE = risk_config.get('risk_per_trade', 0.01)
ATR_MULTIPLIER = risk_config.get('atr_multiplier', 1.5) # New config for ATR SL
MIN_RR_RATIO = config.get('trading_rules', {}).get('min_rr_ratio', 1.5)

def calculate_atr(historical_data: pd.DataFrame, period: int = 14) -> float:
    """Calculates the Average True Range (ATR) for the given data."""
    if historical_data is None or historical_data.empty:
        return 0.0
    # Ensure columns are named correctly for pandas_ta
    data = historical_data.copy()
    data.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}, inplace=True, errors='ignore')
    atr = data.ta.atr(length=period)
    return atr.iloc[-1] if atr is not None and not atr.empty else 0.0

def _calculate_position_size(entry: float, stop_loss: float, trade_type: str) -> Optional[float]:
    """Calculates the position size based on risk parameters."""
    if not ACCOUNT_SIZE or not RISK_PER_TRADE:
        return None

    dollar_risk = ACCOUNT_SIZE * RISK_PER_TRADE

    if trade_type.upper() == "LONG":
        risk_per_asset = entry - stop_loss
    elif trade_type.upper() == "SHORT":
        risk_per_asset = stop_loss - entry
    else:
        return None

    return dollar_risk / risk_per_asset if risk_per_asset > 0 else None

def _calculate_rr_ratio(entry: float, stop_loss: float, targets: List[float], trade_type: str) -> Optional[float]:
    """Calculates the Risk/Reward ratio for the first target."""
    if not targets:
        return None

    first_target = targets[0]

    if trade_type.upper() == "LONG":
        reward = first_target - entry
        risk = entry - stop_loss
    elif trade_type.upper() == "SHORT":
        reward = entry - first_target
        risk = stop_loss - entry
    else:
        return None

    return round(reward / risk, 2) if risk > 0 else None

def _calculate_confidence_score(pattern: WavePattern) -> float:
    """Calculates a confidence score based on the pattern's quality."""
    return round(pattern.confidence_score, 2)

def _get_fib_retracement(start: float, end: float) -> Dict[float, float]:
    """Calculates Fibonacci retracement levels for a move."""
    height = end - start
    return {level: end - level * height for level in [0.382, 0.5, 0.618]}

def _get_fib_extension(p_start: float, p_end: float, p_retrace_end: float) -> Dict[float, float]:
    """Calculates Fibonacci extension levels from the end of a retracement."""
    height = p_end - p_start
    return {level: p_retrace_end + level * height for level in [1.0, 1.272, 1.618]}

def calculate_trade_parameters(pattern: WavePattern, historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Main function to calculate trade parameters for a given wave pattern.
    It identifies the pattern type and calls the appropriate setup calculator.
    """
    pattern_type = pattern.pattern_type.lower()
    atr_value = calculate_atr(historical_data)
    if atr_value == 0:
        print(f"WARNING: ATR is zero for {pattern.symbol}. Cannot calculate dynamic stop loss.")
        return None

    # --- Impulse Wave Setups (Anticipating a correction) ---
    if "bullish impulse" in pattern_type and len(pattern.points) >= 6:
        return _calculate_impulse_wave_long_setup(pattern, atr_value)
    if "bearish impulse" in pattern_type and len(pattern.points) >= 6:
        return _calculate_impulse_wave_short_setup(pattern, atr_value)

    # --- Zigzag Corrective Wave Setups (Anticipating a reversal) ---
    if "bullish zigzag" in pattern_type and len(pattern.points) >= 4:
        return _calculate_zigzag_long_setup(pattern, atr_value)
    if "bearish zigzag" in pattern_type and len(pattern.points) >= 4:
        return _calculate_zigzag_short_setup(pattern, atr_value)

    return None

def _build_trade_dict(
    trade_type: str, entry: float, stop_loss: float, targets: List[float],
    pattern: WavePattern, reason: str, entry_zone: Tuple[float, float]
) -> Optional[Dict[str, Any]]:
    """Helper function to assemble the final trade dictionary."""

    # Validate that targets are logical
    if trade_type == "LONG" and all(t <= entry for t in targets): return None
    if trade_type == "SHORT" and all(t >= entry for t in targets): return None

    position_size = _calculate_position_size(entry, stop_loss, trade_type)
    rr_ratio = _calculate_rr_ratio(entry, stop_loss, targets, trade_type)
    confidence_score = _calculate_confidence_score(pattern)

    if rr_ratio is None or rr_ratio < MIN_RR_RATIO:
        return None

    return {
        "type": trade_type,
        "entry": entry,
        "stop_loss": stop_loss,
        "targets": targets,
        "position_size": position_size,
        "reason": reason,
        "pattern_type": pattern.pattern_type,
        "rr_ratio": rr_ratio,
        "confidence_score": confidence_score,
        "entry_zone": entry_zone
    }

def _calculate_impulse_wave_long_setup(pattern: WavePattern, atr_value: float) -> Optional[Dict[str, Any]]:
    """Calculates a LONG trade setup after a 5-wave impulse, anticipating a retracement."""
    p0, _, _, _, _, p5 = pattern.points

    # Entry Zone based on Fibonacci retracement of the whole impulse
    retracements = _get_fib_retracement(p0.price, p5.price)
    entry_zone_top = retracements.get(0.382)
    entry_zone_bottom = retracements.get(0.618)
    if entry_zone_top is None or entry_zone_bottom is None: return None

    entry = entry_zone_bottom # Enter at the deeper retracement level

    # SL is placed below the start of the impulse (p0) + ATR buffer
    stop_loss = p0.price - (ATR_MULTIPLIER * atr_value)

    # Targets are extensions from the bottom of the retracement (assumed to be entry price)
    targets = list(_get_fib_extension(p0.price, p5.price, entry).values())
    targets = sorted([t for t in targets if t > entry])

    return _build_trade_dict("LONG", entry, stop_loss, targets, pattern, "Buy on impulse retracement", (entry_zone_top, entry_zone_bottom))

def _calculate_impulse_wave_short_setup(pattern: WavePattern, atr_value: float) -> Optional[Dict[str, Any]]:
    """Calculates a SHORT trade setup after a 5-wave bearish impulse."""
    p0, _, _, _, _, p5 = pattern.points

    retracements = _get_fib_retracement(p5.price, p0.price) # Reversed for short
    entry_zone_top = retracements.get(0.618)
    entry_zone_bottom = retracements.get(0.382)
    if entry_zone_top is None or entry_zone_bottom is None: return None

    entry = entry_zone_bottom # Enter at the lower retracement

    stop_loss = p0.price + (ATR_MULTIPLIER * atr_value)

    # Targets are extensions from the top of the retracement
    height = p0.price - p5.price
    targets = sorted([entry - level * height for level in [1.0, 1.272, 1.618]], reverse=True)
    targets = [t for t in targets if t < entry]

    return _build_trade_dict("SHORT", entry, stop_loss, targets, pattern, "Sell on bearish impulse retracement", (entry_zone_top, entry_zone_bottom))

def _calculate_zigzag_long_setup(pattern: WavePattern, atr_value: float) -> Optional[Dict[str, Any]]:
    """Calculates a LONG trade at the end of a bullish C-wave of a Zigzag."""
    pA, pB, pC = pattern.points[1:4] # A, B, C points

    entry = pC.price

    # Stop loss below the end of C-wave + ATR buffer
    stop_loss = pC.price - (ATR_MULTIPLIER * atr_value)

    # Targets are extensions of the A-wave, projected from the B-wave
    height = pA.price - pattern.points[0].price
    targets = sorted([pB.price + level * height for level in [0.618, 1.0, 1.618]])
    targets = [t for t in targets if t > entry]

    return _build_trade_dict("LONG", entry, stop_loss, targets, pattern, "Buy after bullish Zigzag completion", (entry, entry))

def _calculate_zigzag_short_setup(pattern: WavePattern, atr_value: float) -> Optional[Dict[str, Any]]:
    """Calculates a SHORT trade at the end of a bearish C-wave of a Zigzag."""
    pA, pB, pC = pattern.points[1:4] # A, B, C points

    entry = pC.price

    # Stop loss above the end of C-wave + ATR buffer
    stop_loss = pC.price + (ATR_MULTIPLIER * atr_value)

    # Targets are extensions of the A-wave, projected from the B-wave
    height = pattern.points[0].price - pA.price
    targets = sorted([pB.price - level * height for level in [0.618, 1.0, 1.618]], reverse=True)
    targets = [t for t in targets if t < entry]

    return _build_trade_dict("SHORT", entry, stop_loss, targets, pattern, "Sell after bearish Zigzag completion", (entry, entry))
