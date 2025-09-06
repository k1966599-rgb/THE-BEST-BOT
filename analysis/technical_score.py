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
        for both RSI and MACD, and generates a score and detailed indicator states.
        """
        required_data_length = 50
        if len(self.df) < required_data_length:
            return {'error': 'Not enough data for indicators.', 'total_score': 0, 'positive_indicators': [], 'negative_indicators': []}

        latest = self.df.iloc[-1]
        price_series = self.df['Close']
        positive_indicators = []
        negative_indicators = []

        # --- Divergence Analysis ---
        rsi_series = self.df[f'RSI_{self.rsi_period}']
        rsi_divergences = detect_divergence(price_series, rsi_series)
        macd_hist_series = self.df[self.macd_histogram_col]
        macd_divergences = detect_divergence(price_series, macd_hist_series)

        divergence_score = 0
        for div in rsi_divergences:
            if div['type'] == 'Bullish':
                divergence_score += 3
                positive_indicators.append("وجود دايفرجنس إيجابي على مؤشر RSI")
            elif div['type'] == 'Bearish':
                divergence_score -= 3
                negative_indicators.append("وجود دايفرجنس سلبي على مؤشر RSI")
        for div in macd_divergences:
            if div['type'] == 'Bullish':
                divergence_score += 3
                positive_indicators.append("وجود دايفرجنس إيجابي على مؤشر MACD")
            elif div['type'] == 'Bearish':
                divergence_score -= 3
                negative_indicators.append("وجود دايفرجنس سلبي على مؤشر MACD")

        # --- Standard Indicator Analysis ---
        momentum_score = 0
        if latest[f'RSI_{self.rsi_period}'] < 30:
            momentum_score += 1
            positive_indicators.append(f"مؤشر RSI في منطقة تشبع بيعي ({latest[f'RSI_{self.rsi_period}']:.1f})")
        if latest[f'RSI_{self.rsi_period}'] > 70:
            momentum_score -= 1
            negative_indicators.append(f"مؤشر RSI في منطقة تشبع شرائي ({latest[f'RSI_{self.rsi_period}']:.1f})")

        if latest[self.macd_column_base] > latest[self.macd_signal_col]:
            if self.df.iloc[-2][self.macd_column_base] < self.df.iloc[-2][self.macd_signal_col]:
                momentum_score += 2
                positive_indicators.append("حدوث تقاطع إيجابي جديد في MACD")
            else:
                momentum_score += 1
                positive_indicators.append("مؤشر MACD إيجابي (فوق خط الإشارة)")
        else:
            if self.df.iloc[-2][self.macd_column_base] > self.df.iloc[-2][self.macd_signal_col]:
                momentum_score -= 2
                negative_indicators.append("حدوث تقاطع سلبي جديد في MACD")
            else:
                momentum_score -= 1
                negative_indicators.append("مؤشر MACD سلبي (تحت خط الإشارة)")

        volatility_score = 0
        if latest['Close'] < latest['BBL_20_2.0']:
            volatility_score = 1
            positive_indicators.append("السعر يلامس الحد السفلي لبولينجر باند")
        elif latest['Close'] > latest['BBU_20_2.0']:
            volatility_score = -1
            negative_indicators.append("السعر يلامس الحد العلوي لبولينجر باند")

        stoch_score = 0
        if latest['STOCHk_14_3_3'] < 20:
            stoch_score = 1
            positive_indicators.append("مؤشر ستوكاستيك في منطقة تشبع بيعي")
        elif latest['STOCHk_14_3_3'] > 80:
            stoch_score = -1
            negative_indicators.append("مؤشر ستوكاستيك في منطقة تشبع شرائي")

        volume_score = 0
        obv_slope = self.df['OBV'].rolling(5).mean().diff().iloc[-1]
        price_slope = self.df['Close'].rolling(5).mean().diff().iloc[-1]
        if obv_slope > 0 and price_slope > 0:
            volume_score = 1
            positive_indicators.append("مؤشر OBV يؤكد الاتجاه الصاعد")
        elif obv_slope < 0 and price_slope < 0:
            volume_score = -1
            negative_indicators.append("مؤشر OBV يؤكد الاتجاه الهابط")

        # --- Moving Average Analysis ---
        ma_score = 0
        if 'SMA_50' in self.df.columns and latest['Close'] > latest['SMA_50']:
            ma_score += 1
            positive_indicators.append("السعر يتداول فوق متوسط 50")
        elif 'SMA_50' in self.df.columns:
            ma_score -=1
            negative_indicators.append("السعر يتداول تحت متوسط 50")

        if 'SMA_200' in self.df.columns and latest['Close'] > latest['SMA_200']:
            ma_score += 2
            positive_indicators.append("السعر يتداول فوق متوسط 200 (إشارة طويلة المدى)")
        elif 'SMA_200' in self.df.columns:
            ma_score -= 2
            negative_indicators.append("السعر يتداول تحت متوسط 200 (إشارة طويلة المدى)")

        if 'SMA_50' in self.df.columns and 'SMA_200' in self.df.columns and latest['SMA_50'] > latest['SMA_200']:
            ma_score += 2
            positive_indicators.append("متوسط 50 فوق متوسط 200 (تقاطع ذهبي محتمل)")
        elif 'SMA_50' in self.df.columns and 'SMA_200' in self.df.columns:
            ma_score -= 2
            negative_indicators.append("متوسط 50 تحت متوسط 200 (تقاطع موت محتمل)")


        total_score = divergence_score + momentum_score + volatility_score + stoch_score + volume_score + ma_score

        return {
            'total_score': total_score,
            'rsi': round(latest[f'RSI_{self.rsi_period}'], 2),
            'macd_is_bullish': bool(latest[self.macd_column_base] > latest[self.macd_signal_col]),
            'obv_is_bullish': bool(obv_slope > 0),
            'rsi_divergence': rsi_divergences[0] if rsi_divergences else None,
            'macd_divergence': macd_divergences[0] if macd_divergences else None,
            'positive_indicators': positive_indicators,
            'negative_indicators': negative_indicators
        }
