import os
import requests  # for gmail requests
import whisper  # for local speech recognition
from groq import Groq  # for online llm
from ollama import chat  # for local llm
from beautiful_date import D, days, hours  # for google calendar. A comfortable way to set the date
from datetime import datetime
from colorama import Fore, Style, init  # for multicoloured output to the console
from dotenv import load_dotenv  # to load values from .env
from inspect import stack
from typing import Literal

# google stuff (gmail). Why did I choose to learn from scratch instead of using the cat library?
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# google calendar library. https://github.com/kuzmoyev/google-calendar-simple-api
from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event

from todoist_api_python.api import TodoistAPI  # Todoist. https://developer.todoist.com/rest/v2/#overview

from chromadb import Client  # Local vector db

from tavily import TavilyClient  # Internet search

from elevenlabs.client import ElevenLabs  # Online tts
from elevenlabs import save

from sql import sql_select, sql_setting_get

init()  # that cmd would also have a different coloured output
load_dotenv()  # load variables from the .env file


path = '\\'.join(os.path.dirname(os.path.abspath(__file__)).split('\\')[:-1])


groq_api_key = os.getenv('GROQ_API')  # Groq
groq_client = Groq(api_key=groq_api_key) # https://console.groq.com/docs/quickstart


todoist_api_key = os.getenv('TODOIST_API')  # Todoist. TODO: local todolist
todoist_api = TodoistAPI(str(todoist_api_key))  # https://developer.todoist.com/rest/v2/#overview


tavily_api_key = os.getenv('TAVILY_API_KEY')
tavily_client = TavilyClient(api_key=tavily_api_key)


elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key)


chromadb_client = Client()  # chromadb. Local vector datebase
vector_memory = chromadb_client.create_collection("all-my-documents")  # https://github.com/chroma-core/chroma


CREDENTIALS_FILE = f'{path}\\client_secret.json'  # required for gmail and google calendar
num_of_gmail_accounts = sql_setting_get('number of gmail accounts')
TOKEN_FILES = [f'{path}\\token_{i}.json' for i in range(num_of_gmail_accounts)]


calendar = GoogleCalendar(credentials_path=CREDENTIALS_FILE)  # type: ignore https://github.com/kuzmoyev/google-calendar-simple-api



def print_colorama(text: str = None, color: str = 'green'): # type: ignore
    # this function is in function.py, but it is better to declare it again.
    colors = {'green': Fore.GREEN, 'red': Fore.RED, 'yellow': Fore.YELLOW}
    
    func = stack()[1].function

    color = colors.get(color, Fore.GREEN)

    print(f'{color}{func}{Style.RESET_ALL}: {str(text)}')


def llm_api(messages: list, model: str = None, fast_model: str = False): # type: ignore

    local_llm = sql_setting_get('local llm')
    if fast_model and model is None:
        model = 'qwen2:1.5b' if local_llm else 'llama-3.1-8b-instant'
    elif model is None:
        model = 'phi3' if local_llm else 'llama-3.1-70b-versatile'

    local_llm = sql_setting_get('local llm')
    return ollama_api(messages, model) if local_llm else groq_api(messages, model)


def groq_api(messages: list, model: str = 'llama-3.1-70b-versatile'):
    response = groq_client.chat.completions.create(
            messages=messages,
            model=model)
    return response.choices[0].message.content


def ollama_api(messages: list, model: str = 'phi3'):
    response = chat(model=model, 
                    messages=messages)
    return response['message']['content']



def vector_datebase_load():
    role, content, time = sql_select('*') # type: ignore
    
    print_colorama()

    if content == []:
        return

    vector_memory.add(
        documents=content,
        metadatas=[{'role': role[i], 'time': time[i]} for i in range(len(content))],
        ids=[f'{content[i]}-{role[i]}-{time[i]}' for i in range(len(content))]  # an obligatory element that must be individualised
    )


