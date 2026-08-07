import json
from state import JobState
import pandas as pd
import os

# company_name: str
#     role: str
#     application_link: str
#     recruiter_email: str
#     recruiter_name: str
#     status: str
#     date_applied: str
#     cv_link: str
#     cl_link: str
#     raw_input: str
#     extraction_success: bool
#     retry_count: int

def save_to_csv(state: JobState):
    file_path = 'data/applications.csv'
    df = pd.DataFrame(
        [
            [
            state.get('company_name'),
            state.get('role'),
            state.get('application_link'),
            state.get('recruiter_name'),
            state.get('recruiter_email'),
            state.get('status'),
            state.get('date_applied'),
            state.get('cv_link'),
            state.get('cl_link')
            ]
        ],
        columns=[
            'company_name',
            'role',
            'application_link',
            'recruiter_name',
            'recruiter_email',
            'status',
            'date_applied',
            'cv_link',
            'cl_link', 
        ]
    )
    file_exists = os.path.exists(file_path)

    df.to_csv(file_path,index=False,mode='a',header=not file_exists)
    return state