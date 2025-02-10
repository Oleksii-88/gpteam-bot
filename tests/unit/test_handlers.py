"""Тесты для обработчиков команд."""
import pytest
from unittest.mock import AsyncMock, patch
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes
from app.main import start, echo, make_admin, revoke_admin, my_roles
from app.roles import UserRole, add_role, clear_roles, get_user_roles, has_role

@pytest.fixture
def update():
    """Фикстура для создания объекта Update."""
    update = AsyncMock(spec=Update)
    update.effective_user = AsyncMock(spec=User)
    update.effective_user.id = 12345
    update.effective_user.first_name = "Test User"
    update.message = AsyncMock(spec=Message)
    update.message.chat = AsyncMock(spec=Chat)
    return update

@pytest.fixture
def context():
    """Фикстура для создания объекта Context."""
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    return context

@pytest.fixture(autouse=True)
def cleanup():
    """Очищает роли после каждого теста."""
    yield
    clear_roles()

@pytest.mark.asyncio
async def test_start_command(update, context):
    """Тест команды /start."""
    await start(update, context)
    assert update.message.reply_text.called
    args = update.message.reply_text.call_args[0][0]
    assert "Привет" in args
    assert update.effective_user.first_name in args
    assert "подать заявку на регистрацию" in args.lower()

@pytest.mark.asyncio
async def test_echo_without_role(update, context):
    """Тест echo без роли пользователя."""
    update.message.text = "Test message"
    await echo(update, context)
    assert update.message.reply_text.called
    assert "необходимо зарегистрироваться" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_echo_with_role(update, context):
    """Тест echo с ролью пользователя."""
    add_role(update.effective_user.id, UserRole.USER)
    update.message.text = "Test message"
    await echo(update, context)
    assert update.message.reply_text.called
    assert "необходимо зарегистрироваться" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_make_admin_without_admin_role(update, context):
    """Тест make_admin без роли администратора."""
    context.args = ["67890"]
    await make_admin(update, context)
    assert update.message.reply_text.called
    assert "У вас нет прав" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_make_admin_with_admin_role(update, context):
    """Тест make_admin с ролью администратора."""
    add_role(update.effective_user.id, UserRole.ADMIN)
    context.args = ["67890"]
    await make_admin(update, context)
    assert update.message.reply_text.called
    assert "добавлена роль администратора" in update.message.reply_text.call_args[0][0]
    assert has_role(67890, UserRole.ADMIN)

@pytest.mark.asyncio
async def test_revoke_admin_with_admin_role(update, context):
    """Тест revoke_admin с ролью администратора."""
    add_role(update.effective_user.id, UserRole.ADMIN)
    target_user_id = 67890
    add_role(target_user_id, UserRole.ADMIN)
    context.args = [str(target_user_id)]
    await revoke_admin(update, context)
    assert update.message.reply_text.called
    assert "отозвана роль администратора" in update.message.reply_text.call_args[0][0]
    assert not has_role(target_user_id, UserRole.ADMIN)

@pytest.mark.asyncio
async def test_revoke_admin_without_admin_role(update, context):
    """Тест revoke_admin без роли администратора."""
    target_user_id = 67890
    add_role(target_user_id, UserRole.ADMIN)
    context.args = [str(target_user_id)]
    await revoke_admin(update, context)
    assert update.message.reply_text.called
    assert "У вас нет прав" in update.message.reply_text.call_args[0][0]
    assert has_role(target_user_id, UserRole.ADMIN)

@pytest.mark.asyncio
async def test_revoke_admin_non_admin_user(update, context):
    """Тест revoke_admin для пользователя без роли администратора."""
    add_role(update.effective_user.id, UserRole.ADMIN)
    target_user_id = 67890
    context.args = [str(target_user_id)]
    await revoke_admin(update, context)
    assert update.message.reply_text.called
    assert "не является администратором" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_revoke_admin_no_user_id(update, context):
    """Тест revoke_admin без указания ID пользователя."""
    add_role(update.effective_user.id, UserRole.ADMIN)
    context.args = []
    await revoke_admin(update, context)
    assert update.message.reply_text.called
    assert "Неверный формат ID" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_revoke_admin_invalid_user_id(update, context):
    """Тест revoke_admin с неверным форматом ID пользователя."""
    add_role(update.effective_user.id, UserRole.ADMIN)
    context.args = ["not_a_number"]
    await revoke_admin(update, context)
    assert update.message.reply_text.called
    assert "Неверный формат ID пользователя" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_my_roles_command(update, context):
    """Тест команды my_roles."""
    add_role(update.effective_user.id, UserRole.USER)
    add_role(update.effective_user.id, UserRole.ADMIN)
    await my_roles(update, context)
    assert update.message.reply_text.called
    response = update.message.reply_text.call_args[0][0]
    assert "необходимо зарегистрироваться" in response.lower()
