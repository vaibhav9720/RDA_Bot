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


# ---------------- CSS ----------------
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 95%;
    }

    h1 {
        font-size: 42px !important;
        font-weight: 800 !important;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }

    h2, h3 {
        color: #111827;
        font-weight: 700 !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        border-bottom: 1px solid #e5e7eb;
    }

    .stTabs [data-baseweb="tab"] {
        height: 45px;
        padding: 10px 18px;
        background-color: #f3f4f6;
        border-radius: 12px 12px 0 0;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: white !important;
    }

    div[data-testid="stForm"] {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 18px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-testid="stTextArea"] textarea {
        border-radius: 10px;
        border: 1px solid #d1d5db;
        background-color: #f9fafb;
    }

    .stSelectbox div[data-baseweb="select"] {
        border-radius: 10px;
        background-color: #f9fafb;
    }

    .stButton button,
    .stDownloadButton button,
    div[data-testid="stFormSubmitButton"] button {
        background-color: #2563eb;
        color: white;
        border-radius: 12px;
        padding: 10px 24px;
        font-weight: 700;
        border: none;
    }

    .stButton button:hover,
    .stDownloadButton button:hover,
    div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #1d4ed8;
        color: white;
    }

    .metric-card {
        background: linear-gradient(135deg, #2563eb, #1e40af);
        padding: 18px;
        border-radius: 18px;
        color: white;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }

    label {
        font-weight: 600 !important;
        color: #374151 !important;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- FUNCTIONS ----------------
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


def prepare_dashboard_data(df):
    dash_df = df.copy()

    dash_df["Plan_Date_Parsed"] = pd.to_datetime(
        dash_df["Plan_date"].astype(str),
        format="%d%m%y",
        errors="coerce"
    )

    dash_df["Submission_Date_Parsed"] = pd.to_datetime(
        dash_df["Submission_date"].astype(str),
        format="%d%m%y",
        errors="coerce"
    )

    today = pd.Timestamp.today().normalize()

    dash_df["Days_Left"] = (
        dash_df["Plan_Date_Parsed"] - today
    ).dt.days

    dash_df["Is_Overdue"] = (
        (dash_df["Days_Left"] < 0) &
        (dash_df["Status"] != "Completed")
    )

    dash_df["Approaching_Deadline"] = (
        (dash_df["Days_Left"] >= 0) &
        (dash_df["Days_Left"] <= 7) &
        (dash_df["Status"] != "Completed")
    )

    dash_df["Priority"] = pd.to_numeric(
        dash_df["Priority"],
        errors="coerce"
    ).fillna(0).astype(int)

    return dash_df


def rename_plan_date_for_display(input_df):
    return input_df.rename(
        columns={
            "Plan_date": "Mech Input Availability Date"
        }
    )


sheet = connect_to_sheet()
df = load_data(sheet)


# ---------------- HEADER ----------------
st.title("RDA Firm Project Assistant")
st.caption(
    "Manage project tasks, priorities, revisions and mech input availability dates."
)

if not df.empty:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"<div class='metric-card'><h3>{len(df)}</h3><p>Total Tasks</p></div>",
            unsafe_allow_html=True
        )

    with col2:
        completed = len(df[df["Status"] == "Completed"])
        st.markdown(
            f"<div class='metric-card'><h3>{completed}</h3><p>Completed</p></div>",
            unsafe_allow_html=True
        )

    with col3:
        pending = len(df[df["Status"] != "Completed"])
        st.markdown(
            f"<div class='metric-card'><h3>{pending}</h3><p>Pending</p></div>",
            unsafe_allow_html=True
        )

    with col4:
        projects = df["Project_name"].nunique()
        st.markdown(
            f"<div class='metric-card'><h3>{projects}</h3><p>Projects</p></div>",
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)


tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ New Details",
    "✏️ Edit Details",
    "➕ Add New Unit",
    "📊 View Tasks",
    "📈 Dashboard"
])


