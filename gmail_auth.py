import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime
from googleapiclient.discovery import build
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch
import torch.nn.functional as F
from nodes.db import get_all_applications, update_application
import base64
import re
from html import unescape
from bs4 import BeautifulSoup

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
MODEL_PATH = "./results/checkpoint-24"
CONFIDENCE_THRESHOLD = 0.35
STRONG_SIGNALS = {
    "rejected": ["unfortunately, we will not", "will not be moving forward", "decided to move forward with other candidates", "not selected for this position"],
    "offer": ["pleased to offer you", "we are excited to offer", "welcome to the team"],
    "interview": ["would like to invite you for an interview", "schedule an interview", "next round of interviews"],
}

def check_strong_signal(text):
    lower = text.lower()
    for label, phrases in STRONG_SIGNALS.items():
        for phrase in phrases:
            if phrase in lower:
                return label
    return None


def get_email_body(service, msg_id):
    msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    payload = msg_data.get('payload', {})

    def collect_parts(part, mime_type, collected):
        if part.get('mimeType') == mime_type:
            data = part.get('body', {}).get('data', '')
            if data:
                decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                collected.append(decoded)
        for subpart in part.get('parts', []):
            collect_parts(subpart, mime_type, collected)

    html_parts = []
    collect_parts(payload, 'text/html', html_parts)

    if html_parts:
        soup = BeautifulSoup(' '.join(html_parts), 'html.parser')
        for tag in soup(['style', 'script']):
            tag.decompose()
        text = soup.get_text(separator=' ')
        return re.sub(r'\s+', ' ', text).strip()

    plain_parts = []
    collect_parts(payload, 'text/plain', plain_parts)
    return ' '.join(plain_parts)
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
    service = build('gmail', 'v1', credentials=creds)
    return service


def search_emails_for_company(service, company_name, after_date, max_results=5):
    query = f'in:inbox subject:"{company_name}" after:{after_date}'
    
    results = service.users().messages().list(
        userId='me', q=query, maxResults=max_results
    ).execute()
    
    messages = results.get('messages', [])
    
    email_bodies = []
    for msg in messages:
        body_text = get_email_body(service, msg['id'])
        email_bodies.append({
            'id': msg['id'],
            'snippet': body_text 
        })
    
    return email_bodies

# def format_date_for_gmail(date_str):
#     try:
#         date_obj = datetime.strptime(date_str, "%Y-%m-%d") # convert to datetime object
#         return date_obj.strftime("%Y/%m/%d") # convert back to string in the format Gmail expects
#     except ValueError:
#         raise ValueError("Incorrect date format, should be YYYY-MM-DD")
    
def load_classifier():
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval()  # tells the model "we're using you to predict, not training you"
    return tokenizer, model

def classify_email(text, tokenizer, model):
    inputs = tokenizer(text, truncation=True, max_length=512, padding=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
    
    probabilities = F.softmax(outputs.logits, dim=1)
    confidence, predicted_label = torch.max(probabilities, dim=1)
    
    label_map = {0: "interview", 1: "offer", 2: "rejected", 3: "test"}
    predicted = int (predicted_label.item());
    return label_map[predicted], confidence.item()

def check_for_status_update(service, tokenizer, model, app_id, company_name, date_applied, SEARCH_FROM_DATE="2026/07/01"):
    candidate_emails = search_emails_for_company(service, company_name, SEARCH_FROM_DATE)
    relevant_emails = [e for e in candidate_emails if check_strong_signal(e["snippet"])]

    if not relevant_emails:
        return {"app_id": app_id, "status": "no_emails_found"}

    for email in relevant_emails:
        strong_label = check_strong_signal(email["snippet"])
        if strong_label:
            update_application(app_id, status=strong_label)
            return {"app_id": app_id, "status": "updated", "new_status": strong_label, "confidence": 1.0, "body": email["snippet"]}

    best_label = None
    best_confidence = 0.0
    best_body = ""
    for email in relevant_emails:
        label, confidence = classify_email(email["snippet"], tokenizer, model)
        if confidence > best_confidence:
            best_confidence = confidence
            best_label = label
            best_body = email["snippet"]

    if best_confidence >= CONFIDENCE_THRESHOLD:
        update_application(app_id, status=best_label)
        return {"app_id": app_id, "status": "updated", "new_status": best_label, "confidence": best_confidence, "body": best_body}
    else:
        return {"app_id": app_id, "status": "needs_review", "guessed_label": best_label, "confidence": best_confidence, "body": best_body}
    
if __name__ == "__main__":
    service = get_gmail_service()
    tokenizer, model = load_classifier()
    
    apps = get_all_applications()
    for app in apps:
        try:
            app_id, company_name, role, link, rname, remail, status, date_applied, cv, cl = app
            result = check_for_status_update(service, tokenizer, model, app_id, company_name, date_applied)
            print(result)
        except ValueError as e:
            print(f"⚠️ Skipping app {app_id} ({company_name}) — bad date format: {date_applied}")
        
# if __name__ == "__main__":
#     tokenizer, model = load_classifier()
    
#     test_email = "We're excited to invite you for a technical interview next week."
#     label, confidence = classify_email(test_email, tokenizer, model)
#     print(f"Predicted: {label} (confidence: {confidence:.2f})")

# if __name__ == "__main__":
#     service = get_gmail_service()
#     date_for_search = format_date_for_gmail("2026-07-25")
#     results = search_emails_for_company(service, "Google", date_for_search)
#     for r in results:
#         print(r)
#     print("✅ Authenticated successfully!")