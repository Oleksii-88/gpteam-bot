from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, ValidationError
from typing import Optional
import os
import logging
import json
from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse

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

from starlette.requests import ClientDisconnect
from starlette.background import BackgroundTask

@app.post("/webhook")
async def telegram_webhook(request: Request) -> dict:
    try:
        # Получаем тело запроса как bytes
        try:
            body_bytes = await request.body()
        except ClientDisconnect:
            logger.warning("Client disconnected while reading request body")
            return {"ok": True}  # Возвращаем 200 OK для Telegram
        
        # Декодируем bytes в строку
        body_str = body_bytes.decode()
        # Парсим JSON
        update = json.loads(body_str)
        
        # Логируем входящий запрос
        logger.info(f"Received update: {body_str}")
        
        # Проверяем наличие сообщения
        if 'message' not in update:
            logger.error("No message in update")
            return {"ok": False, "error": "No message in update"}
            
        message = update['message']
        chat_id = str(message['chat']['id'])
        text = message.get('text', '')
        
        # Обрабатываем команду /start
        if text == '/start':
            try:
                response_text = "Привет!"
                logger.info(f"Sending response to chat {chat_id}: {response_text}")
                result = await telegram_service.send_message(chat_id, response_text)
                logger.info(f"Send message result: {result}")
                return {"ok": True, "result": result}
            except Exception as e:
                logger.error(f"Error sending message: {str(e)}")
                return {"ok": False, "error": f"Failed to send message: {str(e)}"}
            
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"ok": False, "error": str(e)}
    try:
        body_bytes = await request.body()
        body = json.loads(body_bytes)
        logger.info(f"Raw JSON body: {json.dumps(body, indent=2)}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        return {"status": "error", "detail": "Invalid JSON"}
    except Exception as e:
        logger.error(f"Error reading request body: {e}")
        return {"status": "error", "detail": str(e)}
    try:
        # Логируем входящий JSON
        try:
            body = await request.json()
            logger.info(f"Raw JSON body: {json.dumps(body, indent=2)}")
        except ClientDisconnect:
            logger.warning("Client disconnected while reading webhook request body")
            return JSONResponse({"status": "error", "detail": "Client disconnected"}, status_code=499)
        except Exception as e:
            logger.error(f"Error reading webhook request body: {e}")
            raise HTTPException(status_code=400, detail=f"Error reading request body: {str(e)}")
    except ClientDisconnect:
        logger.warning("Client disconnected while reading request body")
        return {"status": "error", "detail": "Client disconnected"}
    except Exception as e:
        logger.error(f"Error reading request body: {e}")
        raise HTTPException(status_code=400, detail=f"Error reading request body: {str(e)}")
    
    try:
        update = TelegramUpdate.parse_obj(body)
        logger.info("Successfully parsed TelegramUpdate model")
    except ValidationError as e:
        logger.error(f"Failed to parse TelegramUpdate model: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid update format: {str(e)}")
    # Логируем входящий запрос
    try:
        logger.info(f"Received webhook update: {json.dumps(update.dict(), indent=2)}")
    except Exception as e:
        logger.error(f"Error logging update: {e}")
        logger.error(f"Raw update: {update}")

    # Проверяем наличие сообщения
    if not update.message:
        logger.error("No message in update")
        raise HTTPException(status_code=400, detail="Message not found in update")

    try:
        logger.info(f"Full message content: {json.dumps(update.message, indent=2)}")
    except Exception as e:
        logger.error(f"Error logging message content: {e}")

    # Извлекаем chat_id и текст
    # Извлекаем данные из сообщения
    try:
        if not update.message:
            logger.error("Message is None")
            raise HTTPException(status_code=400, detail="Message not found in update")
            
        logger.info(f"Processing message: {update.message}")
        
        chat_id = str(update.message.chat.id)
        text = update.message.text or ""
        
        logger.info(f"Extracted chat_id: {chat_id}, text: {text}")
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid message format: {str(e)}")
    except Exception as e:
        logger.error(f"Error extracting message details: {e}")
        logger.error(f"Raw message: {update.message}")
        raise HTTPException(status_code=400, detail=f"Error processing message: {str(e)}")

    if not chat_id or not text:
        logger.error(f"Invalid message format: chat_id={chat_id}, text={text}")
        raise HTTPException(status_code=400, detail="Invalid message format")

    logger.info(f"Processing message from chat {chat_id}: {text}")
    
    # Обрабатываем команду /start
    if text == "/start":
        logger.info(f"Processing /start command for chat_id {chat_id}")
        ai_response = "Привет!"
        logger.info(f"Generated welcome message: {ai_response}")
    else:
        # Получаем ответ от AI для обычных сообщений
        try:
            logger.info(f"Getting AI response for message: {text}")
            ai_response = await ai_service.get_response(text)
            logger.info(f"Got AI response: {ai_response}")
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            raise HTTPException(status_code=500, detail="Error getting AI response")
    
    # Логируем попытку отправки сообщения
    logger.info(f"Attempting to send message to chat_id {chat_id}")

    # Отправляем ответ в Telegram
    try:
        logger.info(f"Sending message to Telegram - chat_id: {chat_id}, message: {ai_response}")
        telegram_response = await telegram_service.send_message(chat_id, ai_response)
        logger.info(f"Telegram API response: {json.dumps(telegram_response, indent=2)}")
        if not telegram_response.get('ok'):
            logger.error(f"Telegram API returned error: {telegram_response}")
            raise HTTPException(status_code=500, detail=f"Telegram API error: {telegram_response.get('description', 'Unknown error')}")
    except Exception as e:
        logger.error(f"Error sending Telegram message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending Telegram message: {str(e)}")

    # Логируем взаимодействие
    try:
        log = Log(
            chat_id=chat_id,
            input_message=text,
            ai_request=text,
            ai_response=ai_response,
            status="success" if telegram_response.get("ok") else "error"
        )
        db.add(log)
        await db.commit()
        logger.info("Interaction logged successfully")
    except Exception as e:
        logger.error(f"Error logging interaction: {e}")
        # Не прерываем работу бота из-за ошибки логирования
        
    return {"status": "ok"}
    
    db.add(log)
    await db.commit()

    return {"status": "success"}
