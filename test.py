from nodes.extraction_data import extract_fields
from nodes.save_data_to_csv import save_to_csv

test_state = {
    "raw_input": "Software Engineer at Google. Apply here: google.com/careers. Contact recruiter Jane Doe at jane@google.com",
    "status": "applied",
    "date_applied": "2026-07-25",
    "cv_link": "cv_google.pdf",
    "cl_link": "cl_google.pdf"
}

result = extract_fields(test_state)
save_to_csv(result)