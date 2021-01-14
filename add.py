from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from app import dp
from model import Birthday, db


class AddOrder(StatesGroup):
    waiting_for_name = State()
    waiting_for_date = State()


@dp.message_handler(lambda message: message.text == 'Добавить', state='*')
async def add_step1(message: types.Message):

    await message.answer('Введите имя')
    await AddOrder.waiting_for_name.set()


@dp.message_handler(state=AddOrder.waiting_for_name, content_types=types.ContentTypes.TEXT)
async def add_step2(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    await message.answer('Введите дату дня рождения')
    await AddOrder.waiting_for_date.set()


@dp.message_handler(state=AddOrder.waiting_for_date, content_types=types.ContentTypes.TEXT)
async def add_step3(message: types.Message, state: FSMContext):
    data = await state.get_data()

    birthday = Birthday(chat_id=message.chat.id,
                        name=data.get('name'),
                        birthday=message.text)
    db.add(birthday)
    db.commit()
