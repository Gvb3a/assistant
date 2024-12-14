from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, FSInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from colorama import Fore, Style, init

import os

from dotenv import load_dotenv
from datetime import datetime


if __name__ == '__main__' or '.' not in __name__:
    from api import speech_recognition, llm_api, files_to_text
    from llm_answer import system_prompt, llm_select_tool, llm_use_tool
    from sql import sql_check_user, sql_select_history, sql_insert_message
    from log import log
    from magic import markdown_to_html
else:
    from .api import speech_recognition, llm_api, files_to_text
    from .llm_answer import system_prompt, llm_select_tool, llm_use_tool
    from .sql import sql_check_user, sql_select_history, sql_insert_message
    from .log import log
    from .magic import markdown_to_html
    

load_dotenv()
init()

bot_token = os.getenv('BOT_TOKEN')
# TODO: admin id


class FSM(StatesGroup):
    processing = State()  # is enabled if the request is being processed


bot = Bot(token=str(bot_token))
dp = Dispatcher()


async def download_file_for_id(file_id, extension):

    file = await bot.get_file(file_id)
    file_path = str(file.file_path)
    now = datetime.now()
    file_name = f'{now.strftime("%Y%m%d_%H%M%S")}.{extension}'

    await bot.download_file(file_path, file_name)

    return file_name


@dp.message(CommandStart())  # /start command handler
async def process_start_command(message: Message) -> None:
    await message.answer('Hi! I am an agent with access to the internet and WolframAlpha. You can ask for actual information and any calculations.  \n\n[GitHub](https://github.com/Gvb3a/assistant)', parse_mode='Markdown')    



@dp.message(StateFilter(default_state))
async def message_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(FSM.processing)
    chat_id = message.chat.id
    user = message.from_user.full_name
    user_id =  message.from_user.id
    username = message.from_user.username
    message_id = message.message_id
    sql_check_user(user_id=user_id, telegram_name=user, telegram_username=username)

    temp_message_text = ['Selecting tool - 🔍', 'Using the tool - ⚙️', 'Generating response - 🤖']
    temp_message_id = message_id + 1

    files = []
    
    if message.voice:
        await message.reply('Recognizing audio...')
        file_name = await download_file_for_id(file_id=message.voice.file_id, extension='mp3')
        
        text = speech_recognition(file_name=file_name).strip()
        os.remove(file_name)
        
        temp_message_text[0] = temp_message_text[0][:-2] + '✅'
        await bot.edit_message_text(chat_id=chat_id, message_id=temp_message_id, text=f'Recognized: {text}')

        temp_message_id += 1
    
    elif message.photo:
        await message.reply('Every time you ask a new image question, you will have to submit the image again.')
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_name = file.file_path.split('/')[-1]
        await bot.download_file(file_path, file_name)

        files = [file_name]

        text = str(message.caption) if message.caption else 'Describe the image'

        temp_message_id += 1

    elif message.document:
        await message.reply('Every time you ask a new document question, you will have to submit the document again.')
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        file_name = file.file_path.split('/')[-1]
        await bot.download_file(file_path, file_name)

        files = [file_name]

        text = str(message.caption) if message.caption else 'Describe the document'

        temp_message_id += 1

    if message.text:
        text = str(message.text)
    
    await message.reply('\n'.join(temp_message_text))


    messages = sql_select_history(id=user_id)
    messages.insert(0, {'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': text})
    
    for file in files:
        if not(file.endswith('.png') or file.endswith('.jpg') or file.endswith('.jpeg') or file.endswith('.webp')):
            messages[-1]['content'] += f'\n\n{file}:\n{files_to_text(file)}'
            files.remove(file)

    log(f'new message by {user}. messages: {text}, files: {files}')

    tools = llm_select_tool(messages=messages, files=files)
    temp_message_text[0] = temp_message_text[0][:-2] + '✅'
    await bot.edit_message_text(chat_id=chat_id, message_id=temp_message_id, text='\n'.join(temp_message_text))

    tool_result, images = await llm_use_tool(tools=tools)
    temp_message_text[1] = temp_message_text[1][:-2] + '✅'
    await bot.edit_message_text(chat_id=chat_id, message_id=temp_message_id, text='\n'.join(temp_message_text))

    
    
    sql_insert_message(user_id=user_id, role='user', content=text)

    if bool(tool_result) + bool(images):
        messages.append({'role': 'system', 'content': 'tool result:\n' + tool_result})
        sql_insert_message(user_id=user_id, role='system', content='tool result:\n' + tool_result)
        
    answer = llm_api(messages=messages, files=files, provider='google')
    await bot.delete_message(chat_id=chat_id, message_id=temp_message_id)
    log(f'answer to {user}({text}): {answer}')
    sql_insert_message(user_id=user_id, role='assistant', content=answer)


    # TODO: images don't send
    files += images
    images = images[:9]
    if images:
        media_group = []
        for image in images:
            caption = answer[:1000] if images is images[0] else None
            media = image if image.startswith('https:') else FSInputFile(image)
            media_group.append(InputMediaPhoto(media=media, caption=caption))
        try:
            await message.answer_media_group(media=media_group)
            answer = answer[:1000]
        except Exception as e:
            print('media group error', e)
        finally:
            for image in images:
                if not image.startswith('https:'):
                    os.remove(image)

    while answer:
        try:
            await message.answer(markdown_to_html(answer[:4000]), parse_mode='HTML')
        except Exception as e:
            print(e)
            await message.answer(answer[:4000])
        answer = answer[4000:]

    try:
        for file in files:
            if not file.startswith('https:'):
                os.remove(file.split('/')[-1])    
    except Exception as e:
        print(e)

    await state.clear()

@dp.message(StateFilter(FSM.processing))
async def message_processing(message: Message):
    await message.answer('Message is being processed. Wait. \nIf processing does not stop for a long time, write to the admin (@gvb3a)')
    


if __name__ == '__main__':
    log('Bot is launched')
    dp.run_polling(bot)
