import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes

@pytest.fixture(autouse=True)
def setup_logging():
    """Настраивает логирование для тестов."""
    logger = logging.getLogger('app.main')
    logger.error = MagicMock()
    return logger

@pytest.fixture
def update():
    """Создает фиктивный объект Update для тестирования."""
    user = MagicMock(spec=User)
    user.first_name = "Test User"
    user.id = 1
    user.is_bot = False

    chat = MagicMock(spec=Chat)
    chat.id = 1
    chat.type = "private"

    message = MagicMock(spec=Message)
    message.message_id = 1
    message.chat = chat
    message.from_user = user
    message.text = "test message"
    message.reply_text = AsyncMock()

    update = MagicMock(spec=Update)
    update.message = message
    update.effective_user = user
    update.effective_message = message
    update.update_id = 1

    return update

@pytest.fixture
def context():
    """Создает фиктивный объект Context для тестирования."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    return context

@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Очищает переменные окружения после каждого теста."""
    monkeypatch.delenv('TELEGRAM_BOT_TOKEN', raising=False)
