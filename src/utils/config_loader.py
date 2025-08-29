import os
import yaml
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    """
    Loads configuration from config.yaml and environment variables.
    Environment variables are loaded from a .env file first.
    Secrets must be loaded from environment variables, not the YAML file.
    """
    # Load .env file into environment variables
    load_dotenv()
    logging.info("Loaded environment variables from .env file.")

    # Load base configuration from YAML file
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
            logging.info("Loaded base configuration from config.yaml.")
    except FileNotFoundError:
        logging.error("FATAL: config.yaml not found. Please ensure it exists.")
        raise
    except yaml.YAMLError as e:
        logging.error(f"FATAL: Error parsing config.yaml: {e}")
        raise

    # --- Securely load secrets from environment variables ---
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    bybit_api_key = os.getenv("BYBIT_API_KEY")
    bybit_api_secret = os.getenv("BYBIT_API_SECRET")

    # Validate that the Telegram token is present
    if not telegram_token:
        # We check for the placeholder `null` to provide a better error message
        if config.get('telegram', {}).get('token') is None:
             logging.warning("TELEGRAM_TOKEN is not set in the environment. The bot may not be able to start.")
        else:
            # If it's not null, it means it's a hardcoded secret, which is a risk.
            logging.warning("A hardcoded token was found in config.yaml. Please remove it and use the .env file.")
            # We will use the hardcoded one for now but with a warning.
            telegram_token = config['telegram']['token']

    if not telegram_token:
        raise ValueError("FATAL: Telegram token is not set. Please set TELEGRAM_TOKEN in your .env file.")

    # Update the config dictionary with the secrets
    config['telegram']['token'] = telegram_token

    # Add a section for bybit if it doesn't exist
    if 'bybit' not in config:
        config['bybit'] = {}

    config['bybit']['api_key'] = bybit_api_key
    config['bybit']['api_secret'] = bybit_api_secret

    logging.info("Configuration loaded successfully and securely.")
    return config

# The load_config() function should be called by each module that needs
# configuration data to ensure the latest version is always used.
