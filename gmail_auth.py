import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from nodes.db import get_all_applications, update_application
import base64
import re
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
CONFIDENCE_THRESHOLD = 0.55

STRONG_SIGNALS = {
    "rejected": [
        "unfortunately, we will not", "will not be moving forward",
        "decided to move forward with other candidates", "not selected for this position",
        "not found a suitable position", "have not found a suitable",
        "will not be extending an offer", "won't be able to offer you",
        "decided to pursue other candidates", "position has been filled",
        "not be proceeding with your candidacy", "chosen to go with another candidate",
        "unable to offer you a position", "not the right fit at this time",
        "unable to consider your application", "regret to inform you that we were unable",
        "not been able to proceed with your application",
        "not been able to move forward with your application",
        "not been able to proceed with your candidacy",
        "not been able to move forward with your candidacy",
        "not been able to consider your candidacy",
        "not been able to move forward with your application at this time",
    ],
    "interview": [
        "would like to invite you for an interview", "schedule an interview",
        "next round of interviews", "would like to schedule a call",
        "set up a call", "hop on a call", "chat about the role",
        "technical interview", "panel interview", "video call", "phone interview",
        "would like to discuss your application", "would like to discuss your candidacy",
        "would like to discuss your qualifications", "would like to discuss your experience",
        "would like to discuss your background", "would like to discuss your skills",
        "would like to discuss your fit for the role",
    ],
    "offer": [
        "pleased to offer you", "we are excited to offer", "welcome to the team",
        "delighted to offer", "formal offer of employment", "offer letter attached",
        "congratulations, you've got the job", "extend an offer",
        "we are thrilled to offer you", "we are happy to offer you",
        "we are pleased to extend an offer", "we are excited to extend an offer",
        "we are delighted to extend an offer", "we are thrilled to extend an offer",
        "we are happy to extend an offer", "we are pleased to offer you the position",
    ],
    "test": [
        "complete the attached", "coding assessment", "take-home",
        "technical assessment", "complete the online", "skills evaluation",
        "case study", "coding challenge", "please complete this",
        "please complete the attached", "please complete the online",
        "please complete the coding assessment", "please complete the take-home",
        "please complete the technical assessment", "please complete the skills evaluation",
        "please complete the case study", "please complete the coding challenge",
    ],
}

OUTCOME_KEYWORDS = [
    "interview", "invite you", "schedule a call", "next round",
    "unfortunately", "not moving forward", "not selected", "other candidates",
    "assessment", "coding test", "take-home", "technical challenge",
    "offer", "pleased to offer", "welcome to the team", "congratulations",
    "decided to proceed", "move forward with your application",
    "not found a suitable position", "not been able to proceed",
    "unable to consider your application", "regret to inform you",
]

REFERENCE_EXAMPLES = {
    "rejected": [
        "Unfortunately, we will not be moving forward with your application, but we appreciate your time and interest.",
        "We regret to inform you that we were unable to consider your application in the shortlist.",
        "We have carefully reviewed your documents, and unfortunately, we have not found a suitable position for you at this time.",
        "After careful review, we have decided to move forward with other candidates whose profiles more closely match our current requirements.",
        "We're sorry to say that we won't be able to offer you a position at this time.",
        "The position has since been filled by another candidate.",
        "Your application was reviewed by our team, and unfortunately we won't be pursuing your candidacy further at this time.",
        "We wanted to personally reach out and let you know that the team ultimately decided to pursue other candidates.",
        "Regrettably, your candidacy did not progress past this stage of our interview process.",
        "We regret that despite a strong application, we are unable to offer you a position within our organization at the present time.",
    ],
    "interview": [
        "We would like to schedule a technical interview with you next week. Please let us know your availability.",
        "We were impressed by your profile and would like to move forward with a first-round interview.",
        "Would you be free for a quick 20 minute call this week to discuss the role further?",
        "We're pleased to let you know that your application has advanced to the interview stage.",
        "Our hiring team would like to invite you for an interview - please share your availability.",
        "We'd love to set up time to talk through your experience with our team lead.",
    ],
    "offer": [
        "We are pleased to offer you the position. Please find your offer letter attached, including salary and start date.",
        "Congratulations! We are delighted to formally offer you the role.",
        "Welcome to the team! Please review the attached offer letter and let us know if you have any questions.",
        "We're thrilled to extend you an official offer for the position, subject to a standard reference check.",
        "This letter confirms our formal offer of employment for the position discussed during your interviews.",
    ],
    "test": [
        "As the next step, please complete the attached coding assessment within 5 days.",
        "Before scheduling an interview, we'd like you to complete a short take-home exercise.",
        "Please complete the attached technical assessment so we can move your application forward.",
        "As part of our hiring process, please complete this online skills evaluation.",
        "We ask all shortlisted candidates to complete a brief written exercise as the next step.",
    ],
    "acknowledged": [
    "Thank you for your interest and for applying to this opportunity. We are excited to learn more about your background and experience.",
    "A member of our recruiting team will review your application carefully. We may not be able to contact every applicant individually.",
    "Your application has been received and is currently being reviewed by our hiring team.",
    "Thank you for submitting your application. If your profile matches our requirements, we will be in touch to discuss next steps.",
    "We have received your application and will reach out if we would like to move forward with the process.",
],
}


