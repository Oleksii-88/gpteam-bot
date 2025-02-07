from fastapi import FastAPI, Request
import uvicorn
import socket
import logging
import json
import os
import httpx
from typing import Optional
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токена бота
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")

app = FastAPI()

@app.get("/test")
async def test_endpoint():
    return {
        "status": "ok",
        "hostname": socket.gethostname(),
        "message": "Test successful!"
    }

async def send_telegram_message(chat_id: str, text: str):
    """Отправка сообщения в Telegram"""
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
            raise

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        # Читаем данные запроса
        update_data = await request.json()
        logger.info(f"Received update: {json.dumps(update_data)}")
        
        # Проверяем наличие сообщения
        if 'message' not in update_data:
            return {"ok": True, "message": "No message in update"}
            
        message = update_data['message']
        chat_id = str(message['chat']['id'])
        text = message.get('text', '')
        
        # Обработка команды /start
        if text == '/start':
            response_text = "Привет! Я бот для обработки запросов. Чем могу помочь?"
        else:
            response_text = f"Вы написали: {text}\nСкоро я научусь отвечать более осмысленно!"
        
        # Отправляем ответ
        await send_telegram_message(chat_id, response_text)
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
