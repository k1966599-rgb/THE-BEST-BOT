import pandas as pd
import traceback
from typing import List, Tuple
import pandas as pd
from src.data.bybit_client import BybitClient
from src.elliott_wave_engine.engine import ElliottWaveEngine
from src.analysis.wave_structure import WavePattern

def h4_long_term_strategy(symbol: str, strict: bool = True) -> Tuple[List[WavePattern], pd.DataFrame]:
    """
    Fetches 4-hour data, runs Elliott Wave analysis, and returns the patterns
    along with the data used (which now includes indicators like ATR).
    """
    try:
        client = BybitClient()
        # Bybit API uses minutes for intervals, so 4 * 60 = 240
        historical_data = client.get_historical_data(symbol, "240")

        if historical_data is None or historical_data.empty:
            print(f"Could not fetch historical data for {symbol} on 4h timeframe.")
            return [], pd.DataFrame()

        # Instantiate the engine and run the analysis
        engine = ElliottWaveEngine(symbol, "4h", historical_data)
        scenarios = engine.run_analysis(strict=strict)

        if not scenarios:
            return [], engine.data

        # Extract the primary pattern from each scenario
        patterns = [scenario.primary_pattern for scenario in scenarios]

        # Return both the patterns and the data (with indicators)
        return patterns, engine.data
    except Exception as e:
        print(f"An error occurred in H4 strategy for {symbol}: {e}")
        traceback.print_exc()
        return [], pd.DataFrame() # Return empty list and DataFrame on error
