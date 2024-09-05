import os
import requests  # for gmail and wolfram alpha requests
import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from groq import Groq  # for online llm
from beautiful_date import D, days, hours  # for google calendar. A comfortable way to set the date
from datetime import datetime
from colorama import Fore, Style, init  # for multicoloured output to the console
from dotenv import load_dotenv  # to load values from .env
from inspect import stack
from urllib.parse import quote
from time import sleep

# google stuff (gmail). Why did I choose to learn from scratch instead of using the cat library?
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# google calendar library. https://github.com/kuzmoyev/google-calendar-simple-api
from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event

from todoist_api_python.api import TodoistAPI  # Todoist. https://developer.todoist.com/rest/v2/#overview

from tavily import TavilyClient  # Internet search

if __name__ == '__main__' or '.' not in __name__:
    from online_sql import sql_select, sql_incert
    from online_config import prompt_for_transform_query_wolfram
else:
    from .online_sql import sql_select, sql_incert
    from .online_config import prompt_for_transform_query_wolfram


init()  # that cmd would also have a different coloured output
load_dotenv()  # load variables from the .env file


path = '\\'.join(os.path.dirname(os.path.abspath(__file__)).split('\\')[:-1])


groq_api_key = os.getenv('GROQ_API')  # Groq
groq_client = Groq(api_key=groq_api_key) # https://console.groq.com/docs/quickstart


todoist_api_key = os.getenv('TODOIST_API')  # Todoist. TODO: local todolist
todoist_api = TodoistAPI(str(todoist_api_key))  # https://developer.todoist.com/rest/v2/#overview


tavily_api_key = os.getenv('TAVILY_API_KEY')
tavily_client = TavilyClient(api_key=tavily_api_key)

from gradio_client import Client
os.environ['HF_TOKEN'] = str(os.getenv('HUGGING_FACE_TOKEN'))
hugging_face_flux_client = Client('black-forest-labs/FLUX.1-dev')


from chromadb import Client  # Local vector db
chromadb_client = Client()  # chromadb. Local vector datebase
vector_memory = chromadb_client.create_collection("all-my-documents")  # https://github.com/chroma-core/chroma

WOLFRAM_SIMPLE_API = os.getenv('WOLFRAM_SIMPLE_API_KEY')
WOLFRAM_SHOW_STEPS_API = os.getenv('WOLFRAM_SHOW_STEPS_RESULT')


CREDENTIALS_FILE = f'{path}\\client_secret.json'  # required for gmail and google calendar
num_of_gmail_accounts = 3
TOKEN_FILES = [f'{path}\\token_{i}.json' for i in range(num_of_gmail_accounts)]


calendar = GoogleCalendar(credentials_path=CREDENTIALS_FILE)  #https://github.com/kuzmoyev/google-calendar-simple-api



def print_colorama(text: str | None = None, color: str = 'green'):
    '''When this function is called in another function, its green name is displayed (via stak) and then the text that is passed.
    Made to avoid writing {Fore.GREEN}{func name}{Style.RESET_ALL}: {text} all the time.'''
    colors = {'green': Fore.GREEN, 'red': Fore.RED, 'yellow': Fore.YELLOW}
    
    func = stack()[1].function

    color = colors.get(color, Fore.GREEN)

    print(f'{color}{func}{Style.RESET_ALL}: {str(text)}')


def llm_api(messages: list[dict[str, str]], fast_model: bool = False, model: str | None = None) -> str:
    local_llm = sql_select(var='local_llm', table='Settings')[0][0]

    if model is None:
        if fast_model and local_llm:
            var = 'fast_local_llm_model'
        elif local_llm:
            var = 'local_llm_model'
        elif fast_model:
            var = 'fast_llm_model'
        else:
            var = 'llm_model'
        model = sql_select(var=var, table='Settings')[0][0]

    return groq_api(messages, str(model))


def groq_api(messages: list, model: str = 'llama-3.1-70b-versatile') -> str:
    response = groq_client.chat.completions.create(
            messages=messages,
            model=model)
    return str(response.choices[0].message.content)


