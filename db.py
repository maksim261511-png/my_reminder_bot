import asyncpg
import os

DB_URL = os.environ.get("DATABASE_URL")  # Render даст эту переменную

async def init_db():
    conn = await asyncpg.connect(DB_URL)
    await conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        time TIMESTAMP,
        task TEXT,
        repeating TEXT DEFAULT NULL
    )
    """)
    await conn.close()


async def add_task(user_id, remind_time, task, repeating=None):
    conn = await asyncpg.connect(DB_URL)
    await conn.execute(
        "INSERT INTO tasks(user_id, time, task, repeating) VALUES($1,$2,$3,$4)",
        user_id, remind_time, task, repeating
    )
    await conn.close()


async def get_tasks(user_id=None):
    conn = await asyncpg.connect(DB_URL)
    if user_id:
        rows = await conn.fetch("SELECT * FROM tasks WHERE user_id=$1 ORDER BY id", user_id)
    else:
        rows = await conn.fetch("SELECT * FROM tasks ORDER BY id")
    await conn.close()
    return rows


async def delete_task(task_id):
    conn = await asyncpg.connect(DB_URL)
    await conn.execute("DELETE FROM tasks WHERE id=$1", task_id)
    await conn.close()


async def clear_tasks(user_id):
    conn = await asyncpg.connect(DB_URL)
    await conn.execute("DELETE FROM tasks WHERE user_id=$1", user_id)
    await conn.close()