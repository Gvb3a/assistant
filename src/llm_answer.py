from datetime import datetime
from typing import Literal
import asyncio

if __name__ == '__main__' or '.' not in __name__:
    from api import llm_api, calculator, wolfram_short_answer, wolfram_full_answer, google_short_answer, google_full_answer

else:
    from .api import llm_api, calculator, wolfram_short_answer, wolfram_full_answer, google_short_answer, google_full_answer


system_prompt = 'You are a helpful assistant with access to Wolfram Alpha, Google, and calucaltor. You are a Telegram bot (don\'t use LaTeX) providing the best answers.'


# TODO: let him decide for himself, not based on a machine solution.
functions_description = {
   'calculator': {
        'description': 'For simple calculations (use Python syntax, e.g., ^ as **, decimal point for fractional numbers)',
        'output_file': False
    },
    'wolfram_short_answer': {
        'description': 'For complex calculations, solving equations, or using specific WolframAlpha features (e.g., weather, exchange rates, today date, sometimes full-fledged tasks if you set the prompt well and etc). Use in most cases',
        'output_file': False
    },
    'wolfram_full_answer': {  # TODO: Improve prompt
        'description': 'Full Wolfram Alpha answer with pictures and step-by-step solutions. Can be used for complex and tabular data',
        'output_file': True
    },
    'google_short_answer': {
        'description': 'For general internet queries that require brief relevant information.',
        'output_file': False
    },
    'google_full_answer': {
        'description': 'For queries needing full-text information from the internet (e.g., entire lyrics or detailed articles).',
        'output_file': True
    }
}

prompt_for_chatbot_assistant = 'You are the chatbot\'s assistant, in charge of choosing the right tool for each request. Available functions:\n\n'

for items in functions_description.items():
    prompt_for_chatbot_assistant += f'{items[0]}: {items[1]["description"]}\n'

prompt_for_chatbot_assistant += f"""\nAnswer in the following format:

Thought: You should always think about what to do. What the user wants to see, what is the best tool to use and what inputs to use? Think only in English

<function_name>: <function_input>


You can call multiple functions (unless the model herself is unable to answer), each time spelling out the names of the function and the query for it. You can call the same function multiple times, so don't be afraid to split questions into the same function. Don't forget to convert the queries, and also avoid obscene queries in functions. Use tools only when they are needed. You should not call functions during a normal conversation (or if the model can answer itself)

You'll be given a message history."""

function_dict = {  # TODO: separate functions for files 
    'calculator': calculator,
    'wolfram_short_answer': wolfram_short_answer,
    'wolfram_full_answer': wolfram_full_answer,
    'google_short_answer': google_short_answer,
    'google_full_answer': google_full_answer
}



# TODO: files to context, auto-translate
def llm_select_tool(messages: list | str) -> list:

    if type(messages) == list:
        user_message = '\n'.join(f'{i["role"]}: {i["content"]}' for i in messages)
    else:
        user_message = messages

    message_history = [
        {'role': 'system',
         'content': prompt_for_chatbot_assistant},
        {
        'role': 'user',
        'content': user_message
        }
    ]

    llm_answer = llm_api(messages=message_history, provider='groq')
    answers = llm_answer.split('\n')
    tools = []
    for answer in answers:
        try:
            func_name, func_input = answer.split(':')
        except ValueError:
            continue
        
        func_name = func_name.strip().lower()
        if func_name in function_dict:
            tools.append({'func_name': func_name, 'func_input': func_input.strip()})

    print('llm_select_tool', user_message, tools)
    return tools



async def execute_tool(func_name: str, func_input: str):
    'Wrap a synchronous function into an asynchronous function'
    return await asyncio.to_thread(function_dict[func_name], func_input)


async def llm_use_tool(tools: list[dict]) -> tuple[str, list]:
    
    tasks = [
        execute_tool(tool['func_name'], tool['func_input'])
        for tool in tools
    ]
    
    results = await asyncio.gather(*tasks)

    str_results = []
    images = []
    for i, func_result in enumerate(results):
        if type(func_result) == str:
            str_results.append(f"{tools[i]['func_name']}({tools[i]['func_input']}): {func_result}")
        else:
            str_results.append(f"{tools[i]['func_name']}({tools[i]['func_input']}): {func_result[0]}")
            images.extend(func_result[1])

    print('llm_use_tool', ', '.join(str_results))
    
    return '\n'.join(str_results), images


# TODO: FILES
def llm_full_answer(messages: list, provider: Literal['groq', 'google'] = 'groq') -> str:

    tools = llm_select_tool(messages=messages)
    tool_result, images = asyncio.run(llm_use_tool(tools=tools))


    if type(messages) == str:
        user_message = messages
        messages = [{'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message}]
    else:
        messages.insert(0, {'role': 'system', 'content': system_prompt})

    if bool(tool_result) + bool(images):
        messages.append({'role': 'assistant', 'content': 'tool result:\n' + tool_result})
        

    return llm_api(messages=messages, provider=provider)