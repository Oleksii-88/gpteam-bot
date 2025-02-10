"""Тесты для основного модуля бота."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes
from app.main import start, button_handler, echo, make_admin, revoke_admin, my_roles
from app.roles import UserRole, add_role, clear_roles, has_role
from app.registration import RegistrationStatus, create_registration_request, clear_requests, approve_registration

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
    context.bot.send_message = AsyncMock()
    return context

@pytest.fixture(autouse=True)
def clear_data():
    """Очищает данные перед каждым тестом."""
    clear_roles()
    clear_requests()

@pytest.mark.asyncio
async def test_start_command_new_user(update, context):
    """Тест команды /start для нового пользователя."""
    # Запускаем команду
    await start(update, context)
    
    # Проверяем, что пользователю предложено зарегистрироваться
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Для использования бота необходимо зарегистрироваться" in call_args

@pytest.mark.asyncio
async def test_start_command_admin(update, context):
    """Тест команды /start для администратора."""
    # Делаем пользователя администратором и зарегистрированным пользователем
    add_role(update.effective_user.id, UserRole.ADMIN)
    add_role(update.effective_user.id, UserRole.USER)
    
    # Создаем и одобряем заявку
    create_registration_request(update.effective_user.id, "test_user", "Test User")
    approve_registration(update.effective_user.id, admin_id=54321)
    
    # Запускаем команду
    await start(update, context)
    
    # Проверяем, что администратору показана кнопка проверки заявок
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[1]
    assert "reply_markup" in call_args
    keyboard = call_args["reply_markup"].inline_keyboard
    assert any("Проверить заявки" in button.text for row in keyboard for button in row)

@pytest.mark.asyncio
async def test_start_command_pending_user(update, context):
    """Тест команды /start для пользователя с заявкой на рассмотрении."""
    # Создаем заявку на регистрацию
    create_registration_request(update.effective_user.id, "test_user", "Test User")
    
    # Запускаем команду
    await start(update, context)
    
    # Проверяем сообщение о статусе заявки
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "находится на рассмотрении" in call_args

@pytest.mark.asyncio
async def test_button_handler_check_requests_not_admin(context):
    """Тест обработки кнопки проверки заявок не администратором."""
    # Создаем объект query
    query = MagicMock()
    query.data = "check_requests"
    query.from_user = MagicMock(spec=User)
    query.from_user.id = 123
    query.answer = AsyncMock()
    query.message = MagicMock(spec=Message)
    query.message.edit_text = AsyncMock()
    
    # Создаем объект update
    update = MagicMock(spec=Update)
    update.callback_query = query
    
    # Запускаем обработчик
    await button_handler(update, context)
    
    # Проверяем, что доступ запрещен
    query.message.edit_text.assert_called_once_with("У вас нет прав для просмотра заявок.")

@pytest.mark.asyncio
async def test_button_handler_check_requests_admin_no_requests(context):
    """Тест обработки кнопки проверки заявок администратором без заявок."""
    # Создаем объект query
    query = MagicMock()
    query.data = "check_requests"
    query.from_user = MagicMock(spec=User)
    query.from_user.id = 123
    query.answer = AsyncMock()
    query.message = MagicMock(spec=Message)
    query.message.edit_text = AsyncMock()
    
    # Делаем пользователя администратором
    add_role(query.from_user.id, UserRole.ADMIN)
    
    # Создаем объект update
    update = MagicMock(spec=Update)
    update.callback_query = query
    
    # Запускаем обработчик
    await button_handler(update, context)
    
    # Проверяем сообщение об отсутствии заявок
    query.message.edit_text.assert_called_once()
    call_args = query.message.edit_text.call_args[0][0]
    assert "Нет активных заявок" in call_args

@pytest.mark.asyncio
async def test_button_handler_check_requests_admin_with_requests(context):
    """Тест обработки кнопки проверки заявок администратором с заявками."""
    # Создаем объект query
    query = MagicMock()
    query.data = "check_requests"
    query.from_user = MagicMock(spec=User)
    query.from_user.id = 123
    query.answer = AsyncMock()
    query.message = MagicMock(spec=Message)
    query.message.chat_id = 123
    query.message.edit_text = AsyncMock()
    
    # Делаем пользователя администратором
    add_role(query.from_user.id, UserRole.ADMIN)
    
    # Создаем тестовую заявку
    create_registration_request(456, "test_user", "Test User")
    
    # Создаем объект update
    update = MagicMock(spec=Update)
    update.callback_query = query
    
    # Запускаем обработчик
    await button_handler(update, context)
    
    # Проверяем, что бот отправил сообщение с заявкой
    assert context.bot.send_message.call_count == 1
    call_args = context.bot.send_message.call_args[1]
    assert call_args["chat_id"] == query.message.chat_id
    assert "test_user" in call_args["text"]
    assert "reply_markup" in call_args  # Проверяем наличие кнопок

@pytest.mark.asyncio
async def test_button_handler_approve_request(context):
    """Тест обработки кнопки одобрения заявки."""
    # Создаем тестовую заявку
    user_id = 456
    create_registration_request(user_id, "test_user", "Test User")
    
    # Создаем объект query
    query = MagicMock()
    query.data = f"approve_{user_id}"
    query.from_user = MagicMock(spec=User)
    query.from_user.id = 123
    query.answer = AsyncMock()
    query.message = MagicMock(spec=Message)
    query.message.chat_id = 123
    query.message.edit_text = AsyncMock()
    
    # Делаем пользователя администратором
    add_role(query.from_user.id, UserRole.ADMIN)
    
    # Создаем объект update
    update = MagicMock(spec=Update)
    update.callback_query = query
    
    # Запускаем обработчик
    await button_handler(update, context)
    
    # Проверяем, что заявка одобрена
    query.message.edit_text.assert_called_once()
    call_args = query.message.edit_text.call_args[0][0]
    assert "одобрена" in call_args.lower()
    
    # Проверяем, что пользователю отправлено уведомление
    context.bot.send_message.assert_called_once()
    call_args = context.bot.send_message.call_args[1]
    assert call_args["chat_id"] == user_id
    assert "одобрена" in call_args["text"].lower()

@pytest.mark.asyncio
async def test_button_handler_reject_request(context):
    """Тест обработки кнопки отклонения заявки."""
    # Создаем тестовую заявку
    user_id = 456
    create_registration_request(user_id, "test_user", "Test User")
    
    # Создаем объект query
    query = MagicMock()
    query.data = f"reject_{user_id}"
    query.from_user = MagicMock(spec=User)
    query.from_user.id = 123
    query.answer = AsyncMock()
    query.message = MagicMock(spec=Message)
    query.message.chat_id = 123
    query.message.edit_text = AsyncMock()
    
    # Делаем пользователя администратором
    add_role(query.from_user.id, UserRole.ADMIN)
    
    # Создаем объект update
    update = MagicMock(spec=Update)
    update.callback_query = query
    
    # Запускаем обработчик
    await button_handler(update, context)
    
    # Проверяем, что заявка отклонена
    query.message.edit_text.assert_called_once()
    call_args = query.message.edit_text.call_args[0][0]
    assert "отклонена" in call_args.lower()
    
    # Проверяем, что пользователю отправлено уведомление
    context.bot.send_message.assert_called_once()
    call_args = context.bot.send_message.call_args[1]
    assert call_args["chat_id"] == user_id
    assert "отклонена" in call_args["text"].lower()

@pytest.mark.asyncio
async def test_echo_not_registered(update, context):
    """Тест обработки сообщения от незарегистрированного пользователя."""
    # Запускаем обработчик
    await echo(update, context)
    
    # Проверяем, что пользователю предложено зарегистрироваться
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "необходимо зарегистрироваться" in call_args.lower()

@pytest.mark.asyncio
async def test_echo_registered(update, context):
    """Тест обработки сообщения от зарегистрированного пользователя."""
    # Регистрируем пользователя
    create_registration_request(update.effective_user.id, "test_user", "Test User")
    add_role(update.effective_user.id, UserRole.USER)
    
    # Добавляем текст сообщения
    update.message.text = "Привет"
    
    # Запускаем обработчик
    await echo(update, context)
    
    # Проверяем, что бот ответил на сообщение
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert len(call_args) > 0  # Проверяем, что ответ не пустой

@pytest.mark.asyncio
async def test_make_admin_success(update, context):
    """Тест успешного добавления роли администратора"""
    # Устанавливаем роль ADMIN для текущего пользователя
    add_role(update.effective_user.id, UserRole.ADMIN)
    
    # Устанавливаем ID пользователя, которому будем давать права
    target_user_id = 456
    context.args = [str(target_user_id)]
    
    # Вызываем функцию
    await make_admin(update, context)
    
    # Проверяем результат
    assert has_role(target_user_id, UserRole.ADMIN)
    assert update.message.reply_text.call_args[0][0] == f"Пользователю {target_user_id} добавлена роль администратора."

@pytest.mark.asyncio
async def test_make_admin_invalid_id(update, context):
    """Тест добавления роли администратора с некорректным ID"""
    # Устанавливаем роль ADMIN для текущего пользователя
    add_role(update.effective_user.id, UserRole.ADMIN)
    
    # Устанавливаем некорректный ID
    context.args = ["not_a_number"]
    
    # Вызываем функцию
    await make_admin(update, context)
    
    # Проверяем сообщение об ошибке
    assert update.message.reply_text.call_args[0][0] == "Пожалуйста, укажите корректный ID пользователя"

@pytest.mark.asyncio
async def test_make_admin_no_id(update, context):
    """Тест добавления роли администратора без указания ID"""
    # Устанавливаем роль ADMIN для текущего пользователя
    add_role(update.effective_user.id, UserRole.ADMIN)
    
    # Не устанавливаем аргументы
    context.args = []
    
    # Вызываем функцию
    await make_admin(update, context)
    
    # Проверяем сообщение об ошибке
    assert update.message.reply_text.call_args[0][0] == "Пожалуйста, укажите корректный ID пользователя"

@pytest.mark.asyncio
async def test_revoke_admin_success(update, context):
    """Тест успешного отзыва роли администратора"""
    # Устанавливаем роль ADMIN для текущего пользователя
    add_role(update.effective_user.id, UserRole.ADMIN)
    
    # Устанавливаем ID пользователя и даем ему права админа
    target_user_id = 456
    add_role(target_user_id, UserRole.ADMIN)
    context.args = [str(target_user_id)]
    
    # Вызываем функцию
    await revoke_admin(update, context)
    
    # Проверяем результат
    assert not has_role(target_user_id, UserRole.ADMIN)
    assert update.message.reply_text.call_args[0][0] == f"У пользователя {target_user_id} отозвана роль администратора."

@pytest.mark.asyncio
async def test_revoke_admin_not_admin(update, context):
    """Тест отзыва роли администратора у пользователя без прав админа"""
    # Устанавливаем роль ADMIN для текущего пользователя
    add_role(update.effective_user.id, UserRole.ADMIN)
    
    # Устанавливаем ID пользователя без прав админа
    target_user_id = 456
    context.args = [str(target_user_id)]
    
    # Вызываем функцию
    await revoke_admin(update, context)
    
    # Проверяем сообщение
    assert update.message.reply_text.call_args[0][0] == f"Пользователь {target_user_id} не является администратором."

@pytest.mark.asyncio
async def test_revoke_admin_invalid_id(update, context):
    """Тест отзыва роли администратора с некорректным ID"""
    # Устанавливаем роль ADMIN для текущего пользователя
    add_role(update.effective_user.id, UserRole.ADMIN)
    
    # Устанавливаем некорректный ID
    context.args = ["not_a_number"]
    
    # Вызываем функцию
    await revoke_admin(update, context)
    
    # Проверяем сообщение об ошибке
    assert update.message.reply_text.call_args[0][0] == "Неверный формат ID пользователя"

@pytest.mark.asyncio
async def test_my_roles_with_roles(update, context):
    """Тест просмотра ролей при наличии ролей у пользователя"""
    # Регистрируем пользователя
    user_id = update.effective_user.id
    create_registration_request(user_id, "test_user", "Test User")
    approve_registration(user_id, 123)
    add_role(user_id, UserRole.USER)
    add_role(user_id, UserRole.ADMIN)
    
    # Вызываем функцию
    await my_roles(update, context)
    
    # Проверяем результат
    response = update.message.reply_text.call_args[0][0]
    assert "admin" in response and "user" in response

@pytest.mark.asyncio
async def test_my_roles_no_roles(update, context):
    """Тест просмотра ролей при отсутствии ролей у пользователя"""
    # Регистрируем пользователя
    user_id = update.effective_user.id
    create_registration_request(user_id, "test_user", "Test User")
    approve_registration(user_id, 123)
    
    # Вызываем функцию
    await my_roles(update, context)
    
    # Проверяем результат
    assert update.message.reply_text.call_args[0][0] == "Ваши роли: нет ролей"
