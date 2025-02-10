import pytest
from app.main import start, echo

@pytest.mark.asyncio
async def test_start_command(update, context):
    """Тест команды /start."""
    # Выполняем команду
    await start(update, context)
    
    # Проверяем, что был отправлен правильный ответ
    assert update.message.reply_text.call_count == 1
    args = update.message.reply_text.call_args[0][0]
    assert "Привет" in args
    assert update.effective_user.first_name in args
    assert "необходимо зарегистрироваться" in args

@pytest.mark.asyncio
async def test_echo_handler(update, context):
    """Тест эхо-обработчика."""
    test_message = "Тестовое сообщение"
    update.message.text = test_message
    
    # Проверяем сообщение о необходимости регистрации
    await echo(update, context)
    assert update.message.reply_text.call_count == 1
    args = update.message.reply_text.call_args[0][0]
    assert "необходимо зарегистрироваться" in args
