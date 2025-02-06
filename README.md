# Telegram AI Bot with FastAPI

This is an MVP implementation of a Telegram bot that integrates with OpenAI's API and includes PostgreSQL logging.

## Features

- FastAPI backend with webhook endpoint for Telegram
- OpenAI API integration
- PostgreSQL logging of all interactions
- Asynchronous implementation
- Modular structure for easy expansion

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Telegram Bot Token
- OpenAI API Key

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the root directory with the following variables:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
```

## Database Setup

1. Create a PostgreSQL database
2. The tables will be created automatically when you first run the application

## Running the Application

1. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Set up your Telegram webhook:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_SERVER_URL>/webhook
   ```

## Project Structure

```
app/
├── api/
├── database/
│   └── connection.py
├── models/
│   └── log.py
├── services/
│   ├── ai_service.py
│   └── telegram_service.py
└── main.py
```

## Usage

1. Start a chat with your Telegram bot
2. Send any message
3. The bot will process your message through the AI service and respond
4. All interactions are automatically logged in the PostgreSQL database

## Development

The project is structured to be easily extensible:
- Add new API endpoints in the `api` directory
- Create new services in the `services` directory
- Add new models in the `models` directory
