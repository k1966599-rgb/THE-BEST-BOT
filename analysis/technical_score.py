import pandas as pd
from typing import Dict, Any
from .divergence import detect_divergence

class TechnicalIndicators:
    def __init__(self, df: pd.DataFrame, config: dict = None):
        self.df = df.copy()
        if config is None: config = {}
        self.config = config
        self.rsi_period = config.get('RSI_PERIOD', 14)
        # Assuming standard MACD params
        self.macd_column_base = "MACD_12_26_9"
        self.macd_histogram_col = "MACDh_12_26_9"
        self.macd_signal_col = "MACDs_12_26_9"

    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """
        Analyzes pre-calculated technical indicators from the dataframe, including divergence
        for both RSI and MACD, and generates a score.
        """
        required_data_length = 50
        if len(self.df) < required_data_length:
            return {'error': 'Not enough data for indicators.', 'total_score': 0}

        latest = self.df.iloc[-1]
        price_series = self.df['Close']

        # --- Divergence Analysis ---
        # 1. RSI Divergence
        rsi_series = self.df[f'RSI_{self.rsi_period}']
        rsi_divergences = detect_divergence(price_series, rsi_series)

        # 2. MACD Divergence (using histogram)
        macd_hist_series = self.df[self.macd_histogram_col]
        macd_divergences = detect_divergence(price_series, macd_hist_series)

        divergence_score = 0
        for div in rsi_divergences + macd_divergences:
            if div['type'] == 'Bullish':
                divergence_score += 3
            elif div['type'] == 'Bearish':
                divergence_score -= 3

        # --- Standard Indicator Analysis ---
        momentum_score = 0
        if latest[f'RSI_{self.rsi_period}'] < 30 and latest[self.macd_column_base] > latest[self.macd_signal_col]:
            momentum_score = 2
        elif latest[f'RSI_{self.rsi_period}'] > 70 and latest[self.macd_column_base] < latest[self.macd_signal_col]:
            momentum_score = -2
        # Crossover check
        elif latest[self.macd_column_base] > latest[self.macd_signal_col] and self.df.iloc[-2][self.macd_column_base] < self.df.iloc[-2][self.macd_signal_col]:
            momentum_score = 1
        elif latest[self.macd_column_base] < latest[self.macd_signal_col] and self.df.iloc[-2][self.macd_column_base] > self.df.iloc[-2][self.macd_signal_col]:
            momentum_score = -1

        volatility_score = 0
        if latest['Close'] < latest['BBL_20_2.0']: volatility_score = 1
        elif latest['Close'] > latest['BBU_20_2.0']: volatility_score = -1

        stoch_score = 0
        if latest['STOCHk_14_3_3'] < 20 and latest['STOCHk_14_3_3'] > latest['STOCHd_14_3_3']: stoch_score = 1
        elif latest['STOCHk_14_3_3'] > 80 and latest['STOCHk_14_3_3'] < latest['STOCHd_14_3_3']: stoch_score = -1

        volume_score = 0
        obv_slope = self.df['OBV'].rolling(5).mean().diff().iloc[-1]
        price_slope = self.df['Close'].rolling(5).mean().diff().iloc[-1]
        if obv_slope > 0 and price_slope > 0: volume_score = 1
        elif obv_slope < 0 and price_slope < 0: volume_score = -1
        elif obv_slope > 0 and price_slope < 0: volume_score = 2
        elif obv_slope < 0 and price_slope > 0: volume_score = -2

        total_score = divergence_score + momentum_score + volatility_score + stoch_score + volume_score

        return {
            'total_score': total_score,
            'rsi': round(latest[f'RSI_{self.rsi_period}'], 2),
            'macd_is_bullish': bool(latest[self.macd_column_base] > latest[self.macd_signal_col]),
            'obv_is_bullish': bool(obv_slope > 0),
            'rsi_divergence': rsi_divergences[0] if rsi_divergences else None,
            'macd_divergence': macd_divergences[0] if macd_divergences else None
        }
