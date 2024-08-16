import sqlite3

from colorama import Fore, Style, init
from datetime import datetime
from inspect import stack

from config import system_prompt

init()


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
        cursor.execute("INSERT INTO History (role, content, time) VALUES (?, ?, ?)", ('system', system_prompt, datetime.now().strftime('%Y.%m.%d %H:%M')))

    print(f'Database size: {len(row)}')

    connection.commit()
    connection.close()


def sql_select(n = 6):
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


sql_launch()
