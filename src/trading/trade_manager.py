from typing import Dict, Any, Optional

def manage_active_trade(trade: Dict[str, Any], current_price: float) -> Optional[Dict[str, Any]]:
    """
    Manages a single active trade, checking for SL/TP hits and determining actions.

    Args:
        trade: The trade object dictionary from the state manager.
        current_price: The current market price of the asset.

    Returns:
        An event dictionary if an action is required, otherwise None.
    """
    status = trade.get('status', 'ACTIVE')
    if status != 'ACTIVE':
        return None # Only manage active trades

    stop_loss = trade.get('stop_loss')
    targets = trade.get('targets', [])
    hit_targets_indices = trade.get('hit_targets_indices', [])

    # 1. Check for Stop Loss Hit
    if current_price <= stop_loss:
        return {
            'event': 'SL_HIT',
            'trade_id': trade.get('id'),
            'symbol': trade.get('symbol')
        }

    # 2. Check for new Take Profit hits
    for i, target_price in enumerate(targets):
        if i not in hit_targets_indices and current_price >= target_price:
            # This is a new TP hit
            if i == 0: # First Take Profit
                return {
                    'event': 'TP1_HIT',
                    'trade_id': trade.get('id'),
                    'symbol': trade.get('symbol'),
                    'target_index': i,
                    'target_price': target_price,
                    'new_stop_loss': trade.get('entry') # Recommend moving SL to entry
                }
            else: # Subsequent Take Profits
                return {
                    'event': 'TP_HIT',
                    'trade_id': trade.get('id'),
                    'symbol': trade.get('symbol'),
                    'target_index': i,
                    'target_price': target_price
                }

    # 3. If no events, return None
    return None
