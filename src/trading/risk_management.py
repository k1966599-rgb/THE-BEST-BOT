import pandas as pd
import pandas_ta as ta
from typing import Dict, Any, Optional, List, Tuple
from src.elliott_wave_engine.core.wave_structure import WavePattern, WavePoint
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
        rsi_at_point1 = data['rsi'].iloc[point1.idx]
        rsi_at_point2 = data['rsi'].iloc[point2.idx]

        price_at_point1 = point1.price
        price_at_point2 = point2.price

        # Bearish divergence: Higher high in price, lower high in RSI
        if price_at_point2 > price_at_point1 and rsi_at_point2 < rsi_at_point1:
            return True

        return False
    except (IndexError, KeyError):
        return False

def _build_trade_dict(
    trade_type: str, entry: float, stop_loss: float, targets: List[float],
    pattern: WavePattern, reason: str
) -> Optional[Dict[str, Any]]:
    """Helper function to assemble the final trade dictionary."""
    if trade_type == "LONG" and all(t <= entry for t in targets): return None
    if trade_type == "SHORT" and all(t >= entry for t in targets): return None

    position_size = _calculate_position_size(entry, stop_loss, trade_type)
    rr_ratio = _calculate_rr_ratio(entry, stop_loss, targets, trade_type)

    # Use the simple quality score for now, can be enhanced later
    confidence_score = round(pattern.confidence_score, 2)

    if rr_ratio is None or rr_ratio < MIN_RR_RATIO: return None

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
        "entry_zone": (entry * 1.005, entry * 0.995) # Generic 0.5% entry zone
    }

# --- ADVANCED TRADE CALCULATION LOGIC ---

def calculate_impulsive_trade(pattern: WavePattern, historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calculates a trade based on being inside an impulse wave (1-2-3-4-5).
    - If at wave 2, proposes a trade for wave 3.
    - If at wave 4, proposes a trade for wave 5.
    """
    atr_value = calculate_atr(historical_data)
    if atr_value == 0: return None

    num_points = len(pattern.points)

    # --- Trade Wave 3 (after Wave 2 is complete) ---
    if num_points == 3: # Points 0, 1, 2 are present
        p0, p1, p2 = pattern.points

        # Entry is at the end of wave 2
        entry = p2.price
        stop_loss = p0.price - (atr_value * ATR_MULTIPLIER) # SL below the start of wave 1

        # Target for Wave 3 is 1.618 extension of Wave 1, projected from end of wave 2
        wave_1_height = p1.price - p0.price
        target1 = p2.price + (1.618 * wave_1_height)
        target2 = p2.price + (2.618 * wave_1_height) # Optional larger target

        return _build_trade_dict("LONG", entry, stop_loss, sorted([target1, target2]), pattern, "Anticipating Wave 3")

    # --- Trade Wave 5 (after Wave 4 is complete) ---
    if num_points == 5: # Points 0, 1, 2, 3, 4 are present
        p0, p1, p2, p3, p4 = pattern.points

        entry = p4.price
        stop_loss = p2.price - (atr_value * ATR_MULTIPLIER) # SL below end of wave 2

        # Target for Wave 5 is often related to wave 1
        wave_1_to_3_height = p3.price - p0.price
        target1 = p4.price + (0.618 * wave_1_to_3_height) # User-specified target
        target2 = p4.price + (1.0 * (p1.price - p0.price)) # Wave 5 = Wave 1

        return _build_trade_dict("LONG", entry, stop_loss, sorted([target1, target2]), pattern, "Anticipating Wave 5")

    return None

def calculate_corrective_trade(pattern: WavePattern, historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calculates a SHORT trade after a completed 5-wave impulse, anticipating an ABC correction.
    Requires RSI divergence between wave 3 and 5 as a confirmation.
    """
    atr_value = calculate_atr(historical_data)
    if atr_value == 0: return None

    # Needs a full 5 waves (6 points: 0, 1, 2, 3, 4, 5)
    if len(pattern.points) < 6: return None

    p0, p1, p2, p3, p4, p5 = pattern.points

    # --- RSI Divergence Check (Crucial for Wave 5 exhaustion) ---
    has_divergence = check_rsi_divergence(historical_data, p3, p5)
    if not has_divergence:
        return None # No divergence, no trade

    # Enter SHORT at the end of wave 5
    entry = p5.price
    stop_loss = p5.price + (atr_value * ATR_MULTIPLIER) # Tight SL above the high

    # Target for Wave C is often equal to length of Wave A
    # For now, we use fib retracement of the whole impulse as a proxy
    impulse_height = p5.price - p0.price
    target1 = p5.price - (0.382 * impulse_height)
    target2 = p5.price - (0.500 * impulse_height)
    target3 = p5.price - (0.618 * impulse_height)

    reason = "Anticipating ABC Correction (RSI Divergence Confirmed)"
    return _build_trade_dict("SHORT", entry, stop_loss, sorted([target1, target2, target3]), pattern, reason)