def vector_datebase_search(text: str, n_results: int = 2):

    results = vector_memory.query(
        query_texts=[text],
        n_results=n_results,
        where={"role": "user"}, # optional filter
    )

    # {'ids': [[str, str]], 'distances': [[float, float]], 'metadatas': [[dict, dict]], 'embeddings': None, 'documents': [[str, str]], 'uris': None, 'data': None, 'included': ['metadatas', 'documents', 'distances']}
    pretty_result = []
    for i in range(len(results['ids'][0])):
        pretty_result.append(f"{results['metadatas'][0][i]['role']} at {results['metadatas'][0][i]['time']}: {results['documents'][0][i]}") # type: ignore

    return pretty_result


def vector_datebase_incert(role: str, content: str):

    time = datetime.now().strftime('%Y.%m.%d %H:%M')

    vector_memory.add(
        documents=[content],
        metadatas=[{"role": role, "time": time}],
        ids=[f'{content}-{role}-{time}']
    )



def speech_recognition(file_name: str) -> str:

    local_whisper = sql_setting_get('local whisper')
    if local_whisper:
        
        model = whisper.load_model('base') 
        result = model.transcribe(file_name)

        text = result['text']

    else:

        with open(file_name, "rb") as file:
            translation = groq_client.audio.transcriptions.create(
            file=(file_name, file.read()),
            model="whisper-large-v3")
            
            text = translation.text

    print_colorama(f'{text} local_whisper={local_whisper}')

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


def mail():  # I would move it to function.py (maybe rename it to sql.py), but it would be a circular import
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
    dict_of_unread = {}

    for mail_list in list_of_mail_lists:

        mail_index = list_of_mail_lists.index(mail_list)  # for numbering accounts 1.x, 2.x
        count_of_unread_message = 3  # unread -> read -> read -> unread -> read -> read -> read -> break
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
    # returns a list of all events from start_time to end_time. duration in days
    end_time = start_time + duration * days
    events = calendar[start_time:end_time:'startTime']

    return [f'{event.summary}: {event.start} to {event.end}' for event in events]



def calendar_add_event(summary: str = '(No title)', start: datetime = D.today(), duration_in_hours: int = 24): # type: ignore
    end = start + duration_in_hours * hours
    event = Event(summary, start=start, end=end)
    return calendar.add_event(event)


# Todoist
def todoist_get_tasks() -> list:
    tasks = todoist_api.get_tasks()
    tasks_list = []
    for task in tasks:
        date = task.due.string if task.due else None
        tasks_list.append(f'{task.content}, date: {date}, id: {task.id}')

    return tasks_list


def todoist_new_task(content: str, due_string: str = None) -> str: # type: ignore
    task = todoist_api.add_task(content=content, due_string=due_string)
    return task.id


def todoist_close_task(task_id) -> bool:
    return todoist_api.close_task(task_id=str(task_id))


# Tavily. https://tavily.com/
def tavily_search(text: str, search_depth: Literal['basic', 'advanced'] = 'advanced', max_results: int = 0):
    response = tavily_client.search(query=text, search_depth=search_depth, include_answer=True, include_images=True, max_results=max_results)
    answer = response['answer']
    images = response['images']
    print_colorama(response)
    return answer, images


# elevenlabs
def tts(text: str, voice: str = 'Brittney Hart', model: str ='eleven_turbo_v2_5'):
    
    local_tts = sql_setting_get('local tts')
    file_name = 'tts - ' + ''.join(letter for letter in text[:64] if letter.isalnum() or letter==' ') + '.mp3'

    if local_tts:
        """
        import torch
        from TTS.api import TTS
        
        device = "cpu"

        
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=True).to(device)
        tts.tts(text=str, speaker_wav=str, language=str)

        tts.tts_to_file(text=text, speaker_wav=str, language=str, file_path=str)
        """

    else:
        audio = elevenlabs_client.generate(
            text=text,
            voice=voice,
            model=model
        )
            
        save(audio=audio, filename=file_name)

    return file_name
    

vector_datebase_load()