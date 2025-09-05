import pandas as pd
import numpy as np
from typing import Dict, Any

class TechnicalIndicators:
    def __init__(self, df: pd.DataFrame, config: dict = None):
        self.df = df.copy()
        if config is None: config = {}
        self.config = config

    def _calculate_sma(self, period: int):
        return self.df['close'].rolling(window=period).mean()

    def _calculate_ema(self, period: int):
        return self.df['close'].ewm(span=period, adjust=False).mean()

    def _calculate_rsi(self, period: int = 14):
        delta = self.df['close'].diff(1)
        gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_macd(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        ema_fast = self._calculate_ema(fast_period)
        ema_slow = self._calculate_ema(slow_period)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        return macd_line, signal_line

    def _calculate_bollinger_bands(self, period: int = 20, std_dev: int = 2):
        middle_band = self._calculate_sma(period)
        std = self.df['close'].rolling(window=period).std()
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        return upper_band, middle_band, lower_band

    def _calculate_stochastic(self, k_period: int = 14, d_period: int = 3):
        low_min = self.df['low'].rolling(window=k_period).min()
        high_max = self.df['high'].rolling(window=k_period).max()
        slowk = 100 * ((self.df['close'] - low_min) / (high_max - low_min))
        slowd = slowk.rolling(window=d_period).mean()
        return slowk, slowd

    def _calculate_atr(self, period: int = 14):
        high_low = self.df['high'] - self.df['low']
        high_close = np.abs(self.df['high'] - self.df['close'].shift())
        low_close = np.abs(self.df['low'] - self.df['close'].shift())
        tr = pd.DataFrame({'hl': high_low, 'hc': high_close, 'lc': low_close}).max(axis=1)
        return tr.ewm(alpha=1/period, adjust=False).mean()

    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        required_data_length = 200
        if len(self.df) < required_data_length:
            return {'error': f'Not enough data for indicators.', 'total_score': 0}

        # --- Calculations ---
        sma_200 = self._calculate_sma(200)
        sma_50 = self._calculate_sma(50)
        sma_20 = self._calculate_sma(20)
        rsi = self._calculate_rsi()
        macd, macd_signal = self._calculate_macd()
        upper_band, middle_band, lower_band = self._calculate_bollinger_bands()
        slowk, slowd = self._calculate_stochastic()
        atr = self._calculate_atr(self.config.get('ATR_PERIOD', 14))

        # --- Analysis ---
        current_price = self.df['close'].iloc[-1]

        trend_strength = 0
        if current_price > sma_20.iloc[-1] > sma_50.iloc[-1] > sma_200.iloc[-1]: trend_strength = 4
        elif current_price > sma_20.iloc[-1] > sma_50.iloc[-1]: trend_strength = 2
        elif current_price < sma_20.iloc[-1] < sma_50.iloc[-1] < sma_200.iloc[-1]: trend_strength = -4
        elif current_price < sma_20.iloc[-1] < sma_50.iloc[-1]: trend_strength = -2

        momentum_score = 0
        if rsi.iloc[-1] < 30 and macd.iloc[-1] > macd_signal.iloc[-1]: momentum_score = 2
        elif rsi.iloc[-1] > 70 and macd.iloc[-1] < macd_signal.iloc[-1]: momentum_score = -2

        volatility_score = 0
        if current_price < lower_band.iloc[-1]: volatility_score = 1
        elif current_price > upper_band.iloc[-1]: volatility_score = -1

        stoch_score = 0
        if slowk.iloc[-1] < 20: stoch_score = 1
        elif slowk.iloc[-1] > 80: stoch_score = -1

        total_score = trend_strength + momentum_score + volatility_score + stoch_score

        return {
            'total_score': total_score,
            'rsi': round(rsi.iloc[-1], 2),
            'macd_is_bullish': bool(macd.iloc[-1] > macd_signal.iloc[-1]),
            'bollinger_bands': {
                'upper': round(upper_band.iloc[-1], 4),
                'middle': round(middle_band.iloc[-1], 4),
                'lower': round(lower_band.iloc[-1], 4)
            },
            'stochastic': {
                'slowk': round(slowk.iloc[-1], 2),
                'slowd': round(slowd.iloc[-1], 2)
            },
            'atr': round(atr.iloc[-1], 4)
        }
