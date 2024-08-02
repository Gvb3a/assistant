import sqlite3
import whisper

from colorama import Fore, Style, init
from datetime import datetime, timedelta, timezone
from vectordb import Memory
from os import getenv
from re import sub
from inspect import stack

from config import system_prompt, guiding_prompt, prompt_for_add, prompt_for_close_task
from api import calendar_get_events, calendar_add_event, todoist_get_tasks, todoist_new_task, todoist_close_task, llm_api

from pprint import pprint
init()

memory = Memory()


def print_colorama(text: str = None, color: str = 'green'):

    colors = {'green': Fore.GREEN, 'red': Fore.RED, 'yellow': Fore.YELLOW}
    
    func = stack()[1].function  # allows you to find out the name of the function from which this function is called

    color = colors.get(color, Fore.GREEN)  # get method if no key is found, returns Fore.GREEN

    print(f'{color}{func}{Style.RESET_ALL}: {str(text)}')



def llm_answer(user_message: str) -> str:

    sql_incert('user', user_message)  # save user_message to db

    nw = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    memory.save([user_message], {'role': 'user', 'time': nw})  # save user_message to vector db

    role, content, time = sql_select(n=6)

    messages = []
    for i in range(len(role)):
        messages.append({'role': role[i], 'content': content[i]})


    response_directions = [None, 'Memory', 'Calendar/Todoist for day', 'Calendar/Todoist for week', 'add event/task', 'close task']
    guiding_messages = [{"role": "system", "content": guiding_prompt},
                        {"role": "user", "content": user_message}]
    for _ in range(3):
        
        try:
            guiding_responce = llm_api(guiding_messages)
            response_direction = response_directions[int(guiding_responce)]
            break
        except:
            pass
    else:
        response_direction = None



    if response_direction is not None:

        if response_direction == 'Memory':
            memory_results = memory_search(user_message)
            system_message = f'Vector database search results (may be useless): {memory_results}'

        elif response_direction == 'Calendar/Todoist for day':
            system_message = f'Now {nw}. Today Events in Google Calendar: {calendar_get_events()}\nToday/no time tasks in Todoist: {todoist_get_tasks()}'

        elif response_direction == 'Calendar/Todoist for week':
            system_message = f'Now {nw}. This week\'s events in Google Calendar: {calendar_get_events(duration=7)}\nThis week/no time tasks in Todoist: {todoist_get_tasks()}'

        elif response_direction in ['add event/task', 'close task']:
            
            promt = prompt_for_add if response_direction == 'add event/task' else prompt_for_close_task
            system_messages = [{'role': 'system', 'content': promt},
                                {'role': 'user', 'content': user_message}]
            
            for _ in range(3):
                try:
                    system_message = eval(llm_api(system_messages))
                    break
                except Exception as e:
                    print_colorama(f'{response_direction}: {e}', color='red')
                    system_message = f'Error: {e}'
        
        messages.append({'role': 'system', 'content': system_message})
        sql_incert('system', system_message)

    else:
        system_message = None



    response = llm_api(messages=messages)
    
    print_colorama(f'response_direction: {response_direction}, system_message: {system_message}, response: {response}')
    sql_incert('assistant', response)
    memory.save([response], {'role': 'assistant', 'time': nw})

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
        description TEXT
        )
        ''')
    
    row = cursor.execute(f'SELECT * FROM History').fetchall()
    if row == []:
        cursor.execute("INSERT INTO History (role, content, time) VALUES (?, ?, ?)", ('system', system_prompt, datetime.now().strftime('%Y%m%d %H:%M:%S')))

    print_colorama(f'History size: {len(row)}')

    connection.commit()
    connection.close()


def sql_select(n=6):
    connection = sqlite3.connect('assistant.db') 
    cursor = connection.cursor()

    row = cursor.execute(f'SELECT * FROM History').fetchall()

    if n != '*':
        row = row[-n:]

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
    
    texts = [content[i] for i in range(len(content)) if role[i] != 'system']
    metadata = [{'role': role[i], 'time': time[i]} for i in range(len(content)) if role[i] != 'system']
    
    if metadata != []:
        memory.save(
        texts=texts,
        metadata=metadata
    )

    print_colorama(f'There are {len(metadata)} items in the vector database')


def memory_search(query: str, n:int = 2):
    result = memory.search(query, top_n = n)
    # f'{role} {time}: {chunk}'. time: YYYY-MM-DD HH:MM:SS
    pretty_result = [f'{i["metadata"]["role"]} {str(i["metadata"]["time"])[:10]}: {i["chunk"]}' for i in result]  

    print_colorama(pretty_result)

    return pretty_result


sql_launch()
memory_load()
