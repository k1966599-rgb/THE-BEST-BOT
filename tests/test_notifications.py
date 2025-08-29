import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.background_scanner import handle_analysis_notifications

@pytest.fixture
def mock_app():
    """Fixture to create a mock application object with a mock bot."""
    app = MagicMock()
    app.bot = AsyncMock()
    return app

@pytest.mark.asyncio
async def test_sends_notification_for_new_stage(mock_app):
    """
    Tests that a notification is sent when a new, more advanced stage is detected.
    """
    # GIVEN an analysis context with a new stage
    mock_scenario = MagicMock()
    mock_scenario.start_point.time = '2025-01-01'
    context = {
        'symbol': 'BTCUSDT',
        'decision_path': ['P(4h)', '->OK:impul', 'STAGE_PASSED:4h'],
        '4h_scenarios': [mock_scenario]
    }
    user_id = 12345

    # AND the current notification state is empty
    with patch('src.background_scanner.load_notification_state', return_value={}) as mock_load, \
         patch('src.background_scanner.save_notification_state') as mock_save:

        # WHEN we handle the notification
        await handle_analysis_notifications(mock_app, user_id, context)

        # THEN a message should be sent
        mock_app.bot.send_message.assert_called_once()
        sent_text = mock_app.bot.send_message.call_args[1]['text']
        assert "فرصة محتملة | BTCUSDT | 4H" in sent_text

        # AND the state should be updated and saved
        mock_save.assert_called_once_with({'BTCUSDT_2025-01-01': 'STAGE_PASSED:4h'})

@pytest.mark.asyncio
async def test_does_not_send_notification_for_same_stage(mock_app):
    """
    Tests that a notification is NOT sent if the stage has already been notified.
    """
    # GIVEN an analysis context
    mock_scenario = MagicMock()
    mock_scenario.start_point.time = '2025-01-01'
    context = {
        'symbol': 'BTCUSDT',
        'decision_path': ['P(4h)', '->OK:impul', 'STAGE_PASSED:4h'],
        '4h_scenarios': [mock_scenario]
    }
    user_id = 12345

    # AND the notification for this stage has already been sent
    existing_state = {'BTCUSDT_2025-01-01': 'STAGE_PASSED:4h'}
    with patch('src.background_scanner.load_notification_state', return_value=existing_state) as mock_load, \
         patch('src.background_scanner.save_notification_state') as mock_save:

        # WHEN we handle the notification
        await handle_analysis_notifications(mock_app, user_id, context)

        # THEN no message should be sent
        mock_app.bot.send_message.assert_not_called()

        # AND the state should not be saved again
        mock_save.assert_not_called()

@pytest.mark.asyncio
async def test_sends_notification_for_upgraded_stage(mock_app):
    """
    Tests that a notification is sent when an opportunity progresses to a new stage.
    """
    # GIVEN an analysis context with a more advanced stage
    mock_scenario = MagicMock()
    mock_scenario.start_point.time = '2025-01-01'
    context = {
        'symbol': 'BTCUSDT',
        'decision_path': ['P(4h)', '->OK:impul', 'STAGE_PASSED:4h', 'P(1h)', '->MATCH', 'STAGE_PASSED:ALIGN_1h'],
        '4h_scenarios': [mock_scenario]
    }
    user_id = 12345

    # AND the previously notified stage was the 4h stage
    existing_state = {'BTCUSDT_2025-01-01': 'STAGE_PASSED:4h'}
    with patch('src.background_scanner.load_notification_state', return_value=existing_state) as mock_load, \
         patch('src.background_scanner.save_notification_state') as mock_save:

        # WHEN we handle the notification
        await handle_analysis_notifications(mock_app, user_id, context)

        # THEN a new message should be sent for the upgraded stage
        mock_app.bot.send_message.assert_called_once()
        sent_text = mock_app.bot.send_message.call_args[1]['text']
        assert "تأكيد مبدئي | BTCUSDT | 1H" in sent_text

        # AND the state should be updated and saved with the new stage
        mock_save.assert_called_once_with({'BTCUSDT_2025-01-01': 'STAGE_PASSED:ALIGN_1h'})
