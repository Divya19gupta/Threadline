from langgraph.graph import START, StateGraph, END
from state import JobState
from nodes.extraction_data import extract_fields
from nodes.save_data_to_db import save_to_db

graph = StateGraph(JobState)

# add your two nodes here
graph.add_node("extract_fields", extract_fields) 
graph.add_node("save_to_db", save_to_db) 
# set entry point
graph.add_edge(START, "extract_fields")
graph.add_conditional_edges(
    "extract_fields",
    lambda state: state.get("extraction_success"), 
    {True: "save_to_db", False: END}
)

        
# add edges: extract_fields -> save_to_db -> END
graph.add_edge("save_to_db", END)

app = graph.compile()

# then call app.invoke(test_state) with your sample data
test_state: JobState = {
    "raw_input": "Software Engineer at Google. Apply here: google.com/careers. Contact recruiter Jane Doe at jane@google.com",
    "status": "applied",
    "date_applied": "2026-07-25",
    "cv_link": "cv_google.pdf",
    "cl_link": "cl_google.pdf"
}

result = app.invoke(test_state)
print(result)