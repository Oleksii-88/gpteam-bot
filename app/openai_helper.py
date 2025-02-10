"""Module for interacting with OpenAI API."""
import base64
import os
from typing import Optional, Union

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAIHelper:
    """Helper class for interacting with OpenAI API."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError('OPENAI_API_KEY not found in environment variables')
        self.client = OpenAI(api_key=api_key)

    async def get_chat_response(self, message: str, system_prompt: Optional[str] = None) -> str:
        """
        Get response from OpenAI chat model.
        
        Args:
            message: User message
            system_prompt: Optional system prompt to set context
            
        Returns:
            str: Model's response
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Ошибка при получении ответа от OpenAI: {str(e)}"
            
    async def generate_image(self, prompt: str) -> str:
        """
        Generate image using DALL-E 3.
        
        Args:
            prompt: Description of the image to generate
            
        Returns:
            str: URL of the generated image
        """
        try:
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            return response.data[0].url
        except Exception as e:
            return f"Ошибка при генерации изображения: {str(e)}"
