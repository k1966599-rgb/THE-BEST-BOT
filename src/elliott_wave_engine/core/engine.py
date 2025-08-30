import logging
from typing import List, Dict, Any, Generator, Optional
from collections import defaultdict
import pandas as pd

from .wave_structure import WavePoint, WavePattern, ComplexWavePattern, WaveScenario
from ..indicators.momentum import calculate_rsi, calculate_macd, calculate_stoch_rsi
from ..indicators.volume import calculate_volume_sma
from scipy.signal import find_peaks

# Import pattern logic from the new modular structure
from ..patterns.impulse import generate_impulse_waves, validate_impulse_wave
from ..patterns.zigzag import generate_zigzag_waves, validate_zigzag_wave
from ..patterns.flat import generate_flat_waves, validate_flat_wave
from ..patterns.triangle import generate_triangle_waves, validate_triangle_wave
from ..patterns.diagonal import generate_diagonal_waves, validate_diagonal_wave
from ..patterns.wxy import generate_wxy_waves, validate_wxy_wave


class ElliottWaveEngine:
    def __init__(self, symbol: str, timeframe: str, historical_data: pd.DataFrame, context: dict = None, depth: int = 0):
        self.symbol = symbol
        self.timeframe = timeframe
        self.data = historical_data
        self.context = context
        self.depth = depth
        self.wave_counts: List[WaveScenario] = []
        self._prepare_data()
        self.pivots = self._find_pivots()

    def _prepare_data(self):
        self.data['rsi'] = calculate_rsi(self.data)

        # Calculate MACD
        macd_df = calculate_macd(self.data)
        new_macd_cols = [col for col in macd_df.columns if col not in self.data.columns]
        self.data = self.data.join(macd_df[new_macd_cols])

        # Calculate StochRSI
        stoch_rsi_df = calculate_stoch_rsi(self.data)
        new_stoch_cols = [col for col in stoch_rsi_df.columns if col not in self.data.columns]
        self.data = self.data.join(stoch_rsi_df[new_stoch_cols])

        # Calculate Volume SMA
        self.data['volume_sma'] = calculate_volume_sma(self.data)

        self.data.ta.atr(append=True)

    def _find_pivots(self) -> List[Dict[str, Any]]:
        """
        Internal method to find pivot points. It incorporates robust checks for
        data integrity and uses an adaptive ATR-based prominence.
        """
        # 1. --- Robustness Check: Ensure data has a DatetimeIndex ---
        # This is the permanent fix for the 'int' object has no attribute 'strftime' crash.
        if not isinstance(self.data.index, pd.DatetimeIndex):
            if 'timestamp' in self.data.columns:
                logging.warning(f"Fixing incorrect index for {self.symbol}/{self.timeframe}.")
                self.data = self.data.set_index('timestamp')
                if not isinstance(self.data.index, pd.DatetimeIndex):
                     self.data.index = pd.to_datetime(self.data.index)
            else:
                raise TypeError(f"Cannot find 'timestamp' column to fix index for {self.symbol}/{self.timeframe}.")

        # 2. --- Calculate Prominence using ATR (Median for Robustness) ---
        if 'ATRr_14' not in self.data.columns or self.data['ATRr_14'].isnull().all():
            avg_price = self.data['close'].mean()
            prominence = avg_price * 0.01
            logging.warning(f"ATR data not found for {self.symbol}/{self.timeframe}. Falling back to price-percent prominence.")
        else:
            # Using median instead of mean to make pivot detection more robust against outlier candles (e.g., news spikes)
            median_atr = self.data['ATRr_14'].median()
            if not median_atr or median_atr <= 0 or pd.isna(median_atr):
                avg_price = self.data['close'].mean()
                prominence = avg_price * 0.01
                logging.warning(f"Invalid ATR ({median_atr}) for {self.symbol}/{self.timeframe}. Falling back to price-percent prominence.")
            else:
                # Multipliers adjusted slightly to account for median being generally lower than mean
                prominence_map = {
                    '4h':  median_atr * 10.0,
                    '1h':  median_atr * 7.0,
                    '15m': median_atr * 4.0,
                    '5m':  median_atr * 3.0,
                    '3m':  median_atr * 2.5,
                }
                prominence = prominence_map.get(str(self.timeframe), median_atr * 3.0)

        # 3. --- Find and Clean Pivots ---
        if 'high' not in self.data.columns or 'low' not in self.data.columns:
            raise ValueError("Input DataFrame must contain 'high' and 'low' columns.")

        high_peaks_indices, _ = find_peaks(self.data['high'], prominence=prominence)
        low_peaks_indices, _ = find_peaks(-self.data['low'], prominence=prominence)

        pivots = []
        for i in high_peaks_indices:
            pivots.append({"time": self.data.index[i], "price": self.data['high'].iloc[i], "type": "H", "idx": i})
        for i in low_peaks_indices:
            pivots.append({"time": self.data.index[i], "price": self.data['low'].iloc[i], "type": "L", "idx": i})

        pivots.sort(key=lambda p: p['time'])

        if not pivots: return []

        cleaned_pivots = [pivots[0]]
        for i in range(1, len(pivots)):
            if pivots[i]['type'] != cleaned_pivots[-1]['type']:
                cleaned_pivots.append(pivots[i])

        return cleaned_pivots

    def run_analysis(self, strict: bool = True) -> List[WaveScenario]:
        all_valid_patterns = self._find_all_patterns(strict=strict)
        scenarios = self._group_competing_patterns(all_valid_patterns)
        scenarios.sort(key=lambda s: s.primary_pattern.confidence_score, reverse=True)
        self.wave_counts = scenarios
        return self.wave_counts

    def _find_all_patterns(self, strict: bool = True) -> List[WavePattern]:
        valid_patterns = []
        pattern_generators = {
            "Impulse": generate_impulse_waves,
            "Zigzag": generate_zigzag_waves,
            "Flat": generate_flat_waves,
            "Triangle": generate_triangle_waves,
            "Diagonal": generate_diagonal_waves,
        }
        pattern_validators = {
            "Impulse": validate_impulse_wave,
            "Zigzag": validate_zigzag_wave,
            "Flat": validate_flat_wave,
            "Triangle": validate_triangle_wave,
            "Diagonal": validate_diagonal_wave,
        }
        for name, generator_func in pattern_generators.items():
            for p in generator_func(self.pivots):
                validator_func = pattern_validators.get(name)
                if validator_func:
                    validator_func(self, p) # This now handles rules AND guidelines

                # The validator function populates rules_results. We check if all cardinal rules passed.
                if all(r.passed for r in p.rules_results):
                    if strict:
                        # The validator also populates guidelines_results. Now we can calculate the score.
                        p.calculate_confidence()
                    valid_patterns.append(p)

        # WXY waves are generated from simple correctives
        simple_correctives = [p for p in valid_patterns if "Zigzag" in p.pattern_type or "Flat" in p.pattern_type]
        for p in generate_wxy_waves(self.pivots, simple_correctives):
            validate_wxy_wave(self, p)
            if all(r.passed for r in p.rules_results):
                if strict:
                    p.calculate_confidence()
                valid_patterns.append(p)

        return valid_patterns

    def _group_competing_patterns(self, patterns: List[WavePattern]) -> List[WaveScenario]:
        groups = defaultdict(list)
        for p in patterns: groups[p.points[-1].time].append(p)
        scenarios = []
        for _, competing_patterns in groups.items():
            if competing_patterns:
                competing_patterns.sort(key=lambda p: p.confidence_score, reverse=True)
                scenarios.append(WaveScenario(competing_patterns[0], competing_patterns[1:]))
        return scenarios
