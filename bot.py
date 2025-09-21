import asyncio
import os
import re
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from dateutil import parser

from db import init_db, add_task, get_tasks, delete_task, clear_tasks

API_TOKEN = os.environ.get("API_TOKEN")
if not API_TOKEN:
    raise ValueError("⚠️ Установите API_TOKEN в переменных окружения")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# ------------------------------
# Команда /start
# ------------------------------
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📋 Все задачи", callback_data="list"))
    kb.add(InlineKeyboardButton("🗑 Очистить все", callback_data="clear"))
    kb.add(InlineKeyboardButton("ℹ️ Помощь", callback_data="help"))
    await message.answer("Привет! Я твой умный бот‑напоминалка 📅", reply_markup=kb)


# ------------------------------
# Помощь
# ------------------------------
@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    await message.answer(
        "ℹ Примеры:\n"
        "• через 10 минут: кофе\n"
        "• через 2 часа: работа\n"
        "• завтра в 09:00: зарядка\n"
        "• 31.12.2025 23:59: Новый год 🎉\n\n"
        "🗑 Удалить отдельную задачу: /delete ID (например /delete 2)"
    )


# ------------------------------
# Удаление задачи по ID
# ------------------------------
@dp.message_handler(commands=['delete'])
async def delete_cmd(message: types.Message):
    try:
        _, task_id = message.text.split()
        task_id = int(task_id)
        await delete_task(task_id)
        await message.answer(f"🗑 Задача {task_id} удалена.")
    except:
        await message.answer("❌ Используй: /delete ID")


# ------------------------------
# Inline кнопки
# ------------------------------
@dp.callback_query_handler(lambda c: c.data == "list")
async def list_tasks(callback: types.CallbackQuery):
    tasks = await get_tasks(callback.from_user.id)
    if not tasks:
        await callback.message.answer("❌ Нет задач")
        return
    text = "\n".join([f"{t['id']}. {t['task']} ⏰ {t['time']}" for t in tasks])
    await callback.message.answer("📋 Твои задачи:\n" + text)


@dp.callback_query_handler(lambda c: c.data == "clear")
async def cb_clear(callback: types.CallbackQuery):
    await clear_tasks(callback.from_user.id)
    await callback.message.answer("🗑 Все задачи удалены ✅")


@dp.callback_query_handler(lambda c: c.data == "help")
async def cb_help(callback: types.CallbackQuery):
    await help_cmd(callback.message)


# ------------------------------
# Добавление задачи
# ------------------------------
@dp.message_handler()
async def add_task_handler(message: types.Message):
    txt = message.text.strip()

    # через N минут
    m = re.match(r"через (\d+) минут[: ]*(.*)", txt, re.I)
    if m:
        minutes = int(m.group(1))
        what = m.group(2) or "дело"
        dt = datetime.now() + timedelta(minutes=minutes)
        await add_task(message.from_user.id, dt, what)
        await message.answer(f"✅ {what} через {minutes} минут ({dt.strftime('%H:%M')})")
        return

    # через N часов
    m = re.match(r"через (\d+) часов[: ]*(.*)", txt, re.I)
    if m:
        hours = int(m.group(1))
        what = m.group(2) or "дело"
        dt = datetime.now() + timedelta(hours=hours)
        await add_task(message.from_user.id, dt, what)
        await message.answer(f"✅ {what} через {hours} часов ({dt.strftime('%H:%M')})")
        return

    # конкретная дата/время ("31.12.2025 23:59: Новый год")
    try:
        if ":" in txt and any(c.isdigit() for c in txt):
            what = txt.split(":", 1)[1].strip()
            dstr = txt.split(":", 1)[0].strip()
            dt = parser.parse(dstr, dayfirst=True, fuzzy=True)
            await add_task(message.from_user.id, dt, what)
            await message.answer(f"📅 {what} на {dt}")
            return
    except:
        pass

    await message.answer("❌ Не понял формат. Напиши /help")


# ------------------------------
# Цикл напоминалок
# ------------------------------
async def reminder_worker():
    while True:
        tasks = await get_tasks()
        now = datetime.now()
        for t in tasks:
            dt = t["time"]

            # за 5 минут
            if now + timedelta(minutes=5) >= dt > now:
                await bot.send_message(t["user_id"], f"⏳ Скоро: {t['task']} (через 5 минут)")

            # само событие
            if now >= dt:
                await bot.send_message(t["user_id"], f"🔔 {t['task']}")
                await delete_task(t["id"])

        await asyncio.sleep(30)


# ------------------------------
# Запуск
# ------------------------------
async def on_startup(_):
    await init_db()
    asyncio.create_task(reminder_worker())

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)