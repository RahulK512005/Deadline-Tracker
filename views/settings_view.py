"""Settings and AI Assistant view."""
import streamlit as st
from datetime import date
from services.deadline_service import DeadlineService
from services.gemini_service import GeminiService
from database.database import get_setting, set_setting, execute_query


def render_settings_page(deadline_service: DeadlineService, gemini_service: GeminiService):
    st.markdown(
        """
        <div style="margin-bottom: 24px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #f8fafc;">Settings & AI Assistant</h1>
            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 1.05rem;">
                Manage student profile, Gemini API access, and query your academic planner.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab_profile, tab_assistant, tab_db = st.tabs(["👤 Profile & AI Keys", "🤖 Ask Deadline Tracker", "💾 Database & Demo"])

    with tab_profile:
        st.markdown("##### Student Profile")
        cur_name = get_setting("student_name", "Alex")
        new_name = st.text_input("Student Name", value=cur_name, help="Used for personalized greetings and digests")

        st.markdown("##### Gemini API Key")
        cur_key = get_setting("gemini_api_key", "")
        # Mask if present
        new_key = st.text_input("Gemini API Key", value=cur_key, type="password", help="Obtain a key at https://aistudio.google.com/")

        c_save, c_test = st.columns([2, 3])
        with c_save:
            if st.button("Save Profile & Keys", type="primary"):
                set_setting("student_name", new_name)
                set_setting("gemini_api_key", new_key)
                st.success("Settings saved successfully!")
                st.rerun()

        with c_test:
            if st.button("Test Gemini Connection"):
                test_gemini = GeminiService(api_key=new_key or None)
                ok, msg = test_gemini.test_connection()
                if ok:
                    st.success(f"✅ {msg}")
                else:
                    st.error(f"❌ {msg}")

    with tab_assistant:
        st.markdown("##### 🤖 Ask Deadline Tracker (AI Academic Assistant)")
        st.caption("Ask questions about your deadlines in natural language. Answers are strictly grounded in your database records.")

        example_queries = [
            "What deadlines do I have this week?",
            "When is my next assignment?",
            "Show me all DBMS deadlines.",
            "How many deadlines do I have this month?",
        ]

        st.markdown("**Suggested questions:**")
        cols = st.columns(len(example_queries))
        chosen_query = None
        for i, q in enumerate(example_queries):
            with cols[i]:
                if st.button(q, key=f"sugg_{i}"):
                    chosen_query = q

        user_query = st.text_input(
            "Your Question:",
            value=chosen_query or "",
            placeholder="e.g. When is my next exam?",
            key="user_assistant_input"
        )

        if st.button("Ask Assistant", type="primary", key="btn_ask_assistant"):
            if not user_query.strip():
                st.warning("Please enter a question.")
            else:
                # Gather actual database context
                all_dl = deadline_service.get_all_deadlines(include_completed=True)
                ref = date.today()

                if not all_dl:
                    st.info("You do not have any deadlines recorded in your tracker yet.")
                else:
                    # Construct strict context
                    context_lines = [f"Today's date is {ref.strftime('%Y-%m-%d')} ({ref.strftime('%A')})."]
                    for d in all_dl:
                        urg = d.get_urgency(ref)
                        context_lines.append(
                            f"- Title: {d.title} | Subject: {d.subject} | Type: {d.type} | "
                            f"Date: {d.deadline_date} (Time: {d.deadline_time or 'unspecified'}) | "
                            f"Urgency: {urg.value} | Completed: {'Yes' if d.completed else 'No'} | "
                            f"Notes: {d.description or 'None'}"
                        )
                    context_str = "\n".join(context_lines)

                    with st.spinner("Consulting your academic records..."):
                        active_key = get_setting("gemini_api_key", "") or None
                        active_gemini = GeminiService(api_key=active_key)
                        success, answer = active_gemini.answer_assistant_query(user_query, context_str)

                    if success:
                        st.markdown(
                            f"""
                            <div style="background-color: #1e293b; border-radius: 8px; padding: 18px; margin-top: 14px; border-left: 4px solid #38bdf8;">
                                <div style="font-weight: 700; color: #38bdf8; margin-bottom: 8px;">Answer:</div>
                                <div style="color: #f8fafc; line-height: 1.6;">{answer}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.error(answer)

    with tab_db:
        st.markdown("##### Persistent Database Operations")
        stats = deadline_service.get_statistics()
        st.markdown(
            f"""
            - **Total Upcoming Deadlines:** {stats['total_upcoming']}
            - **Due Today:** {stats['due_today']}
            - **Due This Week:** {stats['due_this_week']}
            - **Overdue:** {stats['overdue']}
            - **Completed:** {stats['completed']}
            """
        )

        st.write("")
        c_db1, c_db2 = st.columns(2)
        with c_db1:
            if st.button("📦 Load Sample Academic Schedule Data", use_container_width=True):
                # Load demo deadlines aligned with current date
                ref = date.today()
                from datetime import timedelta
                samples = [
                    {"title": "CPU Scheduling Algorithms Simulation", "subject": "Operating Systems", "type": "Assignment", "date": ref.strftime("%Y-%m-%d"), "time": "23:59", "description": "Implement FCFS, SJF, and Round Robin simulations in C/Python."},
                    {"title": "Online Quiz 2 - Data Link Layer", "subject": "Computer Networks", "type": "Quiz", "date": (ref + timedelta(days=1)).strftime("%Y-%m-%d"), "time": "14:00", "description": "Covers framing, error detection CRC, and subnet calculations."},
                    {"title": "SQL Queries & Normalization Lab Record", "subject": "DBMS", "type": "Lab", "date": (ref + timedelta(days=4)).strftime("%Y-%m-%d"), "time": "17:00", "description": "Complete exercises 4 to 8 and submit physical record booklet."},
                    {"title": "Architecture & SRS Document Submission", "subject": "Software Engg", "type": "Project", "date": (ref + timedelta(days=6)).strftime("%Y-%m-%d"), "time": "23:59", "description": "Phase 1 group project deliverable with UML diagrams."},
                    {"title": "Mid-Term Examination (Modules 1-3)", "subject": "AI & ML", "type": "Exam", "date": (ref + timedelta(days=12)).strftime("%Y-%m-%d"), "time": "10:00", "description": "Hall ticket required. Closed-book exam in Hall B."},
                    {"title": "Microservices Deployment Seminar", "subject": "Cloud Computing", "type": "Presentation", "date": (ref + timedelta(days=19)).strftime("%Y-%m-%d"), "time": "11:30", "description": "10-minute presentation + 5-minute Q&A with slides."},
                ]
                added = 0
                for s in samples:
                    ok, _, _ = deadline_service.create_deadline(s)
                    if ok:
                        added += 1
                st.toast(f"Loaded {added} sample deadlines!", icon="📦")
                st.success(f"Loaded {added} sample deadlines. Head over to Dashboard to view them!")
                st.rerun()

        with c_db2:
            if st.button("⚠️ Clear All Deadlines", use_container_width=True):
                execute_query("DELETE FROM deadlines;")
                st.toast("Database cleared", icon="🗑️")
                st.success("All deadlines deleted from database.")
                st.rerun()
