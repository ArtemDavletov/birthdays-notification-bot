from aiogram import types

from app import dp
from model import Birthday, db


@dp.message_handler(lambda message: message.text == 'Удалить')
async def delete(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply('Fill in name')

    birthday = Birthday(chat_id=message.chat.id,
                        name=message.text,
                        birthday=Date())
    db.add(birthday)
    db.commit()
