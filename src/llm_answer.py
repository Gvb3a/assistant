from datetime import datetime
from colorama import Fore, init, Style
import asyncio
from inspect import stack

if __name__ == '__main__' or '.' not in __name__:
    from api import (llm_api, calendar_add_event, calendar_get_events,
                     todoist_new_task, todoist_get_tasks, todoist_close_task, tavily_full_search, tavily_qsearch,
                     ask_wolfram_alpha, hugging_face_flux)
    from sql import sql_select_history, sql_incert_history
    from config import serivices, guiding_prompt, prompt_for_edit_calendar_todoist
else:
    from .api import (llm_api, calendar_add_event, calendar_get_events,
                      todoist_new_task, todoist_get_tasks, todoist_close_task, tavily_full_search, tavily_qsearch,
                      ask_wolfram_alpha, hugging_face_flux)
    from .sql import sql_select_history, sql_incert_history
    from .config import serivices, guiding_prompt, prompt_for_edit_calendar_todoist


init()


def print_colorama(text: str | None = None, color: str = 'green'):
    colors = {'green': Fore.GREEN, 'red': Fore.RED, 'yellow': Fore.YELLOW}
    
    func = stack()[1].function

    color = colors.get(color, Fore.GREEN)

    print(f'{color}{func}{Style.RESET_ALL}: {str(text)}')


def llm_regenerate(id: int, user_name: str) -> tuple[str, list]:
    
    # sql_delete_last()

    user_name, user_id, message_id, role, content, time, addition = sql_select_history(id=id, n=5)

    messages = []
    for i in range(len(role)):
        messages.append({'role': role[i], 'content': content[i]})

    answer = llm_api(messages=messages)
    sql_incert_history(user_name=user_name, id=id, role='assistant', content=answer)

    print_colorama(f'id: {id}, answer: {answer}')
    return answer, []


def llm_select_tool(user_message: str, id) -> tuple[str, str]:
    'The beginning of the response chain. Returns action (tool) and action input (for some tools)'
    user_name, user_id, message_id, role, content, time, addition = sql_select_history(id=id, n=2)
    
    message_history_str = ''
    for i in range(len(role)):
        message_history_str += f'{role[i]}: {content[i]}\n'
    message_history_str += f'user: {user_message}'
    message_history = [{
        'role': 'system',
        'content': guiding_prompt
    },
    {
        'role': 'user',
        'content': message_history_str
    }
    ]
    actions = serivices.keys()
    
    for _ in range(3):
        answer = llm_api(message_history)
        try:
            action_index = answer.index('Action:')+len('Action:')
            action = answer[action_index:answer.index('\n', action_index+1)].strip().lower()
            action_input_index = answer.index('Action Input:')+len('Action Input:')
            action_input = answer[action_input_index:].strip().lower()
            if action in actions:
                print_colorama(f'action: {action}, action input: {action_input}')
                return action, action_input
            print(action, action_input)
        except:
            pass
    
    print_colorama(text=f'Failed to get a response. user_message: {user_message}',color='red')
    return 'none', 'none'


async def llm_use_tool(user_message: str, action: str, action_input: str, id: int, user_name: str) -> tuple[str | None, list]:
    '''Using tools. Returns result and images'''
    result = None
    images = []

    nw = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    
    if action == 'none':
        return result, images

    if action == 'wolfram_alpha':
        result, images = await ask_wolfram_alpha(action_input)

    elif action == 'image_generate':
        result, image = await hugging_face_flux(prompt=action_input) # TODO: setting, limit and multiple generations
        images = [image] if image is not None else []

    elif action == 'tavily_answer':
        result, images = await tavily_qsearch(action_input)

    elif action == 'tavily_full_answer':
        result, images = await tavily_full_search(action_input)

    elif action == 'vector_db':
        result = 'Temporarily not available (tell the user that). The ability to work with documents will also be added soon'

    elif action == 'calendar_and_todoist':
        result = f'Now {nw}. Today Events in Google Calendar: {calendar_get_events(duration=3)}(you can only see events from today through the next three days)\nToday/no time tasks in Todoist: {todoist_get_tasks()}'
        

    elif action == 'edit_calendar_or_todoist':
        user_name, user_id, message_id, role, content, time, addition = sql_select_history(id=id, n=2)

        messages_str = ''
        for i in range(len(role)):
            messages_str += f'{role[i]}: {content[i]}\n'
        messages_str += f'user: {user_message}'
        messages = [{
            'role': 'system',
            'content': guiding_prompt
        },
        {
            'role': 'user',
            'content': messages_str
        }
        ]

        for _ in range(3):
            try:
                result = eval(llm_api(messages, fast_model=True))
                break
            except Exception as e:
                print_colorama(f'edit_calendar_or_todoist: {e}')
                result = f'Error: {e}'

    elif action  == 'regenerate':
        result, images = llm_regenerate(id=id, user_name=user_name)


    result = f'{action}: {result}'
    if images:
        result += f'\nPictures will be attached to your response'

        if action == 'wolfram_alpha':
            result += '(Wolfram Alpha answer page and step by step solutions if available)'
        elif 'tavily' in action:
            result += '(thematic pictures)'

    return result, images


def llm_answer(user_message: str, user_name: str, id: int, system_message: str | None = None) -> str:
    
    sql_incert_history(user_name=user_name, id=id, role='user', content=user_message)

    if system_message:
        sql_incert_history(user_name=user_name, id=id, role='system', content=system_message)

    sql_user_name, user_id, message_id, role, content, time, addition = sql_select_history(id=id, n=4)

    messages = []
    for i in range(len(role)):
        messages.append({'role': role[i], 'content': content[i]})
    
    if str(system_message).startswith('image_generate: Image successfully generated'):
        final_response = '\n'.join(str(system_message).split('\n')[1:-1])
    else:
        final_response = llm_api(messages=messages)

    print_colorama(final_response)

    sql_incert_history(user_name=user_name, id=id, role='assistant', content=final_response)
    return final_response


async def llm_full_answer(user_message: str, id: int, user_name: str) -> tuple[str, list]:
    '''The function collects llm_select_tool, llm_use_tool, llm_answer'''

    action, action_input = llm_select_tool(user_message=user_message, id=id)

    system_message, images = await llm_use_tool(user_message=user_message, action=action, action_input=action_input, id=id, user_name=user_name)

    result = llm_answer(user_message=user_message, user_name=user_name, id=id, system_message=system_message)
    
    return result, images




def langchain_answer(text):
    # langchain-community langgraph langchain-anthropic langgraph-checkpoint-sqlite langchain_groq wikipedia wolframalpha tavily-python nest-asyncio
    import nest_asyncio  # for wolfram alpha
    nest_asyncio.apply()

    import os
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

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
