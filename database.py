import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    # جدول الأرقام والجلسات مع عزل تام لكل مستخدم عبر user_id و phone
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_numbers (
            user_id INTEGER,
            phone TEXT,
            session_string TEXT,
            PRIMARY KEY (user_id, phone)
        )
    ''')
    # جدول المشتركين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id INTEGER PRIMARY KEY,
            expiry_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user_number(user_id, phone, session_string=""):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    # تحديث الجلسة إذا كانت موجودة أو إضافتها جديدة للمستخدم حصرياً
    cursor.execute('''
        INSERT INTO user_numbers (user_id, phone, session_string) 
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, phone) 
        DO UPDATE SET session_string = excluded.session_string
    ''', (user_id, phone, session_string))
    conn.commit()
    conn.close()

def get_user_numbers(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT phone FROM user_numbers WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_session_string(user_id, phone):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT session_string FROM user_numbers WHERE user_id = ? AND phone = ?", (user_id, phone))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def delete_user_number(user_id, phone):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_numbers WHERE user_id = ? AND phone = ?", (user_id, phone))
    conn.commit()
    conn.close()

def add_subscriber(user_id, days):
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO subscribers (user_id, expiry_date) VALUES (?, ?)", (user_id, expiry))
    conn.commit()
    conn.close()
    return expiry

def get_subscribers():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, expiry_date FROM subscribers")
    rows = cursor.fetchall()
    conn.close()
    return rows

def is_subscribed(user_id):
    if user_id == 1251313339:  # استثناء المشرف الأساسي زاك
        return True
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT expiry_date FROM subscribers WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        expiry_date = datetime.datetime.strptime(row[0], '%Y-%m-%d')
        if expiry_date > datetime.datetime.now():
            return True
    return False
