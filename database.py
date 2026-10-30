# python, database.py
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        msg_count INTEGER DEFAULT 0,
        last_seen TEXT
    )''')
    # Таблица логов (кто с кем спорил)
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        ai_response TEXT,
        timestamp TEXT
    )''')
    conn.commit()
    return conn

def log_message(user_id, username, first_name, message, ai_response):
    conn = get_db()
    c = conn.cursor()
    
    # Обновляем юзера
    c.execute('SELECT msg_count FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    if row:
        c.execute('UPDATE users SET msg_count = msg_count + 1, last_seen = ? WHERE user_id = ?',
                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_id))
    else:
        c.execute('INSERT INTO users (user_id, username, first_name, msg_count, last_seen) VALUES (?, ?, ?, 1, ?)',
                  (user_id, username, first_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                  
    # Пишем лог
    c.execute('INSERT INTO logs (user_id, message, ai_response, timestamp) VALUES (?, ?, ?, ?)',
              (user_id, message, ai_response, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_stats():
    conn = get_db()
    c = conn.cursor()
    
    # Топ юзеров по сообщениям
    c.execute('SELECT first_name, msg_count FROM users ORDER BY msg_count DESC LIMIT 5')
    top_users = c.fetchall()
    
    # Общее кол-во сообщений и юзеров
    c.execute('SELECT SUM(msg_count) as total_msgs, COUNT(user_id) as total_users FROM users')
    total = c.fetchone()
    
    return top_users, total['total_msgs'] or 0, total['total_users'] or 0

init_db()