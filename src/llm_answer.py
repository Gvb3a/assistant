from datetime import datetime
from colorama import Fore, init, Style

from api import (llm_api, vector_datebase_incert, vector_datebase_search, calendar_add_event, calendar_get_events, 
                 todoist_new_task, todoist_get_tasks, todoist_close_task, tavily_full_search, tavily_qsearch,
                 wolfram_quick_answer)
from sql import sql_select, sql_incert, sql_delete_last
from config import guiding_prompt, prompt_for_close_task, prompt_for_add, prompt_for_transform_query

init()

def llm_regenerate() -> tuple[str, list]:
    
    sql_delete_last()

    role, content, time = sql_select(n=5)

    messages = []
    for i in range(len(role)):
        messages.append({'role': role[i], 'content': content[i]})

    answer = llm_api(messages=messages)
    print('llm regeretare answer', answer)
    sql_incert('assistant', answer)

    return answer, []


def llm_answer(user_message: str) -> tuple[str, list]:

    sql_incert('user', user_message)  # save user_message to db

    nw = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    vector_datebase_incert(role='user', content=user_message)  # save user_message to vector db

    role, content, time = sql_select(n=6)

    messages = []
    for i in range(len(role)):
        messages.append({'role': role[i], 'content': content[i]})
    images = []  # internet search and wolfram alpha returns pictures


    response_directions = [None, 'Memory', 'Calendar/Todoist for day', 'Calendar/Todoist for week', 'add event/task', 
                           'close task', 'quick search internet', 'deep search internet', 'quick wolfram alpha answer', 'full wolfram alpha answer', 
                           'regenerate']
    guiding_messages = [{"role": "system", "content": guiding_prompt},
                        {"role": "user", "content": user_message}]  # TODO: full history
    for _ in range(3):
        
        try:
            guiding_responce = llm_api(guiding_messages)
            response_direction = response_directions[int(guiding_responce)] # type: ignore
            break
        except:
            pass
    else:
        response_direction = None

    print(f'llm_answer. responce direction: {response_direction}')

    if response_direction is not None:
        
        # query transformation. For example wolfram alpha will not understand Use wolfram alpha and solve 3x-1=11, so we make llm transform the query
        if response_direction in ['quick wolfram alpha answer', 'full wolfram alpha answer']:
            transformed_messages = [{
                'role': 'system',
                'content': prompt_for_transform_query
            },
            {
                'role': 'user',
                'content': user_message
            }]
            transformed_query = llm_api(messages=transformed_messages)
            print(f'llm_answer. transformed_query={transformed_query}')



        if response_direction == 'Memory':
            memory_results = vector_datebase_search(user_message)
            system_message = f'Vector database search results (may be useless): {memory_results}'

        elif response_direction == 'Calendar/Todoist for day':
            system_message = f'Now {nw}. Today Events in Google Calendar: {calendar_get_events()}\nToday/no time tasks in Todoist: {todoist_get_tasks()}'

        elif response_direction == 'Calendar/Todoist for week':
            system_message = f'Now {nw}. This week\'s events in Google Calendar: {calendar_get_events(duration=7)}\nThis week/no time tasks in Todoist: {todoist_get_tasks()}'

        elif response_direction in ['add event/task', 'close task']:
            
            promt = prompt_for_add if response_direction == 'add event/task' else prompt_for_close_task
            messages_promt = [{'role': 'system', 'content': promt},
                                {'role': 'user', 'content': user_message}]
            
            for _ in range(3):
                try:
                    system_message = eval(llm_api(messages_promt))
                    break
                except Exception as e:
                    print(f'{Fore.RED}llm_answer{Style.RESET_ALL}. {response_direction}: {e}')
                    system_message = f'Error: {e}'
        
        elif response_direction  == 'quick search internet':
            
            answer, images = tavily_qsearch(text=user_message)

            system_message = f'Internet search short results: {answer}. The images will be attached to your reply. The answer should be no more than 1000 characters'

        elif response_direction  == 'deep search internet':
            
            answer = tavily_full_search(text=user_message)

            system_message = f'Internet search raw content: {answer}'

        elif response_direction  == 'quick wolfram alpha answer':
            
            wolfram_answer = wolfram_quick_answer(transformed_query)
            system_message = f'Wolfram alpha answer: {wolfram_answer}'

        elif response_direction  == 'full wolfram alpha answer':
            
            wolfram_answer = wolfram_quick_answer(transformed_query)
            system_message = f'Access to full wolfram alpha answer has not been made yet. So tell the user. Quick answer {wolfram_answer}'

        elif response_direction  == 'regenerate':
            sql_delete_last()
            response, images = llm_regenerate()
            print(f'{Fore.GREEN}llm_answer{Style.RESET_ALL}(regenarate): {str(response)}')
            return response, images

            
        messages.append({'role': 'system', 'content': system_message})
        sql_incert('system', system_message)

    else:
        system_message = None



    response = llm_api(messages=messages)
    
    print(f'{Fore.GREEN}llm_answer{Style.RESET_ALL}. response_direction: {response_direction}, system_message: {system_message}, response: {response}')
    sql_incert('assistant', response)

    return response, images