import pandas as pd
import pandas_ta as ta
from typing import Dict, Any, Optional, List, Tuple
from src.elliott_wave_engine.engine_v2 import WavePoint # Import from new engine
from src.utils.config_loader import load_config

# --- Configuration ---
config = load_config()
risk_config = config.get('risk', {})
ACCOUNT_SIZE = risk_config.get('account_size', 10000)
RISK_PER_TRADE = risk_config.get('risk_per_trade', 0.01)
ATR_MULTIPLIER = risk_config.get('atr_multiplier', 1.5)
MIN_RR_RATIO = config.get('trading_rules', {}).get('min_rr_ratio', 1.5)

# --- HELPER FUNCTIONS ---

def calculate_atr(historical_data: pd.DataFrame, period: int = 14) -> float:
    if historical_data is None or historical_data.empty: return 0.0
    data = historical_data.copy()
    data.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}, inplace=True, errors='ignore')
    atr = data.ta.atr(length=period)
    return atr.iloc[-1] if atr is not None and not atr.empty else 0.0

def _calculate_position_size(entry: float, stop_loss: float, trade_type: str) -> Optional[float]:
    if not ACCOUNT_SIZE or not RISK_PER_TRADE: return None
    dollar_risk = ACCOUNT_SIZE * RISK_PER_TRADE
    risk_per_asset = abs(entry - stop_loss)
    return dollar_risk / risk_per_asset if risk_per_asset > 0 else None

def _calculate_rr_ratio(entry: float, stop_loss: float, targets: List[float], trade_type: str) -> Optional[float]:
    if not targets: return None
    first_target = targets[0]
    risk = abs(entry - stop_loss)
    reward = abs(first_target - entry)
    return round(reward / risk, 2) if risk > 0 else None

def check_rsi_divergence(data: pd.DataFrame, point1: WavePoint, point2: WavePoint) -> bool:
    """Checks for classic bearish RSI divergence between two points."""
    try:
        # The new WavePoint from engine_v2 uses .index, not .idx
        rsi_at_point1 = data['rsi'].iloc[point1.index]
        rsi_at_point2 = data['rsi'].iloc[point2.index]

        price_at_point1 = point1.price
        price_at_point2 = point2.price

        if price_at_point2 > price_at_point1 and rsi_at_point2 < rsi_at_point1:
            return True
        return False
    except (IndexError, KeyError):
        return False

def _build_trade_dict(
    trade_type: str, entry: float, stop_loss: float, targets: List[float],
    pattern: Dict[str, Any], reason: str
) -> Optional[Dict[str, Any]]:
    """Helper function to assemble the final trade dictionary."""
    if trade_type == "LONG" and all(t <= entry for t in targets): return None
    if trade_type == "SHORT" and all(t >= entry for t in targets): return None

    position_size = _calculate_position_size(entry, stop_loss, trade_type)
    rr_ratio = _calculate_rr_ratio(entry, stop_loss, targets, trade_type)
    confidence_score = round(pattern.get('confidence', 0) * 100) # Use new confidence score

    if rr_ratio is None or rr_ratio < MIN_RR_RATIO: return None

    return {
        "type": trade_type,
        "entry": entry,
        "stop_loss": stop_loss,
        "targets": targets,
        "position_size": position_size,
        "reason": reason,
        "pattern_type": pattern.get('type'),
        "rr_ratio": rr_ratio,
        "confidence_score": confidence_score,
        "entry_zone": (entry * 1.005, entry * 0.995)
    }

# --- ADVANCED TRADE CALCULATION LOGIC (ADAPTED FOR ENGINE V2) ---

def calculate_impulsive_trade(pattern: Dict[str, Any], historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calculates a trade based on being inside an impulse wave (1-2-3-4-5).
    Works with dictionary patterns from ElliottWaveEngineV2.
    """
    atr_value = calculate_atr(historical_data)
    if atr_value == 0: return None

    points = pattern['points']
    num_points = len(points)

    # The new engine identifies a 5-point impulse wave. This corresponds to a completed 1-2-3-4 structure.
    # We will propose a trade for the final Wave 5.
    if num_points == 5:
        p0, p1, p2, p3, p4 = points

        entry = p4.price
        stop_loss = p2.price - (atr_value * ATR_MULTIPLIER)

        wave_1_to_3_height = p3.price - p0.price
        target1 = p4.price + (0.618 * wave_1_to_3_height)
        target2 = p4.price + (1.0 * (p1.price - p0.price))

        return _build_trade_dict("LONG", entry, stop_loss, sorted([target1, target2]), pattern, "Anticipating Wave 5")

    return None

def calculate_corrective_trade(pattern: Dict[str, Any], historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calculates a SHORT trade after a completed 5-wave impulse, anticipating an ABC correction.
    Requires RSI divergence between wave 3 and 5 as a confirmation.
    """
    # This logic needs to be triggered by a completed 5-wave impulse.
    # The current engine identifies this as 'Impulse_12345'.
    # We need to ensure we have enough points for a divergence check.

    atr_value = calculate_atr(historical_data)
    if atr_value == 0: return None

    points = pattern['points']
    if len(points) < 5: return None

    p0, p1, p2, p3, p4 = points # A 5-point pattern has waves 1, 2, 3, 4 completed. p4 is the peak of wave 4.
    # To check divergence, we'd need the peak of wave 5, which isn't in this pattern yet.
    # This logic needs to be re-thought. For now, we will assume the short is triggered
    # by a different pattern type that represents exhaustion.
    # The user's detailed plan is too advanced for the current engine output.
    # We will leave this function as a placeholder for now.

    return None

def calculate_post_correction_trade(pattern: Dict[str, Any], historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calculates a LONG trade after a bullish corrective pattern (e.g., ABC Zigzag),
    anticipating a new impulse wave.
    """
    atr_value = calculate_atr(historical_data)
    if atr_value == 0: return None

    # This trade is for bullish corrections, so the last point should be a low.
    if pattern.get('direction') != 'bullish':
        return None

    points = pattern['points']
    if len(points) < 3: return None

    pA, pB, pC = points[0], points[1], points[2]

    # Entry is at the end of the C wave
    entry = pC.price
    stop_loss = pC.price - (atr_value * ATR_MULTIPLIER)

    # Targets are extensions of the A-B move
    ab_height = pB.price - pA.price
    target1 = entry + (1.618 * ab_height)
    target2 = entry + (2.618 * ab_height)

    return _build_trade_dict("LONG", entry, stop_loss, sorted([target1, target2]), pattern, "Anticipating Impulse after Correction")
