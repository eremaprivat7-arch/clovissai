# Добавь в конец database.py
def add_warn(user_id, reason):
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS warns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        reason TEXT,
        timestamp TEXT
    )''')
    c.execute('INSERT INTO warns (user_id, reason, timestamp) VALUES (?, ?, ?)',
              (user_id, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_warns(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT reason, timestamp FROM warns WHERE user_id = ?', (user_id,))
    return c.fetchall()