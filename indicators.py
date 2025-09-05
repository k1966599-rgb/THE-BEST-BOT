import pandas as pd
import numpy as np
import talib
from typing import Dict, Any

class TechnicalIndicators:
    def __init__(self, df: pd.DataFrame, config: dict = None):
        self.df = df.copy()
        if config is None: config = {}
        self.config = config

    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        required_data_length = 200
        if len(self.df) < required_data_length:
            return {'error': f'Not enough data for indicators.', 'total_score': 0}

        # --- Calculations ---
        self.df['SMA_200'] = talib.SMA(self.df['close'], timeperiod=200)
        self.df['SMA_50'] = talib.SMA(self.df['close'], timeperiod=50)
        self.df['SMA_20'] = talib.SMA(self.df['close'], timeperiod=20)
        self.df['RSI'] = talib.RSI(self.df['close'], timeperiod=14)
        self.df['MACD'], self.df['MACD_signal'], _ = talib.MACD(self.df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
        self.df['upper_band'], self.df['middle_band'], self.df['lower_band'] = talib.BBANDS(self.df['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        self.df['slowk'], self.df['slowd'] = talib.STOCH(self.df['high'], self.df['low'], self.df['close'], fastk_period=14, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
        self.df['ATR'] = talib.ATR(self.df['high'], self.df['low'], self.df['close'], timeperiod=self.config.get('ATR_PERIOD', 14))

        # --- Analysis ---
        current_price = self.df['close'].iloc[-1]
        sma_20 = self.df['SMA_20'].iloc[-1]
        sma_50 = self.df['SMA_50'].iloc[-1]
        sma_200 = self.df['SMA_200'].iloc[-1]

        trend_strength = 0
        if current_price > sma_20 > sma_50 > sma_200: trend_strength = 4
        elif current_price > sma_20 > sma_50: trend_strength = 2
        elif current_price < sma_20 < sma_50 < sma_200: trend_strength = -4
        elif current_price < sma_20 < sma_50: trend_strength = -2

        rsi = self.df['RSI'].iloc[-1]
        macd = self.df['MACD'].iloc[-1]
        macd_signal = self.df['MACD_signal'].iloc[-1]
        momentum_score = 0
        if rsi < 30 and macd > macd_signal: momentum_score = 2
        elif rsi > 70 and macd < macd_signal: momentum_score = -2

        lower_band = self.df['lower_band'].iloc[-1]
        upper_band = self.df['upper_band'].iloc[-1]
        volatility_score = 0
        if current_price < lower_band: volatility_score = 1
        elif current_price > upper_band: volatility_score = -1

        slowk = self.df['slowk'].iloc[-1]
        stoch_score = 0
        if slowk < 20: stoch_score = 1
        elif slowk > 80: stoch_score = -1

        total_score = trend_strength + momentum_score + volatility_score + stoch_score

        return {
            'total_score': total_score,
            'rsi': round(rsi, 2),
            'macd_is_bullish': macd > macd_signal,
            'bollinger_bands': {
                'upper': round(upper_band, 4),
                'middle': round(self.df['middle_band'].iloc[-1], 4),
                'lower': round(lower_band, 4)
            },
            'stochastic': {
                'slowk': round(slowk, 2),
                'slowd': round(self.df['slowd'].iloc[-1], 2)
            },
            'atr': round(self.df['ATR'].iloc[-1], 4)
        }
