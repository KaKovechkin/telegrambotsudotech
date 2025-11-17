from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)

async def ai_answer(user_message: str) -> str:
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты умный ассистент планировщика. "
                        "Отвечай коротко и по делу."
                    )
                },
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
            max_tokens=350
        )

        return response.choices[0].message["content"]

    except Exception as e:
        print("AI ERROR:", e)
        return "⚠ Произошла ошибка при обращении к ИИ."
