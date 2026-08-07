import json
from state import JobState
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()


def extract_fields(state: JobState) -> JobState:
    raw_input = state.get('raw_input')
    prompt = f""" You are a Job Extractor tool. You'll be given a raw text of the job posting, you need to extract the following things:

    - Company Name
    - Job Role
    - Application link
    - Recruiter Email
    - Recruiter Name

    -----------------------------
    INPUT DATA:
    -----------------------------

    Raw Input: {raw_input}

    -----------------------------
    RETURN DATA:
    -----------------------------

    Return ONLY valid JSON with these keys:
    - company_name,
    - role,
    - application_link,
    - recruiter_email,
    - recruiter_name

    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    text = (response.text or "").strip() 
    text = text.replace('```json', '').replace('```', '').strip()
    parsed_data = json.loads(text) 

    state['company_name'] = parsed_data['company_name']
    state['role'] = parsed_data['role']
    state['application_link'] = parsed_data['application_link']
    state['recruiter_email'] = parsed_data['recruiter_email']
    state['recruiter_name'] = parsed_data['recruiter_name']
    state['extraction_success'] = True

    return state