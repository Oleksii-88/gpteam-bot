#!/usr/bin/env python3
"""Основной модуль бота."""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv

# Используем абсолютные импорты – убедитесь, что модули находятся в PYTHONPATH или в одном каталоге.
from app.roles import UserRole, add_role, remove_role, has_role, get_user_roles
from app.decorators import require_role, require_registration
from app.openai_helper import OpenAIHelper
from app.vision_helper import VisionHelper
from app.registration import (
    create_registration_request,
    get_registration_status,
    approve_registration,
    reject_registration,
    get_pending_requests,
    RegistrationStatus,
    is_registered,
)

# Загрузка переменных окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    logger.info(f"Получена команда /start от пользователя {user.id} ({user.first_name})")

    # Проверяем статус регистрации пользователя
    status = get_registration_status(user.id)

    # Проверяем статус регистрации и роли пользователя
    if status == RegistrationStatus.PENDING:
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n"
            "Ваша заявка на регистрацию находится на рассмотрении. "
            "Пожалуйста, ожидайте решения администратора."
        )
        return

    elif status == RegistrationStatus.REJECTED:
        keyboard = [
            [
                InlineKeyboardButton(
                    "📝 Подать заявку повторно", callback_data="request_registration"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n"
            "К сожалению, предыдущая заявка на регистрацию была отклонена. "
            "Вы можете подать заявку повторно.",
            reply_markup=reply_markup,
        )
        return

    elif status == RegistrationStatus.APPROVED or has_role(user.id, UserRole.USER):
        # Убеждаемся, что у пользователя есть роль USER
        if not has_role(user.id, UserRole.USER):
            add_role(user.id, UserRole.USER)
            logger.debug(f"Добавлена роль USER пользователю {user.id}")

        # Если пользователь администратор, добавляем кнопку проверки заявок
        if has_role(user.id, UserRole.ADMIN):
            message = (
                f"Привет, {user.first_name}! 👋\n"
                "Я ваш телеграм-бот. Напишите что-нибудь, и я отвечу."
            )
            keyboard = [
                [
                    InlineKeyboardButton(
                        "📋 Проверить заявки на регистрацию", callback_data="check_requests"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(message, reply_markup=reply_markup)
        else:
            message = (
                f"Привет, {user.first_name}! 👋\n"
                "Я ваш телеграм-бот. Напишите что-нибудь, и я отвечу."
            )
            await update.message.reply_text(message)
        
        logger.debug(f"Отправлено приветственное сообщение пользователю {user.id}")
        return

    # Если пользователь ещё не подавал заявку
    keyboard = [
        [
            InlineKeyboardButton(
                "Подать заявку на регистрацию", callback_data="request_registration"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n"
        "Для использования бота необходимо зарегистрироваться. "
        "Нажмите на кнопку ниже, чтобы подать заявку на регистрацию.",
        reply_markup=reply_markup,
    )
    logger.debug(f"Отправлено приглашение на регистрацию пользователю {user.id}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()

    # Обработка нажатия на кнопку "check_requests" (просмотр заявок администратора)
    if query.data == "check_requests":
        if not has_role(query.from_user.id, UserRole.ADMIN):
            await query.message.edit_text("У вас нет прав для просмотра заявок.")
            return

        pending = get_pending_requests()
        if not pending:
            await query.message.edit_text(
                "Нет активных заявок на регистрацию.\n\n"
                "Нажмите /start чтобы вернуться в главное меню."
            )
            return

        # Сначала обновляем сообщение с информацией, что заявки обрабатываются
        await query.message.edit_text(
            "📋 Список заявок на регистрацию:\n\n"
            "Обрабатываю..."
        )

        # Отправляем каждую заявку отдельным сообщением с кнопками для одобрения/отклонения
        for user_id, request in pending.items():
            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ Одобрить", callback_data=f"approve_{user_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ Отклонить", callback_data=f"reject_{user_id}"
                    ),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=(
                    f"👤 Заявка от {request.first_name} (@{request.username})\n"
                    f"🆔 ID: {request.user_id}\n"
                    f"📅 Дата: {request.request_time.strftime('%Y-%m-%d %H:%M:%S')}"
                ),
                reply_markup=reply_markup,
            )

        # Финальное обновление сообщения администратора
        await query.message.edit_text(
            f"📋 Найдено заявок: {len(pending)}\n\n"
            "Нажмите /start чтобы вернуться в главное меню."
        )
        return

    # Обработка нажатия на кнопку "request_registration" (подача заявки)
    if query.data == "request_registration":
        user = query.from_user
        if create_registration_request(user.id, user.username or "", user.first_name):
            await query.message.edit_text(
                "Ваша заявка на регистрацию принята. "
                "Пожалуйста, ожидайте решения администратора."
            )
            logger.debug(f"Создана заявка на регистрацию от пользователя {user.id}")
        else:
            await query.message.edit_text("У вас уже есть активная заявка на регистрацию.")
        return

    # Обработка одобрения заявки (callback_data вида "approve_{user_id}")
    if query.data.startswith("approve_"):
        user_id = int(query.data.split("_")[1])
        if approve_registration(user_id, query.from_user.id):
            # Добавляем роль USER пользователю
            add_role(user_id, UserRole.USER)
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        "✅ Ваша заявка на регистрацию одобрена! \n"
                        "Теперь вы можете использовать бота. Напишите /start чтобы начать."
                    ),
                )
            except Exception as e:
                logger.error(
                    f"Ошибка при отправке уведомления пользователю {user_id}: {e}"
                )
            await query.message.edit_text(
                f"Заявка пользователя {user_id} одобрена. Пользователь уведомлен."
            )
            logger.debug(f"Одобрена заявка на регистрацию пользователя {user_id}")
        return

    # Обработка отклонения заявки (callback_data вида "reject_{user_id}")
    if query.data.startswith("reject_"):
        user_id = int(query.data.split("_")[1])
        if not has_role(query.from_user.id, UserRole.ADMIN):
            await query.message.edit_text("У вас нет прав для отклонения заявок.")
            return

        if reject_registration(user_id, query.from_user.id):
            keyboard = [
                [
                    InlineKeyboardButton(
                        "📝 Подать заявку повторно", callback_data="request_registration"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            try:
                # Отправляем уведомление пользователю
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        "\u274c Ваша заявка на регистрацию была отклонена. \n"
                        "Вы можете подать заявку повторно, нажав на кнопку ниже."
                    ),
                    reply_markup=reply_markup,
                )
                # Обновляем сообщение администратору
                await query.message.edit_text(
                    f"Заявка пользователя {user_id} отклонена. Пользователь уведомлен."
                )
                logger.debug(f"Отклонена заявка на регистрацию пользователя {user_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
                await query.message.edit_text(
                    f"Ошибка при отправке уведомления пользователю {user_id}."
                )
        return


@require_role(UserRole.ADMIN)
async def make_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Делает пользователя администратором."""
    try:
        user_id = int(context.args[0])
        add_role(user_id, UserRole.ADMIN)
        await update.message.reply_text(
            f"Пользователю {user_id} добавлена роль администратора."
        )
        logger.debug(f"Добавлена роль ADMIN пользователю {user_id}")
    except (ValueError, IndexError):
        await update.message.reply_text("Пожалуйста, укажите корректный ID пользователя")
    except Exception as e:
        logger.error(f"Ошибка при добавлении роли администратора: {e}")
        await update.message.reply_text("Произошла ошибка при добавлении роли")


@require_role(UserRole.ADMIN)
async def revoke_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отзывает права администратора у пользователя."""
    try:
        user_id = int(context.args[0])
        if not has_role(user_id, UserRole.ADMIN):
            await update.message.reply_text(f"Пользователь {user_id} не является администратором.")
            return
        remove_role(user_id, UserRole.ADMIN)
        await update.message.reply_text(f"У пользователя {user_id} отозвана роль администратора.")
        logger.debug(f"Отозвана роль ADMIN у пользователя {user_id}")
    except (ValueError, IndexError):
        await update.message.reply_text("Неверный формат ID пользователя")


@require_registration
async def my_roles(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает роли пользователя."""
    user = update.effective_user
    roles = get_user_roles(user.id)
    roles_str = ", ".join(role.value for role in roles) if roles else "нет ролей"
    await update.message.reply_text(f"Ваши роли: {roles_str}")


@require_role(UserRole.ADMIN)
async def list_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список заявок на регистрацию"""
    pending = get_pending_requests()
    if not pending:
        await update.message.reply_text("Нет активных заявок на регистрацию.")
        return

    for user_id, request in pending.items():
        keyboard = [
            [
                InlineKeyboardButton("Одобрить", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("Отклонить", callback_data=f"reject_{user_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Заявка от {request.first_name} (@{request.username})\n"
            f"ID: {request.user_id}\n"
            f"Дата: {request.request_time.strftime('%Y-%m-%d %H:%M:%S')}",
            reply_markup=reply_markup,
        )


@require_registration
@require_role(UserRole.USER)
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    # Инициализируем OpenAI helper при первом использовании
    if not hasattr(context.bot_data, 'openai_helper'):
        context.bot_data['openai_helper'] = OpenAIHelper()

    # Обычный текстовый ответ
    response = await context.bot_data['openai_helper'].get_chat_response(
        update.message.text,
        system_prompt="Ты - дружелюбный ассистент, который помогает пользователям. Отвечай кратко и по существу. Если пользователь просит создать изображение, предложи использовать команду /generate_image с описанием желаемого изображения."
    )
    
    # Отправляем ответ пользователю
    await update.message.reply_text(response)
    logger.debug(f"Отправлен ответ на сообщение от пользователя {update.effective_user.id}")

@require_role(UserRole.USER)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик фотографий"""
    # Инициализируем Vision helper при первом использовании
    if not hasattr(context.bot_data, 'vision_helper'):
        context.bot_data['vision_helper'] = VisionHelper()

    # Получаем файл фотографии (берем последнюю версию, т.к. она имеет наивысшее качество)
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    
    # Получаем текст сообщения или используем стандартный промпт
    caption = update.message.caption or "Опиши детально, что ты видишь на этом изображении"
    
    # Отправляем сообщение о том, что начали обработку
    processing_message = await update.message.reply_text(
        "Анализирую изображение... Это может занять несколько секунд."
    )
    
    try:
        # Анализируем изображение с учетом промпта
        response = await context.bot_data['vision_helper'].analyze_image(photo_bytes, prompt=caption)
        
        # Отправляем результат анализа
        await update.message.reply_text(response)
    except Exception as e:
        # Логируем ошибку
        logger.error(f"Ошибка при анализе изображения: {str(e)}")
        # Отправляем пользователю сообщение об ошибке
        await update.message.reply_text(f"Ошибка при анализе изображения: {str(e)}")
    finally:
        # Удаляем сообщение о обработке
        await processing_message.delete()
    
    logger.debug(f"Обработано изображение от пользователя {update.effective_user.id}")

@require_role(UserRole.USER)
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Генерация изображения с помощью DALL-E 3"""
    # Проверяем, что команда содержит описание изображения
    if not context.args:
        await update.message.reply_text(
            "Пожалуйста, добавьте описание изображения после команды /generate_image\n" \
            "Например: /generate_image красивый закат на море"
        )
        return

    # Инициализируем OpenAI helper при первом использовании
    if not hasattr(context.bot_data, 'openai_helper'):
        context.bot_data['openai_helper'] = OpenAIHelper()

    # Получаем описание изображения
    prompt = ' '.join(context.args)
    
    # Отправляем сообщение о том, что начали генерацию
    processing_message = await update.message.reply_text(
        "Генерирую изображение... Это может занять несколько секунд."
    )
    
    try:
        # Генерируем изображение
        image_url = await context.bot_data['openai_helper'].generate_image(prompt)
        
        # Отправляем изображение
        await update.message.reply_photo(
            image_url,
            caption=f"Сгенерированное изображение по запросу:\n{prompt}"
        )
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка при генерации изображения: {str(e)}")
    finally:
        # Удаляем сообщение о обработке
        await processing_message.delete()
    
    logger.debug(f"Сгенерировано изображение для пользователя {update.effective_user.id}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(f"Произошла ошибка: {context.error}")
    logger.error(f"Детали обновления: {update}")


def main() -> None:
    """Основная функция для запуска бота."""
    try:
        logger.info("Bot is starting...")
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise ValueError("Не найден токен бота в переменных окружения")
        logger.debug("Токен бота успешно получен")

        application = Application.builder().token(token).build()

        # Регистрируем обработчики команд, callback-запросов и текстовых сообщений
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("make_admin", make_admin))
        application.add_handler(CommandHandler("revoke_admin", revoke_admin))
        application.add_handler(CommandHandler("my_roles", my_roles))
        application.add_handler(CommandHandler("list_requests", list_requests))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        application.add_handler(CommandHandler("generate_image", generate_image))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        application.add_error_handler(error_handler)

        # Запуск бота с использованием polling
        application.run_polling()

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise


if __name__ == "__main__":
    main()