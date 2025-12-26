import aiohttp
import uuid
import json
import ssl
from datetime import datetime
from config import GIGACHAT_CREDENTIALS

# --- КОНСТАНТЫ ---
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# ОБНОВЛЕННАЯ ИНСТРУКЦИЯ
SYSTEM_PROMPT = """
Ты — МойРитм, ассистент.
Твоя задача — анализировать запрос пользователя и управлять его задачами.

ТЕБЕ БУДЕТ ПЕРЕДАН СПИСОК ЗАДАЧ. ИСПОЛЬЗУЙ ЕГО ДЛЯ ОТВЕТОВ.

ПРАВИЛА ВЫВОДА (ЭТО ВАЖНО):
1. Если пользователь хочет СОЗДАТЬ задачу — верни ТОЛЬКО JSON:
{"action": "create_task", "title": "название", "date": "ДД/ММ/ГГГГ", "time": "ЧЧ:ММ"}

2. Если пользователь хочет УДАЛИТЬ задачу — верни ТОЛЬКО JSON:
{"action": "delete_task", "keywords": "слова для поиска"}

3. ВАЖНО: НИКОГДА не пиши вступлений вроде "Вот JSON команда" или "Я создал задачу".
ЕСЛИ ЭТО КОМАНДА — ВЕРНИ ТОЛЬКО JSON-СТРОКУ И НИЧЕГО БОЛЬШЕ.

4. Если это просто вопрос или просьба спланировать день — отвечай обычным текстом.
"""

async def get_token() -> str:
    payload = {'scope': 'GIGACHAT_API_PERS'}
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
        'Authorization': f'Basic {GIGACHAT_CREDENTIALS}'
    }
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession() as session:
        async with session.post(AUTH_URL, headers=headers, data=payload, ssl=ssl_ctx) as resp:
            data = await resp.json()
            if resp.status != 200:
                raise ValueError(f"Auth Error: {data}")
            return data['access_token']

async def ai_answer(user_text: str, tasks_context: str = "Список пуст") -> str:
    try:
        access_token = await get_token()
        now = datetime.now()
        
        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"📅 СЕГОДНЯ: {now.strftime('%d/%m/%Y')}\n"
            f"🕒 ВРЕМЯ: {now.strftime('%H:%M')}\n"
            f"📋 ЗАДАЧИ:\n{tasks_context}"
        )

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        payload = {
            "model": "GigaChat",
            "messages": [
                {"role": "system", "content": full_prompt},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.1  # Минимальная температура для строгости
        }

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        async with aiohttp.ClientSession() as session:
            async with session.post(CHAT_URL, headers=headers, json=payload, ssl=ssl_ctx) as resp:
                result = await resp.json()
                return result['choices'][0]['message']['content']

    except Exception as e:
        return f"Error: {e}"