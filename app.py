import re
import streamlit as st
import pandas as pd
import os
import uuid

from graph import app as agent_app
from nodes.db import init_db, get_all_applications, update_application, delete_application

st.set_page_config(page_title="Threadline", layout="wide")

init_db()  # safe to call every run - only creates the table if missing

if "processing" not in st.session_state:
    st.session_state.processing = False
if "last_result" not in st.session_state:
    st.session_state.last_result = None

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def save_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return ""
    filename = f"{uuid.uuid4().hex[:8]}_{uploaded_file.name}"
    path = os.path.join(UPLOAD_FOLDER, filename)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


def is_valid_email_or_empty(value):
    if not value or str(value).strip() == "":
        return True
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(value)) is not None

def is_valid_name_or_empty(value):
    if not value or str(value).strip() == "":
        return True
    return re.match(r"^[A-Za-z\s\-']+$", str(value)) is not None


# --- Full-screen loading overlay, shown while extraction is running ---
if st.session_state.processing:
    st.markdown("""
        <div style="position: fixed; top:0; left:0; width:100%; height:100%;
                    background: rgba(0,0,0,0.88); z-index:9999;
                    display:flex; flex-direction:column; align-items:center; justify-content:center;
                    color:white; font-size:22px; gap: 12px;">
            <div>🤖 Extracting job details with AI...</div>
            <div style="font-size:14px; color:#aaa;">This usually takes a few seconds</div>
        </div>
    """, unsafe_allow_html=True)

    initial_state = st.session_state.pending_state
    result = agent_app.invoke(initial_state)
    st.session_state.processing = False

    if result.get("extraction_success"):
        st.session_state.last_result = (
            "success",
            f"Saved: {result.get('company_name')} — {result.get('role')}"
        )
        st.session_state.form_key += 1
    else:
        st.session_state.last_result = (
            "error",
            "Extraction failed — please check the posting text and try again."
        )

    st.rerun()


st.title("📋 Threadline: your job hunt, tracked")

if st.session_state.last_result:
    kind, message = st.session_state.last_result
    if kind == "success":
        st.success(message)
    elif kind == "warning":
        st.warning(message)
    else:
        st.error(message)
    st.session_state.last_result = None

left, right = st.columns([1, 2])

if "form_key" not in st.session_state:
    st.session_state.form_key = 0

with left:
    st.subheader("Add a new application")
    raw_text = st.text_area("Paste the job posting text", height=200, key=f"jd_input_{st.session_state.form_key}")
    cv_file = st.file_uploader("CV used (optional)", type=["pdf", "docx"], key=f"cv_input_{st.session_state.form_key}")
    cl_file = st.file_uploader("Cover letter used (optional)", type=["pdf", "docx"], key=f"cl_input_{st.session_state.form_key}")
    date_applied = st.date_input("Date applied", key=f"date_input_{st.session_state.form_key}")

    add_disabled = not raw_text.strip()
    if st.button("Add application", type="primary", disabled=add_disabled):
        cv_link = save_uploaded_file(cv_file)
        cl_link = save_uploaded_file(cl_file)

        st.session_state.pending_state = {
            "raw_input": raw_text,
            "status": "applied",
            "date_applied": str(date_applied),
            "cv_link": cv_link,
            "cl_link": cl_link
        }
        st.session_state.processing = True
        st.rerun()

    if add_disabled:
        st.caption("Paste a job posting above to enable this button.")

with right:
    st.subheader("Your applications")

    apps = get_all_applications()
    columns = ["id", "company_name", "role", "application_link", "recruiter_name",
               "recruiter_email", "status", "date_applied", "cv_link", "cl_link"]
    df = pd.DataFrame(apps, columns=columns)
    df["date_applied"] = pd.to_datetime(df["date_applied"], errors="coerce")

    column_config = {
        "id": st.column_config.NumberColumn("ID", disabled=True),
        "company_name": st.column_config.TextColumn("Company", max_chars=100),
        "role": st.column_config.TextColumn("Role", max_chars=100),
        "application_link": st.column_config.LinkColumn("Link"),
        "recruiter_name": st.column_config.TextColumn("Recruiter", max_chars=100),
        "recruiter_email": st.column_config.TextColumn("Email", max_chars=100),
        "status": st.column_config.SelectboxColumn(
            "Status", options=["applied", "interview", "test", "offer", "rejected"]
        ),
        "date_applied": st.column_config.DateColumn("Date Applied", format="YYYY-MM-DD"),
        "cv_link": st.column_config.TextColumn("CV", disabled=True),
        "cl_link": st.column_config.TextColumn("CL", disabled=True),
    }

    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        column_config=column_config,
        key="applications_editor",
        width="stretch"
    )

    has_changes = not edited_df.equals(df)

    if st.button("Save changes to table", disabled=not has_changes):
        try:
            save_df = edited_df.copy()
            save_df["date_applied"] = save_df["date_applied"].dt.strftime("%Y-%m-%d")

            original_ids = set(df["id"])
            edited_ids = set(save_df["id"])
            deleted_ids = original_ids - edited_ids

            for app_id in deleted_ids:
                delete_application(int(app_id))

            row_errors = []
            for _, row in save_df.iterrows():
                original_row = df[df["id"] == row["id"]]
                if original_row.empty:
                    continue
                orig_compare = original_row.iloc[0].copy()
                orig_compare["date_applied"] = df.loc[df["id"] == row["id"], "date_applied"].dt.strftime("%Y-%m-%d").iloc[0]

                if not row.equals(orig_compare):
                    if not is_valid_email_or_empty(row["recruiter_email"]):
                        row_errors.append(f"Row {int(row['id'])}: recruiter email doesn't look valid, skipped.")
                        continue
                    if not is_valid_name_or_empty(row["recruiter_name"]):
                        row_errors.append(f"Row {int(row['id'])}: recruiter name should only contain letters, skipped.")
                        continue
                    update_application(int(row["id"]), **row.drop("id").to_dict())

            if row_errors:
                st.session_state.last_result = ("warning", " | ".join(row_errors))
            else:
                st.session_state.last_result = ("success", "Changes saved!")

            st.rerun()

        except Exception:
            st.session_state.last_result = (
                "error",
                "⚠️ Couldn't save your changes — please double check the values you entered and try again."
            )
            st.rerun()

    if not has_changes:
        st.caption("Edit a cell above to enable saving.")

    st.download_button(
        "Download as CSV",
        data=df.to_csv(index=False),
        file_name="applications.csv",
        mime="text/csv"
    )