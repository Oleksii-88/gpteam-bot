from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import os
import logging
import json

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
    except Exception as e:
        logger.error(f"Error reading request body: {e}")
    
    response = await call_next(request)
    return response

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[dict]

@app.post("/webhook")
async def telegram_webhook(
    update: TelegramUpdate,
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info(f"Received webhook update: {json.dumps(update.dict(), indent=2)}")
    except Exception as e:
        logger.error(f"Error logging update: {e}")
        logger.error(f"Raw update: {update}")
    try:
        if not update.message:
            logger.error("No message in update")
            raise HTTPException(status_code=400, detail="Message not found in update")

        logger.info(f"Full message content: {json.dumps(update.message, indent=2)}")

    try:
        chat_id = str(update.message.get("chat", {}).get("id"))
        text = update.message.get("text", "")
        logger.info(f"Extracted chat_id: {chat_id}, text: {text}")
    except Exception as e:
        logger.error(f"Error extracting message details: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing message: {str(e)}")

    if not chat_id or not text:
        raise HTTPException(status_code=400, detail="Invalid message format")

    logger.info(f"Processing message from chat {chat_id}: {text}")
    
    # Get AI response
    try:
        ai_response = await ai_service.get_response(text)
        logger.info(f"Got AI response: {ai_response}")
    except Exception as e:
        logger.error(f"Error getting AI response: {e}")
        raise

    # Send response back to Telegram
    try:
        telegram_response = await telegram_service.send_message(chat_id, ai_response)
        logger.info(f"Telegram response: {json.dumps(telegram_response, indent=2)}")
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        raise

    # Log the interaction
    log = Log(
        chat_id=chat_id,
        input_message=text,
        ai_request=text,
        ai_response=ai_response,
        status="success" if telegram_response.get("ok") else "error"
    )
    
    db.add(log)
    await db.commit()

    return {"status": "success"}
