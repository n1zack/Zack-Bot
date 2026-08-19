import sqlite3
import os

def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS phone_numbers (id INTEGER PRIMARY KEY, user_id INTEGER, phone TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY, user_id INTEGER, file_path TEXT)")
    conn.commit()
    conn.close()

def add_phone(user_id, phone):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO phone_numbers (user_id, phone) VALUES (?, ?)", (user_id, phone))
    conn.commit()
    conn.close()

def get_user_phones(user_id):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, phone FROM phone_numbers WHERE user_id = ?", (user_id,))
    data = cursor.fetchall()
    conn.close()
    return data

def delete_phone_by_id(phone_id, user_id):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM phone_numbers WHERE id = ? AND user_id = ?", (phone_id, user_id))
    conn.commit()
    conn.close()
