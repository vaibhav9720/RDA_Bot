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


def format_date_ddmmyy(input_date):
    return input_date.strftime("%d%m%y")


def parse_date_ddmmyy(value):
    try:
        return pd.to_datetime(str(value), format="%d%m%y").date()
    except Exception:
        return date.today()


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

tab1, tab2, tab3, tab4 = st.tabs([
    "➕ New Details",
    "✏️ Edit Details",
    "➕ Add New Unit",
    "📊 View Tasks"
])


# ---------------- TAB 1: NEW DETAILS ----------------
with tab1:
    st.subheader("Enter New Task Details")

    with st.form("new_task_form"):
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

        work_type = st.selectbox(
            "Work Type",
            ["Fresh", "Revision"]
        )

        comments = st.text_area("Comments")

        priority = st.selectbox(
            "Priority",
            [1, 2, 3, 4, 5]
        )

        remarks = st.text_area("Remarks")

        submitted = st.form_submit_button("Submit Task")

    if submitted:
        sheet.append_row([
            client_name,
            project_name,
            unit,
            resource_name,
            format_date_ddmmyy(submission_date),
            format_date_ddmmyy(plan_date),
            status,
            work_type,
            comments,
            priority,
            remarks
        ])

        st.success("Task added successfully!")
        st.rerun()


# ---------------- TAB 2: EDIT DETAILS ----------------
with tab2:
    st.subheader("Edit Existing Task")

    required_columns = [
        "Client_name",
        "Project_name",
        "Unit",
        "Resource_Name",
        "Submission_date",
        "Plan_date",
        "Status",
        "Work_Type",
        "Comments",
        "Priority",
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
            "Select Project to Edit",
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

        with st.form("edit_task_form"):
            unit_edit = st.text_input(
                "Unit",
                value=str(row_data["Unit"])
            )

            resource_edit = st.text_input(
                "Resource Name",
                value=str(row_data["Resource_Name"])
            )

            submission_date_edit = st.date_input(
                "Submission Date",
                parse_date_ddmmyy(row_data["Submission_date"])
            )

            plan_date_edit = st.date_input(
                "Planned Date",
                parse_date_ddmmyy(row_data["Plan_date"])
            )

            status_list = [
                "Not Started",
                "In Progress",
                "Completed"
            ]

            current_status = str(row_data["Status"])

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

            work_type_list = ["Fresh", "Revision"]

            current_work_type = str(row_data["Work_Type"])

            work_type_index = (
                work_type_list.index(current_work_type)
                if current_work_type in work_type_list
                else 0
            )

            work_type_edit = st.selectbox(
                "Work Type",
                work_type_list,
                index=work_type_index
            )

            comments_edit = st.text_area(
                "Comments",
                value=str(row_data["Comments"])
            )

            priority_list = [1, 2, 3, 4, 5]

            try:
                current_priority = int(row_data["Priority"])
            except Exception:
                current_priority = 1

            priority_index = (
                priority_list.index(current_priority)
                if current_priority in priority_list
                else 0
            )

            priority_edit = st.selectbox(
                "Priority",
                priority_list,
                index=priority_index
            )

            remarks_edit = st.text_area(
                "Remarks",
                value=str(row_data["Remarks"])
            )

            submitted_edit = st.form_submit_button("Update Task")

        if submitted_edit:
            row_number = row_to_edit + 2

            sheet.update(f"C{row_number}", [[unit_edit]])
            sheet.update(f"D{row_number}", [[resource_edit]])
            sheet.update(
                f"E{row_number}",
                [[format_date_ddmmyy(submission_date_edit)]]
            )
            sheet.update(
                f"F{row_number}",
                [[format_date_ddmmyy(plan_date_edit)]]
            )
            sheet.update(f"G{row_number}", [[status_edit]])
            sheet.update(f"H{row_number}", [[work_type_edit]])
            sheet.update(f"I{row_number}", [[comments_edit]])
            sheet.update(f"J{row_number}", [[priority_edit]])
            sheet.update(f"K{row_number}", [[remarks_edit]])

            st.success("Task updated successfully!")
            st.rerun()


# ---------------- TAB 3: ADD NEW UNIT ----------------
with tab3:
    st.subheader("Add New Unit to Existing Project")

    if df.empty:
        st.info("No existing projects available. Add a task first.")

    else:
        project_names = df["Project_name"].dropna().unique().tolist()

        selected_project_for_new_unit = st.selectbox(
            "Select Project",
            project_names,
            key="add_unit_project"
        )

        selected_rows = df[
            df["Project_name"] == selected_project_for_new_unit
        ]

        default_client = (
            selected_rows["Client_name"].values[0]
            if not selected_rows.empty
            else ""
        )

        with st.form("add_unit_form"):
            client_name_new = st.text_input(
                "Client Name",
                value=default_client,
                disabled=True
            )

            project_name_new = st.text_input(
                "Project Name",
                value=selected_project_for_new_unit,
                disabled=True
            )

            unit_new = st.text_input("New Unit Name")
            resource_new = st.text_input("Assigned Resource")

            submission_date_new = st.date_input(
                "Submission Date",
                date.today(),
                key="new_unit_submission_date"
            )

            plan_date_new = st.date_input(
                "Planned Date",
                date.today(),
                key="new_unit_plan_date"
            )

            status_new = st.selectbox(
                "Status",
                ["Not Started", "In Progress", "Completed"],
                key="new_unit_status"
            )

            work_type_new = st.selectbox(
                "Work Type",
                ["Fresh", "Revision"],
                key="new_unit_work_type"
            )

            comments_new = st.text_area(
                "Comments",
                key="new_unit_comments"
            )

            priority_new = st.selectbox(
                "Priority",
                [1, 2, 3, 4, 5],
                key="new_unit_priority"
            )

            remarks_new = st.text_area(
                "Remarks",
                key="new_unit_remarks"
            )

            add_unit_submitted = st.form_submit_button("Add Unit")

        if add_unit_submitted:
            sheet.append_row([
                default_client,
                selected_project_for_new_unit,
                unit_new,
                resource_new,
                format_date_ddmmyy(submission_date_new),
                format_date_ddmmyy(plan_date_new),
                status_new,
                work_type_new,
                comments_new,
                priority_new,
                remarks_new
            ])

            st.success("New unit added successfully!")
            st.rerun()


# ---------------- TAB 4: VIEW TASKS ----------------
with tab4:
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
