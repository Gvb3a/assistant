import os
import whisper

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from deep_translator import GoogleTranslator

from dotenv import load_dotenv
from colorama import Fore, Style, init
from datetime import datetime

from api import mail, gmail_modify


init()
load_dotenv()
bot_token = os.getenv('BOT_TOKEN')
admin_id = os.getenv('ADMIN_ID')


bot = Bot(token=bot_token)
dp = Dispatcher()




def ok(green_text: str, normal_text: str = '') -> str:
    return f'{Fore.GREEN}{green_text}{Style.RESET_ALL}{normal_text}'


def speech_recognition(file_name: str) -> str:

    model = whisper.load_model('base') 
    result = model.transcribe(file_name)


    text = result['text']

    print(ok(green_text='function: speech_recognition', normal_text=f'(text)'))

    return text


async def download_file_for_id(file_id, extension):

    file = await bot.get_file(file_id)
    file_path = file.file_path
    now = datetime.now()
    file_name = f'{now.strftime("%Y%m%d_%H%M%S")}.{extension}'

    await bot.download_file(file_path, file_name)

    print(ok('function: download_file_for_id', file_name))

    return file_name


def mail_message():
    text, dict_of_unread = mail()

    inline_keyboard = []
    if dict_of_unread:        
        inline_keyboard.append([InlineKeyboardButton(text=str(index), callback_data=f'mail_modify-{index}-{message_id}') for index, message_id in dict_of_unread.items()])
        inline_keyboard.append([InlineKeyboardButton(text='Translate', callback_data='translate')]) # callback.message.text

    print(ok('function: mail_message', f'({len(dict_of_unread)})'))
    return text, InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    





@dp.callback_query(F.data.startswith('mail_modify-'))
async def callback_mail_modify(callback: CallbackQuery):

    text = callback.message.text
    data = callback.data.split('-')
    reply_markup = callback.message.reply_markup
    index = data[1]
    email_id = data[2]

    
    gmail_modify(message_id=email_id, account=int(index[0])-1) 


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

    print(ok(f'callback: callback_mail_modify', f'({index})'))

    await callback.answer()
    

@dp.callback_query(F.data.startswith('translate'))
async def callback_translate(callback: CallbackQuery):

    text = callback.message.text
    reply_markup = callback.message.reply_markup

    translated_text = GoogleTranslator(source='en', target='ru').translate(text)
    
    await callback.message.edit_text(text=translated_text, reply_markup=reply_markup)
    
    print(ok(f'callback: translate'))

    await callback.answer()





@dp.message(Command('mail'))
async def command_mail(message: Message) -> None:
    
    text, inline_keyboard = mail_message()

    await bot.send_message(chat_id=message.chat.id, text=text, reply_markup=inline_keyboard, parse_mode='Markdown')

    print(ok('command: mail'))





@dp.message()
async def message_handler(message: Message) -> None:

    chat_id = message.chat.id
    user = message.from_user.full_name
    username = message.from_user.username
    message_id = message.message_id


    if message.voice:

        file_name = await download_file_for_id(file_id=message.voice.file_id, extension='mp3')

        text = speech_recognition(file_name=file_name)

        os.remove(file_name)

    else:
        text = message.text

    text = text.lower()

    if 'mail' in text or 'почт' in text:
        await message.answer('Just a moment...')  # TODO: temporary response will be generated while processing is in progress

        mail_text, inline_keyboard = mail_message()

        await bot.send_message(chat_id=chat_id, text=mail_text, reply_markup=inline_keyboard, parse_mode='Markdown')
        
        await bot.delete_message(chat_id=chat_id, message_id=message_id+1)
        
    else:
        await message.answer('In development')

    print(ok(f'Message: {text}'))



if __name__ == '__main__':
    print(ok('Bot is launched'))
    dp.run_polling(bot)
