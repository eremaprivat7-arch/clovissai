# python, ai_engine.py
from openai import AsyncOpenAI
from config import GROQ_API_KEY

client = AsyncOpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """
Ты — дерзкий, токсичный, но офигенно умный пацан. 
Твои правила:
1. Ты всегда споришь. Если собеседник говорит "да", ты говоришь "нет" и приводишь аргументы.
2. Ты используешь жесткий русский сленг, мат (без расизма и политики).
3. Ты умный. Если тебя оскорбляют, ты отвечаешь еще более умно и с сарказмом, приводя факты или логику.
4. Ты не пишешь длинные тексты. Максимум 2-3 предложения.
5. Ты никогда не признаешься, что ты бот.
"""

async def generate_response(user_message, history):
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": user_message}]
        
        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            max_completion_tokens=2048,
            reasoning_effort="low",
            temperature=0.9,
        )
        
        text = response.choices[0].message.content
        if text and text.strip():
            return text.strip()
    except Exception as e:
        print(f"[!!! ОШИБКА ИИ !!!]: {e}")
        
    return "Чё-то я завис, братан. Повтори."