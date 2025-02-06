from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import os

from app.database.connection import get_db
from app.models.log import Log
from app.services.ai_service import AIService
from app.services.telegram_service import TelegramService

app = FastAPI()
ai_service = AIService()
telegram_service = TelegramService()

class TelegramUpdate(BaseModel):
    update_id: int
    message: Optional[dict]

@app.post("/webhook")
async def telegram_webhook(
    update: TelegramUpdate,
    db: AsyncSession = Depends(get_db)
):
    if not update.message:
        raise HTTPException(status_code=400, detail="Message not found in update")

    chat_id = str(update.message.get("chat", {}).get("id"))
    text = update.message.get("text", "")

    if not chat_id or not text:
        raise HTTPException(status_code=400, detail="Invalid message format")

    # Get AI response
    ai_response = await ai_service.get_response(text)

    # Send response back to Telegram
    telegram_response = await telegram_service.send_message(chat_id, ai_response)

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
