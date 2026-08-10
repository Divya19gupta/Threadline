import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    
    if os.path.exists('data/token.json'):
        creds = Credentials.from_authorized_user_file('data/token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('data/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('data/token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

if __name__ == "__main__":
    service = get_gmail_service()
    print("✅ Authenticated successfully!")