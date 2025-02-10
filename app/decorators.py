"""Модуль с декораторами для обработчиков команд."""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from .roles import UserRole, has_role
from .registration import is_registered, get_registration_status, RegistrationStatus

def require_registration(func):
    """Декоратор для проверки регистрации пользователя."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        status = get_registration_status(user.id)

        # Если это команда /start или пользователь зарегистрирован
        if getattr(update.message, 'text', '') == '/start' or is_registered(user.id):
            result = await func(update, context, *args, **kwargs)
            return result

        # Если заявка на рассмотрении
        if status == RegistrationStatus.PENDING:
            await update.message.reply_text(
                "Ваша заявка на регистрацию находится на рассмотрении. "
                "Пожалуйста, ожидайте решения администратора."
            )
            return None

        # Если заявка отклонена
        if status == RegistrationStatus.REJECTED:
            await update.message.reply_text(
                "Ваша заявка на регистрацию была отклонена. "
                "Для получения дополнительной информации свяжитесь с администратором."
            )
            return None

        # Если пользователь не подавал заявку
        if not status:
            await update.message.reply_text(
                "Для использования бота необходимо зарегистрироваться. "
                "Используйте команду /start для подачи заявки."
            )
            return None

    return wrapper

def require_role(role: UserRole):
    """Декоратор для проверки наличия роли у пользователя."""
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user = update.effective_user
            if not has_role(user.id, role):
                await update.message.reply_text(
                    "У вас нет прав для выполнения этой команды."
                )
                return
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator

def send_typing_action(func):
    """Декоратор для отображения действия 'печатает...' во время обработки сообщения."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        await context.bot.send_chat_action(
            chat_id=update.message.chat_id,
            action="typing"
        )
        return await func(update, context, *args, **kwargs)
    return wrapper

def handle_telegram_errors(func):
    """Декоратор для обработки ошибок Telegram."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except Exception as e:
            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text=f"Произошла ошибка: {str(e)}"
            )
            return None
    return wrapper
