test_cases = [
    {
        "raw_input": "Backend Engineer at Spotify. Apply here: spotify.com/careers/backend. Contact recruiter Anna Berg at anna.berg@spotify.com",
        "expected": {
            "company_name": "Spotify",
            "role": "Backend Engineer",
            "application_link": "spotify.com/careers/backend",
            "recruiter_name": "Anna Berg",
            "recruiter_email": "anna.berg@spotify.com"
        }
    },
    {
        "raw_input": "Frontend Developer at Facebook. Apply here: facebook.com/careers/frontend. Contact recruiter John Smith at john.smith@facebook.com",
        "expected": {
            "company_name": "Facebook",
            "role": "Frontend Developer",
            "application_link": "facebook.com/careers/frontend",
            "recruiter_name": "John Smith",
            "recruiter_email": "john.smith@facebook.com"
        }
    },
    {
        "raw_input": "UI/UX Designer at Adobe. Apply here: adobe.com/careers/ui-ux. Contact recruiter David Wilson",
        "expected": {
            "company_name": "Adobe",
            "role": "UI/UX Designer",
            "application_link": "adobe.com/careers/ui-ux",
            "recruiter_name": "David Wilson",
            "recruiter_email": ""   # genuinely not mentioned - real test of "don't hallucinate an email"
        }
    },
    {
        "raw_input": "Product Manager at Tesla. Contact recruiter Lisa Brown at lisa.brown@tesla.com",
        "expected": {
            "company_name": "Tesla",
            "role": "Product Manager",
            "application_link": "",   # genuinely no link in the text
            "recruiter_name": "Lisa Brown",
            "recruiter_email": "lisa.brown@tesla.com"
        }
    },
    {
        # NEW - no recruiter info mentioned at all
        "raw_input": "Data Analyst position open at Airbnb. Apply at airbnb.com/careers/data-analyst.",
        "expected": {
            "company_name": "Airbnb",
            "role": "Data Analyst",
            "application_link": "airbnb.com/careers/data-analyst",
            "recruiter_name": "",
            "recruiter_email": ""
        }
    },
    {
        # NEW - messy, casual, forwarded-email style
        "raw_input": "hey saw this and thought of you - Senior SWE role at Stripe, looks pretty cool. link: stripe.com/jobs/senior-swe. reach out to their recruiter Priya if interested, priya@stripe.com",
        "expected": {
            "company_name": "Stripe",
            "role": "Senior SWE",
            "application_link": "stripe.com/jobs/senior-swe",
            "recruiter_name": "Priya",   # only first name given - tests partial-info handling
            "recruiter_email": "priya@stripe.com"
        }
    },
    {
        # NEW - only company + role, nothing else at all
        "raw_input": "We're hiring a Cloud Infrastructure Engineer at Datadog.",
        "expected": {
            "company_name": "Datadog",
            "role": "Cloud Infrastructure Engineer",
            "application_link": "",
            "recruiter_name": "",
            "recruiter_email": ""
        }
    }
]