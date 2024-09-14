global_settings = {
   'local_llm': 0,
   'local_whisper': 0,
   'local_whisper_model': 'base',
   'llm_model': 'llama-3.1-70b-versatile',
   'fast_llm_model': 'llama-3.1-8b-instant',
   'local_llm_model': 'llama3.1',
   'fast_local_llm_model': 'phi3'
}

system_prompt = """You are a helpful assistant with access to various services (WolframAlpha, tavily, todoist and more). Access to services is provided in the following way: after the user's request, if needed from the system, there will be a message. Provide this information only when it is relevant to the conversation. Always prioritise honesty and transparency in yous. """



serivices = {
   'none': {
       'description': 'If the query does not require any external services (just chatting or when the model itself can answer the query). ',
       'need_transform_query': False
   },
   'wolfram_alpha': {
       'description': 'If the answer requires a wolfram alpha (calculate something, show solution, use wolfram etc).',
       'need_transform_query': True
   },
   'image_generate': {
       'description': 'If the user needs to generate a image. In Action Input there is a prompt. Model FLUX.1 dev is used',
       'need_transform_query': True
   },
   'vector_db': {
       'description': 'If the query requires accessing personal information stored in a vector database.',
       'need_transform_query': False
   },
   'tavily_answer': {
       'description': 'If the response requires Internet access.',
       'need_transform_query': True
   },
   'tavily_full_answer': {
       'description': 'If the answer require full text from the Internet (for example, the entire lyrics of a song or is it better to give the bot all the information).',
       'need_transform_query': True
   },
   'regenerate': {
       'description': 'User asks to regenerate message.',
       'need_transform_query': False
   }
}
guiding_prompt_start = 'You are the chatbot\'s assistant. You have to choose the tool that the chatbot will use. Tools:\n\n'

guiding_prompt_tools = ''

for items in serivices.items():
    guiding_prompt_tools += f'{items[0]} - {items[1]["description"]}\n'

action_input_example = 'For example, Wolfram Alpha will not understand Hi, help me with a solution ... or a query in a non-English language. For image_generate, you can remove the command (Generate image ...) or if the user asks to write the prompt themselves. And for tavily, it helps to give more relevant answers.  You can also censor content and avoid obscene requests. '
guiding_prompt_end = f"""\nAnswer in the following format:

Thought: you should always think about what to do
Action: the action to take, should be one of {', '.join([i for i in serivices.keys()])}
Action Input: if you need to convert the request for an action ({', '.join([item[0] for item in serivices.items() if item[1]['need_transform_query']])}). {action_input_example}If the action does not require Action Input, write None. 

You'll be given a message history"""

guiding_prompt = guiding_prompt_start + guiding_prompt_tools + guiding_prompt_end



prompt_for_edit_calendar_todoist = """Based on the user's request and the instructions, you will have to call the function and substitute the values. Output only the function without any quotation marks (as in the examples)

calendar_add_event(summary: str, start: datetime, duration_in_hours: int = 24) - add a new event to Google calendar.
To add an event for the whole day, you need to specify the name, duration_in_hours multiple of 24 (24, 48, etc) and start as datetime({year}, {month}, {day}, 0, 0).
To add an event for a specific time, you need to specify the name, start as datetime({year}, {month}, {day}, {hour}, {minutes}) and duduration_in_hours (can be a fractional number).

todoist_new_task(content: str, due_string: str = None) - adds a new task to Todoist.
Mandatory content (task name). due_string (optional) - time of task execution. Passed in simple form, for example: tommorow, today at 16:00, every Monday, 18:30, next week, 3 Aug).

todoist_close_task(task_id) - marks the task as completed in Todoist. You will be given a list of all the id's

Examples:

1. User: Add new event Birthday (now 2024-08-02 10:19)
   You: calendar_add_event('Birthday', datetime(2024, 8, 2), 24)

2. User: Add a book to read tomorrow from 18:00 to 19:30 (now 2024-08-02 10:19)
   You: calendar_add_event('Read a book', datetime(2024, 8, 3, 3, 18, 0), 1.5)

4. User: Add task for tomorrow to change the aquarium for tonight (now 2024-08-11 16:14)
   You: todoist_new_task('Change aquarium', 'tommorow evening')

5. User: Add reminder: go to the gym (now 2024-08-11 16:14)
   You: todoist_new_task('Go to the gym', 'today')

6. User: For the 18th of July, make a note that I have to call my dad. (now 2024-06-11 16:14)
   You: todoist_new_task('Call my dad', '18 jule')

7. User: Add global task: parse notes (now 2024-08-11 16:14)
   You: todoist_new_task('Parse notes')

8. User: Mark the task Go to the gym as completed (['Go to the gym, date: 1 Aug, id: 8354485533', 'Unclutter the wardrobe, date: 2 Aug, id: 8257183536']).
   You: todoist_close_task(8354485533)

9. User: Mark brushing teeth for today as done (['Go to gym, date: None, id: 8257183536', 'Brush teeth, date: every day, id: 8259445526']))
   You: todoist_close_task(8259445526)

Now, respond to the query by following the rules
"""


prompt_for_transform_query_wolfram = """You have to turn a user query into a query that wolfram alpha will understand (If the enquiry is normal, leave it that way).

Examples:

1. User: Use wolfram alpha and solve this equation 3x-1=11
   You: 3x-1=11

2. User: Solve 3x^2-7x+4=0
   You: Solve 3x^2-7x+4=0

3. User: {sqrt2}}^{sqrt{2}
   You: sqrt[2]^sqrt[2]

4. User: Slve 2x^2=16
   You: Solve 2x^2=16

5. User: Help me and do the math (567^34)/435-6758
   You: (567^34)/435-6758

6. User: Sum of roots 8x^3-4x^2+11x-36=0
   You: Sum of roots 8x^3-4x^2+11x-36=0

7. User: Use wolfram alpha to find the population of France
   You: France population


Also wolfram alpha only accepts the English language

8. User: x в кубе равно 8
   You: x^3=8

9. User: 14x meno 5 uguale 0
   You: 14x-5=0

10. User: Calculer 456^45
   You: Calculate 456^45


Now, respond to the query by following the rules
"""
