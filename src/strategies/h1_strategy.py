import pandas as pd
import traceback
from typing import List, Tuple
from src.data.bybit_client import BybitClient
from src.elliott_wave_engine.core.engine import ElliottWaveEngine
from src.elliott_wave_engine.core.wave_structure import WaveScenario

def h1_strategy(symbol: str, strict: bool = True) -> Tuple[List[WaveScenario], pd.DataFrame]:
    """
    Fetches 1-hour data, runs analysis, and returns the scenarios and the data with indicators.
    """
    try:
        client = BybitClient()
        # Bybit API uses '60' for the 1-hour interval
        historical_data = client.get_historical_data(symbol, "60")

        if historical_data is None or historical_data.empty:
            print(f"Could not fetch historical data for {symbol} on 1h timeframe.")
            return [], pd.DataFrame()

        # Instantiate the engine and run the analysis
        engine = ElliottWaveEngine(symbol, "1h", historical_data)
        scenarios = engine.run_analysis(strict=strict)

        # Return the scenarios and the data used for analysis
        return scenarios, engine.data
    except Exception as e:
        print(f"An error occurred in H1 strategy for {symbol}: {e}")
        traceback.print_exc()
        return [], pd.DataFrame()
