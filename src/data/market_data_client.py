import logging
import requests
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MarketDataClient:
    """
    A client for fetching general market data from public APIs like CoinGecko.
    """
    def __init__(self):
        self.api_base_url = "https://api.coingecko.com/api/v3"
        logging.info("MarketDataClient initialized.")

    def get_global_market_metrics(self) -> Optional[dict]:
        """
        Fetches global cryptocurrency market metrics, including dominance and total market cap.
        """
        try:
            url = f"{self.api_base_url}/global"
            response = requests.get(url)
            response.raise_for_status() # Raise an exception for bad status codes

            data = response.json().get('data', {})

            total_mcap = data.get('total_market_cap', {}).get('usd', 0)
            btc_dominance = data.get('market_cap_percentage', {}).get('btc', 0)
            eth_dominance = data.get('market_cap_percentage', {}).get('eth', 0)

            metrics = {
                'total_market_cap_usd': total_mcap,
                'btc_dominance_percentage': btc_dominance,
                'eth_dominance_percentage': eth_dominance,
            }
            logging.info(f"Successfully fetched global market metrics: {metrics}")
            return metrics

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching global market data from CoinGecko: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred in get_global_market_metrics: {e}", exc_info=True)
            return None

# Example of how to use it:
if __name__ == '__main__':
    client = MarketDataClient()
    metrics = client.get_global_market_metrics()
    if metrics:
        print("Fetched Metrics:")
        for key, value in metrics.items():
            if "percentage" in key:
                print(f"  {key}: {value:.2f}%")
            else:
                print(f"  {key}: ${value:,.2f}")
