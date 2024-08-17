from datetime import datetime
from colorama import Fore, init, Style

from api import llm_api, vector_datebase_incert, vector_datebase_search, calendar_add_event, calendar_get_events, todoist_new_task, todoist_get_tasks, todoist_close_task
from sql import sql_select, sql_incert
from config import guiding_prompt, prompt_for_close_task, prompt_for_add

def print_colorama(text: str = None, color: str = 'green'): # type: ignore
    
    colors = {'green': Fore.GREEN, 'red': Fore.RED, 'yellow': Fore.YELLOW}
    
    color = colors.get(color, Fore.GREEN)

    print(f'{color}llm_answer{Style.RESET_ALL}: {str(text)}')


def llm_answer(user_message: str) -> str:

    sql_incert('user', user_message)  # save user_message to db

    nw = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    vector_datebase_incert(role='user', content=user_message)  # save user_message to vector db

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
            response_direction = response_directions[int(guiding_responce)] # type: ignore
            break
        except:
            pass
    else:
        response_direction = None



    if response_direction is not None:

        if response_direction == 'Memory':
            memory_results = vector_datebase_search(user_message)
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

    return response