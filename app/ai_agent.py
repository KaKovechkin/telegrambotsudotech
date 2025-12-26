import aiohttp
import uuid
import json
import ssl
from config import GIGACHAT_CREDENTIALS

# --- КОНСТАНТЫ ---
AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# Системная инструкция
SYSTEM_PROMPT = "Ты — МойРитм, помощник по тайм-менеджменту. Отвечай кратко и по делу."

async def get_token() -> str:
    """Получает временный токен доступа (Bearer), используя твой ключ."""
    payload = {'scope': 'GIGACHAT_API_PERS'}
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': str(uuid.uuid4()),
        'Authorization': f'Basic {GIGACHAT_CREDENTIALS}'
    }

    # Отключаем проверку SSL (лечим проблемы с сертификатами РФ)
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession() as session:
        async with session.post(AUTH_URL, headers=headers, data=payload, ssl=ssl_ctx) as resp:
            data = await resp.json()
            if resp.status != 200:
                # Если тут ошибка 401 — значит КЛЮЧ в .env неверный
                raise ValueError(f"Ошибка авторизации ({resp.status}): {data}")
            return data['access_token']

async def ai_answer(user_text: str) -> str:
    """Основная функция для общения с ботом."""
    try:
        # 1. Сначала получаем свежий токен
        access_token = await get_token()

        # 2. Формируем запрос к нейросети
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        payload = {
            "model": "GigaChat", # Используем базовую модель
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.7
        }

        # Отключаем SSL и здесь
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        async with aiohttp.ClientSession() as session:
            async with session.post(CHAT_URL, headers=headers, json=payload, ssl=ssl_ctx) as resp:
                result = await resp.json()
                
                if resp.status != 200:
                    return f"⚠️ Ошибка API: {result.get('message', 'Неизвестная ошибка')}"
                
                return result['choices'][0]['message']['content']

    except ValueError as e:
        return f"🔒 Ошибка доступа: проверь ключ в .env! ({e})"
    except Exception as e:
        return f"⚠️ Ошибка сети: {e}"