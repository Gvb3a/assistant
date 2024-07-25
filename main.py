import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InputMediaPhoto, Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from deep_translator import GoogleTranslator

from dotenv import load_dotenv
from colorama import Fore, Style, init

from api import mail, gmail_modify

init()
load_dotenv()
bot_token = os.getenv('BOT_TOKEN')


bot = Bot(token=bot_token)
dp = Dispatcher()

def ok(s):
    return f'{Fore.GREEN}{s}{Style.RESET_ALL}'




async def mail_message(chat_id):
    text, dict_of_unread = mail()

    inline_keyboard = []
    if dict_of_unread:        
        inline_keyboard.append([InlineKeyboardButton(text=str(index), callback_data=f'mail_modify-{index}-{message_id}') for index, message_id in dict_of_unread.items()])
        inline_keyboard.append([InlineKeyboardButton(text='Translate', callback_data='translate')]) # callback.message.text


    await bot.send_message(chat_id=chat_id, text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard), parse_mode='Markdown')


@dp.callback_query(F.data.startswith('mail_modify-'))
async def mail_modify(callback: CallbackQuery):

    text = callback.message.text
    data = callback.data.split('-')
    reply_markup = callback.message.reply_markup
    index = data[1]
    email_id = data[2]

    
    gmail_modify(email_id, account=int(index[0])-1) 


    index_1 = text.index(index)
    index_2 = text.index('\n', index_1+1)
    temp = text[index_1:index_2]
    
    if temp[-1] in '✅❌':
        temp = temp[:-1] + ('✅' if temp[-1]=='❌' else '❌')
        text = text[:index_1]+temp+text[index_2:]
        
    else:
        temp += '✅'
        index_3 = text.index('\n', index_2+1)
        index_4 = text.find('\n', index_3+1)
        text = text[:index_1]+temp+text[index_2:index_3]+text[index_4:]

    await callback.message.edit_text(text=text, reply_markup=reply_markup)
    await callback.answer()
    

@dp.callback_query(F.data.startswith('translate'))
async def mail_modify(callback: CallbackQuery):

    text = callback.message.text
    reply_markup = callback.message.reply_markup

    translated_text = GoogleTranslator(source='en', target='ru').translate(text)
    
    await callback.message.edit_text(text=translated_text, reply_markup=reply_markup)
    await callback.answer()


@dp.message(Command('mail'))
async def dp_message(message: Message) -> None:
    await message.answer('Just a moment...')
    await mail_message(message.chat.id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id+1)

    print(ok('Command mail'))


@dp.message(F.text)
async def dp_message(message: Message) -> None:

    chat_id = message.chat.id
    text = message.text
    user = message.from_user.full_name
    username = message.from_user.username
    message_id = message.message_id

    if 'mail' in text or 'почт' in text:
        await message.answer('Just a moment...')  # TODO: temporary response will be generated while processing is in progress
        await mail_message(chat_id)
        await bot.delete_message(chat_id=chat_id, message_id=message_id+1)


    print(ok(f'{text} by {user}({username})'))


if __name__ == '__main__':
    print(ok('Bot is launched'))
    dp.run_polling(bot)
