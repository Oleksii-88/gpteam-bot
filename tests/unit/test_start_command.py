"""Тесты для команды /start."""
import pytest
from unittest.mock import AsyncMock, patch
from telegram import Update, User, Message, Chat, InlineKeyboardMarkup
from app.main import start
from app.roles import UserRole, add_role
from app.registration import (
    RegistrationStatus, create_registration_request, approve_registration,
    reject_registration, get_registration_status, clear_requests
)

@pytest.fixture(autouse=True)
def clear_data():
    """Очищает данные перед каждым тестом."""
    clear_requests()

@pytest.fixture
def user():
    """Фикстура для создания объекта User."""
    return AsyncMock(spec=User, id=12345, username="test_user", first_name="Test User")

@pytest.fixture
def update(user):
    """Фикстура для создания объекта Update."""
    update = AsyncMock(spec=Update)
    update.effective_user = user
    update.message = AsyncMock(spec=Message)
    update.message.chat = AsyncMock(spec=Chat)
    return update

@pytest.fixture
def context():
    """Фикстура для создания объекта Context."""
    return AsyncMock()

@pytest.mark.asyncio
async def test_start_new_user(update, context):
    """Тест команды /start для нового пользователя."""
    await start(update, context)
    
    # Проверяем сообщение
    assert update.message.reply_text.called
    args = update.message.reply_text.call_args[0][0]
    assert "Привет" in args
    assert update.effective_user.first_name in args
    assert "подать заявку" in args.lower()
    
    # Проверяем наличие кнопки
    kwargs = update.message.reply_text.call_args[1]
    assert isinstance(kwargs.get('reply_markup'), InlineKeyboardMarkup)

@pytest.mark.asyncio
async def test_start_registered_user(update, context, user):
    """Тест команды /start для зарегистрированного пользователя."""
    # Регистрируем пользователя
    create_registration_request(user.id, user.username, user.first_name)
    approve_registration(user.id, admin_id=54321)
    add_role(user.id, UserRole.USER)
    
    await start(update, context)
    
    # Проверяем сообщение
    assert update.message.reply_text.called
    args = update.message.reply_text.call_args[0][0]
    assert "Привет" in args
    assert update.effective_user.first_name in args
    assert "Напишите что-нибудь" in args

@pytest.mark.asyncio
async def test_start_pending_user(update, context, user):
    """Тест команды /start для пользователя с ожидающей заявкой."""
    # Создаем заявку
    create_registration_request(user.id, user.username, user.first_name)
    
    # Проверяем, что заявка действительно в статусе PENDING
    assert get_registration_status(user.id) == RegistrationStatus.PENDING
    
    await start(update, context)
    
    # Проверяем сообщение
    assert update.message.reply_text.called
    args = update.message.reply_text.call_args[0][0]
    assert "Привет" in args
    assert update.effective_user.first_name in args
    assert "Ваша заявка на регистрацию находится на рассмотрении" in args

@pytest.mark.asyncio
async def test_start_rejected_user(update, context, user):
    """Тест команды /start для пользователя с отклоненной заявкой."""
    # Создаем и отклоняем заявку
    create_registration_request(user.id, user.username, user.first_name)
    reject_registration(user.id, admin_id=54321)
    
    # Проверяем, что заявка действительно в статусе REJECTED
    assert get_registration_status(user.id) == RegistrationStatus.REJECTED
    
    await start(update, context)
    
    # Проверяем сообщение
    assert update.message.reply_text.called
    args = update.message.reply_text.call_args[0][0]
    assert "Привет" in args
    assert update.effective_user.first_name in args
    assert "К сожалению, предыдущая заявка на регистрацию была отклонена" in args
    
    # Проверяем наличие кнопки для повторной подачи
    kwargs = update.message.reply_text.call_args[1]
    assert isinstance(kwargs.get('reply_markup'), InlineKeyboardMarkup)
