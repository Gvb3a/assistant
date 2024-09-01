import sqlite3
from datetime import datetime
from typing import Literal
from colorama import Fore, Style, init

from online_config import global_settings, system_prompt
'''
from .online_config import global_settings, system_prompt
'''

init()

def sql_launch():
    connection = sqlite3.connect('assistant.db') 
    cursor = connection.cursor()
    
    # is used to store user and LLM messages to provide context for responses.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Messages (
        user_name TEXT,
        user_id INT,
        message_id INT,
        role TEXT,
        content TEXT,
        time TEXT,
        addition TEXT 
        )
        ''')
    # user_name - user name in Telegram. It is not very convenient to look by id. user_id - individual for each telegram user id
    # message_id will make it easier to control the history. Each user will have a message_id starting from 0 and increasing.
    # role content time is used by LLMs
    # addition. For example, what technology the user is using (langchain or standard).

    # Users information. The llm will contain the current configuration. For example, whether the user uses the standard model (llm_answer), or any of the langchain models.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
        user_name TEXT,
        telegram_username TEXT,
        user_id INTEGER PRIMARY KEY,
        llm TEXT,
        number_of_messages INT,
        first_message TEXT,
        last_message TEXT
        )
        ''')
    
    # Global setting
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS Settings (
        local_llm INT,
        local_whisper INT,
        local_whisper_model TEXT,
        llm_model TEXT,
        fast_llm_model TEXT,
        local_llm_model TEXT,
        fast_local_llm_model TEXT
        )
        ''')
    
    setting_table = cursor.execute('SELECT * FROM Settings').fetchall()
    if setting_table == []:
        cursor.execute('INSERT INTO Settings (local_llm, local_whisper, local_whisper_model, llm_model, fast_llm_model, local_llm_model, fast_local_llm_model) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (global_settings['local_llm'], global_settings['local_whisper'], global_settings['local_whisper_model'], global_settings['llm_model'], 
                        global_settings['fast_llm_model'], global_settings['local_llm_model'], global_settings['fast_local_llm_model']))

    print(f'{Fore.GREEN}sql_launch{Style.RESET_ALL}')

    connection.commit()
    connection.close()


def sql_select_history(id: int, n: int | str = 5):
    '''Returns user_name, user_id, message_id, role, content, time, addition. Requires id. n - number of messages is optional and by default n = 6, but if you specify *, the entire history will be retrieved'''
    connection = sqlite3.connect('assistant.db') 
    cursor = connection.cursor()

    row = cursor.execute(f'SELECT * FROM Messages WHERE user_id = "{id}"').fetchall()
    
    if row == []:
        row = [['None', id, 0, 'system', system_prompt, datetime.now().strftime("%Y.%m.%d %H:%M:%S"), 'Standart']]
        
    if n != '*':
        row = row[-n:]

    connection.close()
    
    user_name, user_id, message_id, role, content, time, addition = map(list, zip(*row))

    return user_name, user_id, message_id, role, content, time, addition


def sql_select(var, table: Literal['Messages', 'Users', 'Settings'], where_var = None, where_value = None) -> list:
    '''SELECT var FROM table WHERE where_var = where_value. Where_var and where_value are not necessary'''
    connection = sqlite3.connect('assistant.db')
    cursor = connection.cursor()
    
    if where_var is None:
        row = cursor.execute(f'SELECT {var} FROM {table}').fetchall()
    else:
        row = cursor.execute('SELECT ? FROM ? WHERE ? = ?', (var, table, where_var, where_value)).fetchall()

    connection.close()

    return row


def sql_incert_history(user_name: str, id: int, role: str, content: str, addition: str = 'Standart') -> None:
    connection = sqlite3.connect('assistant.db')
    cursor = connection.cursor()

    sql_user_name, sql_user_id, message_id, sql_role, sql_content, time, addition = sql_select_history(id=id, n=1)
    values = (str(user_name), id, message_id[-1]+1, role, content, datetime.now().strftime("%Y.%m.%d %H:%M:%S"), 'Standart')
    
    cursor.execute("INSERT INTO Messages (user_name, user_id, message_id, role, content, time, addition) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                   values)

    connection.commit()
    connection.close()



def sql_incert(table: Literal['Messages', 'Users', 'Settings'], variables: tuple, values: tuple) -> None:
    '''INSERT INTO table variables VALUES values'''
    connection = sqlite3.connect('assistant.db')
    cursor = connection.cursor()
    
    cursor.execute("INSERT INTO ? ? VALUES ?", (table, variables, values))

    connection.commit()
    connection.close()


def sql_update(table: Literal['Messages', 'Users', 'Settings'], variable: str, values, where_var = None, where_value = None) -> None:
    '''UPDATE ? SET ? = ? WHERE ? = ?'''
    connection = sqlite3.connect('assistant.db')
    cursor = connection.cursor()
    
    if where_var is None:
        cursor.execute("UPDATE ? SET ? = ?", (table, variable, values))
    else:
        cursor.execute("UPDATE ? SET ? = ? WHERE ? = ?", (table, variable, values, where_var, where_value))

    connection.commit()
    connection.close()


def sql_delete(table: Literal['Messages', 'Users', 'Settings'], where_var, where_value) -> None:
    '''DELETE FROM table WHERE where_var = where_value'''
    connection = sqlite3.connect('assistant.db')
    cursor = connection.cursor()

    cursor.execute("DELETE FROM ? WHERE ? = ?", (table, where_var, where_value))  # TODO: add mult

    connection.commit()
    connection.close()


sql_launch()