'''
def vector_datebase_load():
    role, content, time = sql_select('*')
    
    print_colorama()

    if content == []:
        return

    vector_memory.add(
        documents=content,
        metadatas=[{'role': role[i], 'time': time[i]} for i in range(len(content))],
        ids=[f'{content[i]}-{role[i]}-{time[i]}' for i in range(len(content))]  # an obligatory element that must be individualised
    )


# TODO: complete overhaul
def vector_datebase_search(text: str, n_results: int = 2): 

    results = vector_memory.query(
        query_texts=[text],
        n_results=n_results,
        where={"role": "user"},
    )

    # {'ids': [[str, str]], 'distances': [[float, float]], 'metadatas': [[dict, dict]], 'embeddings': None, 'documents': [[str, str]], 'uris': None, 'data': None, 'included': ['metadatas', 'documents', 'distances']}
    pretty_result = []
    for i in range(len(results['ids'][0])):
        pretty_result.append(f"{results['metadatas'][0][i]['role']} at {results['metadatas'][0][i]['time']}: {results['documents'][0][i]}")

    return pretty_result


def vector_datebase_incert(role: str, content: str):

    time = datetime.now().strftime('%Y.%m.%d %H:%M')

    vector_memory.add(
        documents=[content],
        metadatas=[{"role": role, "time": time}],
        ids=[f'{content}-{role}-{time}']
    )
'''


def speech_recognition(file_name: str) -> str:

    

    with open(file_name, "rb") as file:
        translation = groq_client.audio.transcriptions.create(
        file=(file_name, file.read()),
        model="whisper-large-v3")
            
        text = translation.text

    print_colorama(f'{text} ')

    return str(text).strip()


# gmail
def gmail_load_credentials() -> list:
    # Returns a list of creds that are required for queries. Creates files like token_<num>.json if they do not exist (you will need to register)
    creds_list = []
    scopes = ['https://mail.google.com/']
    
    for token_file in TOKEN_FILES:

        if os.path.exists(token_file):
            creds = Credentials.from_authorized_user_file(token_file, scopes=scopes)
        else:
            creds = None

        if not creds or not creds.valid:

            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, scopes=scopes)
                creds = flow.run_local_server(port=0)

            with open(token_file, "w") as token:
                token.write(creds.to_json())

        creds_list.append(creds)

    return creds_list


def gmail_list(max_results=5):
    # sample result: [{'messages': [{'id': str, 'threadId': str}, ...], 'nextPageToken': str, 'resultSizeEstimate': 201}]
    creds_list = gmail_load_credentials()
    result_list = []

    for creds in creds_list:
        url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults={max_results}'
        headers = {'Authorization': f'Bearer {creds.token}', 'Content-Type': 'application/json'}

        response = requests.get(
            url=url,
            headers=headers
        )
        
        result_list.append(response.json())

    return result_list
    

def gmail_modify(message_id: str, account: int = 0) -> None:
    # makes a message read if it is not read and vice versa
    creds = gmail_load_credentials()[account]
       
    url = f'https://gmail.googleapis.com/gmail/v1/users/me/threads/{message_id}/modify'

    headers = {
        'Authorization': f'Bearer {creds.token}',
        'Content-Type': 'application/json'
    }

    unread = gmail_message(message_id, creds)[-1]  # snippet, sender, to, subject, unread (bool)
    
    
    if unread:
        body = {
            "removeLabelIds": ["UNREAD"]
        }
    else:
        body = {
            "addLabelIds": ["UNREAD"]
        }
    
    response = requests.post(url, headers=headers, json=body)
    
    response.raise_for_status()

    return


def gmail_message(message_id: str, creds: str):

    service = build('gmail', 'v1', credentials=creds)
    message = service.users().messages().get(userId='me', id=message_id, format='full').execute()

    unread = 'UNREAD' in message['labelIds']

    snippet = message['snippet']

    to = message['payload']['headers'][0]['value']

    s = str(message)

    sender_first_index = s.index("{'name': 'From', 'value': '")+len("{'name': 'From', 'value': '")
    sender_last_index = s.index('<', sender_first_index)
    sender = s[sender_first_index:sender_last_index]

    subject_first_index = s.index("{'name': 'Subject', 'value': '")+len("{'name': 'Subject', 'value': '")
    subject_last_index = s.index("'", subject_first_index)
    subject = s[subject_first_index:subject_last_index]

    
    return snippet, sender, to, subject, unread


