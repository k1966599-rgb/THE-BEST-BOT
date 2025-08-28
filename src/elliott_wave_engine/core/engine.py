from typing import List, Dict, Any, Generator, Optional
from collections import defaultdict
import pandas as pd

from .wave_structure import WavePoint, WavePattern, ComplexWavePattern, WaveScenario
from ..indicators.pivots import find_pivots
from ..indicators.momentum import calculate_rsi, calculate_macd

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
        macd_df = calculate_macd(self.data)
        new_macd_cols = [col for col in macd_df.columns if col not in self.data.columns]
        self.data = self.data.join(macd_df[new_macd_cols])
        self.data.ta.atr(append=True)

    def _find_pivots(self) -> List[Dict[str, Any]]:
        # Use Average True Range (ATR) for prominence calculation.
        # This makes pivot detection adaptive to each asset's specific volatility.
        # A pivot is only considered significant if it's a multiple of the recent average range.
        if 'ATRr_14' not in self.data.columns or self.data['ATRr_14'].isnull().all():
            avg_price = self.data['close'].mean()
            prominence = avg_price * 0.01
            logging.warning(f"ATR data not found for {self.symbol} on {self.timeframe}. Falling back to price-percent prominence.")
            return find_pivots(self.data, prominence=prominence)

        mean_atr = self.data['ATRr_14'].mean()

        # CRITICAL: Ensure mean_atr is a sane, positive value before using it.
        # A prominence of 0 or NaN will crash the underlying scipy function.
        if not mean_atr or mean_atr <= 0 or pd.isna(mean_atr):
            avg_price = self.data['close'].mean()
            prominence = avg_price * 0.01
            logging.warning(f"Invalid ATR value ({mean_atr}) for {self.symbol} on {self.timeframe}. Falling back to price-percent prominence.")
            return find_pivots(self.data, prominence=prominence)

        # Multipliers for ATR. Higher values find more major pivots.
        prominence_map = {
            '4h':  mean_atr * 5.0,
            '240': mean_atr * 5.0,
            '1h':  mean_atr * 3.0,
            '60':  mean_atr * 3.0,
            '15m': mean_atr * 1.5,
            '15':  mean_atr * 1.5,
            '5m':  mean_atr * 1.0,
            '5':   mean_atr * 1.0,
            '3m':  mean_atr * 0.75,
            '3':   mean_atr * 0.75,
        }
        prominence = prominence_map.get(str(self.timeframe), mean_atr * 2.0) # Default prominence
        return find_pivots(self.data, prominence=prominence)

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