# ---------------- TAB 1 ----------------
with tab1:
    st.subheader("Enter New Task Details")

    with st.form("new_task_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            client_name = st.text_input("Client Name")
            project_name = st.text_input("Project Name")
            unit = st.text_input("Unit")

        with col2:
            resource_name = st.text_input("Resource Name")
            submission_date = st.date_input(
                "Date of Submission",
                date.today()
            )
            plan_date = st.date_input(
                "Mech Input Availability Date",
                date.today()
            )

        with col3:
            status = st.selectbox(
                "Status",
                ["Not Started", "In Progress", "Completed"]
            )
            work_type = st.selectbox(
                "Work Type",
                ["Fresh", "Revision"]
            )
            priority = st.selectbox(
                "Priority",
                [1, 2, 3, 4, 5]
            )

        col4, col5 = st.columns(2)

        with col4:
            comments = st.text_area("Comments", height=90)

        with col5:
            remarks = st.text_area("Remarks", height=90)

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


# ---------------- TAB 2 ----------------
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
        st.error("Missing columns: " + ", ".join(missing_columns))

    elif df.empty:
        st.info("No tasks available to edit.")

    else:
        project_names = df["Project_name"].dropna().unique().tolist()

        col_a, col_b = st.columns([1, 2])

        with col_a:
            selected_project = st.selectbox(
                "Select Project to Edit",
                project_names
            )

        project_df = df[df["Project_name"] == selected_project]

        with col_b:
            row_to_edit = st.selectbox(
                "Select Row ID to Edit",
                project_df.index.tolist()
            )

        st.dataframe(
            rename_plan_date_for_display(project_df),
            use_container_width=True,
            height=220
        )

        row_data = df.loc[row_to_edit]

        with st.form("edit_task_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
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

            with col2:
                plan_date_edit = st.date_input(
                    "Mech Input Availability Date",
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

            with col3:
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

                comments_edit = st.text_area(
                    "Comments",
                    value=str(row_data["Comments"]),
                    height=90
                )

                remarks_edit = st.text_area(
                    "Remarks",
                    value=str(row_data["Remarks"]),
                    height=90
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


# ---------------- TAB 3 ----------------
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
            col1, col2, col3 = st.columns(3)

            with col1:
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

            with col2:
                resource_new = st.text_input("Assigned Resource")

                submission_date_new = st.date_input(
                    "Submission Date",
                    date.today(),
                    key="new_unit_submission_date"
                )

                plan_date_new = st.date_input(
                    "Mech Input Availability Date",
                    date.today(),
                    key="new_unit_plan_date"
                )

            with col3:
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

                priority_new = st.selectbox(
                    "Priority",
                    [1, 2, 3, 4, 5],
                    key="new_unit_priority"
                )

            col4, col5 = st.columns(2)

            with col4:
                comments_new = st.text_area(
                    "Comments",
                    height=90,
                    key="new_unit_comments"
                )

            with col5:
                remarks_new = st.text_area(
                    "Remarks",
                    height=90,
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


# ---------------- TAB 4 ----------------
with tab4:
    st.subheader("Current Task Table")

    if df.empty:
        st.info("No tasks found.")
    else:
        st.dataframe(
            rename_plan_date_for_display(df),
            use_container_width=True,
            height=500
        )

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            rename_plan_date_for_display(df).to_excel(
                writer,
                index=False
            )

        st.download_button(
            label="Download Excel",
            data=output.getvalue(),
            file_name="project_tasks.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ---------------- TAB 5 ----------------
with tab5:
    st.subheader("Project Dashboard")

    if df.empty:
        st.info("No data available for dashboard.")

    else:
        dash_df = prepare_dashboard_data(df)

        total_tasks = len(dash_df)
        completed_tasks = len(
            dash_df[dash_df["Status"] == "Completed"]
        )
        pending_tasks = len(
            dash_df[dash_df["Status"] != "Completed"]
        )
        overdue_tasks = dash_df["Is_Overdue"].sum()

        completion_rate = round(
            (completed_tasks / total_tasks) * 100, 1
        ) if total_tasks > 0 else 0

        st.markdown("### Overall Summary")

        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            st.metric("Total Tasks", total_tasks)

        with c2:
            st.metric("Completed", completed_tasks)

        with c3:
            st.metric("Pending", pending_tasks)

        with c4:
            st.metric("Overdue", int(overdue_tasks))

        with c5:
            st.metric("Completion %", f"{completion_rate}%")

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Projects Approaching Mech Input Date")

            deadline_df = dash_df[
                dash_df["Approaching_Deadline"]
            ][[
                "Project_name",
                "Unit",
                "Resource_Name",
                "Plan_date",
                "Days_Left",
                "Priority",
                "Status"
            ]].sort_values("Days_Left")

            deadline_df = rename_plan_date_for_display(deadline_df)

            if deadline_df.empty:
                st.success("No projects approaching mech input date.")
            else:
                st.dataframe(
                    deadline_df,
                    use_container_width=True,
                    height=280
                )

        with col2:
            st.markdown("### Overdue Mech Input Items")

            overdue_df = dash_df[
                dash_df["Is_Overdue"]
            ][[
                "Project_name",
                "Unit",
                "Resource_Name",
                "Plan_date",
                "Days_Left",
                "Priority",
                "Status"
            ]].sort_values("Days_Left")

            overdue_df = rename_plan_date_for_display(overdue_df)

            if overdue_df.empty:
                st.success("No overdue mech input items.")
            else:
                st.dataframe(
                    overdue_df,
                    use_container_width=True,
                    height=280
                )

        st.markdown("---")

        col3, col4 = st.columns(2)

        with col3:
            st.markdown("### Workload by Employee")

            employee_workload = (
                dash_df[dash_df["Status"] != "Completed"]
                .groupby("Resource_Name")
                .size()
                .reset_index(name="Pending_Tasks")
                .sort_values("Pending_Tasks", ascending=False)
            )

            if employee_workload.empty:
                st.info("No pending workload found.")
            else:
                st.bar_chart(
                    employee_workload,
                    x="Resource_Name",
                    y="Pending_Tasks"
                )

                st.dataframe(
                    employee_workload,
                    use_container_width=True,
                    height=220
                )

        with col4:
            st.markdown("### Project Level Metrics")

            project_metrics = (
                dash_df
                .groupby("Project_name")
                .agg(
                    Total_Tasks=("Project_name", "count"),
                    Completed_Tasks=(
                        "Status",
                        lambda x: (x == "Completed").sum()
                    ),
                    Pending_Tasks=(
                        "Status",
                        lambda x: (x != "Completed").sum()
                    ),
                    Avg_Priority=(
                        "Priority",
                        lambda x: round(x.mean(), 1)
                    ),
                    Overdue_Tasks=("Is_Overdue", "sum")
                )
                .reset_index()
            )

            project_metrics["Completion_%"] = round(
                (
                    project_metrics["Completed_Tasks"] /
                    project_metrics["Total_Tasks"]
                ) * 100,
                1
            )

            st.dataframe(
                project_metrics,
                use_container_width=True,
                height=350
            )

        st.markdown("---")

        col5, col6 = st.columns(2)

        with col5:
            st.markdown("### Task Status Distribution")

            status_summary = (
                dash_df["Status"]
                .value_counts()
                .reset_index()
            )

            status_summary.columns = ["Status", "Count"]

            st.bar_chart(
                status_summary,
                x="Status",
                y="Count"
            )

        with col6:
            st.markdown("### Work Type Distribution")

            work_type_summary = (
                dash_df["Work_Type"]
                .value_counts()
                .reset_index()
            )

            work_type_summary.columns = [
                "Work_Type",
                "Count"
            ]

            st.bar_chart(
                work_type_summary,
                x="Work_Type",
                y="Count"
            )

        st.markdown("---")

        st.markdown("### High Priority Pending Work")

        high_priority_df = dash_df[
            (dash_df["Status"] != "Completed") &
            (dash_df["Priority"].isin([1, 2]))
        ][[
            "Project_name",
            "Unit",
            "Resource_Name",
            "Plan_date",
            "Priority",
            "Status",
            "Comments"
        ]]

        high_priority_df = rename_plan_date_for_display(
            high_priority_df
        )

        if high_priority_df.empty:
            st.success("No high-priority pending work.")
        else:
            st.dataframe(
                high_priority_df,
                use_container_width=True,
                height=300
            )
