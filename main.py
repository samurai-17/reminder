import asyncio
import sqlite3
import json
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

bot = Bot("8194727128:AAEiGaDcg8qnepSdb4SaXkuSj0zchqxO6rc")
dp = Dispatcher()

scheduler = AsyncIOScheduler()

weekdays = {
    "понедельник": 0, "вторник": 1, "среда": 2, "четверг": 3,
    "пятница": 4, "суббота": 5, "воскресенье": 6
}


class ScheduleState(StatesGroup):
    waiting_for_schedule = State()


async def send_message(chat_id: int, date: str, event: str):
    await bot.send_message(chat_id, f"🔔 Напоминание! {date} - {event}")


@dp.message(Command("start"))
async def start(mess: Message):
    await mess.answer(f"Привет, {mess.from_user.username}! Рад, что ты пришел сюда! Держи буську😘")


@dp.message(Command("create_schedule"))
async def create_schedule(mess: Message, state: FSMContext):
    await mess.answer("Отправь свое расписание в следующем формате: \nДень недели - занятие - часы:минуты")
    await state.set_state(ScheduleState.waiting_for_schedule)


@dp.message(ScheduleState.waiting_for_schedule)
async def schedule_processing(mess: Message, state: FSMContext):
    list_train = mess.text
    single = list_train.split("\n")
    days = [s.split("-")[0].lower().replace(" ", "") for s in single]
    train = [s.split("-")[1].lower().strip() for s in single]
    time = [s.split("-")[2].strip() for s in single]
    data = {}
    for i in range(len(days)):
        data[days[i]] = train[i] + " - " + time[i]
    json_data = json.dumps(data)
    await mess.answer(f"Твое расписание сохранено!")
    await state.clear()
    conn = sqlite3.connect("trainings")
    cur = conn.cursor()
    cur.execute(
        'CREATE TABLE IF NOT EXISTS trainings (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, training TEXT NOT NULL);')
    conn.commit()
    cur.execute('INSERT INTO trainings (user_id, training) VALUES (?, ?)', (mess.from_user.id, json_data,))
    conn.commit()
    cur.close()
    conn.close()
    schedule_jobs(mess.from_user.id)


def schedule_jobs(chat_id):
    conn = sqlite3.connect("trainings")
    cur = conn.cursor()

    cur.execute("SELECT training FROM trainings WHERE user_id = ?", (chat_id,))
    row = cur.fetchone()
    if row:
        restored_data = json.loads(row[0])
        for day, event in restored_data.items():
            if day in weekdays:
                today = datetime.now()
                target_date = today + timedelta(days=(weekdays[day] - today.weekday()) % 7)
                time = [event.split("-")[1].split(":")[0].strip(), event.split("-")[1].split(":")[1].strip()]
                total = int(time[0]) * 60 + int(time[1]) - 90
                if total < 0:
                    total = 1440 + total
                    target_date = datetime.now()
                hours = total // 60
                minute = total - hours * 60
                run_date = target_date.replace(hour=hours, minute=minute, second=0)  # Время отправки
                scheduler.add_job(send_message, 'date', run_date=run_date, args=[chat_id, day, event])


@dp.message(Command("check_schedule"))
async def check_schedule(mess: Message):
    conn = sqlite3.connect("trainings")
    cur = conn.cursor()

    cur.execute("SELECT training FROM trainings WHERE user_id = ?", (mess.from_user.id,))
    row = cur.fetchone()

    if row:
        restored_data = json.loads(row[0])
        info = ''
        for key in restored_data.keys():
            info += f"{key} - {restored_data.get(key)}\n"
        await mess.answer(info)

    cur.close()
    conn.close()


async def main():
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
