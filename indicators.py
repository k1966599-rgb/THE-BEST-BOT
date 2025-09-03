import pandas as pd
import numpy as np
import talib
from typing import Dict, Any, Tuple

class TechnicalIndicators:
    """وحدة المؤشرات الفنية الشاملة"""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.signals = {}

    def calculate_moving_averages(self) -> Dict[str, Any]:
        """حساب المتوسطات المتحركة"""
        # Simple Moving Averages
        self.df['SMA_20'] = talib.SMA(self.df['close'], timeperiod=20)
        self.df['SMA_50'] = talib.SMA(self.df['close'], timeperiod=50)
        self.df['SMA_200'] = talib.SMA(self.df['close'], timeperiod=200)

        # Exponential Moving Averages
        self.df['EMA_12'] = talib.EMA(self.df['close'], timeperiod=12)
        self.df['EMA_26'] = talib.EMA(self.df['close'], timeperiod=26)
        self.df['EMA_50'] = talib.EMA(self.df['close'], timeperiod=50)

        # تحليل اتجاه المتوسطات
        current_price = self.df['close'].iloc[-1]
        sma_20 = self.df['SMA_20'].iloc[-1]
        sma_50 = self.df['SMA_50'].iloc[-1]
        sma_200 = self.df['SMA_200'].iloc[-1]

        trend_strength = 0
        if current_price > sma_20 > sma_50 > sma_200:
            trend = "صاعد قوي"
            trend_strength = 4
        elif current_price > sma_20 > sma_50:
            trend = "صاعد متوسط"
            trend_strength = 3
        elif current_price > sma_20:
            trend = "صاعد ضعيف"
            trend_strength = 2
        elif current_price < sma_20 < sma_50 < sma_200:
            trend = "هابط قوي"
            trend_strength = -4
        elif current_price < sma_20 < sma_50:
            trend = "هابط متوسط"
            trend_strength = -3
        elif current_price < sma_20:
            trend = "هابط ضعيف"
            trend_strength = -2
        else:
            trend = "عرضي"
            trend_strength = 0

        return {
            'trend': trend,
            'strength': trend_strength,
            'current_price': current_price,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'sma_200': sma_200,
            'ema_12': self.df['EMA_12'].iloc[-1],
            'ema_26': self.df['EMA_26'].iloc[-1]
        }

    def calculate_momentum_indicators(self) -> Dict[str, Any]:
        """مؤشرات الزخم"""
        # RSI
        self.df['RSI'] = talib.RSI(self.df['close'], timeperiod=14)

        # MACD
        self.df['MACD'], self.df['MACD_signal'], self.df['MACD_hist'] = talib.MACD(
            self.df['close'], fastperiod=12, slowperiod=26, signalperiod=9
        )

        # Stochastic
        self.df['STOCH_K'], self.df['STOCH_D'] = talib.STOCH(
            self.df['high'], self.df['low'], self.df['close'],
            fastk_period=14, slowk_period=3, slowd_period=3
        )

        # Williams %R
        self.df['WILLIAMS_R'] = talib.WILLR(
            self.df['high'], self.df['low'], self.df['close'], timeperiod=14
        )

        # تحليل المؤشرات
        rsi = self.df['RSI'].iloc[-1]
        macd = self.df['MACD'].iloc[-1]
        macd_signal = self.df['MACD_signal'].iloc[-1]
        stoch_k = self.df['STOCH_K'].iloc[-1]
        williams_r = self.df['WILLIAMS_R'].iloc[-1]

        # تقييم الزخم
        momentum_score = 0
        momentum_signals = []

        # RSI Analysis
        if rsi > 70:
            momentum_signals.append("RSI: ذروة شراء")
            momentum_score -= 2
        elif rsi < 30:
            momentum_signals.append("RSI: ذروة بيع")
            momentum_score += 2
        elif 50 < rsi < 70:
            momentum_signals.append("RSI: إيجابي")
            momentum_score += 1
        elif 30 < rsi < 50:
            momentum_signals.append("RSI: سلبي")
            momentum_score -= 1

        # MACD Analysis
        if macd > macd_signal and macd > 0:
            momentum_signals.append("MACD: إشارة شراء قوية")
            momentum_score += 2
        elif macd > macd_signal and macd < 0:
            momentum_signals.append("MACD: إشارة شراء ضعيفة")
            momentum_score += 1
        elif macd < macd_signal and macd < 0:
            momentum_signals.append("MACD: إشارة بيع قوية")
            momentum_score -= 2
        else:
            momentum_signals.append("MACD: إشارة بيع ضعيفة")
            momentum_score -= 1

        return {
            'rsi': rsi,
            'macd': macd,
            'macd_signal': macd_signal,
            'stoch_k': stoch_k,
            'stoch_d': self.df['STOCH_D'].iloc[-1],
            'williams_r': williams_r,
            'momentum_score': momentum_score,
            'signals': momentum_signals
        }

    def calculate_volatility_indicators(self) -> Dict[str, Any]:
        """مؤشرات التذبذب"""
        # Bollinger Bands
        self.df['BB_upper'], self.df['BB_middle'], self.df['BB_lower'] = talib.BBANDS(
            self.df['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0
        )

        # Average True Range
        self.df['ATR'] = talib.ATR(self.df['high'], self.df['low'], self.df['close'], timeperiod=14)

        # Directional Movement Index
        self.df['PLUS_DI'] = talib.PLUS_DI(self.df['high'], self.df['low'], self.df['close'], timeperiod=14)
        self.df['MINUS_DI'] = talib.MINUS_DI(self.df['high'], self.df['low'], self.df['close'], timeperiod=14)

        current_price = self.df['close'].iloc[-1]
        bb_upper = self.df['BB_upper'].iloc[-1]
        bb_middle = self.df['BB_middle'].iloc[-1]
        bb_lower = self.df['BB_lower'].iloc[-1]
        atr = self.df['ATR'].iloc[-1]

        # تحليل البولنجر باند
        bb_position = ""
        volatility_score = 0

        if current_price > bb_upper:
            bb_position = "فوق البولنجر العلوي - احتمالية تصحيح"
            volatility_score -= 1
        elif current_price < bb_lower:
            bb_position = "تحت البولنجر السفلي - احتمالية ارتداد"
            volatility_score += 1
        elif current_price > bb_middle:
            bb_position = "فوق الوسط - اتجاه إيجابي"
            volatility_score += 0.5
        else:
            bb_position = "تحت الوسط - اتجاه سلبي"
            volatility_score -= 0.5

        return {
            'bb_upper': bb_upper,
            'bb_middle': bb_middle,
            'bb_lower': bb_lower,
            'bb_position': bb_position,
            'atr': atr,
            'volatility_score': volatility_score,
            'squeeze': abs(bb_upper - bb_lower) / bb_middle < 0.1  # ضغط التذبذب
        }

    def calculate_volume_indicators(self) -> Dict[str, Any]:
        """مؤشرات الحجم"""
        if 'volume' not in self.df.columns:
            return {'error': 'بيانات الحجم غير متوفرة'}

        # Volume Moving Average
        self.df['Volume_SMA'] = talib.SMA(self.df['volume'], timeperiod=20)

        # Money Flow Index
        self.df['MFI'] = talib.MFI(
            self.df['high'], self.df['low'], self.df['close'],
            self.df['volume'], timeperiod=14
        )

        # On Balance Volume
        self.df['OBV'] = talib.OBV(self.df['close'], self.df['volume'])

        current_volume = self.df['volume'].iloc[-1]
        avg_volume = self.df['Volume_SMA'].iloc[-1]
        mfi = self.df['MFI'].iloc[-1]

        volume_analysis = ""
        volume_score = 0

        if current_volume > avg_volume * 1.5:
            volume_analysis = "حجم تداول عالي - قوة في الحركة"
            volume_score += 2
        elif current_volume > avg_volume:
            volume_analysis = "حجم تداول فوق المتوسط"
            volume_score += 1
        elif current_volume < avg_volume * 0.5:
            volume_analysis = "حجم تداول ضعيف"
            volume_score -= 1
        else:
            volume_analysis = "حجم تداول عادي"

        return {
            'current_volume': current_volume,
            'avg_volume': avg_volume,
            'mfi': mfi,
            'obv': self.df['OBV'].iloc[-1],
            'volume_analysis': volume_analysis,
            'volume_score': volume_score
        }

    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """التحليل الشامل للمؤشرات"""
        ma_analysis = self.calculate_moving_averages()
        momentum_analysis = self.calculate_momentum_indicators()
        volatility_analysis = self.calculate_volatility_indicators()
        volume_analysis = self.calculate_volume_indicators()

        # حساب النتيجة الإجمالية
        total_score = (
            ma_analysis.get('strength', 0) +
            momentum_analysis.get('momentum_score', 0) +
            volatility_analysis.get('volatility_score', 0) +
            volume_analysis.get('volume_score', 0)
        )

        # تحديد التوصية
        if total_score >= 6:
            recommendation = "شراء قوي"
        elif total_score >= 3:
            recommendation = "شراء"
        elif total_score >= -2:
            recommendation = "انتظار/محايد"
        elif total_score >= -5:
            recommendation = "بيع"
        else:
            recommendation = "بيع قوي"

        return {
            'moving_averages': ma_analysis,
            'momentum': momentum_analysis,
            'volatility': volatility_analysis,
            'volume': volume_analysis,
            'total_score': total_score,
            'recommendation': recommendation,
            'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
