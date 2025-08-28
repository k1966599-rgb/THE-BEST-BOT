import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from src.elliott_wave_engine.core.wave_structure import WavePattern
from src.utils.config_loader import config

def get_fib_retracement(start_price: float, end_price: float) -> Dict[float, float]:
    """Calculates Fibonacci retracement levels for a given price move."""
    height = end_price - start_price
    return {
        level: end_price - level * height
        for level in [0.236, 0.382, 0.5, 0.618, 0.786]
    }

def get_fib_extension(start_price: float, end_price: float, retracement_price: float) -> Dict[float, float]:
    """Calculates Fibonacci extension levels."""
    height = end_price - start_price
    return {
        level: retracement_price + level * height
        for level in [0.618, 1.0, 1.272, 1.618, 2.0, 2.618]
    }

def calculate_fibonacci_trade_parameters(pattern: WavePattern, historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calculates trade parameters based on Fibonacci retracement for entry and extension for targets.
    This is the new, primary function for determining trade setups.
    """
    if not pattern or len(pattern.points) < 4:  # Need at least a 3-point move (e.g., 0-A-B)
        return None

    # --- Identify the primary move to measure ---
    # For now, we assume a bullish impulse (0-1-2-3-4-5) or a bullish zigzag (0-A-B-C)
    # The logic can be expanded for more pattern types.
    if "impulse" in pattern.pattern_type.lower() and len(pattern.points) >= 6:
        p_start = pattern.points[0]
        p_end = pattern.points[5]
        p_correction_end = pattern.points[5] # Placeholder, real correction is not yet formed
    elif "zigzag" in pattern.pattern_type.lower():
        p_start = pattern.points[0]
        p_end = pattern.points[1] # The 'A' wave of the impulse that preceded the zigzag
        p_correction_end = pattern.points[3] # The 'C' point of the zigzag
    else:
        # Fallback for other simple patterns, assuming the last 3 points form the move
        p_start = pattern.points[-4] if len(pattern.points) >= 4 else pattern.points[0]
        p_end = pattern.points[-3]
        p_correction_end = pattern.points[-1]

    # --- 1. Calculate Retracement for Entry Zone ---
    retracements = get_fib_retracement(p_start.price, p_end.price)
    entry_zone_top = retracements.get(0.5)
    entry_zone_bottom = retracements.get(0.618)

    if entry_zone_top is None or entry_zone_bottom is None:
        return None

    # This is the "calm" logic: we define a zone and wait.
    # The actual entry trigger will be handled by the proposer logic later.
    # For now, we can use the 61.8 level as the proposed entry.
    entry_price = entry_zone_bottom

    # --- 2. Define Stop-Loss ---
    atr_col = next((col for col in historical_data.columns if 'atr' in col.lower()), None)
    if not atr_col: return None
    latest_atr = historical_data[atr_col].iloc[-1]
    if pd.isna(latest_atr): return None

    # Place SL below the start of the impulse move or the low of the correction, with an ATR buffer.
    stop_loss_price = p_correction_end.price - (2 * latest_atr)
    # For an impulse, the true SL should be below p_start, but p_correction_end is safer after a correction
    if "impulse" in pattern.pattern_type.lower():
        stop_loss_price = p_start.price - (2* latest_atr)


    if stop_loss_price >= entry_price:
        return None # Invalid trade setup

    # --- 3. Calculate Extension for Targets ---
    extensions = get_fib_extension(p_start.price, p_end.price, entry_price)
    targets = [price for level, price in extensions.items() if level >= 1.272]

    # --- 4. Position Sizing (Optional) ---
    account_size = config.get('risk', {}).get('account_size')
    risk_per_trade = config.get('risk', {}).get('risk_per_trade')

    position_size = None
    if account_size and risk_per_trade:
        # Calculate size based on the specific entry price
        dollar_risk = account_size * risk_per_trade
        risk_per_asset = entry_price - stop_loss_price
        if risk_per_asset > 0:
            position_size = dollar_risk / risk_per_asset

    return {
        "entry_zone": (entry_zone_top, entry_zone_bottom),
        "entry": entry_price,
        "stop_loss": stop_loss_price,
        "targets": sorted(targets),
        "position_size": position_size,
        "reason": f"Fib Retracement from {p_start.price:.2f} to {p_end.price:.2f}"
    }
