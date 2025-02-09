from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ValidationError
from typing import Optional
import os
import logging
import json
import asyncio
from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse
from starlette.background import BackgroundTask

from app.database.connection import get_db
from app.models.user import User
from app.services.telegram_service import TelegramService
from app.services.user_service import UserService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация сервисов
app = FastAPI()
telegram_service = TelegramService()
user_service = UserService()

# ID администратора (замените на реальный ID)
ADMIN_ID = os.getenv("ADMIN_TELEGRAM_ID")

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    try:
        from app.database.connection import init_db
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        body = await request.body()
        if body:
            logger.info(f"Request body: {body.decode()}")
    except ClientDisconnect:
        logger.warning("Client disconnected while reading request body in middleware")
        return JSONResponse({"status": "error", "detail": "Client disconnected"}, status_code=499)
    except Exception as e:
        logger.error(f"Error reading request body: {e}")
    
    try:
        response = await call_next(request)
        return response
    except ClientDisconnect:
        logger.warning("Client disconnected while processing request")
        return JSONResponse({"status": "error", "detail": "Client disconnected"}, status_code=499)
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise

class Chat(BaseModel):
    id: int
    type: str
    first_name: Optional[str] = None
    username: Optional[str] = None

class Message(BaseModel):
    message_id: int
    chat: Chat
    text: Optional[str] = None
    date: int

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[Message]

