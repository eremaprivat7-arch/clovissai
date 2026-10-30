# python, bot.py
import asyncio
import random
import sqlite3
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart, BaseFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_IDS
from ai_engine import generate_response
from osint import check_username, check_phone

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

BOT_TRIGGER = "grok"
chat_histories = {}
DB_PATH = "stats.db"

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, first_name TEXT, msg_count INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS warns (user_id INTEGER, reason TEXT, timestamp TEXT)''')
    conn.commit()
    return conn

conn = init_db()

def log_message(user_id, first_name):
    c = conn.cursor()
    c.execute('SELECT msg_count FROM users WHERE user_id=?', (user_id,))
    if c.fetchone():
        c.execute('UPDATE users SET msg_count=msg_count+1 WHERE user_id=?', (user_id,))
    else:
        c.execute('INSERT INTO users (user_id, first_name, msg_count) VALUES (?, ?, 1)', (user_id, first_name))
    conn.commit()

def get_stats():
    c = conn.cursor()
    c.execute('SELECT first_name, msg_count FROM users ORDER BY msg_count DESC LIMIT 5')
    return c.fetchall()

def add_warn(user_id, reason):
    c = conn.cursor()
    c.execute('INSERT INTO warns VALUES (?, ?, ?)', (user_id, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

# --- ФИЛЬТР АДМИНА ---
class IsAdmin(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in ADMIN_IDS

# --- FSM ДЛЯ ИГРЫ ---
class GameStates(StatesGroup):
    guessing = State()

# --- ЛОГИКА ИИ ---
def get_history(chat_id):
    return chat_histories.get(chat_id, [])

def add_to_history(chat_id, role, text):
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []
    chat_histories[chat_id].append({"role": role, "content": text})
    if len(chat_histories[chat_id]) > 6:
        chat_histories[chat_id] = chat_histories[chat_id][-6:]

# --- КОМАНДЫ ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 ИИ", callback_data="menu_ai"), InlineKeyboardButton(text="🔍 OSINT", callback_data="menu_osint")],
        [InlineKeyboardButton(text="🎮 Игра", callback_data="menu_game")],
        [InlineKeyboardButton(text="📊 Стата", callback_data="menu_stats")]
    ])
    await message.reply("Здарова! Выбирай чё надо:", reply_markup=kb)

@dp.callback_query(F.data.startswith("menu_"))
async def handle_menu(callback: types.CallbackQuery, state: FSMContext):
    action = callback.data.split("_")[1]
    
    if action == "ai":
        await callback.message.answer("Напиши свой вопрос.")
    elif action == "osint":
        await callback.message.answer("Кидай ник или номер.")
    elif action == "game":
        target = random.randint(1, 100)
        await state.update_data(target=target)
        await state.set_state(GameStates.guessing)
        await callback.message.answer("Загадал от 1 до 100. Пиши!")
    elif action == "stats":
        top = get_stats()
        text = "📊 Топ болтунов:\n"
        for i, u in enumerate(top, 1):
            text += f"{i}. {u[0]} — {u[1]}\n"
        await callback.message.answer(text)
    await callback.answer()

@dp.message(Command("ai"))
async def cmd_ai(message: types.Message):
    text = message.text.replace("/ai", "").strip()
    if not text:
        await message.reply("Напиши вопрос.")
        return
    msg = await message.reply("Думаю...")
    ai_text = await generate_response(text, [])
    await msg.edit_text(ai_text)

@dp.message(Command("osint"))
async def cmd_osint(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Кидай ник или номер.")
        return
    target = args[1]
    msg = await message.reply("Ищу...")
    if target.replace("+", "").isdigit():
        await msg.edit_text(check_phone(target))
    else:
        async with aiohttp.ClientSession() as session:
            data = await check_username(session, target)
        text = f"🔍 Результаты:\n\n"
        for p, s in data.items():
            text += f"{p}: {s}\n"
        await msg.edit_text(text)

# --- АДМИНКА ---
@dp.message(Command("ban"), IsAdmin())
async def cmd_ban(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение того, кого банить.")
        return
    target = message.reply_to_message.from_user.id
    try:
        await message.chat.ban(target)
        await message.reply(f"Пользователь забанен.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")

@dp.message(Command("warn"), IsAdmin())
async def cmd_warn(message: types.Message):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение того, кому дать варн.")
        return
    target = message.reply_to_message.from_user.id
    reason = message.text.replace("/warn", "").strip() or "Без причины"
    add_warn(target, reason)
    await message.reply(f"Варн выдан. Причина: {reason}")

# --- ИГРА ---
@dp.message(GameStates.guessing, F.text.regexp(r'^\d+$'))
async def handle_guess(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target = data.get("target")
    guess = int(message.text)
    if guess < target:
        await message.reply("Больше!")
    elif guess > target:
        await message.reply("Меньше!")
    else:
        await message.reply(f"Угадал! Это {target}. 🎉")
        await state.clear()

# --- ОБЫЧНЫЕ СООБЩЕНИЯ (ИИ) ---
@dp.message(F.text)
async def handle_message(message: types.Message, state: FSMContext):
    if not message.text:
        return
    current_state = await state.get_state()
    if current_state == GameStates.guessing.state:
        return

    user_text = message.text
    chat_id = message.chat.id

    if message.from_user:
        if message.from_user.is_bot:
            return
        user_id = message.from_user.id
        first_name = message.from_user.first_name or "unknown"
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == bot.id
        log_message(user_id, first_name)
    else:
        is_reply_to_bot = False

    is_mentioned = False
    if message.chat.type in ['group', 'supergroup']:
        is_mentioned = BOT_TRIGGER.lower() in user_text.lower()
    else:
        is_mentioned = True

    should_reply = False
    if message.chat.type == 'private':
        should_reply = True
    elif message.chat.type in ['group', 'supergroup']:
        if is_reply_to_bot or is_mentioned:
            should_reply = True

    if should_reply:
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

        try:
            await message.reply(ai_text)
        except Exception as e:
            print(f"[DEBUG] Ошибка отправки: {e}")

# --- ДЛЯ КАНАЛОВ ---
@dp.channel_post(F.text)
async def handle_channel(post: types.Message):
    user_text = post.text
    chat_id = post.chat.id

    if BOT_TRIGGER.lower() not in user_text.lower():
        return

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
    if not ai_text:
        ai_text = "Чё-то я подвис."
        
    add_to_history(chat_id, "assistant", ai_text)
    try:
        await post.reply(ai_text)
    except:
        pass

async def main():
    print(f"Мега-бот запущен! Триггер: '{BOT_TRIGGER}'")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())