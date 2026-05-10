import streamlit as st
import pandas as pd
import gspread
from datetime import date
import io
import json


st.set_page_config(
    page_title="RDA Firm Project Assistant",
    layout="wide"
)


@st.cache_resource
def connect_to_sheet():
    creds_dict = json.loads(st.secrets["GSPREAD_CREDENTIALS"])
    gc = gspread.service_account_from_dict(creds_dict)
    sheet = gc.open("Project_Tasks").sheet1
    return sheet


def load_data(sheet):
    data = sheet.get_all_records()
    return pd.DataFrame(data)


sheet = connect_to_sheet()
df = load_data(sheet)

st.title("RDA Firm Project Assistant")

tab1, tab2, tab3 = st.tabs(
    ["➕ Add Task", "📊 View Tasks", "✏️ Edit Task"]
)


with tab1:
    st.subheader("Enter New Task Details")

    with st.form("task_form"):
        client_name = st.text_input("Client Name")
        project_name = st.text_input("Project Name")
        unit = st.text_input("Unit")
        resource_name = st.text_input("Resource Name")
        submission_date = st.date_input(
            "Date of Submission",
            date.today()
        )
        plan_date = st.date_input(
            "Planned Date of Completion",
            date.today()
        )
        status = st.selectbox(
            "Status",
            ["Not Started", "In Progress", "Completed"]
        )
        remarks = st.text_area("Remarks")

        submitted = st.form_submit_button("Submit Task")

    if submitted:
        sheet.append_row([
            client_name,
            project_name,
            unit,
            resource_name,
            str(submission_date),
            str(plan_date),
            status,
            remarks
        ])

        st.success("Task added successfully!")
        st.cache_data.clear()
        st.rerun()


with tab2:
    st.subheader("Current Task Table")

    if df.empty:
        st.info("No tasks found.")
    else:
        st.dataframe(df, use_container_width=True)

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        st.download_button(
            label="Download Excel",
            data=output.getvalue(),
            file_name="project_tasks.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


with tab3:
    st.subheader("Edit Existing Task")

    required_columns = [
        "Client_name",
        "Project_name",
        "Unit",
        "Resource_Name",
        "Submission_date",
        "Plan_date",
        "Status",
        "Remarks"
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        st.error(
            "Missing columns in Google Sheet: "
            + ", ".join(missing_columns)
        )

    elif df.empty:
        st.info("No tasks available to edit.")

    else:
        project_names = df["Project_name"].dropna().unique().tolist()

        selected_project = st.selectbox(
            "Select Project",
            project_names
        )

        project_df = df[
            df["Project_name"] == selected_project
        ]

        st.dataframe(project_df, use_container_width=True)

        row_to_edit = st.selectbox(
            "Select Row ID to Edit",
            project_df.index.tolist()
        )

        row_data = df.loc[row_to_edit]

        try:
            default_plan_date = pd.to_datetime(
                row_data["Plan_date"]
            ).date()
        except Exception:
            default_plan_date = date.today()

        with st.form("edit_form"):
            unit_edit = st.text_input(
                "Unit",
                value=row_data["Unit"]
            )

            resource_edit = st.text_input(
                "Resource Name",
                value=row_data["Resource_Name"]
            )

            plan_date_edit = st.date_input(
                "Planned Date",
                default_plan_date
            )

            status_list = [
                "Not Started",
                "In Progress",
                "Completed"
            ]

            current_status = row_data["Status"]

            status_index = (
                status_list.index(current_status)
                if current_status in status_list
                else 0
            )

            status_edit = st.selectbox(
                "Status",
                status_list,
                index=status_index
            )

            remarks_edit = st.text_area(
                "Remarks",
                value=row_data["Remarks"]
            )

            submitted_edit = st.form_submit_button(
                "Update Task"
            )

        if submitted_edit:
            row_number = row_to_edit + 2

            sheet.update(f"C{row_number}", [[unit_edit]])
            sheet.update(f"D{row_number}", [[resource_edit]])
            sheet.update(f"F{row_number}", [[str(plan_date_edit)]])
            sheet.update(f"G{row_number}", [[status_edit]])
            sheet.update(f"H{row_number}", [[remarks_edit]])

            st.success("Task updated successfully!")
            st.rerun()
