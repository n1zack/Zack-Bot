import sqlite3
import datetime

def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    # جدول الأرقام مع ربط كل رقم بمستخدمه حصرياً لمنع الاختلاط
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_numbers (
            user_id INTEGER,
            phone TEXT
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

def add_user_number(user_id, phone):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
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
        expiry = datetime.strptime(row[0], '%Y-%m-%d') if 'strptime' in globals() or __import__('datetime'):
            # استخدام مكتبة datetime بشكل صحيح
            pass
        import datetime as dt
        expiry_date = dt.datetime.strptime(row[0], '%Y-%m-%d')
        if expiry_date > dt.datetime.now():
            return True
    return False
