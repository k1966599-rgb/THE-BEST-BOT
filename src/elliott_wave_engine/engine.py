from typing import List, Dict, Any, Generator, Optional
from collections import defaultdict
import pandas as pd

from .wave_structure import WavePoint, WavePattern, WaveRuleResult, ComplexWavePattern, WaveScenario
from .indicators.pivots import find_pivots
from .indicators.momentum import calculate_rsi, calculate_macd
from .indicators.volume import analyze_wave_volume
from .generators.impulse_generator import generate_impulse_waves
from .validators.impulse_validator import validate_impulse_wave, score_impulse_wave_guidelines
from .generators.zigzag_generator import generate_zigzag_waves
from .validators.zigzag_validator import validate_zigzag_wave
from .generators.flat_generator import generate_flat_waves
from .validators.flat_validator import validate_flat_wave
from .generators.triangle_generator import generate_triangle_waves
from .validators.triangle_validator import validate_triangle_wave
from .generators.diagonal_generator import generate_diagonal_waves
from .validators.diagonal_validator import validate_diagonal_wave
from .generators.wxy_generator import generate_wxy_waves
from .validators.wxy_validator import validate_wxy_wave

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
        # Calculate RSI and assign it
        self.data['rsi'] = calculate_rsi(self.data)

        # Calculate MACD and join only the new columns to avoid overlap errors
        macd_df = calculate_macd(self.data)
        new_macd_cols = [col for col in macd_df.columns if col not in self.data.columns]
        self.data = self.data.join(macd_df[new_macd_cols])

        # Calculate ATR for dynamic stop-loss and other calculations
        # The pandas-ta library will name the column e.g., "ATRr_14"
        self.data.ta.atr(append=True)

    def _find_pivots(self) -> List[Dict[str, Any]]:
        avg_price = self.data['close'].mean()

        # Dynamic prominence based on timeframe to improve detection
        # Higher prominence for larger timeframes, lower for smaller ones.
        prominence_map = {
            '4h':  avg_price * 0.005,   # 0.5% for 4-hour
            '240': avg_price * 0.005,
            '1h':  avg_price * 0.002,   # 0.2% for 1-hour
            '60':  avg_price * 0.002,
            '15m': avg_price * 0.001,   # 0.1% for 15-minute
            '15':  avg_price * 0.001,
            '5m':  avg_price * 0.0007,  # 0.07% for 5-minute
            '5':   avg_price * 0.0007,
            '3m':  avg_price * 0.0005,  # 0.05% for 3-minute
            '3':   avg_price * 0.0005,
        }
        # Use the timeframe of the engine instance, with a default fallback
        prominence = prominence_map.get(str(self.timeframe), avg_price * 0.002)

        pivots = find_pivots(self.data, prominence=prominence)
        return pivots

    def run_analysis(self, strict: bool = True) -> List[WaveScenario]:
        all_valid_patterns = self._find_all_patterns(strict=strict)
        scenarios = self._group_competing_patterns(all_valid_patterns)
        if self.context and self.depth == 0:
            self._apply_contextual_scoring(scenarios)

        if strict:
            scenarios.sort(key=lambda s: s.primary_pattern.confidence_score, reverse=True)

        self.wave_counts = scenarios
        return self.wave_counts

    def _find_all_patterns(self, strict: bool = True) -> List[WavePattern]:
        valid_patterns = []

        # --- Impulse Waves ---
        for p in generate_impulse_waves(self.pivots):
            validate_impulse_wave(self, p)
            if all(r.passed for r in p.rules_results):
                if strict:
                    score_impulse_wave_guidelines(self, p)
                    p.calculate_confidence()
                valid_patterns.append(p)

        # --- Zigzag Waves ---
        for p in generate_zigzag_waves(self.pivots):
            validate_zigzag_wave(self, p)
            if all(r.passed for r in p.rules_results):
                if strict:
                    p.calculate_confidence()
                valid_patterns.append(p)

        # --- Flat Waves ---
        for p in generate_flat_waves(self.pivots):
            validate_flat_wave(self, p)
            if all(r.passed for r in p.rules_results):
                if strict:
                    p.calculate_confidence()
                valid_patterns.append(p)

        # --- Triangle Waves ---
        for p in generate_triangle_waves(self.pivots):
            validate_triangle_wave(self, p)
            if all(r.passed for r in p.rules_results):
                if strict:
                    p.calculate_confidence()
                valid_patterns.append(p)

        # --- Diagonal Waves ---
        for p in generate_diagonal_waves(self.pivots):
            validate_diagonal_wave(self, p)
            if all(r.passed for r in p.rules_results):
                if strict:
                    p.calculate_confidence()
                valid_patterns.append(p)

        # --- Complex WXY Waves ---
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
            if not competing_patterns: continue
            competing_patterns.sort(key=lambda p: p.confidence_score, reverse=True)
            scenarios.append(WaveScenario(competing_patterns[0], competing_patterns[1:]))
        return scenarios

    def _apply_contextual_scoring(self, scenarios: List[WaveScenario]):
        pass

    def _validate_sub_wave(self, p_start: WavePoint, p_end: WavePoint, is_impulse: bool) -> bool:
        # Optimization: Limit recursion depth to prevent hanging on large datasets
        if self.depth > 0:
            return True

        sub_df = self.data.loc[p_start.time:p_end.time]
        if len(sub_df) < 5: return False
        sub_engine = ElliottWaveEngine(self.symbol, self.timeframe, sub_df, depth=self.depth + 1)
        sub_scenarios = sub_engine.run_analysis()
        if not sub_scenarios: return False
        best_pattern = sub_scenarios[0].primary_pattern
        if is_impulse: return "Impulse" in best_pattern.pattern_type
        else: return "Zigzag" in best_pattern.pattern_type or "Flat" in best_pattern.pattern_type or "Triangle" in best_pattern.pattern_type
