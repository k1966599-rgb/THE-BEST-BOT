import pandas as pd
import numpy as np
from typing import Dict, List
from scipy.signal import find_peaks

class SupportResistanceAnalysis:
    """
    وحدة تحليل الدعوم والمقاومة المتقدمة
    تحدد مناطق العرض والطلب وتوفر بيانات مفصلة للتقارير.
    """
    def __init__(self, df: pd.DataFrame, lookback_period: int = 100, tolerance: float = 0.015):
        self.df = df.copy()
        self.lookback_period = lookback_period
        self.tolerance = tolerance

    def find_all_levels(self) -> Dict[str, List[Dict]]:
        data = self.df.tail(self.lookback_period)
        if len(data) < 20: return {'supports': [], 'resistances': []}

        resistance_indices, _ = find_peaks(data['high'], prominence=data['high'].std() * 0.5, distance=5)
        support_indices, _ = find_peaks(-data['low'], prominence=data['low'].std() * 0.5, distance=5)

        supports = [{'price': data['low'].iloc[i], 'volume': data['volume'].iloc[i]} for i in support_indices]
        resistances = [{'price': data['high'].iloc[i], 'volume': data['volume'].iloc[i]} for i in resistance_indices]
        return {'supports': supports, 'resistances': resistances}

    def cluster_levels_to_zones(self, levels: List[Dict]) -> List[Dict]:
        if not levels: return []

        sorted_levels = sorted(levels, key=lambda x: x['price'])
        zones, current_zone = [], [sorted_levels[0]]

        for i in range(1, len(sorted_levels)):
            price_diff = abs(sorted_levels[i]['price'] - current_zone[-1]['price']) / current_zone[-1]['price']
            if price_diff <= self.tolerance:
                current_zone.append(sorted_levels[i])
            else:
                zones.append(self.create_zone_from_cluster(current_zone))
                current_zone = [sorted_levels[i]]
        if current_zone:
            zones.append(self.create_zone_from_cluster(current_zone))
        return zones

    def create_zone_from_cluster(self, cluster: List[Dict]) -> Dict:
        prices = [p['price'] for p in cluster]
        zone_start, zone_end = min(prices), max(prices)
        touches = len(prices)

        # Add a small buffer to single-point zones
        if touches == 1:
            buffer = zone_start * (self.tolerance / 2)
            zone_start -= buffer
            zone_end += buffer

        strength_score = touches * (1 + (sum(p.get('volume', 0) for p in cluster) / self.df['volume'].mean()) / 10)

        if strength_score > 8: strength_text = "عالية جداً"
        elif strength_score > 5: strength_text = "قوية"
        elif strength_score > 2: strength_text = "متوسطة"
        else: strength_text = "ضعيفة"

        return {'start': zone_start, 'end': zone_end, 'touches': touches, 'strength_score': round(strength_score, 2), 'strength_text': strength_text}

    def get_comprehensive_sr_analysis(self) -> Dict:
        if len(self.df) < self.lookback_period:
            return {'error': f'Not enough data for S/R analysis. Need {self.lookback_period}, got {len(self.df)}.', 'sr_score': 0}
        levels = self.find_all_levels()
        support_zones = self.cluster_levels_to_zones(levels['supports'])
        resistance_zones = self.cluster_levels_to_zones(levels['resistances'])

        current_price = self.df['close'].iloc[-1]

        demand_zones = sorted([z for z in support_zones if z['end'] < current_price], key=lambda x: x['strength_score'], reverse=True)
        supply_zones = sorted([z for z in resistance_zones if z['start'] > current_price], key=lambda x: x['strength_score'], reverse=True)

        primary_demand = demand_zones[0] if demand_zones else None
        primary_supply = supply_zones[0] if supply_zones else None

        # Add distance calculation
        if primary_demand:
            primary_demand['distance'] = current_price - primary_demand['end']
        if primary_supply:
            primary_supply['distance'] = primary_supply['start'] - current_price

        sr_score = 0
        if primary_demand: sr_score += primary_demand.get('strength_score', 0) / 2
        if primary_supply: sr_score -= primary_supply.get('strength_score', 0) / 2

        return {
            'primary_demand_zone': primary_demand,
            'primary_supply_zone': primary_supply,
            'sr_score': round(sr_score, 2)
        }
