import asyncio
import os
import re
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from db import init_db, add_reminder, add_repeating, get_repeating, get_reminders, delete_reminder, clear_user_tasks

# ⚠️ Токен загружаем из переменной окружения
API_TOKEN = os.environ.get("API_TOKEN")

if not API_TOKEN:
    raise ValueError("8467618548:AAG5q1K8cGnHJvLg_RVopDrWIjxeV84E86I")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# ------------------------------
# Команды
# ------------------------------
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    reply_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    reply_kb.add(
        KeyboardButton("📋 Показать все задачи"),
        KeyboardButton("📅 Задачи на сегодня")
    )
    reply_kb.add(
        KeyboardButton("ℹ️ Помощь"),
        KeyboardButton("🗑 Удалить все задачи")
    )

    await message.reply(
        "Привет! Я твой бот‑напоминалка 📅\n\n"
        "✍ Примеры задач:\n"
        "• через 5 минут: чай\n"
        "• 15.07.2025 08:30: самолёт\n"
        "• завтра в 09:00: зарядка\n"
        "• послезавтра в 20:00: встреча\n"
        "• через полчаса: кофе\n"
        "• каждый день в 07:00: бег\n"
        "• каждую неделю в пн 18:00: спорт\n\n"
        "Используй кнопки снизу 👇",
        reply_markup=reply_kb
    )


@dp.message_handler(commands=["help"])
async def help_cmd(message: types.Message):
    await message.reply(
        "ℹ️ Поддерживаемые форматы:\n"
        "• через 10 минут: кофе\n"
        "• через 2 часа: уроки\n"
        "• завтра в 08:00: зарядка\n"
        "• послезавтра в 18:30: концерт\n"
        "• 31.12.2025 23:59: новый год 🎉\n"
        "• каждый день в 07:30: бег\n"
        "• каждую неделю в вт 19:00: звонок маме\n"
    )


@dp.message_handler(commands=["listall"])
async def listall_cmd(message: types.Message):
    uid = message.from_user.id
    tasks = []
    for rid, _, t, task in get_reminders(uid):
        dt = datetime.fromisoformat(t)
        tasks.append(f"🕐 {task} ⏰ {dt.strftime('%d.%m.%Y %H:%M')}")
    for rid, _, typ, data, task in get_repeating(uid):
        if typ == "daily":
            h, m = map(int, data.split(":"))
            tasks.append(f"🔁 {task} ⏰ каждый день {h:02d}:{m:02d}")
        elif typ == "weekly":
            tasks.append(f"🗓 {task} ⏰ каждую неделю {data}")
    if tasks:
        await message.reply("📋 Задачи:\n" + "\n".join(tasks))
    else:
        await message.reply("❌ У тебя нет задач")


@dp.message_handler(commands=["today"])
async def today_cmd(message: types.Message):
    uid = message.from_user.id
    now = datetime.now()
    today = []
    for _, _, t, task in get_reminders(uid):
        dt = datetime.fromisoformat(t)
        if dt.date() == now.date():
            today.append(f"🕐 {task} ⏰ {dt.strftime('%H:%M')}")
    if today:
        await message.reply("📋 Сегодня:\n" + "\n".join(today))
    else:
        await message.reply("Сегодня задач нет ✅")


# ------------------------------
# Работа через кнопки
# ------------------------------
@dp.message_handler(lambda m: m.text == "📋 Показать все задачи")
async def btn_listall(message: types.Message):
    await listall_cmd(message)

@dp.message_handler(lambda m: m.text == "📅 Задачи на сегодня")
async def btn_today(message: types.Message):
    await today_cmd(message)

@dp.message_handler(lambda m: m.text == "ℹ️ Помощь")
async def btn_help(message: types.Message):
    await help_cmd(message)

@dp.message_handler(lambda m: m.text == "🗑 Удалить все задачи")
async def btn_clear(message: types.Message):
    clear_user_tasks(message.from_user.id)
    await message.answer("🗑 Все твои задачи удалены!")


