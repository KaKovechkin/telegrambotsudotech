import aiohttp

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"  # или phi3

async def ai_answer(user_text: str) -> str:
    try:
        payload = {
            "model": MODEL,
            "prompt": user_text,
            "stream": False
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(OLLAMA_URL, json=payload) as resp:
                if resp.status != 200:
                    return f"⚠️ Ошибка Ollama: {await resp.text()}"

                data = await resp.json()
                return data.get("response", "⚠️ Модель не ответила")

    except Exception as e:
        return f"⚠️ Ошибка: {e}"
