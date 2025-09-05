import pandas as pd
from typing import Dict, Any

class TechnicalIndicators:
    def __init__(self, df: pd.DataFrame, config: dict = None):
        self.df = df.copy() # Expects a dataframe with indicators already calculated
        if config is None: config = {}
        self.config = config

    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """
        Analyzes pre-calculated technical indicators from the dataframe and generates a score.
        """
        required_data_length = 200
        if len(self.df) < required_data_length:
            return {'error': 'Not enough data for indicators.', 'total_score': 0}

        latest = self.df.iloc[-1]
        previous = self.df.iloc[-2]
        current_price = latest['Close']

        # --- Analysis using pre-calculated columns ---

        # 1. Momentum Score
        momentum_score = 0
        if latest['RSI_14'] < 30 and latest['MACD_12_26_9'] > latest['MACDs_12_26_9']: momentum_score = 2
        elif latest['RSI_14'] > 70 and latest['MACD_12_26_9'] < latest['MACDs_12_26_9']: momentum_score = -2
        elif latest['MACD_12_26_9'] > latest['MACDs_12_26_9'] and previous['MACD_12_26_9'] < previous['MACDs_12_26_9']: momentum_score = 1
        elif latest['MACD_12_26_9'] < latest['MACDs_12_26_9'] and previous['MACD_12_26_9'] > previous['MACDs_12_26_9']: momentum_score = -1

        # 2. Volatility Score
        volatility_score = 0
        if current_price < latest['BBL_20_2.0']: volatility_score = 1
        elif current_price > latest['BBU_20_2.0']: volatility_score = -1

        # 3. Stochastic Score
        stoch_score = 0
        if latest['STOCHk_14_3_3'] < 20 and latest['STOCHk_14_3_3'] > latest['STOCHd_14_3_3']: stoch_score = 1
        elif latest['STOCHk_14_3_3'] > 80 and latest['STOCHk_14_3_3'] < latest['STOCHd_14_3_3']: stoch_score = -1

        # 4. Volume Score
        volume_score = 0
        obv_slope = self.df['OBV'].rolling(5).mean().diff().iloc[-1]
        price_slope = self.df['Close'].rolling(5).mean().diff().iloc[-1]
        if obv_slope > 0 and price_slope > 0: volume_score = 1
        elif obv_slope < 0 and price_slope < 0: volume_score = -1
        elif obv_slope > 0 and price_slope < 0: volume_score = 2 # Bullish divergence
        elif obv_slope < 0 and price_slope > 0: volume_score = -2 # Bearish divergence

        total_score = momentum_score + volatility_score + stoch_score + volume_score

        return {
            'total_score': total_score,
            'rsi': round(latest['RSI_14'], 2),
            'macd_is_bullish': bool(latest['MACD_12_26_9'] > latest['MACDs_12_26_9']),
            'obv_is_bullish': bool(obv_slope > 0),
        }
