"""Тесты для декораторов."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes
from app.decorators import (
    require_registration, require_role,
    send_typing_action, handle_telegram_errors
)
from app.roles import UserRole, add_role, clear_roles
from app.registration import create_registration_request, clear_requests, RegistrationStatus, is_registered, approve_registration

@pytest.fixture
def update():
    """Фикстура для создания объекта Update."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 123
    update.effective_user.first_name = "Test User"
    update.effective_user.username = "test_user"
    update.message = MagicMock(spec=Message)
    update.message.chat = MagicMock(spec=Chat)
    update.message.chat.id = 123
    update.message.reply_text = AsyncMock()
    return update

@pytest.fixture
def context():
    """Фикстура для создания объекта Context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    context.bot.send_message = AsyncMock()
    return context

@pytest.fixture(autouse=True)
def clear_data():
    """Очищает данные перед каждым тестом."""
    clear_roles()
    clear_requests()
    yield

@pytest.mark.asyncio
async def test_check_user_registered_not_registered(update, context):
    """Тест декоратора check_user_registered для незарегистрированного пользователя."""
    # Создаем тестовую функцию
    @require_registration
    async def test_func(update, context):
        return "success"

    # Вызываем функцию
    result = await test_func(update, context)
    
    # Проверяем, что функция не выполнилась и отправлено сообщение о регистрации
    assert result is None
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Для использования бота необходимо зарегистрироваться" in call_args

@pytest.mark.asyncio
async def test_check_user_registered_pending(update, context):
    """Тест декоратора check_user_registered для пользователя с заявкой на рассмотрении."""
    # Создаем заявку
    create_registration_request(update.effective_user.id, "test_user", "Test User")
    
    # Создаем тестовую функцию
    @require_registration
    async def test_func(update, context):
        return "success"

    # Вызываем функцию
    result = await test_func(update, context)
    
    # Проверяем, что функция не выполнилась и отправлено сообщение о статусе заявки
    assert result is None
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "находится на рассмотрении" in call_args

@pytest.mark.asyncio
async def test_check_user_registered_approved(update, context):
    """Тест декоратора check_user_registered для зарегистрированного пользователя."""
    # Создаем и одобряем заявку
    create_registration_request(update.effective_user.id, "test_user", "Test User")
    approve_registration(update.effective_user.id, 123)
    add_role(update.effective_user.id, UserRole.USER)
    
    # Проверяем, что пользователь зарегистрирован
    assert is_registered(update.effective_user.id)
    
    # Создаем тестовую функцию
    @require_registration
    async def test_func(update, context):
        return "success"

    # Вызываем функцию
    result = await test_func(update, context)
    
    # Проверяем, что функция выполнилась успешно
    assert result == "success"

@pytest.mark.asyncio
async def test_check_user_role_no_role(update, context):
    """Тест декоратора check_user_role для пользователя без нужной роли."""
    # Создаем тестовую функцию
    @require_role(UserRole.ADMIN)
    async def test_func(update, context):
        return "success"

    # Вызываем функцию
    result = await test_func(update, context)
    
    # Проверяем, что функция не выполнилась и отправлено сообщение об отказе
    assert result is None
    update.message.reply_text.assert_called_once_with("У вас нет прав для выполнения этой команды.")

@pytest.mark.asyncio
async def test_check_user_role_has_role(update, context):
    """Тест декоратора check_user_role для пользователя с нужной ролью."""
    # Добавляем роль пользователю
    add_role(update.effective_user.id, UserRole.ADMIN)
    
    # Создаем тестовую функцию
    @require_role(UserRole.ADMIN)
    async def test_func(update, context):
        return "success"

    # Вызываем функцию
    result = await test_func(update, context)
    
    # Проверяем, что функция выполнилась успешно
    assert result == "success"

@pytest.mark.asyncio
async def test_send_typing_action(update, context):
    """Тест декоратора send_typing_action."""
    # Создаем тестовую функцию
    @send_typing_action
    async def test_func(update, context):
        return "success"

    # Вызываем функцию
    result = await test_func(update, context)
    
    # Проверяем, что бот отправил действие typing
    context.bot.send_chat_action.assert_called_once_with(
        chat_id=update.message.chat_id,
        action="typing"
    )
    assert result == "success"

@pytest.mark.asyncio
async def test_handle_telegram_errors_no_error(update, context):
    """Тест декоратора handle_telegram_errors без ошибок."""
    # Создаем тестовую функцию
    @handle_telegram_errors
    async def test_func(update, context):
        return "success"

    # Вызываем функцию
    result = await test_func(update, context)
    
    # Проверяем успешное выполнение
    assert result == "success"

@pytest.mark.asyncio
async def test_handle_telegram_errors_with_error(update, context):
    """Тест декоратора handle_telegram_errors с ошибкой."""
    # Создаем тестовую функцию
    @handle_telegram_errors
    async def test_func(update, context):
        raise Exception("Test error")

    # Вызываем функцию
    result = await test_func(update, context)
    
    # Проверяем, что ошибка обработана и отправлено сообщение
    context.bot.send_message.assert_called_once()
    call_args = context.bot.send_message.call_args[1]
    assert call_args["chat_id"] == update.message.chat_id
    assert "Произошла ошибка" in call_args["text"]
    assert result is None
