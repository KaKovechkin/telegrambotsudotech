
import os
from dotenv import load_dotenv

load_dotenv()

# Токен Telegram-бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# API-ключ Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Путь к базе данных SQLite
DB_PATH = os.getenv("DB_PATH", "database.db")

GROQ_MODEL = "llama3-70b-8192"
