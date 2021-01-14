import logging
from datetime import datetime

import aioschedule
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import Date

from config import config
# Configure logging
from model import db, Birthday

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
)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Welcoming",
                        reply_markup=markup_request)


# lambda message: message.text == 'Все'
@dp.message_handler(commands=['all'])
async def all(message: types.Message):

    birthdays = db.query(Birthday).all()

    if len(birthdays) == 0:
        await message.reply('Список пуст')
    else:
        # for b in birthdays:
        await message.reply(',\n'.join(map(lambda b: str(b.name) + ' ' + str(b.birthday), birthdays)))
        # await message.reply(str(b.name) + ' ' + str(b.birthday) + ',\n')


class AddOrder(StatesGroup):
    waiting_for_name = State()
    waiting_for_date = State()


class DeleteOrder(StatesGroup):
    waiting_for_name = State()


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
                        birthday=datetime(year=year, month=month, day=day))

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


async def job():
    db.query(Birthday).filter()

aioschedule.every().day.at("00:00").do(job)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
