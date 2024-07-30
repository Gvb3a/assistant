import os
import requests
import whisper
from groq import Groq
from ollama import chat
from beautiful_date import D, days, hours
from colorama import Fore, Style, init
from dotenv import load_dotenv
from random import choice

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event

from config import LOCAL_WHISPER, LOCAL_LLM

init()
load_dotenv()


number_of_accounts = 3
path = os.path.dirname(os.path.abspath(__file__))

groq_api_key = os.getenv('GROQ_API_KEY')
client = Groq(api_key=groq_api_key)

TOKEN_FILES = [f'{path}\\token_{i}.json' for i in range(number_of_accounts)]
CREDENTIALS_FILE = f'{path}\\client_secret.json'

calendar = GoogleCalendar(credentials_path=CREDENTIALS_FILE)


def llm_api(messages: list, model: str = None, fast_model: str = False):

    if fast_model and model is None:
        model = 'qwen2:1.5b' if LOCAL_LLM else 'llama-3.1-8b-instant'
    elif model is None:
        model = 'phi3' if LOCAL_LLM else 'llama-3.1-70b-versatile'

    return ollama_api(messages, model) if LOCAL_LLM else groq_api(messages, model)


def groq_api(messages: list, model: str = 'llama-3.1-70b-versatile'):
    response = client.chat.completions.create(
            messages=messages,
            model=model)
    return response.choices[0].message.content


def ollama_api(messages: list, model: str = 'phi3'):
    response = chat(model=model, 
                    messages=messages)
    return response['message']['content']


def speech_recognition(file_name: str) -> str:

    if LOCAL_WHISPER:
        
        model = whisper.load_model('base') 
        result = model.transcribe(file_name)

        text = result['text']

    else:

        with open(file_name, "rb") as file:
            translation = client.audio.transcriptions.create(
            file=(file_name, file.read()),
            model="whisper-large-v3")
            
            text = translation.text

    print('function: speech_recognition. ', f'Recognised: {text.strip()}. LOCAL_WHISPER={LOCAL_WHISPER}')

    return text.strip()


def gmail_load_credentials() -> list:
    # возращает список creds, которые необходимы для запросов. Создает файлы типа token_<num>.json если их не было (необходимо будет пройти регестрацию). Количество creds
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
    # makes a message read if it is not read
    creds = gmail_load_credentials()[account]
       
    url = f'https://gmail.googleapis.com/gmail/v1/users/me/threads/{message_id}/modify'

    headers = {
        'Authorization': f'Bearer {creds.token}',
        'Content-Type': 'application/json'
    }

    unread = gmail_message(message_id, creds)[-1]
    
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

    return None


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


def mail():
    result = ''
    list_of_mail_lists  = gmail_list(max_results=10)
    # {'messages': [{'id': 'str', 'threadId': 'str'}, ...], 'nextPageToken': 'str', 'resultSizeEstimate': int}
    dict_of_unread = {}

    for mail_list in list_of_mail_lists:

        mail_index = list_of_mail_lists.index(mail_list)
        count_of_unread_message = 3
        unread_messages = False 

        # In gmail_message, I need the creds variable, and since gmail_load_credentials returns a list of creds, we take the creds at index
        creds = gmail_load_credentials()[mail_index]  

        for message in mail_list['messages']:
            
            message_index = mail_list['messages'].index(message)
            index = round(mail_index + message_index/10 + 1.1, 1)

            snippet, sender, to, subject, unread = gmail_message(message_id=message['id'], creds=creds)

            if unread:
                if unread_messages:
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
    
    return result, dict_of_unread


def get_events(start_time=D.today(), duration: int = 1):
    # returns a list of all events from start_time to end_time. duration in days
    end_time = start_time + duration * days
    events = calendar[start_time:end_time:'startTime']

    return [f'{event.summary}: {event.start} to {event.end}' for event in events]


def add_event_without_time(summary: str = '(No title)', start = D.today(), duration: int = 1):
    # by 'without time' we mean an all-day event. duration in days
    end = start + duration * days
    event = Event(summary, start=start, end=end)

    return calendar.add_event(event)


def add_event_with_time(summary: str = '(No title)', start = D.now(), duration: int = 1):
    # Event with a specific time. duration in hours
    end = start + duration * hours
    event = Event(summary, start=start, end=end)

    return calendar.add_event(event)
