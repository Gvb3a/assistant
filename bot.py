from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from deep_translator import GoogleTranslator
from dotenv import load_dotenv
from colorama import Fore, Style, init
from datetime import datetime
from os import getenv, remove

from api import mail, gmail_modify, speech_recognition
from function import llm_answer
    

init()
load_dotenv()


bot_token = getenv('BOT_TOKEN')
admin_id = getenv('ADMIN_ID')


bot = Bot(token=bot_token)
dp = Dispatcher()




def mail_message():
    text, dict_of_unread = mail()

    inline_keyboard = []
    if dict_of_unread:        
        inline_keyboard.append([InlineKeyboardButton(text=str(index), callback_data=f'mail_modify-{index}-{message_id}') for index, message_id in dict_of_unread.items()])
        inline_keyboard.append([InlineKeyboardButton(text='Translate', callback_data='translate')]) # callback.message.text

    return text, InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


async def download_file_for_id(file_id, extension):

    file = await bot.get_file(file_id)
    file_path = file.file_path
    now = datetime.now()
    file_name = f'{now.strftime("%Y%m%d_%H%M%S")}.{extension}'

    await bot.download_file(file_path, file_name)

    return file_name


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


    await callback.answer()
    

@dp.callback_query(F.data.startswith('translate'))
async def callback_translate(callback: CallbackQuery):

    text = callback.message.text
    reply_markup = callback.message.reply_markup

    translated_text = GoogleTranslator(source='en', target='ru').translate(text)
    
    await callback.message.edit_text(text=translated_text, reply_markup=reply_markup)

    await callback.answer()





@dp.message(Command('mail'))
async def command_mail(message: Message) -> None:
    
    text, inline_keyboard = mail_message()

    await bot.send_message(chat_id=message.chat.id, text=text, reply_markup=inline_keyboard, parse_mode='Markdown')





@dp.message()
async def message_handler(message: Message) -> None:

    chat_id = message.chat.id
    user = message.from_user.full_name
    username = message.from_user.username
    message_id = message.message_id


    if message.voice:
        
        file_name = await download_file_for_id(file_id=message.voice.file_id, extension='mp3')

        text = speech_recognition(file_name=file_name).strip()

        await message.reply(text)
        remove(file_name)

    else:
        text = message.text 

    answer = llm_answer(text)

    try:
        await message.answer(answer, parse_mode='Markdown')
    except:
        await message.answer(answer)



if __name__ == '__main__':
    print(f'{Fore.GREEN}Bot is launched{Style.RESET_ALL}') 
    dp.run_polling(bot)
