import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InputMediaPhoto, Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv

from api import mail


load_dotenv()
bot_token = os.getenv('BOT_TOKEN')


bot = Bot(token=bot_token)
dp = Dispatcher()


@dp.message(F.text)
async def dp_message(message: Message) -> None:
    message_text = message.text

    if 'mail' in message_text.lower() or 'почта' in message_text.lower():
        text, list_of_unread = mail()
        inline_keyboard = []
        for id, k in list_of_unread:
            inline_keyboard.append([InlineKeyboardButton(text=str(k), callback_data=str(id))])
        await message.answer(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard))


@dp.callback_query(F.data)   # воссоздает то же меню, что и /start
async def inline_back_handler(callback: CallbackQuery):
    l = sql_mode_or_language(callback.from_user.id, 'language')
    await callback.message.edit_text(text=start_list[l], reply_markup=start_keyboard(l))
    await callback.answer()

if __name__ == '__main__':
    print('Bot is launched')
    dp.run_polling(bot)