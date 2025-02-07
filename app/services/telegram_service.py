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
        print(f"Sending message to {chat_id}: {text}")
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": text
                }
                print(f"Making request to {url} with data: {data}")
                response = await client.post(url, json=data)
                result = response.json()
                print(f"Telegram API response: {result}")
                return result
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            raise
