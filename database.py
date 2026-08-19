import sqlite3

def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    # إنشاء جدول حفظ أرقام المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_numbers (
            user_id INTEGER,
            phone TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user_number(user_id, phone):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    # منع تكرار نفس الرقم لنفس المستخدم
    cursor.execute("SELECT phone FROM user_numbers WHERE user_id = ? AND phone = ?", (user_id, phone))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO user_numbers (user_id, phone) VALUES (?, ?)", (user_id, phone))
        conn.commit()
    conn.close()

def get_user_numbers(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT phone FROM user_numbers WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]
