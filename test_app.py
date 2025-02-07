from fastapi import FastAPI, Request
import uvicorn
import socket
import logging
import json
from typing import Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/test")
async def test_endpoint():
    return {
        "status": "ok",
        "hostname": socket.gethostname(),
        "message": "Test successful!"
    }

@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        # Читаем данные запроса
        update_data = await request.json()
        logger.info(f"Received update: {json.dumps(update_data)}")
        
        # Простой ответ для подтверждения работы вебхука
        return {"ok": True, "message": "Webhook received"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
