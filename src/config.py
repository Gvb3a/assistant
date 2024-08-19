
# When creating the database, the values will be taken from here. This is done to make it convenient to change values
db_defult_settings = [  
   {'name': 'number of gmail accounts', 'value': 3},
   {'name': 'local whisper', 'value': 0}, # If 1, whisper(speech recognition) is used locally, otherwise(0) via the Groq API.
   {'name': 'local llm', 'value': 0},  # 0 - groqcloud, 1 - ollama
   {'name': 'local tts', 'value': 0},  # 0 - elevenlabs, 1 - https://github.com/coqui-ai/TTS 
   {'name': 'tts enabled', 'value': 1} 
]  # TODO: vector db. Problem with circular import when changing a value


system_prompt = """You are a helpful assistant with access to various services (google calendar, todoist), but mostly you just chat in Telegram. You communicate with Boris, the developer who created you.  Access to services is provided in the following way: after the user's request, if needed from the system, there will be a message. Provide this information only when it is relevant to the conversation. Always prioritise honesty and transparency in yous."""
n = 10
guiding_prompt = f"""You are the chatbot's assistant. Your task is to write a number between 0 and {n} based on the following conditions:

0 - If the query is for casual conversation (just chatting. Will mostly ask other items directly). Examples: How's it going; Remember, my favourite book is Lord of the Rings; The internet is so cool
1 - If the answer requires accessing a vector database (when the user asks some fact about himself). Examples: What's my favourite book
2 - If the chatbot requires Google calendar and/or Todoist for this day (or no time) to respond. Examples: What I've got today; What I need to do
3 - If the chatbot requires Google calendar and/or Todoist for the next week/tomorrow to respond. Examples: What's my plan for this week; What about tomorrow?
4 - If the request means that ChatBot will add an event/task to Google Calendar/Todois. Examples: Add a new event for today from 12:00 to 13:30; Add a new task(reminder): change the aquarium at 6:00 p.m.
5 - If the request means that ChatBot marks the task complete. Examples: Mark the task completed Go to the gym.
6 - If the answer require internet access to reply. ChatBot will receive a short reply with up-to-date information. Examples: What is the current status of Elon Mask, Find the pictures of Tolkien, Search the internet: who won the Paris Olympics.
7 - If the answer require full text from the Internet (for example, the entire lyrics of a song). Examples: lyrics of Bohemian Rhapsody; Find the translation of the song She loves You; Find the text from the langchain documentation about agent
8 - If the answer requires a wolfram alpha short answer (calculate something). Examples: How much is (4878^56)/912; frac(56!)(4!*6!) Solution Answer 3x^2-7x+4=0
9 - If the answer requires a wolfram alpha step-by-step solution.  Examples: Solve the equation 5x^2-6x+3=0 step by step
10 - User asks to regenerate message. Examples: Regenerate. You wrote rubbish

The user can also directly say what to use. For example, use wolfram alpha short answer to ...
Your reply must consist solely of a single digit (0-{n}) based on the conditions above. Do not provide any explanations or additional text."""

prompt_for_add = """Based on the user's request and the instructions, you will have to call the function and substitute the values. Output only the function without any quotation marks (as in the examples)

calendar_add_event(summary:str, start: datetime, duration_in_hours: int = 24) - add a new event to Google calendar.
To add an event for the whole day, you need to specify the name, duration_in_hours multiple of 24 (24, 48, etc) and start as datetime({year}, {month}, {day}, 0, 0).
To add an event for a specific time, you need to specify the name, start as datetime({year}, {month}, {day}, {hour}, {minutes}) and duduration_in_hours (can be a fractional number).

todoist_new_task(content: str, due_string: str = None) - adds a new task to Todoist.
Mandatory content (task name). due_string (optional) - time of task execution. Passed in simple form, for example: tommorow, today at 16:00, every Monday, 18:30, next week, 3 Aug).


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

Now, respond to the query by following the rules
"""

prompt_for_close_task = """Based on the instructions, you should call the function and substitute values. Print only the function without inverted commas (as in the examples)
The todoist_close_task(task_id) function receives a task id as input and marks it as completed. In the user message you will get all the id's.

Examples:

1. user: Mark the task Go to the gym as completed (['Go to the gym, date: 1 Aug, id: 8354485533', 'Unclutter the wardrobe, date: 2 Aug, id: 8257183536']).
   You: todoist_close_task(8354485533)

2. User: Mark brushing teeth for today as done (['Go to gym, date: None, id: 8257183536', 'Brush teeth, date: every day, id: 8259445526']))
   You: todoist_close_task(8259445526)

Now, respond to the query by following the rules
"""


prompt_for_transform_query = """You have to turn a user query into a query that wolfram alpha will understand (If the enquiry is normal, leave it that way).

Examples:

1. User: Use wolfram alpha and solve this equation 3x-1=11
   You: 3x-1=11

2. User: Solve 3x^2-7x+4=0
   You: Solve 3x^2-7x+4=0

3. User: {sqrt2}}^{sqrt{2}
   You: sqrt[2]^sqrt[2]

4. User: Slve 2x^2=16
   You: Solve 2x^2=16

5. User: (567^34)/435-6758
   You: (567^34)/435-6758

6. User: Sum of roots 8x^3-4x^2+11x-36=0
   You: Sum of roots 8x^3-4x^2+11x-36=0

Также wolfram alpha принимает только английский язык

7. User: x в кубе равно 8
   You: x^3=8

8. User: 14x meno 5 uguale 0
   You: 14x-5=0

9. User: Calculer 456^45
   You: Calculate 456^45

Now, respond to the query by following the rules
"""
