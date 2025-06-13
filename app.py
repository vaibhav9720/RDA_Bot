import streamlit as st
import pandas as pd
import gspread
from datetime import datetime, date
import io
import json
# --- Authenticate and load sheet ---
#Uncomment Below line when running on local & past the credentials file from Buddy Bot
#gc = gspread.service_account(filename="credentials.json")
#Code To read credentials from cloud
creds_dict = json.loads(st.secrets["GSPREAD_CREDENTIALS"])
gc = gspread.service_account_from_dict(creds_dict)
sheet = gc.open("Project_Tasks").sheet1  # Update name if needed

# --- Load data ---
data = sheet.get_all_records()
df = pd.DataFrame(data)

st.title("RDA Firm Project Assistant")
st.subheader("📋 Enter New Task Details")

# --- Add New Task ---
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
    sheet.append_row([
        client_name, project_name, unit, resource_name,
        str(submission_date), str(plan_date), status, remarks
    ])
    st.success("✅ Task added successfully!")
    st.rerun()

# --- Task Table Display ---
st.subheader("📊 Current Task Table")
st.dataframe(df.head(8))  # Limit rows like original

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

if not df.empty:
    project_names = df['Project_name'].unique().tolist()
    selected_project = st.selectbox("Select a Project to Edit", project_names)

    project_df = df[df['Project_name'] == selected_project]
    st.dataframe(project_df)

    editable_indices = project_df.index.tolist()
    row_to_edit = st.selectbox("Select Row ID to Edit", editable_indices)

    row_data = df.loc[row_to_edit]
    default_plan_date = pd.to_datetime(row_data['Plan_date']).date() if row_data['Plan_date'] else date.today()

    with st.form("edit_form"):
        unit_edit = st.text_input("Unit", row_data['Unit'])
        resource_edit = st.text_input("Resource Name", row_data['Resource_Name'])
        plan_date_edit = st.date_input("Planned Date", default_plan_date)
        status_edit = st.selectbox("Status", ["Not Started", "In Progress", "Completed"], index=["Not Started", "In Progress", "Completed"].index(row_data['Status']))
        remarks_edit = st.text_area("Remarks", row_data['Remarks'])
        submitted_edit = st.form_submit_button("Update Task")

    if submitted_edit:
        row_number = row_to_edit + 2  # +2 because header is row 1 and gspread is 1-indexed
        sheet.update(f'C{row_number}', [[unit_edit]])
        sheet.update(f'D{row_number}', [[resource_edit]])
        sheet.update(f'F{row_number}', [[str(plan_date_edit)]])
        sheet.update(f'G{row_number}', [[status_edit]])
        sheet.update(f'H{row_number}', [[remarks_edit]])
        st.success("✅ Task updated successfully!")
        st.rerun()
else:
    st.info("ℹ️ No tasks found. Add a task first.")

# --- Add New Unit to Existing Project ---
st.subheader("➕ Add New Unit to Existing Project")

if not df.empty:
    selected_project_for_new_unit = st.selectbox("Select Project to Add New Unit", project_names, key="add_unit")

    client_info = df[df['Project_name'] == selected_project_for_new_unit]['Client_name'].values
    default_client = client_info[0] if len(client_info) > 0 else ""

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
        sheet.append_row([
            client_name_new, project_name_new, unit_new, resource_new,
            str(submission_date_new), str(plan_date_new), status_new, remarks_new
        ])
        st.success("✅ New unit added under the existing project!")
        st.rerun()
else:
    st.info("ℹ️ No existing projects available. Add a task first.")
