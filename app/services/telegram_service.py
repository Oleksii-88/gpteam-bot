import httpx
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, chat_id: str, text: str) -> dict:
        logger.info(f"Sending message to {chat_id}: {text}")
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": text
                }
                logger.info(f"Making request to {url} with data: {data}")
                response = await client.post(url, json=data)
                result = response.json()
                logger.info(f"Telegram API response: {result}")
                return result
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}", exc_info=True)
            raise