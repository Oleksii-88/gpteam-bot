"""Module for interacting with OpenAI Vision API."""
import os
import base64
from typing import List, Optional, Union
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class VisionHelper:
    """Helper class for interacting with OpenAI Vision API."""
    
    def __init__(self):
        """Initialize Vision helper."""
        self.client = AsyncOpenAI()
    


    async def analyze_image(self, image_data: bytearray, prompt: Optional[str] = None) -> str:
        """
        Analyze image using Google Cloud Vision API.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            str: Description of the image contents
        """
        try:
            # Кодируем изображение в base64
            image_b64 = base64.b64encode(image_data).decode('utf-8')
            
            # Формируем запрос к API
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt if prompt else "Опиши детально, что ты видишь на этом изображении. Обрати внимание на:\n"
                            "1. Основные объекты и их расположение\n"
                            "2. Текст, если он есть\n"
                            "3. Людей, их действия и эмоции\n"
                            "4. Цвета и общую атмосферу"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ]
                }
            ]
            
            # Отправляем запрос в OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            # Пробрасываем ошибку дальше для обработки на уровне бота
            raise Exception(f"Ошибка при анализе изображения: {str(e)}")
