from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto

from deep_translator import GoogleTranslator
from dotenv import load_dotenv
from colorama import Fore, Style, init
from datetime import datetime
from os import getenv, remove

if __name__ == '__main__' or '.' not in __name__:
    from api import mail, gmail_modify, speech_recognition
    from llm_answer import llm_select_tool, llm_use_tool, llm_answer, llm_regenerate
else:
    from .api import mail, gmail_modify, speech_recognition
    from .llm_answer import llm_select_tool, llm_use_tool, llm_answer, llm_regenerate
    

init()
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


bot_token = getenv('BOT_TOKEN')
admin_id = getenv('ADMIN_ID')


bot = Bot(token=str(bot_token))
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
    file_path = str(file.file_path)
    now = datetime.now()
    file_name = f'{now.strftime("%Y%m%d_%H%M%S")}.{extension}'

    await bot.download_file(file_path, file_name)

    return file_name


@dp.callback_query(F.data.startswith('mail_modify-'))
async def callback_mail_modify(callback: CallbackQuery):

    text = str(callback.message.text)
    data = str(callback.data).split('-')
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


@dp.message(Command('regenerate'))
async def command_regenerate(message: Message) -> None:
    chat_id = message.chat.id
    id = message.from_user.id
    message_id = message.message_id

    answer, images = llm_regenerate(id=id)

    try:
        await message.answer(text=answer, parse_mode='Markdown')
    except:
        await message.answer(text=answer)

    

@dp.message()
async def message_handler(message: Message) -> None:
    chat_id = message.chat.id
    user = message.from_user.full_name
    user_id =  message.from_user.id
    username = message.from_user.username
    message_id = message.message_id


    if message.voice:
        await message.reply('Start speech recognition')
        file_name = await download_file_for_id(file_id=message.voice.file_id, extension='mp3')

        text = speech_recognition(file_name=file_name).strip()
        remove(file_name)
        
        temp_text = f'Recognized: {text}'
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id+1, text=temp_text)

    else:
        temp_text = ''
        text = str(message.text)
        await message.reply(temp_text + '\nSelecting a tool')
    print(f'{text} by {user}')

    try:
        action, action_input = llm_select_tool(user_message=text, id=id)
        if action != 'none':
            temp_text = temp_text + f'\ntool: {action}'
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id+1, text=temp_text + ('' if action == 'none' else '\nUsing the tool') )
            system_message, images = await llm_use_tool(user_message=text, action=action, action_input=action_input, id=id, user_name=user)
        else:
            system_message, images = None, []
        await bot.edit_message_text(chat_id=chat_id, message_id=message_id+1, text=temp_text + '\nAsking the llm')
        answer = llm_answer(user_message=text, user_name=user, id=user_id, system_message=system_message)
        await bot.delete_message(chat_id=chat_id, message_id=message_id+1)
    except Exception as e:
        print(f'message_handler 1: {e}')
        answer, images = 'Error. Try again later or contact admin', []

    try:
        if images == []:
            if len(answer) > 4000:  # TODO
                inline_button = InlineKeyboardButton(text='Regenerate', callback_data='regenerate')
                inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[[inline_button]])
                answer = answer[:4000]
                await message.answer(answer, reply_markup=inline_keyboard)

            else:
                await message.answer(answer, parse_mode='Markdown')
        else:
            caption = answer[:1000]
            media = [InputMediaPhoto(media=FSInputFile(path=images[0]), 
                                     caption=caption)]
            for image in images[1:]:
                media.append(InputMediaPhoto(media=FSInputFile(path=image)))
            await message.answer_media_group(media=media, parse_mode='Markdown')

            for image in images:
                remove(image)

    except Exception as e:
        print(f'message_handler 2: {e}')
        answer = answer[:4000]
        await message.answer(answer)



if __name__ == '__main__':
    print(f'{Fore.GREEN}Bot is launched{Style.RESET_ALL}') 
    dp.run_polling(bot)
