"""Tests for VisionHelper class."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import base64
from app.vision_helper import VisionHelper

# Фикстура для мока OpenAI клиента
@pytest.fixture
def mock_openai_client():
    with patch('app.vision_helper.AsyncOpenAI') as mock_client:
        # Создаем мок для chat.completions.create
        mock_completion = AsyncMock()
        mock_completion.return_value.choices = [
            MagicMock(message=MagicMock(content="Тестовый ответ"))
        ]
        mock_client.return_value.chat.completions.create = mock_completion
        yield mock_client

@pytest.fixture
def vision_helper(mock_openai_client):
    """Фикстура для создания экземпляра VisionHelper с моком OpenAI."""
    return VisionHelper()

@pytest.mark.asyncio
async def test_analyze_image_basic(vision_helper, mock_openai_client):
    """Тест базового анализа изображения без промпта."""
    # Подготавливаем тестовые данные
    test_image = b"test image data"
    
    # Вызываем метод
    result = await vision_helper.analyze_image(test_image)
    
    # Проверяем результат
    assert result == "Тестовый ответ"
    
    # Проверяем, что API был вызван с правильными параметрами
    call_args = vision_helper.client.chat.completions.create.call_args
    assert call_args.kwargs['model'] == "gpt-4o"
    assert call_args.kwargs['max_tokens'] == 500
    
    # Проверяем структуру сообщения
    messages = call_args.kwargs['messages']
    assert len(messages) == 1
    assert messages[0]['role'] == "user"
    assert len(messages[0]['content']) == 2
    assert messages[0]['content'][0]['type'] == "text"
    assert messages[0]['content'][1]['type'] == "image_url"
    
    # Проверяем, что изображение закодировано в base64
    image_url = messages[0]['content'][1]['image_url']['url']
    assert image_url.startswith("data:image/jpeg;base64,")

@pytest.mark.asyncio
async def test_analyze_image_with_prompt(vision_helper):
    """Тест анализа изображения с пользовательским промптом."""
    test_image = b"test image data"
    test_prompt = "Что на фото?"
    
    result = await vision_helper.analyze_image(test_image, prompt=test_prompt)
    
    # Проверяем, что промпт был правильно передан
    call_args = vision_helper.client.chat.completions.create.call_args
    messages = call_args.kwargs['messages']
    assert messages[0]['content'][0]['text'] == test_prompt

@pytest.mark.asyncio
async def test_analyze_image_error_handling(vision_helper, mock_openai_client):
    """Тест обработки ошибок при анализе изображения."""
    # Настраиваем мок для имитации ошибки
    mock_openai_client.return_value.chat.completions.create.side_effect = Exception("Test error")
    
    with pytest.raises(Exception) as exc_info:
        await vision_helper.analyze_image(b"test image")
    
    assert str(exc_info.value) == "Ошибка при анализе изображения: Test error"

@pytest.mark.asyncio
async def test_analyze_image_base64_encoding(vision_helper):
    """Тест корректности base64 кодирования изображения."""
    test_image = b"test image data"
    
    await vision_helper.analyze_image(test_image)
    
    # Проверяем корректность base64 кодирования
    call_args = vision_helper.client.chat.completions.create.call_args
    messages = call_args.kwargs['messages']
    image_url = messages[0]['content'][1]['image_url']['url']
    
    # Извлекаем base64 часть
    base64_part = image_url.split('base64,')[1]
    
    # Проверяем, что это валидный base64
    try:
        decoded = base64.b64decode(base64_part)
        assert decoded == test_image
    except Exception as e:
        pytest.fail(f"Invalid base64 encoding: {e}")
