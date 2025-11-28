import os
from dotenv import load_dotenv

load_dotenv()  # читает .env

BOT_TOKEN = os.getenv("BOT_TOKEN", "")


DB_PATH = os.getenv("DB_PATH", "database.db")
