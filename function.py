import sqlite3
import whisper

from colorama import Fore, Style, init
from datetime import datetime, timedelta, timezone
from vectordb import Memory
from os import getenv
from re import sub

from config import LOCAL_WHISPER, system_promt, guiding_promt
from api import get_events, llm_api

from pprint import pprint
init()

memory = Memory()


def print_green(green_text: str, normal_text: str = ''):
    print(f'{Fore.GREEN}{green_text}{Style.RESET_ALL}{normal_text}')


def print_red(red_text: str, normal_text: str = '') -> str:
    print(f'{Fore.RED}{red_text}{Style.RESET_ALL}{normal_text}')


def llm_guiding_answer(user_message: str):

    promt = guiding_promt + user_message

    role, content, time = sql_select(n=3)
    messages = []

    for i in range(len(role)):
        messages.append({'role': role[i], 'content': content[i]})
    messages.append({"role": "system", "content": promt})
    messages.append({"role": "user", "content": user_message})
    
    print('llm_guiding: ', end='')
    pprint(messages)
    for _ in range(3):
        try:
            response = llm_api(messages=messages, fast_model=True)
            response = [None, 'Memory', 'Calendar', 'Todoist', 'Email'][int(response)]
            print_green(green_text='function: llm_guiding_answer. ', normal_text=response)
            return response
        
        except Exception as e:
            print_red(red_text=f'function: llm_guiding_answer. Error: {e}')

    return None

def llm_answer(user_message: str) -> str:

    guiding_responce = llm_guiding_answer(user_message)  # by promt returns a number between 1 and 5
    response_direction = guiding_responce

    memory.save([user_message], {'role': 'user', 'time': datetime.now()})

    if response_direction == 'Memory':
        memory_results = memory_search(user_message)
        user_message += f'\n\n((system: Vector database search results (may be useless): {memory_results}))'

    elif response_direction == 'Calendar':
        user_message += f'\n\n((system: Google calendar timetable for day (it\'s {datetime.now()}): {get_events()}))'


    sql_incert('user', user_message)


    role, content, time = sql_select(n=6)

    messages = [{'role': 'system', 'content': system_promt}]
    for i in range(len(role)):
        messages.append({'role': role[i], 'content': content[i]})
    
    pprint(messages)
    response = llm_api(messages=messages)

    sql_incert('assistant', response)
    
    print_green('function: llm_answer')
    
    return response


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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Setting (
        variable TEXT,
        value TEXT,
        description Text
        )
        ''')

    connection.commit()
    connection.close()


def sql_select(n=6):
    connection = sqlite3.connect('assistant.db') 
    cursor = connection.cursor()

    row = cursor.execute(f'SELECT * FROM History').fetchall()

    if n == '*':
        row = cursor.execute(f'SELECT * FROM History').fetchall()
    else:
        row = cursor.execute(f'SELECT * FROM History ORDER BY time LIMIT {n}').fetchall()

    role, content, time = [], [], []

    for rows in row:
        role.append(rows[0])
        content.append(rows[1])
        time.append(rows[2])


    connection.close()

    return role, content, time


def sql_incert(role: str, content: str):
    connection = sqlite3.connect('assistant.db')
    cursor = connection.cursor()
    
    time = datetime.now()
    cursor.execute("INSERT INTO History (role, content, time) VALUES (?, ?, ?)", (str(role), str(content), str(time)))

    connection.commit()
    connection.close()


def memory_load():

    role, content, time = sql_select(n='*')

    if role == []:
        return
    
    metadata = [{'role': i_role, 'time': i_time} for i_role, i_time in zip(role, time)]

    # re.sub(r'\{{\{.*?\}}\}}', '', text) - removes all text between ((system: and )) 
    content = [sub(r'\(\(system: .*?\)\)', '', i) for i in content]

    memory.save(
        texts=content,
        metadata=metadata
    )

    print_green('function: memory_load')


def memory_search(query: str, n:int = 2):
    result = memory.search(query, top_n = n)
    # f'{role} {time}: {chunk}'. time: YYYY-MM-DD HH:MM:SS
    pretty_result = [f'{i["metadata"]["role"]} {i["metadata"]["time"][:10]}: {i["chunk"]}' for i in result]  
    print_green('function: memory_search. ', pretty_result)

    return pretty_result


sql_launch()
memory_load()
