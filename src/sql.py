import sqlite3
from datetime import datetime

from config import db_defult_settings, system_prompt


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
        CREATE TABLE IF NOT EXISTS Settings (
        name TEXT,
        value INT
        )
        ''')
    
    history_row = cursor.execute(f'SELECT * FROM History').fetchall()
    if history_row == []:
        cursor.execute("INSERT INTO History (role, content, time) VALUES (?, ?, ?)", ('system', system_prompt, datetime.now().strftime('%Y.%m.%d %H:%M')))

    setting_row = cursor.execute(f'SELECT * FROM Settings').fetchall()
    if setting_row == []:
        print('Update Settings to db_defult_settings')
        for setting in db_defult_settings:
            cursor.execute("INSERT INTO Settings (name, value) VALUES (?, ?)", (setting['name'], setting['value']))

    print(f'Database size: {len(history_row)}')

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


def sql_setting_get(name: str) -> int:
    connection = sqlite3.connect('assistant.db')
    cursor = connection.cursor()
    
    result = cursor.execute(f"SELECT value FROM Settings WHERE name = '{name}'").fetchall()[0][0]

    connection.commit()
    connection.close()

    return result


def sql_setting_update(name: str, new_value: int) -> None:
    connection = sqlite3.connect('assistant.db')
    cursor = connection.cursor()
    
    cursor.execute("UPDATE Settings SET value = ? WHERE name = ?", (new_value, name))

    connection.commit()
    connection.close()


sql_launch()