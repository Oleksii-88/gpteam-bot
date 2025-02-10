"""Тесты для функции main."""
import os
import pytest
from unittest.mock import patch, MagicMock
from app.main import main

def test_main_success():
    """Тест успешного запуска бота."""
    # Подготавливаем моки
    mock_app = MagicMock()
    mock_builder = MagicMock()
    mock_builder.token.return_value.build.return_value = mock_app
    
    with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'test_token'}), \
         patch('telegram.ext.Application.builder', return_value=mock_builder):
        # Запускаем main
        main()
        
        # Проверяем, что токен был использован правильно
        mock_builder.token.assert_called_once_with('test_token')
        
        # Проверяем, что все обработчики были добавлены
        assert mock_app.add_handler.call_count >= 7  # start, make_admin, revoke_admin, my_roles, list_requests, button_handler, echo
        assert mock_app.add_error_handler.call_count == 1
        
        # Проверяем, что бот был запущен
        mock_app.run_polling.assert_called_once()

@pytest.mark.asyncio
async def test_main_no_token():
    """Тест запуска бота без токена."""
    with patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': ''}, clear=True), \
         pytest.raises(ValueError, match="Не найден токен бота в переменных окружения"):
        await main()
