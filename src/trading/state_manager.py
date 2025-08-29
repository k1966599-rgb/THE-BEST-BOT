import json
from typing import List, Dict, Any

STATE_FILE = "active_trades.json"

def load_active_trades() -> List[Dict[str, Any]]:
    """
    Loads the list of active trades from the state file.
    Returns an empty list if the file doesn't exist or is invalid.
    """
    try:
        with open(STATE_FILE, "r") as f:
            trades = json.load(f)
            if isinstance(trades, list):
                return trades
            return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_active_trades(trades: List[Dict[str, Any]]) -> bool:
    """
    Saves the list of active trades to the state file.
    Returns True on success, False on failure.
    """
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(trades, f, indent=4)
        return True
    except (IOError, TypeError) as e:
        print(f"ERROR: Could not save active trades to {STATE_FILE}: {e}")
        return False

def add_trade(new_trade: Dict[str, Any]) -> bool:
    """
    Adds a single new trade to the state file.
    """
    active_trades = load_active_trades()
    # Add a unique identifier for the trade if it doesn't have one
    if 'id' not in new_trade:
        import uuid
        new_trade['id'] = str(uuid.uuid4())
    active_trades.append(new_trade)
    return save_active_trades(active_trades)

def remove_trade(trade_id: str) -> bool:
    """
    Removes a trade from the state file by its unique ID.
    """
    active_trades = load_active_trades()
    initial_count = len(active_trades)
    trades_to_keep = [trade for trade in active_trades if trade.get('id') != trade_id]

    if len(trades_to_keep) < initial_count:
        return save_active_trades(trades_to_keep)
    return False # Trade ID not found

def update_trade(updated_trade: Dict[str, Any]) -> bool:
    """
    Updates an existing trade in the state file.
    """
    trade_id = updated_trade.get('id')
    if not trade_id:
        return False

    active_trades = load_active_trades()
    trade_found = False
    for i, trade in enumerate(active_trades):
        if trade.get('id') == trade_id:
            active_trades[i] = updated_trade
            trade_found = True
            break

    if trade_found:
        return save_active_trades(active_trades)
    return False

# --- Deferred Setups State Management ---

DEFERRED_SETUPS_FILE = "deferred_setups.json"

def load_deferred_setups() -> List[Dict[str, Any]]:
    """
    Loads the list of deferred trade setups from its state file.
    """
    try:
        with open(DEFERRED_SETUPS_FILE, "r") as f:
            setups = json.load(f)
            if isinstance(setups, list):
                return setups
            return []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_deferred_setups(setups: List[Dict[str, Any]]) -> bool:
    """
    Saves the list of deferred trade setups to its state file.
    """
    try:
        with open(DEFERRED_SETUPS_FILE, "w") as f:
            json.dump(setups, f, indent=4)
        return True
    except (IOError, TypeError) as e:
        print(f"ERROR: Could not save deferred setups to {DEFERRED_SETUPS_FILE}: {e}")
        return False
