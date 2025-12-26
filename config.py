import os
from dotenv import load_dotenv

load_dotenv()  # читает .env

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

DB_PATH = os.getenv("DB_PATH", "database.db")