def mail() -> tuple[str, dict]:  # I would move it to function.py (maybe rename it to sql.py), but it would be a circular import
    '''Returns str with all emails (example output in the function) and also a dictionary with emails id'''
    """
    # Example result:
    1.1: *from*  # bold (text go as Markdown)
    subject
    _snippet_  # italic
    —————————————————————
    2.2: *from*
    subject
    _snippet_
    =======================================
    2.1: *from*
    subject
    _snippet_
    """
    result = str()
    list_of_mail_lists  = gmail_list(max_results=15)
    # {'messages': [{'id': 'str', 'threadId': 'str'}, ...], 'nextPageToken': 'str', 'resultSizeEstimate': int}
    dict_of_unread = {}  # 1.1: <id>

    for mail_list in list_of_mail_lists:

        mail_index = list_of_mail_lists.index(mail_list)  # for numbering accounts
        count_of_unread_message = 3  # unread -> read -> unread -> read -> read -> break
        unread_messages = False  # To check if there are any unread messages at all

        # In gmail_message, I need the creds variable, and since gmail_load_credentials returns a list of creds, we take the creds at index
        creds = gmail_load_credentials()[mail_index]  

        for message in mail_list['messages']:
            
            message_index = mail_list['messages'].index(message)
            index = round(mail_index + message_index/10 + 1.1, 1)  # 0.0 -> 1.1, 0.1 -> 1.2. Without round 0.1+1.1 = 1.2000000000000002 

            snippet, sender, to, subject, unread = gmail_message(message_id=message['id'], creds=creds)

            if unread:
                if unread_messages:  # do not add ————————————————————— before the first unread
                    result += '\n' + "—"*21 + '\n'
                result += f'{index}: *{sender}*\n{subject}\n_{snippet}_'
                dict_of_unread[index] = message['id']
                unread_messages = True

            elif count_of_unread_message > 0:
                count_of_unread_message -= 1

            elif unread_messages:
                if mail_index + 1 != len(list_of_mail_lists):
                    result += '\n' + "="*33 + '\n'
                break

            else:
                break

    if result == '':
        result = 'No unread mail✅'
    
    print_colorama(f'Email count: {len(dict_of_unread)}')
    return result, dict_of_unread


# Google Calendar
def calendar_get_events(start_time=D.today(), duration: int = 1) -> list:
    '''Returns a list of all events from start_time to end_time. duration in days. By default will return today's events'''

    end_time = start_time + duration * days
    events = calendar[start_time:end_time:'startTime']

    return [f'{event.summary}: {event.start} to {event.end}' for event in events]



def calendar_add_event(summary: str = '(No title)', start = D.today(), duration_in_hours: int = 24):
    end = start + duration_in_hours * hours
    event = Event(summary, start=start, end=end)
    return calendar.add_event(event)


# Todoist
def todoist_get_tasks() -> list:
    '''Returns a list of all todoist tasks, their date and id'''
    tasks = todoist_api.get_tasks()
    tasks_list = []
    for task in tasks:
        date = task.due.string if task.due else None
        tasks_list.append(f'{task.content}, date: {date}, id: {task.id}')

    return tasks_list


def todoist_new_task(content: str, due_string: str | None = None) -> str:
    '''Create new todoist task. Returns id. 
    About due date: https://todoist.com/help/articles/introduction-to-due-dates-and-due-times-q7VobO'''
    task = todoist_api.add_task(content=content, due_string=due_string)
    return task.id


def todoist_close_task(task_id) -> bool:
    '''Marks todoist tasks completed by id. Returns True if successful, otherwise False'''
    return todoist_api.close_task(task_id=str(task_id))



# wolfram alpha
async def download_image_async(url: str, filename: str):
    '''Asynchronously download an image from a URL. Returns path to image or False'''
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=60) as response:
            
            if response.status == 200:
                async with aiofiles.open(filename, 'wb') as file:
                    await file.write(await response.read())

                full_path = os.path.abspath(filename)
                return full_path
            
            else:
                return False
            

def wolfram_quick_answer(text: str) -> str:
    '''Return wolfram short answer (asynchronously)'''
    query = quote(text)
    return requests.get(f'https://api.wolframalpha.com/v1/result?appid={WOLFRAM_SIMPLE_API}&i={query}').text


async def wolfram_simple_answer(text: str) -> str | bool:
    '''Return link to wolfram simple answer (asynchronously)'''
    query = quote(text)
    link = f'https://api.wolframalpha.com/v1/simple?appid={WOLFRAM_SIMPLE_API}&i={query}%3F'

    filename = f"wolfram_simple_answer-{datetime.now().strftime('%Y%m%d_%H%M%S%f')}.png"
    path = await download_image_async(link, filename)

    print_colorama(str(path))

    return str(path)


