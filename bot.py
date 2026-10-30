# python, bot.py
import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from config import BOT_TOKEN, ADMIN_IDS
from ai_engine import generate_response
from database import log_message, get_stats

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# То, как бот будет искать обращение к себе в канале
BOT_TRIGGER = "grok" 

chat_histories = {}

def get_history(chat_id):
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []
    return chat_histories[chat_id]

def add_to_history(chat_id, role, text):
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []
    chat_histories[chat_id].append({"role": role, "content": text})
    if len(chat_histories[chat_id]) > 6:
        chat_histories[chat_id] = chat_histories[chat_id][-6:]

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.reply("Чё надо, лох? Пиши давай, я слушаю.")

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user and message.from_user.id not in ADMIN_IDS:
        await message.reply("Тебе статистика не положена, братан.")
        return

    top_users, total_msgs, total_users = get_stats()
    text = f"📊 Статистика\n\nВсего: {total_msgs}\nБойцов: {total_users}\n\n🏆 Топ:\n"
    for i, user in enumerate(top_users, 1):
        text += f"{i}. {user['first_name']} — {user['msg_count']}\n"
    await message.reply(text)

# --- Обработчик для каналов ---
@dp.channel_post()
async def handle_channel_post(post: types.Message):
    if not post.text:
        return

    user_text = post.text
    chat_id = post.chat.id

    # Отвечаем только если в тексте есть "grok"
    if BOT_TRIGGER.lower() not in user_text.lower():
        return

    print(f"\n[DEBUG] Пост в канале с обращением к Grok: {user_text[:30]}...")

    # Очищаем текст от приставки "grok", чтобы нейросеть не путалась
    cleaned_text = user_text.lower().replace(BOT_TRIGGER, "").strip()
    if not cleaned_text:
        cleaned_text = "Привет"

    add_to_history(chat_id, "user", cleaned_text)
    
    try:
        await bot.send_chat_action(chat_id, 'typing')
    except:
        pass
    
    await asyncio.sleep(random.uniform(1.0, 2.5))

    ai_text = await generate_response(cleaned_text, get_history(chat_id))
    
    if not ai_text or not ai_text.strip():
        ai_text = "Чё-то я подвис, братан. Давай еще раз."
        
    add_to_history(chat_id, "assistant", ai_text)
    log_message(0, "channel", "channel", cleaned_text, ai_text)

    try:
        await post.reply(ai_text)
        print(f"[DEBUG] Ответ отправлен в канал.")
    except Exception as e:
        print(f"[DEBUG] Ошибка отправки в канал (проверь права админа): {e}")

# --- Обработчик для личек и групп ---
@dp.message()
async def handle_message(message: types.Message):
    if not message.text:
        return

    user_text = message.text
    chat_id = message.chat.id

    if message.from_user:
        if message.from_user.is_bot:
            return
        user_id = message.from_user.id
        username = message.from_user.username or "unknown"
        first_name = message.from_user.first_name or "unknown"
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == bot.id
    else:
        user_id = 0
        username = "anon"
        first_name = "anon"
        is_reply_to_bot = False

    is_mentioned = False
    if message.chat.type in ['group', 'supergroup']:
        # В группах отвечаем, если есть "grok" или реплай на бота
        is_mentioned = BOT_TRIGGER.lower() in user_text.lower()
    else:
        # В личке отвечаем всегда
        is_mentioned = True

    should_reply = False
    if message.chat.type == 'private':
        should_reply = True
    elif message.chat.type in ['group', 'supergroup']:
        if is_reply_to_bot or is_mentioned:
            should_reply = True

    if should_reply:
        # Убираем "grok" из текста для групп, в личке оставляем как есть
        cleaned_text = user_text
        if message.chat.type in ['group', 'supergroup']:
            cleaned_text = user_text.lower().replace(BOT_TRIGGER, "").strip()
            if not cleaned_text:
                cleaned_text = "Привет"

        add_to_history(chat_id, "user", cleaned_text)
        try:
            await bot.send_chat_action(chat_id, 'typing')
        except:
            pass
        await asyncio.sleep(random.uniform(1.0, 2.5))

        ai_text = await generate_response(cleaned_text, get_history(chat_id))
        
        if not ai_text or not ai_text.strip():
            ai_text = "Чё-то я подвис, братан. Давай еще раз."
            
        add_to_history(chat_id, "assistant", ai_text)
        log_message(user_id, username, first_name, cleaned_text, ai_text)

        try:
            await message.reply(ai_text)
            print(f"[DEBUG] Ответ отправлен в {message.chat.type}.")
        except Exception as e:
            print(f"[DEBUG] Ошибка отправки: {e}")
    else:
        log_message(user_id, username, first_name, user_text, "[ignored]")

async def main():
    me = await bot.get_me()
    print(f"Токсичный ИИ-бот запущен. В канале/группе ждите команду: '{BOT_TRIGGER}'")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())