from datetime import datetime
from colorama import Fore, init, Style
import asyncio

from api import (llm_api, vector_datebase_incert, vector_datebase_search, calendar_add_event, calendar_get_events, 
                 todoist_new_task, todoist_get_tasks, todoist_close_task, tavily_full_search, tavily_qsearch,
                 ask_wolfram_alpha)
from sql import sql_select, sql_incert, sql_delete_last
from config import guiding_prompt, prompt_for_close_task, prompt_for_add, prompt_for_transform_query_wolfram, prompt_for_transform_query_tavily


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


async def llm_answer(user_message: str) -> tuple[str, list]:
    '''The basic command for llm. This is where the check (what to use), the associated calculation (e.g. wolfram alpha) and the answer itself take place. 
    
    I had to make it asynchronous because of ask_wolfram_alpha, which is asynchronous.'''

    sql_incert('user', user_message)  # save user_message to db

    nw = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    vector_datebase_incert(role='user', content=user_message)  # save user_message to vector db

    role, content, time = sql_select(n=6)

    messages = []
    for i in range(len(role)):
        messages.append({'role': role[i], 'content': content[i]})
    images = []  # internet search and wolfram alpha returns pictures


    response_directions = [None, 'Memory', 'Calendar/Todoist for day', 'Calendar/Todoist for week', 'add event/task', 
                           'close task', 'quick search internet', 'deep search internet', 'wolfram alpha', 'regenerate']
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
        long_system_message = False  # If the system message is very large, I will remove three messages to simplify the llm
        # query transformation. For example wolfram alpha will not understand Use wolfram alpha and solve 3x-1=11, so we make llm transform the query
        start = datetime.now()
        if response_direction in ['wolfram alpha', 'quick search internet', 'deep search internet']:
            
            if response_direction == 'wolfram alpha':
                transformed_promt = prompt_for_transform_query_wolfram
            else:
                transformed_promt = prompt_for_transform_query_tavily

            transformed_messages = [{
                'role': 'system',
                'content': transformed_promt
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
            
            answer, images = await tavily_qsearch(text=transformed_query)

            system_message = f'Internet search short results: {answer}\nThe images (wolfram alpha and step by step answer page) will be attached to your reply. The answer should be no more than 1000 characters'

        elif response_direction  == 'deep search internet':

            long_system_message = True
            
            answer, images = await tavily_full_search(text=transformed_query)

            system_message = f'Internet search raw content: {answer}'

        elif response_direction  == 'wolfram alpha':
            
            long_system_message = True

            wolfram_answer, step_by_step, images = await ask_wolfram_alpha(transformed_query)
            system_message = f'''Wolfram alpha short answer: {wolfram_answer}. 
                \nStep by step solutions (may be useless): {step_by_step}. 
                \nWolframAlpha answer images will be attached to your response.  
                The answer should be no more than 1000 characters'''

        elif response_direction  == 'regenerate':
            sql_delete_last()
            response, images = llm_regenerate()
            print(f'{Fore.GREEN}llm_answer{Style.RESET_ALL}(regenarate): {str(response)}')
            return response, images

        print(datetime.now()-start)
        messages.append({'role': 'system', 'content': system_message})
        sql_incert('system', system_message)

        if long_system_message:
            messages = messages[3:]

    else:
        system_message = None



    response = llm_api(messages=messages)
    
    print(f'{Fore.GREEN}llm_answer{Style.RESET_ALL}. response_direction: {response_direction}, system_message: {system_message}, response: {response}')
    sql_incert('assistant', response)

    return response, images


def langchain_answer(text):
    # langchain-community langgraph langchain-anthropic langgraph-checkpoint-sqlite langchain_groq wikipedia wolframalpha tavily-python nest-asyncio
    import nest_asyncio  # for wolfram alpha
    nest_asyncio.apply()

    import os
    from dotenv import load_dotenv

    load_dotenv()

    os.environ["GROQ_API_KEY"] = os.getenv('GROQ_API_KEY')
    os.environ["TAVILY_API_KEY"] = os.getenv('TAVILY_API_KEY')
    os.environ["WOLFRAM_ALPHA_APPID"] = os.getenv('WOLFRAM_SIMPLE_API_KEY')
    # os.environ["LANGSMITH_API_KEY"] = 'LANGSMITH_API_KEY'
    # os.environ["LANGSMITH_TRACING"] = 'true'

    from langchain.agents import load_tools
    from langchain.agents import initialize_agent

    from langchain_groq import ChatGroq
    llm = ChatGroq(model="llama-3.1-70b-versatile")

    from langchain_community.tools import TavilySearchResults, TavilyAnswer
    from langchain_community.utilities.wolfram_alpha import WolframAlphaAPIWrapper

    tavily_search_results = TavilySearchResults(include_raw_content=True)
    tavily_answer = TavilyAnswer()

    tools = load_tools(['wikipedia', 'wolfram-alpha'], llm=llm) + [tavily_search_results, tavily_answer]

    agent = initialize_agent(llm=llm, tools=tools, verbose=True)

    result = agent.run(text)

    return result
