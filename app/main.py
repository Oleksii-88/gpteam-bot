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
from app.models.log import Log
from app.services.ai_service import AIService
from app.services.telegram_service import TelegramService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
ai_service = AIService()
telegram_service = TelegramService()

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

async def process_telegram_update(update_data: dict):
    """Process Telegram update in background"""
    try:
        logger.info(f"Starting to process update: {json.dumps(update_data)}")
        
        if 'message' not in update_data:
            logger.error("No message in update")
            return
            
        message = update_data['message']
        chat_id = str(message['chat']['id'])
        text = message.get('text', '')
        
        logger.info(f"Processing message: chat_id={chat_id}, text={text}")
        
        if text == '/start':
            response_text = "Привет! Я бот для обработки запросов. Чем могу помочь?"
            logger.info(f"Sending response to chat {chat_id}: {response_text}")
            try:
                result = await telegram_service.send_message(chat_id, response_text)
                logger.info(f"Send message result: {result}")
            except Exception as e:
                logger.error(f"Error sending message: {str(e)}", exc_info=True)
        else:
            logger.info(f"Received non-command message: {text}")
            
    except Exception as e:
        logger.error(f"Error processing update: {str(e)}", exc_info=True)

@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict:
    try:
        # Быстро читаем тело запроса
        update_data = await request.json()
        
        # Логируем запрос
        logger.info(f"Received update: {json.dumps(update_data)}")
        
        # Запускаем обработку в фоне
        asyncio.create_task(process_telegram_update(update_data))
        
        # Сразу отвечаем Telegram
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
        return {"ok": False, "error": str(e)}