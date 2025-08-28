import pandas as pd
import traceback
from typing import List
from src.data.bybit_client import BybitClient
from src.elliott_wave_engine.engine import ElliottWaveEngine
from src.analysis.wave_structure import BaseWavePattern

def h4_long_term_strategy(symbol: str, strict: bool = True) -> List[BaseWavePattern]:
    """
    Fetches 4-hour data and runs the Elliott Wave analysis to find long-term patterns.
    """
    try:
        client = BybitClient()
        # Bybit API uses minutes for intervals, so 4 * 60 = 240
        historical_data = client.get_historical_data(symbol, "240")

        if historical_data is None or historical_data.empty:
            print(f"Could not fetch historical data for {symbol} on 4h timeframe.")
            return []

        # Instantiate the engine and run the analysis
        engine = ElliottWaveEngine(symbol, "4h", historical_data)
        scenarios = engine.run_analysis(strict=strict)

        if not scenarios:
            return []

        # Extract the primary pattern from each scenario and return it
        patterns = [scenario.primary_pattern for scenario in scenarios]

        return patterns
    except Exception as e:
        print(f"An error occurred in H4 strategy for {symbol}: {e}")
        traceback.print_exc()
        return [] # Return empty list on error to prevent hanging
