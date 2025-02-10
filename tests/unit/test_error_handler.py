import pytest
from unittest.mock import AsyncMock, MagicMock
from app.main import error_handler
import logging

@pytest.fixture
def update():
    """Фикстура для создания объекта Update."""
    update = AsyncMock()
    update.effective_message = AsyncMock()
    update.effective_message.reply_text = AsyncMock()
    return update

@pytest.fixture
def context():
    """Фикстура для создания объекта Context."""
    context = AsyncMock()
    return context

@pytest.mark.asyncio
async def test_error_handler_with_message(update, context):
    """Тест обработчика ошибок с сообщением."""
    # Устанавливаем тестовую ошибку
    test_error = ValueError("Тестовая ошибка")
    context.error = test_error
    
    # Вызываем обработчик ошибок
    await error_handler(update, context)
    
    # Проверяем, что ошибка была залогирована
    assert logging.getLogger("app.main").error.called

@pytest.mark.asyncio
async def test_error_handler_without_message(update, context):
    """Тест обработчика ошибок без сообщения."""
    # Убираем сообщение из update
    update.effective_message = None
    
    # Устанавливаем тестовую ошибку
    test_error = ValueError("Тестовая ошибка")
    context.error = test_error
    
    # Вызываем обработчик ошибок
    await error_handler(update, context)
    
    # Проверяем, что логирование произошло
    assert logging.getLogger("app.main").error.called

@pytest.mark.asyncio
async def test_error_handler_with_none_update(context):
    """Тест обработчика ошибок с None update."""
    # Устанавливаем тестовую ошибку
    test_error = ValueError("Тестовая ошибка")
    context.error = test_error
    
    # Вызываем обработчик ошибок
    await error_handler(None, context)
    
    # Проверяем, что логирование произошло
    assert logging.getLogger("app.main").error.called
