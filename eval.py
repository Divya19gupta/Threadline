import time

from nodes.extraction_data import extract_fields
from eval_data import test_cases
from state import JobState

total_fields = 0
correct_fields = 0

for case in test_cases:
    state: JobState = {"raw_input": case["raw_input"], "status": "applied", "date_applied": "2026-08-01", "cv_link": "", "cl_link": ""}
    result = extract_fields(state)
    
    for field, expected_value in case["expected"].items():
        if result.get(field) == expected_value:
            correct_fields += 1
        total_fields += 1
        time.sleep(15)


accuracy = correct_fields / total_fields * 100 
print(f"Field-level accuracy: {accuracy}%")