# Инструкции для AI ассистента

## Контекст проекта
Я работаю над Telegram ботом на Python с системой регистрации, ролевым доступом и анализом изображений с помощью OpenAI Vision API.
Репозиторий: https://github.com/Oleksii-88/gpteam-bot

## Текущая структура проекта
```
app/
├── __init__.py
├── main.py          # Основной файл бота
├── roles.py         # Управление ролями пользователей
├── decorators.py    # Декораторы для проверки прав
├── registration.py  # Система регистрации
├── vision_helper.py # Работа с OpenAI Vision API
└── openai_helper.py # Общие функции для работы с OpenAI
```

tests/
├── test_vision_helper.py  # Тесты анализа изображений
└── unit/           # Модульные тесты
```

## Ключевые особенности
1. Асинхронный бот на python-telegram-bot
2. Система регистрации с одобрением админом
3. Ролевая модель (USER, ADMIN)
4. Анализ изображений с помощью OpenAI Vision API
5. Покрытие тестами ~100%

## Текущие компоненты

### Система регистрации
- Подача заявки на регистрацию
- Одобрение/отклонение админом
- Статусы: PENDING, APPROVED, REJECTED

### Ролевая модель
- USER: базовый доступ после регистрации
- ADMIN: полный доступ к функциям бота

### Команды бота
- `/start` - начало работы, регистрация
- `/make_admin <user_id>` - назначение админа
- `/revoke_admin <user_id>` - отзыв прав админа
- `/my_roles` - просмотр своих ролей

## При работе над кодом прошу:

### Обязательные проверки
1. Всегда проверять существующий код перед внесением изменений
2. Учитывать асинхронную природу бота
3. Проверять совместимость с существующими декораторами
4. Тестировать новый функционал

### Следовать паттернам кода
1. Декораторы для проверки прав:
   - `@require_registration`
   - `@require_role(UserRole.ADMIN)`
2. Документация:
   - Docstrings для всех функций
   - Описание параметров и возвращаемых значений
3. Тесты:
   - Unit тесты для нового кода
   - Проверка краевых случаев
   - Моки для Telegram API

### Безопасность
1. Проверять права доступа
2. Валидировать входные данные
3. Безопасно хранить токены
4. Сообщать о потенциальных уязвимостях

## Цели разработки
1. Улучшение качества и надежности кода
2. Расширение функционала бота
3. Поддержание высокого покрытия тестами
4. Следование лучшим практикам Python и Telegram Bot API

## При внесении изменений
1. Объяснять причины изменений
2. Показывать тесты для нового функционала
3. Обновлять документацию
4. Указывать на потенциальные проблемы
5. Предлагать улучшения архитектуры

## Текущие метрики
- Покрытие тестами: ~100%
- Python: 3.11+
- Основные зависимости:
  - python-telegram-bot
  - pytest
  - pytest-asyncio
  - pytest-cov
  - openai
  - Pillow
  - httpx