def looks_relevant(snippet):
    lower = snippet.lower()
    return any(keyword in lower for keyword in OUTCOME_KEYWORDS)


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


def get_search_term(company_name):
    suffixes = [" GmbH & Co. KGaA", " GmbH & Co. KG", " GmbH", " AG", " Inc.", " Inc", " LLC", " Ltd."]
    cleaned = company_name
    for suffix in suffixes:
        cleaned = cleaned.replace(suffix, "")
    return cleaned.strip()


def load_classifier():
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    reference_embeddings = {
        label: embedder.encode(examples)
        for label, examples in REFERENCE_EXAMPLES.items()
    }
    return embedder, reference_embeddings


def classify_email(text, embedder, reference_embeddings):
    text_embedding = embedder.encode(text)
    best_label, best_score = None, -1.0
    for label, embeddings in reference_embeddings.items():
        scores = util.cos_sim(text_embedding, embeddings)
        max_score = scores.max().item()
        if max_score > best_score:
            best_score = max_score
            best_label = label
    return best_label, best_score


def check_for_status_update(service, embedder, reference_embeddings, app_id, company_name, date_applied, SEARCH_FROM_DATE="2026/07/01"):
    search_term = get_search_term(company_name)
    candidate_emails = search_emails_for_company(service, search_term, SEARCH_FROM_DATE)
    relevant_emails = [e for e in candidate_emails if looks_relevant(e["snippet"])]

    if not relevant_emails:
        return {"app_id": app_id, "status": "no_emails_found"}

    for email in relevant_emails:
        strong_label = check_strong_signal(email["snippet"])
        if strong_label:
            update_application(app_id, status=strong_label)
            return {"app_id": app_id, "status": "updated", "new_status": strong_label, "confidence": 1.0, "body": email["snippet"]}

    best_label = None
    best_confidence = -1.0
    best_body = ""
    for email in relevant_emails:
        label, confidence = classify_email(email["snippet"], embedder, reference_embeddings)
        if confidence > best_confidence:
            best_confidence = confidence
            best_label = label
            best_body = email["snippet"]

    if best_label == "acknowledged" and best_confidence >= CONFIDENCE_THRESHOLD:
        return {"app_id": app_id, "status": "acknowledged_only", "confidence": best_confidence, "body": best_body}

    if best_confidence >= CONFIDENCE_THRESHOLD:
        update_application(app_id, status=best_label)
        return {"app_id": app_id, "status": "updated", "new_status": best_label, "confidence": best_confidence, "body": best_body}
    else:
        return {"app_id": app_id, "status": "needs_review", "guessed_label": best_label, "confidence": best_confidence, "body": best_body}

if __name__ == "__main__":
    service = get_gmail_service()
    embedder, reference_embeddings = load_classifier()

    apps = get_all_applications()
    for app in apps:
        try:
            app_id, company_name, role, link, rname, remail, status, date_applied, cv, cl = app
            result = check_for_status_update(service, embedder, reference_embeddings, app_id, company_name, date_applied)
            print(result)
        except ValueError as e:
            print(f"⚠️ Skipping app {app_id} ({company_name}) — bad date format: {date_applied}")