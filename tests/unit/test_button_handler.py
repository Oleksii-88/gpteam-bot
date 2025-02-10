"""Тесты для обработчика кнопок."""
import pytest
from unittest.mock import AsyncMock, patch
from telegram import Update, User, CallbackQuery, Message
from app.main import button_handler
from app.roles import UserRole, add_role
from app.registration import (
    RegistrationStatus, create_registration_request, clear_requests,
    reject_registration
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
def query(user):
    """Фикстура для создания объекта CallbackQuery."""
    query = AsyncMock(spec=CallbackQuery)
    query.data = ""
    query.from_user = user
    query.message = AsyncMock(spec=Message)
    return query

@pytest.fixture
def update(query):
    """Фикстура для создания объекта Update."""
    update = AsyncMock(spec=Update)
    update.callback_query = query
    return update

@pytest.fixture
def context():
    """Фикстура для создания объекта Context."""
    context = AsyncMock()
    context.bot = AsyncMock()
    return context

@pytest.mark.asyncio
async def test_button_handler_request_registration(update, context, user):
    """Тест обработки запроса на регистрацию."""
    update.callback_query.data = "request_registration"
    
    await button_handler(update, context)
    
    # Проверяем, что сообщение было обновлено
    update.callback_query.message.edit_text.assert_called_once()
    args = update.callback_query.message.edit_text.call_args[0][0]
    assert "заявка на регистрацию принята" in args.lower()

@pytest.mark.asyncio
async def test_button_handler_request_registration_duplicate(update, context, user):
    """Тест обработки повторного запроса на регистрацию."""
    # Создаем существующую заявку
    create_registration_request(user.id, user.username, user.first_name)
    
    update.callback_query.data = "request_registration"
    
    await button_handler(update, context)
    
    # Проверяем, что было отправлено сообщение об ошибке
    update.callback_query.message.edit_text.assert_called_once()
    args = update.callback_query.message.edit_text.call_args[0][0]
    assert "уже есть активная заявка" in args.lower()

@pytest.mark.asyncio
async def test_button_handler_check_requests_not_admin(update, context, user):
    """Тест просмотра заявок не администратором."""
    update.callback_query.data = "check_requests"
    
    await button_handler(update, context)
    
    # Проверяем сообщение об отсутствии прав
    update.callback_query.message.edit_text.assert_called_once()
    args = update.callback_query.message.edit_text.call_args[0][0]
    assert "у вас нет прав" in args.lower()

@pytest.mark.asyncio
async def test_button_handler_check_requests_admin(update, context, user):
    """Тест просмотра заявок администратором."""
    # Делаем пользователя администратором
    add_role(user.id, UserRole.ADMIN)
    
    update.callback_query.data = "check_requests"
    
    await button_handler(update, context)
    
    # Проверяем сообщение о заявках
    update.callback_query.message.edit_text.assert_called_once()
    args = update.callback_query.message.edit_text.call_args[0][0]
    assert "нет активных заявок" in args.lower()

@pytest.mark.asyncio
async def test_button_handler_approve_request(update, context, user):
    """Тест одобрения заявки на регистрацию."""
    # Делаем пользователя администратором
    add_role(user.id, UserRole.ADMIN)
    
    # Создаем заявку от другого пользователя
    other_user_id = 67890
    create_registration_request(other_user_id, "other_user", "Other User")
    
    update.callback_query.data = f"approve_{other_user_id}"
    
    await button_handler(update, context)
    
    # Проверяем сообщение об одобрении
    update.callback_query.message.edit_text.assert_called_once()
    args = update.callback_query.message.edit_text.call_args[0][0]
    assert "пользователь уведомлен" in args.lower()

@pytest.mark.asyncio
async def test_button_handler_reject_request(update, context, user):
    """Тест отклонения заявки на регистрацию."""
    # Делаем пользователя администратором
    add_role(user.id, UserRole.ADMIN)
    
    # Создаем заявку от другого пользователя
    other_user_id = 67890
    create_registration_request(other_user_id, "other_user", "Other User")
    
    update.callback_query.data = f"reject_{other_user_id}"
    
    await button_handler(update, context)
    
    # Проверяем, что сначала отправляется уведомление пользователю
    context.bot.send_message.assert_called_once()
    send_args = context.bot.send_message.call_args
    assert send_args[1]["chat_id"] == other_user_id
    assert "заявка на регистрацию была отклонена" in send_args[1]["text"]
    
    # Затем проверяем сообщение администратору
    update.callback_query.message.edit_text.assert_called_once()
    edit_args = update.callback_query.message.edit_text.call_args[0][0]
    assert "пользователь уведомлен" in edit_args.lower()
