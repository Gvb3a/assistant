import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests


SCOPES = ['https://mail.google.com/']

TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'client_secret.json'


def gmail_load_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


def gmail_list(user_id='me', max_results=5):
    
    try:
        creds = gmail_load_credentials()

        url = f'https://gmail.googleapis.com/gmail/v1/users/{user_id}/messages?maxResults={max_results}'
        headers = {'Authorization': f'Bearer {creds.token}', 'Content-Type': 'application/json'}

        response = requests.get(
            url=url,
            headers=headers
        )

        response.raise_for_status()
        
        return response.json()
    
    except Exception as e:
        e = f'Gmail List Error: {e}'
        print(e)
        return e
    

def gmail_modify(message_id: str) -> bool:
    # makes a message read if it is not read
    try:
        creds = gmail_load_credentials()

        url = f'https://gmail.googleapis.com/gmail/v1/users/me/threads/{message_id}/modify'
        headers = {
            'Authorization': f'Bearer {creds.token}',
            'Content-Type': 'application/json'
        }


        labelIds = gmail_message(message_id)['labelIds']
        if 'UNREAD' in labelIds:
            body = {
                "removeLabelIds": ["UNREAD"]
            }
        else:
            body = {
                "addLabelIds": ["UNREAD"]
            }

        
        response = requests.post(url, headers=headers, json=body)
        
        response.raise_for_status()

        return True
    except Exception as e:
        print(f'Gmail Message Error: {e}')
        return False


def gmail_message(message_id: str):
    try:
        creds = gmail_load_credentials()

        service = build('gmail', 'v1', credentials=creds)
        message = service.users().messages().get(userId='me', id=message_id, format='full').execute()

        unread = 'UNREAD' in message['labelIds']

        snippet = message['snippet']

        s = str(message)

        sender_first_index = s.index("{'name': 'From', 'value': '")+len("{'name': 'From', 'value': '")
        sender_last_index = s.index('<', sender_first_index)
        sender = s[sender_first_index:sender_last_index]

        subject_first_index = s.index("{'name': 'Subject', 'value': '")+len("{'name': 'Subject', 'value': '")
        subject_last_index = s.index("'", subject_first_index)
        subject = s[subject_first_index:subject_last_index]

        
        return sender, subject, snippet, unread
    
    except Exception as e:
        e = f'Gmail Message Error: {e}'
        print(e)
        return e


def mail():
    result = ''
    mail_list = gmail_list(max_results=10)
    # {'messages': [{'id': 'str', 'threadId': 'str'}, ...], 'nextPageToken': 'str', 'resultSizeEstimate': int}
    list_of_unread = []
    count_of_unread_message = 3
    for i in mail_list['messages']:
        
        j = mail_list['messages'].index(i)
        sender, subject, snippet, unread = gmail_message(i['id'])

        if unread:
            result += f'{j}: *{sender}*\n{subject}\n_{snippet}_'
            list_of_unread.append([i['id'], j])

        elif count_of_unread_message > 0:
            result += f'- {sender}\n{subject}'
            count_of_unread_message -= 1

        else:
            break

        result += '\n—————————————————————\n'
    
    return result, list_of_unread
