import os
import datetime
import psycopg2

SUPABASE_URL = "postgresql://neondb_owner:npg_3AlBEIVMT0on@ep-lively-bonus-axwosu8s.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require"

def get_db_connection():
    return psycopg2.connect(SUPABASE_URL, connect_timeout=10)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_numbers (
            user_id BIGINT,
            phone TEXT,
            session_string TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id BIGINT PRIMARY KEY,
            expiry_date TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def add_user_number(user_id, phone, session_string=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT session_string FROM user_numbers WHERE user_id = %s AND phone = %s", (user_id, phone))
    if cursor.fetchone():
        cursor.execute("UPDATE user_numbers SET session_string = %s WHERE user_id = %s AND phone = %s", (session_string, user_id, phone))
    else:
        cursor.execute("INSERT INTO user_numbers (user_id, phone, session_string) VALUES (%s, %s, %s)", (user_id, phone, session_string))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_numbers(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT phone FROM user_numbers WHERE user_id = %s", (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [row[0] for row in rows]

def get_session_string(user_id, phone):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT session_string FROM user_numbers WHERE user_id = %s AND phone = %s", (user_id, phone))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None

def delete_user_number(user_id, phone):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_numbers WHERE user_id = %s AND phone = %s", (user_id, phone))
    conn.commit()
    cursor.close()
    conn.close()

def add_subscriber(user_id, days):
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO subscribers (user_id, expiry_date) VALUES (%s, %s) ON CONFLICT (user_id) DO UPDATE SET expiry_date = EXCLUDED.expiry_date",
        (user_id, expiry)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return expiry

def get_subscribers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, expiry_date FROM subscribers")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def is_subscribed(user_id):
    if user_id == 1251313339:  # زاك المشرف الأساسي
        return True
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT expiry_date FROM subscribers WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        expiry_date = datetime.datetime.strptime(row[0], '%Y-%m-%d')
        if expiry_date > datetime.datetime.now():
            return True
    return False
