import asyncio
import logging
from datetime import datetime

import aioschedule
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import config
# Configure logging
from model import db, Birthday, Notification

logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

markup_request = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton('Все')
).add(
    KeyboardButton('Добавить')
).add(
    KeyboardButton('Удалить')
).add(
    KeyboardButton('Изменить время оповещения')
)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply('Welcoming',
                        reply_markup=markup_request)


# lambda message: message.text == 'Все' commands=['all']
@dp.message_handler(lambda message: message.text == 'Все')
async def all(message: types.Message):
    birthdays = db.query(Birthday).all()

    if len(birthdays) == 0:
        await message.reply('Список пуст')
    else:
        # for b in birthdays:
        await message.reply(',\n'.join(map(lambda b: str(b.name) + ' ' +
                                                     str(b.day) + '.' +
                                                     str(b.month) + '.' +
                                                     str(b.year), birthdays)))
        # await message.reply(str(b.name) + ' ' + str(b.birthday) + ',\n')


class AddOrder(StatesGroup):
    waiting_for_name = State()
    waiting_for_date = State()


class DeleteOrder(StatesGroup):
    waiting_for_name = State()


class NotificationTimeOrder(StatesGroup):
    waiting_for_time = State()


# lambda message: message.text == 'Добавить'
@dp.message_handler(lambda message: message.text == 'Добавить', state='*')
async def add_step1(message: types.Message):
    await message.answer('Введите имя', reply_markup=types.InlineKeyboardMarkup())
    await AddOrder.waiting_for_name.set()


@dp.message_handler(state=AddOrder.waiting_for_name, content_types=types.ContentTypes.TEXT)
async def add_step2(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    await message.answer(
        'Введите дату дня рождения в формате DD.MM.YYYY,\n если год не известен напишите 0000 вместо него')
    await AddOrder.waiting_for_date.set()


@dp.message_handler(state=AddOrder.waiting_for_date, content_types=types.ContentTypes.TEXT)
async def add_step3(message: types.Message, state: FSMContext):
    data = await state.get_data()

    day, month, year = map(int, message.text.split('.'))

    birthday = Birthday(chat_id=message.chat.id,
                        name=data.get('name'),
                        year=year,
                        month=month,
                        day=day)

    db.add(birthday)
    db.commit()
    await state.finish()


@dp.message_handler(lambda message: message.text == 'Удалить', state='*')
async def delete_step1(message: types.Message):
    await message.answer('Введите имя', reply_markup=types.InlineKeyboardMarkup())
    await DeleteOrder.waiting_for_name.set()


@dp.message_handler(state=DeleteOrder.waiting_for_name, content_types=types.ContentTypes.TEXT)
async def delete_step2(message: types.Message, state: FSMContext):
    birthday = db.query(Birthday).filter(Birthday.name == message.text).first()

    if birthday is None:
        await message.reply('No such name in the list')
    else:
        db.delete(birthday)

        db.commit()
        await state.finish()


@dp.message_handler(lambda message: message.text == 'Изменить время оповещения', state='*')
async def update_time_step1(message: types.Message):
    await message.answer('Введите время', reply_markup=types.InlineKeyboardMarkup())
    await NotificationTimeOrder.waiting_for_time.set()


@dp.message_handler(state=NotificationTimeOrder.waiting_for_time, content_types=types.ContentTypes.TEXT)
async def update_time_step2(message: types.Message, state: FSMContext):
    birthday = db.query(Notification).filter(Notification.chat_id == message.chat.id).first()

    if birthday is None:
        notification = Notification(chat_id=message.chat.id,
                                    time=message.text)
        db.add(notification)
        db.commit()
    else:
        db.query(Notification).filter(Notification.chat_id == message.chat.id).update({'time': message.text})
        db.commit()

    await state.finish()


async def send_notification(birthday, curr_year):
    # if birthday.year == '0000':
    #     SendMessage(chat_id=birthday.chat_id,
    #                 text=f'Today is the {curr_year - birthday.year} birthday of {birthday.name}')
    # else:
    #     SendMessage(chat_id=birthday.chat_id, text=f'Today is the birthday of {birthday.name}')
    if birthday.year == '0000':
        await bot.send_message(chat_id=birthday.chat_id,
                               text=f'Today is the {curr_year - birthday.year} birthday of {birthday.name}')
    else:
        await bot.send_message(chat_id=birthday.chat_id, text=f'Today is the birthday of {birthday.name}')


async def job():
    curr_day = str(datetime.today().day)
    curr_month = str(datetime.today().month)
    curr_year = str(datetime.today().year)

    birthdays = db.query(Birthday).filter(Birthday.month == int(curr_month),
                                          Birthday.day == int(curr_day)).all()

    for b in birthdays:
        aioschedule.every(1).day.at('00:55').do(lambda: send_notification(b, curr_year))


# TODO: 1)Write checking correct data 2) Add timezone 3) Tune time of notification


async def scheduler():
    aioschedule.every().day.at('00:54').do(job)

    # loop = asyncio.get_event_loop()
    while True:
        # loop.run_until_complete(aioschedule.run_pending())
        # time.sleep(1)
        await aioschedule.run_pending()
        await asyncio.sleep(1)


DELAY = 10


def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(DELAY, repeat, coro, loop)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.call_later(DELAY, repeat, scheduler, loop)
    executor.start_polling(dp, skip_updates=True, loop=loop)
