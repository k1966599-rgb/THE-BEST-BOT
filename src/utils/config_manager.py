import ruamel.yaml
from typing import List, Optional

CONFIG_FILE = "config.yaml"

def get_symbols_from_config() -> List[str]:
    """Reads the list of symbols to scan from the config file."""
    yaml, config = _load_yaml_and_config()
    if not config or 'scanner' not in config:
        return []
    return config['scanner'].get('symbols_to_scan', [])

def _load_yaml_and_config():
    """Loads the yaml object and config data."""
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.load(f)
        return yaml, config
    except FileNotFoundError:
        return None, None

def add_symbol_to_config(symbol: str) -> bool:
    """
    Adds a new symbol to the 'symbols_to_scan' list in config.yaml,
    preserving comments and formatting.
    Returns True if the symbol was added, False if it already existed or failed.
    """
    yaml, config = _load_yaml_and_config()
    if not config or 'scanner' not in config:
        return False

    # Ensure 'symbols_to_scan' exists in the scanner section
    if 'symbols_to_scan' not in config['scanner'] or config['scanner']['symbols_to_scan'] is None:
        config['scanner']['symbols_to_scan'] = []

    symbols = config['scanner']['symbols_to_scan']
    if symbol in symbols:
        return False  # Symbol already exists

    symbols.append(symbol)
    # The list is modified in-place, so we just need to dump the config.

    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f)

    return True

def remove_symbol_from_config(symbol: str) -> bool:
    """
    Removes a symbol from the 'symbols_to_scan' list in config.yaml,
    preserving comments and formatting.
    Returns True if the symbol was removed, False if it was not found or failed.
    """
    yaml, config = _load_yaml_and_config()
    if not config or 'scanner' not in config or 'symbols_to_scan' not in config['scanner']:
        return False

    symbols = config['scanner']['symbols_to_scan']
    if symbol not in symbols:
        return False # Symbol not found

    symbols.remove(symbol)
    # The list is modified in-place, so we just need to dump the config.

    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f)

    return True
