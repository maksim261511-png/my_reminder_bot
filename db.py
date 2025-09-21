import sqlite3
from datetime import datetime

DB_PATH = "tasks.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS reminders(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 time TEXT,
                 task TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS repeating(
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 type TEXT,
                 data TEXT,
                 task TEXT)""")
    conn.commit()
    conn.close()


def add_reminder(user_id, remind_time: datetime, task: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO reminders(user_id,time,task) VALUES (?,?,?)",
              (user_id, remind_time.isoformat(), task))
    conn.commit()
    conn.close()


def get_reminders(user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("SELECT id,user_id,time,task FROM reminders WHERE user_id=?", (user_id,))
    else:
        c.execute("SELECT id,user_id,time,task FROM reminders")
    data = c.fetchall()
    conn.close()
    return data


def delete_reminder(rid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE id=?", (rid,))
    conn.commit()
    conn.close()


def add_repeating(user_id, typ, data, task):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO repeating(user_id,type,data,task) VALUES (?,?,?,?)",
              (user_id, typ, data, task))
    conn.commit()
    conn.close()


def get_repeating(user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if user_id:
        c.execute("SELECT id,user_id,type,data,task FROM repeating WHERE user_id=?", (user_id,))
    else:
        c.execute("SELECT id,user_id,type,data,task FROM repeating")
    data = c.fetchall()
    conn.close()
    return data


def clear_user_tasks(uid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM reminders WHERE user_id=?", (uid,))
    c.execute("DELETE FROM repeating WHERE user_id=?", (uid,))
    conn.commit()
    conn.close()