import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from src.elliott_wave_engine.core.wave_structure import WavePattern
from src.utils.config_loader import config

def get_fib_retracement(start_price: float, end_price: float) -> Dict[float, float]:
    """Calculates Fibonacci retracement levels for a given price move."""
    height = end_price - start_price
    if height == 0: return {}
    return {
        level: end_price - level * height
        for level in [0.382, 0.5, 0.618, 0.786]
    }

def get_fib_extension(p_start: float, p_end: float, p_correction: float) -> Dict[float, float]:
    """Calculates Fibonacci extension levels."""
    height = p_end - p_start
    if height == 0: return {}
    return {
        level: p_correction + level * height
        for level in [1.0, 1.272, 1.618, 2.0, 2.618]
    }

def calculate_fibonacci_trade_parameters(pattern: WavePattern, historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calculates trade parameters based on the type of Elliott Wave pattern.
    - For Impulse waves (1-5), it anticipates a correction to enter.
    - For Corrective waves (ABC, ABCDE), it enters after the correction is believed to be complete.
    """
    try:
        pattern_type = pattern.pattern_type.lower()
        points = pattern.points

        # --- Strategy 1: Enter on a correction AFTER a 5-wave Impulse ---
        if "impulse" in pattern_type and len(points) >= 6:
            p0, p1, p2, p3, p4, p5 = points

            retracements = get_fib_retracement(p0.price, p5.price)
            entry_zone_top = retracements.get(0.5)
            entry_zone_bottom = retracements.get(0.618)
            if entry_zone_top is None or entry_zone_bottom is None: return None

            entry_price = entry_zone_bottom
            stop_loss_price = p0.price # Invalidation is the start of the impulse

            # Targets are extensions from the potential bottom of the correction (entry_price)
            targets = get_fib_extension(p0.price, p5.price, entry_price)

            reason = f"انتظار تصحيح للموجة الدافعة من {p0.price:.2f} إلى {p5.price:.2f}"

        # --- Strategy 2: Enter AFTER a corrective pattern (Zigzag, Flat, Triangle) ---
        elif any(corr in pattern_type for corr in ["zigzag", "flat", "triangle"]):
            if len(points) < 4: return None # Need at least p0-A-B-C

            p_correction_start = points[0]
            if "triangle" in pattern_type and len(points) >= 6:
                p_correction_end = points[5] # Point E
                p_breakout_level = points[3] # Point D
            else: # ABC patterns
                p_correction_end = points[3] # Point C
                p_breakout_level = points[2] # Point B

            # Entry is a breakout above a key level of the correction
            entry_price = p_breakout_level.price
            stop_loss_price = p_correction_end.price # Invalidation is the low of the correction

            # Targets are extensions from the end of the correction
            targets = get_fib_extension(p_correction_start.price, p_breakout_level.price, p_correction_end.price)

            reason = f"الدخول بعد انتهاء نمط تصحيحي من نوع {pattern.pattern_type}"

        else:
            # Pattern type is not supported for trade calculation
            return None

        # --- Common final calculations ---
        if stop_loss_price >= entry_price: return None

        # --- Position Sizing (Optional) ---
        account_size = config.get('risk', {}).get('account_size')
        risk_per_trade = config.get('risk', {}).get('risk_per_trade')
        position_size = None
        if account_size and risk_per_trade:
            dollar_risk = account_size * risk_per_trade
            risk_per_asset = entry_price - stop_loss_price
            if risk_per_asset > 0:
                position_size = dollar_risk / risk_per_asset

        return {
            "entry_zone": (entry_zone_top, entry_zone_bottom) if "impulse" in pattern_type else (entry_price, entry_price),
            "entry": entry_price,
            "stop_loss": stop_loss_price,
            "targets": sorted(list(targets.values())),
            "position_size": position_size,
            "reason": reason
        }

    except (IndexError, KeyError, TypeError) as e:
        print(f"DEBUG: Could not calculate fib parameters for pattern {pattern.pattern_type} due to structure error: {e}")
        return None
