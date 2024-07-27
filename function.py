import sqlite3
import whisper


from dotenv import load_dotenv
from colorama import Fore, Style, init
from groq import Groq
from datetime import datetime
# from vectordb import Memory
from os import getenv

from config import LOCAL_WHISPER


init()
load_dotenv()


groq_api_key = getenv('GROQ_API_KEY')


# memory = Memory()
client = Groq(api_key=groq_api_key)



def ok(green_text: str, normal_text: str = '') -> str:
    return f'{Fore.GREEN}{green_text}{Style.RESET_ALL}{normal_text}'


def groq_answer(user_message: str) -> str:
    
    """
    guiding_promt = f\"""You're the chatbot's assistant. You have to choose a number from 0-5. 0 if the answer does not require any sources (just chatting). 
                        1 if the answer requires a memory search (vector database). 2 if the answer requires a Google calendar query. 
                        3 - If the answer requires a query in todolist (tasks). 4 - If an email query is required. 
                        The answer MUST consist ONLY of a digit. User message: {user_message}\"""
    
    guiding_response = client.chat.completions.create(
    messages=[{"role": "system", "content": guiding_promt}],
    model="llama-3.1-8b-instant")
    
    response_direction = [None, 'Memory', 'Calendar', 'Todoist', 'Email'][int(guiding_response.choices[0].message.content)]
    print('groq_answer: response_direction =', response_direction)
    """

    messages = sql_select()

    messages.append({'role': 'user', 'content': user_message})



    response = client.chat.completions.create(messages=messages, model="llama-3.1-70b-versatile").choices[0].message.content

    sql_incert('user', user_message)
    sql_incert('assistant', response)
    
    print(response)
    
    return response


def speech_recognition(file_name: str) -> str:

    if LOCAL_WHISPER:
        
        model = whisper.load_model('base') 
        result = model.transcribe(file_name)


        text = result['text']

    else:

        with open(file_name, "rb") as file:
            translation = client.audio.transcriptions.create(
            file=(file_name, file.read()),
            model="whisper-large-v3")
            
            text = translation.text

    print(ok(green_text='function: speech_recognition', normal_text=f'({text})'), LOCAL_WHISPER)

    return text



def sql_launch():
    connection = sqlite3.connect('assistant.db') 
    cursor = connection.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS History (
        role TEXT,
        content TEXT,
        time Text
        )
        ''')
    
    if cursor.execute(f'SELECT * FROM History').fetchall() == []:
        promt = 'You are a useful ai assistant with access to various services, but mostly play the role of a pleasant conversationalist. Your creator and the person you are communicating with is called Boris'
        cursor.execute("INSERT INTO History (role, content, time) VALUES (?, ?, ?)", ('system', promt, str(datetime.now())))

    connection.commit()
    connection.close()


def sql_select(n: int = 6):
    connection = sqlite3.connect('assistant.db') 
    cursor = connection.cursor()

    row = cursor.execute(f'SELECT * FROM History').fetchall()[-n:]

    messages = [{'role': i[0], 'content': i[1]} for i in row]

    connection.close()

    return messages


def sql_incert(role: str, content: str):
    connection = sqlite3.connect('assistant.db')
    cursor = connection.cursor()
    
    time = datetime.now()
    cursor.execute("INSERT INTO History (role, content, time) VALUES (?, ?, ?)", (str(role), str(content), str(time)))

    connection.commit()
    connection.close()


