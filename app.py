import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, date
import io

# SQLite DB setup
engine = create_engine("sqlite:///project_tasks.db")

# Create table (assumes plan_date column already exists)
def create_table():
    with engine.connect() as conn:
        conn.execute(text('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            project_name TEXT,
            unit TEXT,
            resource_name TEXT,
            submission_date TEXT,
            plan_date TEXT,
            status TEXT,
            remarks TEXT
        )
        '''))
create_table()

st.title("RDA Firm Project Assistant")
st.subheader("📋 Enter New Task Details")

# --- Task Submission Form ---
with st.form("task_form"):
    client_name = st.text_input("Client Name")
    project_name = st.text_input("Project Name")
    unit = st.text_input("Unit (Part of Project)")
    resource_name = st.text_input("Resource Name")
    submission_date = st.date_input("Date of Submission", date.today())
    plan_date = st.date_input("Planned Date of Completion", date.today())
    status = st.selectbox("Status", ["Not Started", "In Progress", "Completed"])
    remarks = st.text_area("Remarks")
    submitted = st.form_submit_button("Submit Task")

if submitted:
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO tasks (client_name, project_name, unit, resource_name, submission_date, plan_date, status, remarks)
                VALUES (:client_name, :project_name, :unit, :resource_name, :submission_date, :plan_date, :status, :remarks)
            """),
            {
                "client_name": client_name,
                "project_name": project_name,
                "unit": unit,
                "resource_name": resource_name,
                "submission_date": str(submission_date),
                "plan_date": str(plan_date),
                "status": status,
                "remarks": remarks
            }
        )
    st.success("✅ Task added successfully!")
    st.rerun()

# --- Task Table Display ---
st.subheader("📊 Current Task Table")
df = pd.read_sql("SELECT * FROM tasks limit 8", con=engine)
st.dataframe(df)

# --- Download Button ---
if not df.empty:
    excel_filename = "project_tasks.xlsx"
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    processed_data = output.getvalue()

    st.download_button(
        label="📥 Download Excel",
        data=processed_data,
        file_name=excel_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- Edit Existing Tasks ---
st.subheader("✏️ Edit Existing Task")

project_names = pd.read_sql("SELECT DISTINCT project_name FROM tasks", con=engine)

if not project_names.empty:
    selected_project = st.selectbox("Select a Project to Edit", project_names['project_name'])
    project_df = pd.read_sql(
        "SELECT * FROM tasks WHERE project_name = :project_name",
        con=engine,
        params={"project_name": selected_project}
    )
    st.dataframe(project_df)

    row_to_edit = st.selectbox("Select Row ID to Edit", project_df['id'])
    row_data = project_df[project_df['id'] == row_to_edit].iloc[0]

    # Safe parsing of plan_date
    default_plan_date = date.today()
    if row_data['plan_date']:
        try:
            default_plan_date = pd.to_datetime(row_data['plan_date']).date()
        except:
            pass

    with st.form("edit_form"):
        unit_edit = st.text_input("Unit", row_data['unit'])
        resource_edit = st.text_input("Resource Name", row_data['resource_name'])
        plan_date_edit = st.date_input("Planned Date", default_plan_date)
        status_edit = st.selectbox(
            "Status",
            ["Not Started", "In Progress", "Completed"],
            index=["Not Started", "In Progress", "Completed"].index(row_data['status'])
        )
        remarks_edit = st.text_area("Remarks", row_data['remarks'])
        submitted_edit = st.form_submit_button("Update Task")

    if submitted_edit:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE tasks
                    SET unit = :unit,
                        resource_name = :resource,
                        plan_date = :plan_date,
                        status = :status,
                        remarks = :remarks
                    WHERE id = :row_id
                """),
                {
                    "unit": unit_edit,
                    "resource": resource_edit,
                    "plan_date": str(plan_date_edit),
                    "status": status_edit,
                    "remarks": remarks_edit,
                    "row_id": row_to_edit
                }
            )
        st.success("✅ Task updated successfully!")
        st.rerun()
else:
    st.info("ℹ️ No projects found. Add a task first.")

# --- Add New Unit to Existing Project ---
st.subheader("➕ Add New Unit to Existing Project")

if not project_names.empty:
    selected_project_for_new_unit = st.selectbox("Select Project to Add New Unit", project_names['project_name'], key="add_unit")

    client_info = pd.read_sql(
        "SELECT DISTINCT client_name FROM tasks WHERE project_name = :project_name",
        con=engine,
        params={"project_name": selected_project_for_new_unit}
    )
    default_client = client_info['client_name'].iloc[0] if not client_info.empty else ""

    with st.form("add_unit_form"):
        client_name_new = st.text_input("Client Name", value=default_client, disabled=True)
        project_name_new = st.text_input("Project Name", value=selected_project_for_new_unit, disabled=True)
        unit_new = st.text_input("New Unit Name")
        resource_new = st.text_input("Assigned Resource")
        submission_date_new = st.date_input("Submission Date", date.today(), key="new_unit_date")
        plan_date_new = st.date_input("Planned Date", date.today(), key="new_unit_plan")
        status_new = st.selectbox("Status", ["Not Started", "In Progress", "Completed"], key="new_unit_status")
        remarks_new = st.text_area("Remarks", key="new_unit_remarks")
        add_unit_submitted = st.form_submit_button("Add Unit")

    if add_unit_submitted:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO tasks (client_name, project_name, unit, resource_name, submission_date, plan_date, status, remarks)
                    VALUES (:client_name, :project_name, :unit, :resource_name, :submission_date, :plan_date, :status, :remarks)
                """),
                {
                    "client_name": default_client,
                    "project_name": selected_project_for_new_unit,
                    "unit": unit_new,
                    "resource_name": resource_new,
                    "submission_date": str(submission_date_new),
                    "plan_date": str(plan_date_new),
                    "status": status_new,
                    "remarks": remarks_new
                }
            )
        st.success("✅ New unit added under the existing project!")
        st.rerun()
else:
    st.info("ℹ️ No existing projects available. Add a task first.")