async def wolfram_step_by_step(text: str) -> tuple[str, list]:
    '''Returns a step by step solution in the form of a string and a list of picture links (asynchronously)'''
    query = quote(text)
    url = f'https://api.wolframalpha.com/v1/query?appid={WOLFRAM_SHOW_STEPS_API}&input={query}&podstate=Step-by-step%20solution'

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            soup = BeautifulSoup(content, "xml")

            subpods = soup.find_all("subpod", {"title": "Possible intermediate steps"})
            
            step_images = []
            step_plain = ''

            for subpod in subpods:
                img_tag = subpod.find("img")
                if img_tag:
                    step_resp_img = img_tag.get("src")
                    step_images.append(step_resp_img)
                
                plain_tag = subpod.find('plaintext')
                step_resp = plain_tag.get_text('\n', strip=True)
                step_resp = step_resp.replace('Answer: | \n |', '\nAnswer:\n') if plain_tag else False
                if step_resp:
                    step_plain += step_resp + '\n\n'
            
            nw = datetime.now().strftime('%Y%m%d_%H%M%S%f')
            downloaded_image_paths = await asyncio.gather(*[download_image_async(url, f'wolfram_step_by_step-{nw}-{i}.png') for i, url in enumerate(step_images)])

            print_colorama(f'{url}, images: {step_images}')
            return step_plain, downloaded_image_paths


async def ask_wolfram_alpha(text: str) -> tuple[str, list]:
    '''Asynchronous function. Returns quick response, step by step solution text and downloaded image paths (simple(page) and step by step)'''
    # all three queries take 2 seconds

    quick_answer = wolfram_quick_answer(text)

    if 'Wolfram|Alpha did not understand your input' in quick_answer:
        print(f'ask_wolfram_alpha: Wolfram|Alpha did not understand {text}. Ask llm')
        messages = [
            {'role': 'user', 'content': prompt_for_transform_query_wolfram},
            {'role': 'user', 'content': text}
        ]
        text = llm_api(messages=messages)
        quick_answer = wolfram_quick_answer(text)

    simple_answer_task = asyncio.create_task(wolfram_simple_answer(text))
    step_by_step_task = asyncio.create_task(wolfram_step_by_step(text))

    simple_answer_link = await simple_answer_task
    step_by_step_solution, step_images = await step_by_step_task

    images = [image for image in step_images if image]
    if simple_answer_link:
        images.insert(0, simple_answer_link)
    
    print_colorama(text)
    return quick_answer, images



# Tavily. https://tavily.com/
async def tavily_qsearch(text: str) -> tuple[str, list[str]]:
    '''Asynchronous function. Returns a short answer on the topic using the internet, photos and urls. (include_answer=True, max_results=0)'''
    response = tavily_client.search(query=text, search_depth='basic', include_answer=True, include_images=True, max_results=0)
    answer = response['answer']
    images_url = response['images']
    nw = datetime.now().strftime('%Y%m%d_%H%M%S%f')
    downloaded_images = await asyncio.gather(*[download_image_async(url, f'tavily_qsearch-{nw}-{i}.png') for i, url in enumerate(images_url)])
    images = [image for image in downloaded_images if image]
    print_colorama(f'answer: {answer}, images: {images}')
    return answer, images


async def tavily_full_search(text: str, max_results: int = 3):
    '''Asynchronous function. Returns text from multiple pages on a web request (include_raw_content=True) and photos'''
    response = tavily_client.search(query=text, search_depth='advanced', include_raw_content=True, include_images=True, max_results=max_results)
    results = response['results']
    images_url = response['images']
    nw = datetime.now().strftime('%Y%m%d_%H%M%S%f')
    downloaded_images = await asyncio.gather(*[download_image_async(url, f'tavily_qsearch-{nw}-{i}.png') for i, url in enumerate(images_url)])
    images = [image for image in downloaded_images if image]
    print_colorama(f'{results}, {images}')

    return results, images


async def hugging_face_flux(prompt: str, seed: int = 0, randomize_seed: bool = True, width: int = 1024, height: int = 1024, guidance_scale: float = 3.5, num_inference_steps: int = 28) -> tuple[str | None, int | None]:
    # TODO: add user limits and possibly multiple hugging face accounts 

    attempts = 3

    if not 0 <= seed <= 2**31-1:
        seed = 0

    if not 256 <= width <= 2048:
        width = 1024

    if not 256 <= height <= 2048:
        height = 1024

    if not 1 <= guidance_scale <= 15:
        guidance_scale = 3.5

    if not 1 <= num_inference_steps <= 50:
        num_inference_steps = 28

    for _ in range(attempts):
        try:
            result = hugging_face_flux_client.predict(
                prompt=prompt,
                seed=seed,
                randomize_seed=randomize_seed,
                width=width,
                height=height,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps
            )
            path = result[0]
            seed = result[1]
            result = f'Image successfully generated and will be sent to the user. \nPrompt: `{prompt}`\nSeed: `{seed}`'
            break
        except Exception as e:
            path = None
            result = f'Error: {e}. Don\'t lie to the user and let them know about the error and when they can use it (or tell them to contact admin)'
            print_colorama(color='RED', text=f'Error: {e}')
            

    return result, path