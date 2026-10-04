"""All Deadlines view: search, filters, manual deadline creation, and management."""
import streamlit as st
from datetime import date
from models.deadline import Deadline, DeadlineType, UrgencyLevel
from services.deadline_service import DeadlineService
from utils.date_utils import format_display_date
from views.dashboard_view import render_deadline_card


def render_all_deadlines_page(service: DeadlineService):
    st.markdown(
        """
        <div style="margin-bottom: 24px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #f8fafc;">All Deadlines</h1>
            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 1.05rem;">
                Search, filter, and manage all your academic commitments.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Section 14: Manual Deadline Creation
    with st.expander("➕ Add Deadline Manually", expanded=False):
        st.markdown("##### New Academic Deadline")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            m_title = st.text_input("Title *", placeholder="e.g. DBMS Assignment 2", key="man_title")
            m_subject = st.text_input("Subject *", placeholder="e.g. Database Systems", key="man_subj")
            m_type = st.selectbox("Type", [t.value for t in DeadlineType], index=0, key="man_type")
        with col_m2:
            m_date = st.date_input("Deadline Date *", value=date.today(), key="man_date")
            m_time = st.text_input("Deadline Time (Optional, e.g. 23:59)", placeholder="23:59", key="man_time")
            m_desc = st.text_area("Description / Notes", placeholder="Submission instructions or topics...", key="man_desc")

        date_str = m_date.strftime("%Y-%m-%d")

        # Duplicate checking before adding
        if m_title and m_subject:
            dups = service.find_possible_duplicates(m_title, m_subject, date_str)
            if dups:
                st.warning(f"⚠️ **Duplicate detected!** Found '{dups[0].title}' for subject '{dups[0].subject}' on {dups[0].deadline_date}.")

        if st.button("Add Deadline", type="primary", key="btn_manual_add"):
            if not m_title.strip():
                st.error("Title is required.")
            else:
                success, err, dl = service.create_deadline({
                    "title": m_title,
                    "subject": m_subject or "General",
                    "type": m_type,
                    "deadline_date": date_str,
                    "deadline_time": m_time.strip() if m_time.strip() else None,
                    "description": m_desc.strip(),
                    "confidence": "high",
                    "source_document": "manual_entry",
                })
                if success:
                    st.toast(f"Deadline '{m_title}' added successfully!", icon="✅")
                    st.success(f"Added '{m_title}'!")
                    st.rerun()
                else:
                    st.error(err)

    st.write("")

    # Search & Filters Bar
    f_col1, f_col2, f_col3, f_col4 = st.columns([3, 2, 2, 1.5])
    with f_col1:
        search_query = st.text_input("🔍 Search", placeholder="Search by title, subject, or keywords...", label_visibility="collapsed")
    with f_col2:
        distinct_subjects = service.get_distinct_subjects()
        subj_options = ["All Subjects"] + distinct_subjects
        selected_subj = st.selectbox("Subject Filter", subj_options, label_visibility="collapsed")
    with f_col3:
        status_options = ["All Deadlines", "Pending Only", "Completed Only", "Overdue Only"]
        selected_status = st.selectbox("Status Filter", status_options, label_visibility="collapsed")
    with f_col4:
        sort_choice = st.selectbox("Sort", ["Date (Asc)", "Date (Desc)"], label_visibility="collapsed")

    sort_order = "ASC" if "Asc" in sort_choice else "DESC"

    # Query items
    all_items = service.get_all_deadlines(
        include_completed=(selected_status != "Pending Only"),
        subject=selected_subj,
        search_query=search_query,
        sort_order=sort_order
    )

    # Apply client status filter if needed
    ref = date.today()
    if selected_status == "Completed Only":
        all_items = [d for d in all_items if d.completed]
    elif selected_status == "Overdue Only":
        all_items = [d for d in all_items if d.is_overdue(ref)]
    elif selected_status == "Pending Only":
        all_items = [d for d in all_items if not d.completed]

    st.caption(f"Showing **{len(all_items)}** deadlines")

    if not all_items:
        st.info("No deadlines match your current search and filter criteria.")
        return

    # View Mode Toggle: Cards or Table
    view_mode = st.radio("View as:", ["Cards", "Table"], horizontal=True, label_visibility="collapsed")

    if view_mode == "Cards":
        for dl in all_items:
            render_deadline_card(dl, service, key_prefix="all")
    else:
        # Table view
        table_rows = []
        for dl in all_items:
            urg = dl.get_urgency(ref)
            table_rows.append({
                "Status": "✓ Completed" if dl.completed else urg.value,
                "Title": dl.title,
                "Subject": dl.subject,
                "Type": dl.type,
                "Date": format_display_date(dl.deadline_date),
                "Time": dl.deadline_time or "—",
                "Days Left": dl.days_remaining(ref) if not dl.completed else "Done",
                "Source": dl.source_document or "manual",
            })
        st.dataframe(table_rows, use_container_width=True, hide_index=True)
