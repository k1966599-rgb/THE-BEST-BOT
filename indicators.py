import pandas as pd
import numpy as np
import talib
from typing import Dict, Any

class TechnicalIndicators:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        # A single lookback for all indicators. The longest is 200 for SMA.
        required_data_length = 200
        if len(self.df) < required_data_length:
            return {'error': f'Not enough data for indicators. Need {required_data_length}, got {len(self.df)}.', 'total_score': 0}

        # --- Calculations ---
        self.df['SMA_200'] = talib.SMA(self.df['close'], timeperiod=200)
        self.df['SMA_50'] = talib.SMA(self.df['close'], timeperiod=50)
        self.df['SMA_20'] = talib.SMA(self.df['close'], timeperiod=20)
        self.df['RSI'] = talib.RSI(self.df['close'], timeperiod=14)
        self.df['MACD'], self.df['MACD_signal'], _ = talib.MACD(self.df['close'], fastperiod=12, slowperiod=26, signalperiod=9)

        # --- Analysis ---
        current_price = self.df['close'].iloc[-1]
        sma_20 = self.df['SMA_20'].iloc[-1]
        sma_50 = self.df['SMA_50'].iloc[-1]
        sma_200 = self.df['SMA_200'].iloc[-1]

        # Trend Score
        trend_strength = 0
        if current_price > sma_20 > sma_50 > sma_200: trend_strength = 4
        elif current_price > sma_20 > sma_50: trend_strength = 2
        elif current_price < sma_20 < sma_50 < sma_200: trend_strength = -4
        elif current_price < sma_20 < sma_50: trend_strength = -2

        # Momentum Score
        rsi = self.df['RSI'].iloc[-1]
        macd = self.df['MACD'].iloc[-1]
        macd_signal = self.df['MACD_signal'].iloc[-1]
        momentum_score = 0
        if rsi < 30 and macd > macd_signal: momentum_score = 2 # Oversold + Bullish cross
        elif rsi > 70 and macd < macd_signal: momentum_score = -2 # Overbought + Bearish cross

        total_score = trend_strength + momentum_score

        return {
            'total_score': total_score,
            'rsi': round(rsi, 2),
            'macd_is_bullish': macd > macd_signal
        }
