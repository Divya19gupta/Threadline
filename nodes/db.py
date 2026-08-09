import sqlite3

def init_db():
    conn = sqlite3.connect("data/applications.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            role TEXT,
            application_link TEXT,
            recruiter_name TEXT,
            recruiter_email TEXT,
            status TEXT,
            date_applied TEXT,
            cv_link TEXT,
            cl_link TEXT
        )
    """)
    
    conn.commit()
    conn.close()


def get_all_applications():
    conn = sqlite3.connect("data/applications.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM applications")
    applications = cursor.fetchall()
    
    conn.close()
    return applications 

def update_application(app_id, **fields):
    allowed_fields = {
        'company_name', 'role', 'application_link', 
        'recruiter_name', 'recruiter_email', 'status', 
        'date_applied', 'cv_link', 'cl_link'
    }
    
    updates = {k: v for k, v in fields.items() if k in allowed_fields}
    
    if not updates:
        print("No valid fields to update.")
        return
    
    set_clause = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [app_id]
    
    conn = sqlite3.connect("data/applications.db")
    cursor = conn.cursor()
    cursor.execute(f"UPDATE applications SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()

def delete_application(app_id):
    conn = sqlite3.connect("data/applications.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    conn.commit()
    conn.close()