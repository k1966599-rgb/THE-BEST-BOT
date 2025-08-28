import pandas as pd
from typing import List, Dict, Any, Optional
from src.analysis.wave_structure import WavePattern
from src.utils.config_loader import config

def calculate_position_size(account_size: float, risk_per_trade: float, entry_price: float, sl_price: float) -> Optional[float]:
    """Calculates the position size in the asset."""
    if (entry_price - sl_price) == 0:
        return None

    dollar_risk = account_size * risk_per_trade
    risk_per_asset = entry_price - sl_price
    position_size = dollar_risk / risk_per_asset
    return position_size

def calculate_smart_sl_tp(pattern: WavePattern, timeframe: str, historical_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calculates smart entry, stop-loss (using ATR), take-profit levels, and position size
    based on the key points of a wave pattern and risk parameters.
    """
    # We need a 5-wave impulse (6 points) to calculate SL/TP reliably.
    if not pattern or len(pattern.points) < 6:
        return None

    # Assuming a bullish impulse (0-1-2-3-4-5) as bearish patterns are filtered out.
    p0, p1, p2, p3, p4, p5 = pattern.points

    # --- Refined Entry Logic ---
    # Set entry at a slight pullback from the peak of wave 5 to ensure a better entry price.
    pullback_amount = (p5.price - p4.price) * 0.236 # e.g., 23.6% pullback of wave 5's length
    entry_price = p5.price - pullback_amount

    # --- ATR-based Stop-Loss Logic ---
    # Find the ATR column (e.g., 'ATRr_14')
    atr_col = next((col for col in historical_data.columns if 'atr' in col.lower()), None)
    if not atr_col:
        print("ATR column not found in data. Cannot calculate ATR-based SL.")
        return None

    # Get the latest ATR value
    latest_atr = historical_data[atr_col].iloc[-1]
    if pd.isna(latest_atr):
        print("Latest ATR value is NaN. Cannot calculate SL.")
        return None

    # Place stop-loss below wave 4 using a 2x ATR buffer.
    stop_loss_price = p4.price - (2 * latest_atr)

    # Basic validation: for a long trade, stop loss must be below entry.
    if stop_loss_price >= entry_price:
        return None

    # --- Take-Profit Logic (using Fibonacci Extensions of the whole impulse) ---
    # Calculate the total height of the impulse wave (P5 - P0)
    impulse_height = p5.price - p0.price
    if impulse_height <= 0:
        return None # Should not happen in a valid bullish impulse

    # --- Timeframe-Dependent Target Logic ---
    if timeframe == '4h':
        # Aggressive targets for long-term trades
        tp_multipliers = [1.618, 2.0, 2.618]
    elif timeframe == '1h':
        # Medium targets for mid-term trades
        tp_multipliers = [1.0, 1.618, 2.0]
    else:
        # Conservative targets for short-term/scalp trades (15m, 5m, 3m)
        tp_multipliers = [0.618, 1.0, 1.618]

    # Projecting from the top of the impulse wave (p5) is a standard method.
    targets = [p5.price + (impulse_height * m) for m in tp_multipliers]

    # --- Position Sizing ---
    account_size = config.get('risk', {}).get('account_size')
    risk_per_trade = config.get('risk', {}).get('risk_per_trade')

    position_size = None
    if account_size and risk_per_trade:
        position_size = calculate_position_size(account_size, risk_per_trade, entry_price, stop_loss_price)

    trade_params = {
        "entry": entry_price,
        "stop_loss": stop_loss_price,
        "targets": targets,
        "position_size": position_size
    }

    return trade_params