async def process_telegram_update(update_data: dict, db: AsyncSession):
    """Process Telegram update in background"""
    try:
        logger.info(f"Starting to process update: {json.dumps(update_data)}")
        
        # Обработка callback query (нажатия на кнопки)
        if 'callback_query' in update_data:
            callback_query = update_data['callback_query']
            callback_data = callback_query['data']
            user_id = str(callback_query['from']['id'])
            
            if callback_data == 'request_registration':
                # Проверяем, нет ли уже заявки
                existing_user = await user_service.get_user_by_telegram_id(db, user_id)
                if existing_user and existing_user.status == 'pending':
                    await telegram_service.send_message(
                        chat_id=user_id,
                        text="⚠️ У вас уже есть активная заявка на рассмотрении."
                    )
                    return
                
                # Создаем нового пользователя или обновляем статус
                user_data = callback_query['from']
                if existing_user:
                    user = await user_service.update_user_status(db, user_id, 'pending')
                else:
                    user = await user_service.create_user(
                        db,
                        telegram_id=user_id,
                        username=user_data.get('username'),
                        first_name=user_data.get('first_name')
                    )
                
                # Отправляем уведомление пользователю
                await telegram_service.send_message(
                    chat_id=user_id,
                    text="✅ Ваша заявка на регистрацию отправлена администратору. Пожалуйста, ожидайте подтверждения."
                )
                
                # Отправляем уведомление админу
                if ADMIN_ID:
                    await telegram_service.send_admin_notification(
                        admin_chat_id=ADMIN_ID,
                        user={
                            'telegram_id': user_id,
                            'username': user_data.get('username'),
                            'first_name': user_data.get('first_name')
                        }
                    )
                return
            callback_query = update_data['callback_query']
            callback_data = callback_query['data']
            user_id = str(callback_query['from']['id'])
            
            if callback_data == 'request_registration':
                logger.info(f"Processing registration request from user {user_id}")
                # Проверяем, нет ли уже заявки
                existing_user = await user_service.get_user_by_telegram_id(db, user_id)
                if existing_user and existing_user.status == 'pending':
                    await telegram_service.send_message(
                        chat_id=user_id,
                        text="⚠️ У вас уже есть активная заявка на рассмотрении."
                    )
                    return
                
                # Создаем нового пользователя или обновляем статус
                user_data = callback_query['from']
                if existing_user:
                    user = await user_service.update_user_status(db, user_id, 'pending')
                    logger.info(f"Updated user {user_id} status to pending")
                else:
                    user = await user_service.create_user(
                        db,
                        telegram_id=user_id,
                        username=user_data.get('username'),
                        first_name=user_data.get('first_name')
                    )
                    logger.info(f"Created new user {user_id}")
                
                # Отправляем уведомление пользователю
                await telegram_service.send_message(
                    chat_id=user_id,
                    text="✅ Ваша заявка на регистрацию отправлена администратору. Пожалуйста, ожидайте подтверждения."
                )
                
                # Отправляем уведомление админу
                if ADMIN_ID:
                    logger.info(f"Sending admin notification to {ADMIN_ID}")
                    await telegram_service.send_admin_notification(
                        admin_chat_id=ADMIN_ID,
                        user={
                            'telegram_id': user_id,
                            'username': user_data.get('username'),
                            'first_name': user_data.get('first_name')
                        }
                    )
                else:
                    logger.warning("ADMIN_ID not set, skipping admin notification")
            
            elif callback_data.startswith('approve_'):
                target_user_id = callback_data.split('_')[1]
                if str(user_id) == ADMIN_ID:
                    user = await user_service.update_user_status(db, target_user_id, 'approved')
                    if user:
                        await telegram_service.send_message(
                            chat_id=target_user_id,
                            text="✅ Ваша заявка на регистрацию одобрена! Теперь вы можете пользоваться ботом."
                        )
                        await telegram_service.send_message(
                            chat_id=user_id,
                            text=f"Пользователь {target_user_id} успешно одобрен."
                        )
            
            elif callback_data.startswith('reject_'):
                target_user_id = callback_data.split('_')[1]
                if str(user_id) == ADMIN_ID:
                    user = await user_service.update_user_status(db, target_user_id, 'rejected')
                    if user:
                        await telegram_service.send_message(
                            chat_id=target_user_id,
                            text="❌ К сожалению, ваша заявка на регистрацию отклонена."
                        )
                        await telegram_service.send_message(
                            chat_id=user_id,
                            text=f"Пользователь {target_user_id} отклонен."
                        )
            
            return
        
        # Обработка обычных сообщений
        if 'message' not in update_data:
            logger.error("No message in update")
            return
            
        message = update_data['message']
        chat_id = str(message['chat']['id'])
        text = message.get('text', '')
        
        logger.info(f"Processing message: chat_id={chat_id}, text={text}")
        
        # Проверяем статус пользователя
        user = await user_service.get_user_by_telegram_id(db, chat_id)
        logger.info(f"User status for {chat_id}: {user.status if user else 'Not registered'}")
        
        if text == '/start':
            logger.info(f"Processing /start command for user {chat_id}")
            if not user or user.status == 'rejected':
                # Новый или отклоненный пользователь
                response_text = "👋 Добро пожаловать! Для использования бота необходимо зарегистрироваться."
                keyboard = telegram_service.get_registration_keyboard()
                logger.info(f"Sending registration keyboard to {chat_id}")
                await telegram_service.send_message(
                    chat_id=chat_id,
                    text=response_text,
                    reply_markup=keyboard
                )
                return
            elif user.status == 'pending':
                await telegram_service.send_message(
                    chat_id=chat_id,
                    text="⏳ Ваша заявка на регистрацию находится на рассмотрении. Пожалуйста, ожидайте."
                )
                return
            elif user.status == 'approved':
                await telegram_service.send_message(
                    chat_id=chat_id,
                    text="✅ Добро пожаловать! Вы уже зарегистрированы."
                )
                return
            elif user.status == 'pending':
                response_text = "⏳ Ваша заявка на регистрацию находится на рассмотрении. Пожалуйста, ожидайте."
                await telegram_service.send_message(chat_id=chat_id, text=response_text)
                return
            elif user.status == 'rejected':
                response_text = "❌ К сожалению, ваша заявка была отклонена. Вы можете подать новую заявку."
                keyboard = telegram_service.get_registration_keyboard()
                await telegram_service.send_message(chat_id=chat_id, text=response_text, reply_markup=keyboard)
                return
            elif user.status == 'approved':
                response_text = "✅ Добро пожаловать! Чем могу помочь?"
                await telegram_service.send_message(chat_id=chat_id, text=response_text)
                return
        
        # Проверяем доступ для всех остальных сообщений
        if not user or user.status != 'approved':
            response_text = "⚠️ Для использования бота необходимо зарегистрироваться."
            keyboard = telegram_service.get_registration_keyboard()
            await telegram_service.send_message(
                chat_id=chat_id,
                text=response_text,
                reply_markup=keyboard
            )
            return
        
        # Обработка сообщений для зарегистрированных пользователей
        response_text = f"Вы написали: {text}\nСкоро я научусь отвечать более осмысленно!"
        await telegram_service.send_message(chat_id=chat_id, text=response_text)
            
    except Exception as e:
        logger.error(f"Error processing update: {str(e)}", exc_info=True)

@app.post("/webhook")
async def telegram_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        # Быстро читаем тело запроса
        update_data = await request.json()
        logger.info(f"Webhook received update: {json.dumps(update_data)}")
        await process_telegram_update(update_data, db)
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}", exc_info=True)
        return {"ok": False, "error": str(e)}}
        
        # Логируем запрос
        logger.info(f"Received update: {json.dumps(update_data)}")
        
        # Запускаем обработку в фоне
        asyncio.create_task(process_telegram_update(update_data))
        
        # Сразу отвечаем Telegram
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return {"ok": False, "error": str(e)}