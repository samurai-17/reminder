from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
import datetime
from main import bot

DAYS = ['Понедельник','Вторник','Среда','Четверг','Пятница','Суббота','Воскресенье']


current_day = datetime.datetime.today().weekday()
keyboard_days = DAYS[current_day:] + DAYS[:current_day]
day_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text=day,callback_data=day)
    ] for day in keyboard_days
])


async def set_commands():
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="create_schedule", description="Создать расписание тренировок"),
        BotCommand(command="check_schedule", description="Посмотреть расписание")
    ]
    await bot.set_my_commands(commands)