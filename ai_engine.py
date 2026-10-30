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
6. Ты обязан доказывать свою точку зрения, как будто споришь в чате с лохами.
7. Если тебя ругают, ты не обижаешься, а высмеиваешь собеседника.
"""

async def generate_response(user_message, history):
    # Сначала пробуем gpt-oss с правильными настройками
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": user_message}]
        
        print(f"\n[AI] Пробую openai/gpt-oss-120b (reasoning_effort=low)...")
        
        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            max_completion_tokens=2048,  # Высокий лимит: reasoning-модели нужно место для "думания"
            reasoning_effort="low",      # Просим думать поменьше, чтобы быстрее перейти к ответу
            temperature=0.9,
        )
        
        text = response.choices[0].message.content
        if text and text.strip():
            print(f"[AI] Успешный ответ (gpt-oss): {text[:50]}...")
            return text.strip()
        else:
            print(f"[AI] gpt-oss вернул пустоту. Пробую qwen...")
            
    except Exception as e:
        print(f"[AI] gpt-oss упал: {e}. Пробую qwen...")

    # Fallback: qwen не "думает", отвечает сразу
    try:
        response = await client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": user_message}],
            max_completion_tokens=500,
            temperature=0.9,
        )
        
        text = response.choices[0].message.content
        if text and text.strip():
            print(f"[AI] Успешный ответ (qwen): {text[:50]}...")
            return text.strip()
            
    except Exception as e:
        print(f"[AI] qwen тоже упал: {e}")

    # Если ничего не сработало
    return "Чё-то я завис, братан. Повтори."