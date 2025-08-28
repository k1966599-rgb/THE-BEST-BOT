import yaml
from typing import Dict, Any
import os
import logging

def load_config() -> Dict[str, Any]:
    """
    Loads the configuration from config.yaml in the root directory.
    """
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if config:
                logging.info("Configuration file loaded successfully.")
                return config
            else:
                logging.warning("Configuration file is empty.")
                return {}
    except FileNotFoundError:
        logging.error(f"Configuration file not found at {config_path}. Please ensure it exists.")
        return {}
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML configuration file: {e}")
        return {}

# Load config once on startup to be used by other modules
config = load_config()

def get_symbols_to_scan() -> list[str]:
    """
    Returns the list of symbols to scan from the config.
    """
    symbols = config.get('symbols_to_scan', [])
    if not symbols or not isinstance(symbols, list):
        logging.warning("'symbols_to_scan' not found or is not a list in config.yaml. Defaulting to BTCUSDT.")
        return ['BTCUSDT']
    return symbols
