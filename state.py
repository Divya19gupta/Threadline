from typing_extensions import TypedDict, NotRequired

class JobState(TypedDict):
    company_name: NotRequired[str]
    role: NotRequired[str]
    application_link: NotRequired[str]
    recruiter_email: NotRequired[str]
    recruiter_name: NotRequired[str]
    status: str
    date_applied: str
    cv_link: str
    cl_link: str
    raw_input: str
    extraction_success: NotRequired[bool]
    retry_count: NotRequired[int]