import sqlite3
from typing import Literal
from datetime import datetime, timezone
from log import log

def utc_time():
    # Get the current time in UTC + 0
    time = datetime.now(timezone.utc)
    return time.strftime('%Y.%m.%d %H:%M:%S')

def sql_launch():
    connection = sqlite3.connect('assistant.db') 
    cursor = connection.cursor()
    
    # is used to store user and LLM messages to provide context for responses.
    # TODO: files
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Messages (
        user_name TEXT,
        user_id INT,
        role TEXT,
        content TEXT,
        time TEXT
        )
        ''')

    # TODO: individual settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
        telegram_name TEXT,
        telegram_username TEXT,
        user_id INTEGER PRIMARY KEY,
        number_of_messages INT,
        first_message TEXT,
        last_message TEXT
        )
        ''')
    
    # TODO: settings

    connection.commit()
    connection.close()


def sql_check_user(telegram_name: str, telegram_username: str, user_id: int):
    connection = sqlite3.connect('assistant.db')
    cursor = connection.cursor()
    
    user = cursor.execute('SELECT * FROM Users WHERE user_id = ?', (user_id, )).fetchone()
    if user is None:
        log(f'new user {telegram_name} {telegram_username} {user_id}')
        time = utc_time()
        cursor.execute('INSERT INTO Users (telegram_name, telegram_username, user_id, number_of_messages, first_message, last_message) VALUES (?, ?, ?, ?, ?, ?)', (telegram_name, telegram_username, user_id, 1, time, time))

    else:
        cursor.execute('UPDATE Users SET number_of_messages = number_of_messages + 1, last_message = ? WHERE user_id = ?', (utc_time(), user_id))

    connection.commit()
    connection.close()


def sql_select_history(id: int, n: int | str = 5):
    ''
    connection = sqlite3.connect('assistant.db') 
    cursor = connection.cursor()

    role_content = cursor.execute('SELECT role, content FROM Messages WHERE user_id = ? ORDER BY time DESC LIMIT ?', (id, n)).fetchall()[::-1]   
    connection.close()
    
    return [{'role': i[0], 'content': i[1]} for i in role_content]


# TODO: clear context
def sql_insert_message(user_id: int, role: Literal['user', 'assistant', 'system'], content: str):
    connection = sqlite3.connect('assistant.db') 
    cursor = connection.cursor()

    user_name = cursor.execute('SELECT telegram_name FROM Users WHERE user_id = ?', (user_id,)).fetchone()[0]

    cursor.execute('INSERT INTO Messages (user_name, user_id, role, content, time) VALUES (?, ?, ?, ?, ?)', (user_name, user_id, role, content, utc_time()))

    connection.commit()
    connection.close()


sql_launch()