# ------------------------------
# Парсер задач
# ------------------------------
@dp.message_handler()
async def add_tasks(message: types.Message):
    uid = message.from_user.id
    txt = message.text.lower().strip()

    # 1. Конкретная дата
    m = re.match(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})\s+(\d{1,2}):(\d{2})[: ]?(.*)", txt)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        h, mi, what = int(m.group(4)), int(m.group(5)), m.group(6)
        dt = datetime(y, mo, d, h, mi)
        add_reminder(uid, dt, what)
        await message.reply(f"📅 {what} на {dt.strftime('%d.%m.%Y %H:%M')}")
        return

    # 2. Завтра
    m = re.match(r"завтра в\s+(\d{1,2}):(\d{2})[: ]?(.*)", txt)
    if m:
        h, mi, what = int(m.group(1)), int(m.group(2)), m.group(3)
        dt = datetime.now() + timedelta(days=1)
        dt = dt.replace(hour=h, minute=mi, second=0, microsecond=0)
        add_reminder(uid, dt, what)
        await message.reply(f"📅 Завтра {what} в {dt.strftime('%H:%M')}")
        return

    # 3. Послезавтра
    m = re.match(r"послезавтра в\s+(\d{1,2}):(\d{2})[: ]?(.*)", txt)
    if m:
        h, mi, what = int(m.group(1)), int(m.group(2)), m.group(3)
        dt = datetime.now() + timedelta(days=2)
        dt = dt.replace(hour=h, minute=mi, second=0, microsecond=0)
        add_reminder(uid, dt, what)
        await message.reply(f"📅 Послезавтра {what} в {dt.strftime('%H:%M')}")
        return

    # 4. Через N минут / часов
    m = re.match(r"через (\d+) (минут[уы]?|час[ауов]*)[: ]?(.*)", txt)
    if m:
        num, unit, what = int(m.group(1)), m.group(2), m.group(3)
        delta = timedelta(minutes=num) if "мин" in unit else timedelta(hours=num)
        dt = datetime.now() + delta
        add_reminder(uid, dt, what)
        await message.reply(f"✅ {what} ⏰ {dt.strftime('%H:%M')}")
        return

    # 5. Через полчаса
    if txt.startswith("через полчаса"):
        what = txt.split(":", 1)[1] if ":" in txt else "дело"
        dt = datetime.now() + timedelta(minutes=30)
        add_reminder(uid, dt, what.strip())
        await message.reply(f"✅ {what} через полчаса ({dt.strftime('%H:%M')})")
        return

    # 6. Через полдня
    if txt.startswith("через полдня"):
        what = txt.split(":", 1)[1] if ":" in txt else "дело"
        dt = datetime.now() + timedelta(hours=12)
        add_reminder(uid, dt, what.strip())
        await message.reply(f"✅ {what} через полдня ({dt.strftime('%H:%M')})")
        return

    # 7. Через неделю
    m = re.match(r"через неделю в\s+(\d{1,2}):(\d{2})[: ]?(.*)", txt)
    if m:
        h, mi, what = int(m.group(1)), int(m.group(2)), m.group(3)
        dt = datetime.now() + timedelta(weeks=1)
        dt = dt.replace(hour=h, minute=mi, second=0, microsecond=0)
        add_reminder(uid, dt, what)
        await message.reply(f"📅 {what} через неделю в {dt.strftime('%H:%M')}")
        return

    # 8. Каждый день
    m = re.match(r"каждый день в\s+(\d{1,2}):(\d{2})[: ]?(.*)", txt)
    if m:
        h, mi, what = int(m.group(1)), int(m.group(2)), m.group(3)
        add_repeating(uid, "daily", f"{h}:{mi}", what)
        await message.reply(f"🔁 {what} ⏰ ежедневно {h:02d}:{mi:02d}")
        return

    # 9. Каждую неделю
    m = re.match(r"каждую неделю в\s+(\w+)\s+(\d{1,2}):(\d{2})[: ]?(.*)", txt)
    if m:
        day, h, mi, what = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)
        add_repeating(uid, "weekly", f"{day} {h:02d}:{mi:02d}", what)
        await message.reply(f"🗓 {what} ⏰ каждую неделю {day} {h:02d}:{mi:02d}")
        return

    await message.reply("❌ Не понял формат. Используй /help.")


# ------------------------------
# Фоновый воркер
# ------------------------------
async def reminder_worker():
    while True:
        now = datetime.now()
        for rid, uid, t, task in get_reminders():
            dt = datetime.fromisoformat(t)
            if dt <= now:
                await bot.send_message(uid, f"🔔 {task}")
                delete_reminder(rid)
        for rid, uid, typ, data, task in get_repeating():
            if typ == "daily":
                h, mi = map(int, data.split(":"))
                if now.hour == h and now.minute == mi and now.second < 5:
                    await bot.send_message(uid, f"🔁 {task}")
            elif typ == "weekly":
                parts = data.split()
                if len(parts) == 2:
                    day, hm = parts
                    h, mi = map(int, hm.split(":"))
                    weekdays = {"пн":0,"вт":1,"ср":2,"чт":3,"пт":4,"сб":5,"вс":6}
                    wd = weekdays.get(day[:2], None)
                    if wd is not None and now.weekday() == wd:
                        if now.hour == h and now.minute == mi and now.second < 5:
                            await bot.send_message(uid, f"🗓 {task}")
        await asyncio.sleep(5)


# ------------------------------
# Запуск
# ------------------------------
async def on_startup(_):
    init_db()
    asyncio.create_task(reminder_worker())

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)