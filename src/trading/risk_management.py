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

def _calculate_rr_ratio(entry: float, stop_loss: float, targets: List[float]) -> Optional[float]:
    """Calculates the Risk/Reward ratio for the first target."""
    if not targets or (entry - stop_loss) == 0:
        return None

    reward = targets[0] - entry
    risk = entry - stop_loss
    return round(reward / risk, 2) if risk > 0 else None

def _calculate_confidence_score(pattern: WavePattern) -> float:
    """
    Calculates a confidence score for the trade setup.
    For now, it's primarily based on the underlying Elliott Wave pattern's confidence.
    """
    # Base score is the pattern's confidence from the engine's guideline checks
    base_score = pattern.confidence_score

    # Future enhancements could add points for other confluences (e.g., proximity to key moving averages, etc.)

    return round(base_score, 2)

def calculate_fibonacci_trade_parameters(pattern: WavePattern, historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calculates trade parameters, now including R:R and a confidence score.
    """
    try:
        pattern_type = pattern.pattern_type.lower()
        points = pattern.points

        if "impulse" in pattern_type and len(points) >= 6:
            p0, _, _, _, _, p5 = points
            retracements = get_fib_retracement(p0.price, p5.price)
            entry_zone_top = retracements.get(0.5)
            entry_zone_bottom = retracements.get(0.618)
            if entry_zone_top is None or entry_zone_bottom is None: return None
            entry_price = entry_zone_bottom
            stop_loss_price = p0.price
            targets = get_fib_extension(p0.price, p5.price, entry_price)
            reason = f"انتظار تصحيح للموجة الدافعة"
        elif any(corr in pattern_type for corr in ["zigzag", "flat", "triangle"]):
            if len(points) < 4: return None
            p_correction_start = points[0]
            p_breakout_level = points[2] if "zigzag" in pattern_type or "flat" in pattern_type else points[3] # B or D
            p_correction_end = points[3] if "zigzag" in pattern_type or "flat" in pattern_type else points[5] # C or E
            entry_price = p_breakout_level.price
            stop_loss_price = p_correction_end.price
            targets = get_fib_extension(p_correction_start.price, p_breakout_level.price, p_correction_end.price)
            reason = f"الدخول بعد انتهاء نمط تصحيحي"
        else:
            return None

        if stop_loss_price >= entry_price: return None

        final_targets = sorted(list(targets.values()))
        if not final_targets: return None

        # --- NEW: Calculate R:R and Confidence ---
        rr_ratio = _calculate_rr_ratio(entry_price, stop_loss_price, final_targets)
        confidence_score = _calculate_confidence_score(pattern)

        # --- Position Sizing ---
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
            "targets": final_targets,
            "position_size": position_size,
            "reason": f"{reason} ({pattern.pattern_type})",
            "pattern_type": pattern.pattern_type,
            "rr_ratio": rr_ratio,
            "confidence_score": confidence_score
        }

    except (IndexError, KeyError, TypeError, AttributeError) as e:
        print(f"DEBUG: Could not calculate fib parameters for pattern {pattern.pattern_type} due to structure error: {e}")
        return None
