import httpx
import os
import logging
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

load_dotenv()
logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, chat_id: str, text: str, reply_markup: Optional[Dict] = None) -> dict:
        logger.info(f"Sending message to {chat_id}: {text}")
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                }
                if reply_markup:
                    data["reply_markup"] = reply_markup
                    
                logger.info(f"Making request to {url} with data: {data}")
                response = await client.post(url, json=data)
                result = response.json()
                logger.info(f"Telegram API response: {result}")
                return result
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}", exc_info=True)
            raise

    def get_registration_keyboard(self) -> Dict:
        return {
            "inline_keyboard": [
                [{
                    "text": "Подать запрос на регистрацию",
                    "callback_data": "request_registration"
                }]
            ]
        }

    def get_admin_approval_keyboard(self, user_id: str) -> Dict:
        return {
            "inline_keyboard": [
                [
                    {
                        "text": "✅ Принять",
                        "callback_data": f"approve_{user_id}"
                    },
                    {
                        "text": "❌ Отклонить",
                        "callback_data": f"reject_{user_id}"
                    }
                ]
            ]
        }

    async def send_admin_notification(self, admin_chat_id: str, user: Dict[str, Any]) -> None:
        text = (
            f"📝 Новая заявка на регистрацию:\n\n"
            f"Имя: {user.get('first_name', 'Не указано')}\n"
            f"Username: @{user.get('username', 'Не указан')}\n"
            f"ID: {user['telegram_id']}"
        )
        await self.send_message(
            chat_id=admin_chat_id,
            text=text,
            reply_markup=self.get_admin_approval_keyboard(user['telegram_id'])
        )