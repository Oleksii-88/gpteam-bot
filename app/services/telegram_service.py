import httpx
import os
from dotenv import load_dotenv

load_dotenv()

class TelegramService:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, chat_id: str, text: str) -> dict:
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Sending message to chat {chat_id}")
        logger.info(f"Message text: {text}")
        logger.info(f"Using Telegram API URL: {self.base_url}/sendMessage")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text
                    }
                )
                response_json = response.json()
                logger.info(f"Telegram API response: {response_json}")
                return response_json
            except Exception as e:
                logger.error(f"Error sending message to Telegram: {e}")
                logger.error(f"Response status code: {getattr(response, 'status_code', 'N/A')}")
                logger.error(f"Response text: {getattr(response, 'text', 'N/A')}")
                raise
