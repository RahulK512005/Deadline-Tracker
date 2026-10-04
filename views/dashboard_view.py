"""Dashboard view displaying greeting, workload alerts, statistics, and urgency sections."""
import streamlit as st
from datetime import date
from models.deadline import Deadline, UrgencyLevel, DeadlineType
from services.deadline_service import DeadlineService
from services.digest_service import DigestService
from services.notification_service import NotificationService
from utils.date_utils import format_display_date, get_time_of_day_greeting


def render_deadline_card(dl: Deadline, service: DeadlineService, key_prefix: str = "dash"):
    """Render a single interactive deadline card."""
    ref = date.today()
    urgency = dl.get_urgency(ref)
    days = dl.days_remaining(ref)

    # Urgency badge color mapping
    badge_colors = {
        UrgencyLevel.OVERDUE: ("#ef4444", "#450a0a", "⚠️ Overdue"),
        UrgencyLevel.DUE_TODAY: ("#f87171", "#7f1d1d", "🔴 Due Today"),
        UrgencyLevel.TOMORROW: ("#fb923c", "#7c2d12", "🟠 Tomorrow"),
        UrgencyLevel.THIS_WEEK: ("#facc15", "#713f12", "🟡 This Week"),
        UrgencyLevel.UPCOMING: ("#60a5fa", "#1e3a8a", "🔵 Upcoming"),
        UrgencyLevel.COMPLETED: ("#4ade80", "#14532d", "✓ Completed"),
    }
    border_color, bg_badge, label = badge_colors.get(urgency, ("#94a3b8", "#1e293b", urgency.value))

    # Days remaining label
    if dl.completed:
        status_label = "Completed"
    elif days < 0:
        status_label = f"{abs(days)} day{'s' if abs(days) > 1 else ''} overdue"
    elif days == 0:
        status_label = "Due Today"
    elif days == 1:
        status_label = "Due Tomorrow"
    else:
        status_label = f"{days} days remaining"

    with st.container():
        st.markdown(
            f"""
            <div style="background-color: #1e293b; border-left: 4px solid {border_color}; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.2);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <span style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8;">{dl.subject}</span>
                        <h4 style="margin: 2px 0 6px 0; color: #f8fafc; font-size: 1.1rem;">{dl.title}</h4>
                    </div>
                    <span style="background-color: {bg_badge}; color: #f8fafc; padding: 3px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; border: 1px solid {border_color};">
                        {label}
                    </span>
                </div>
                <div style="display: flex; flex-wrap: wrap; gap: 14px; font-size: 0.85rem; color: #cbd5e1; margin-top: 6px;">
                    <div>📅 <strong>Due:</strong> {format_display_date(dl.deadline_date, include_weekday=True)} {f'at {dl.deadline_time}' if dl.deadline_time else ''}</div>
                    <div>🏷️ <strong>Type:</strong> {dl.type}</div>
                    <div>⏳ <strong>Status:</strong> {status_label}</div>
                    {f'<div style="color: #fbbf24;">🔍 AI Confidence: {dl.confidence.capitalize()}</div>' if dl.confidence != 'high' else ''}
                </div>
                {f'<div style="margin-top: 8px; font-size: 0.85rem; color: #94a3b8; line-height: 1.4;">{dl.description}</div>' if dl.description else ''}
            </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns([2, 1.2, 1.2, 5])
        with col1:
            if dl.completed:
                if st.button("↩️ Reopen", key=f"reopen_{key_prefix}_{dl.id}", help="Mark as incomplete"):
                    service.mark_completed(dl.id, False)
                    st.rerun()
            else:
                if st.button("✓ Complete", key=f"comp_{key_prefix}_{dl.id}", help="Mark as completed"):
                    service.mark_completed(dl.id, True)
                    st.rerun()
        with col2:
            with st.popover("✏️ Edit"):
                render_edit_form(dl, service, f"pop_{key_prefix}_{dl.id}")
        with col3:
            if st.button("🗑️ Delete", key=f"del_{key_prefix}_{dl.id}", help="Delete deadline"):
                service.delete_deadline(dl.id)
                st.toast(f"Deleted '{dl.title}'", icon="🗑️")
                st.rerun()


def render_edit_form(dl: Deadline, service: DeadlineService, key: str):
    """Render edit deadline popover form."""
    st.markdown(f"**Edit Deadline #{dl.id}**")
    new_title = st.text_input("Title", value=dl.title, key=f"edit_title_{key}")
    new_subject = st.text_input("Subject", value=dl.subject, key=f"edit_subj_{key}")

    all_types = [t.value for t in DeadlineType]
    cur_type_idx = all_types.index(dl.type) if dl.type in all_types else 0
    new_type = st.selectbox("Type", all_types, index=cur_type_idx, key=f"edit_type_{key}")

    current_date = dl.get_parsed_date() or date.today()
    new_date = st.date_input("Deadline Date", value=current_date, key=f"edit_date_{key}")
    new_time = st.text_input("Deadline Time (Optional, HH:MM)", value=dl.deadline_time or "", key=f"edit_time_{key}")
    new_desc = st.text_area("Description", value=dl.description or "", key=f"edit_desc_{key}")

    if st.button("Save Changes", key=f"save_edit_{key}", type="primary"):
        date_str = new_date.strftime("%Y-%m-%d")
        success, err, _ = service.update_deadline(dl.id, {
            "title": new_title,
            "subject": new_subject,
            "type": new_type,
            "deadline_date": date_str,
            "deadline_time": new_time if new_time.strip() else None,
            "description": new_desc,
        })
        if success:
            st.toast("Deadline updated successfully!", icon="✅")
            st.rerun()
        else:
            st.error(err)


def render_dashboard(service: DeadlineService, student_name: str = "Student"):
    """Main dashboard rendering function."""
    greeting = get_time_of_day_greeting()
    ref_date = date.today()

    # Header
    st.markdown(
        f"""
        <div style="margin-bottom: 24px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #f8fafc;">{greeting}, {student_name}</h1>
            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 1.05rem;">Stay ahead of your academic deadlines.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Workload Alert Detection (Section 28)
    is_heavy, heavy_count, heavy_items = service.check_heavy_workload(ref_date=ref_date, threshold=4, days_window=3)
    if is_heavy:
        st.warning(
            f"⚠️ **Heavy workload detected!** You have **{heavy_count} deadlines** within the next 3 days. Prioritize your submissions today.",
            icon="⚠️"
        )

    # Statistics Cards (Section 7)
    stats = service.get_statistics(ref_date=ref_date)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div style="background-color: #1e293b; border-radius: 8px; padding: 16px; border: 1px solid rgba(255,255,255,0.08); text-align: center;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em;">TOTAL UPCOMING</div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #38bdf8; margin: 4px 0;">{stats['total_upcoming']}</div>
                <div style="font-size: 0.75rem; color: #64748b;">Pending assignments & exams</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"""
            <div style="background-color: #1e293b; border-radius: 8px; padding: 16px; border: 1px solid rgba(255,255,255,0.08); text-align: center;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em;">DUE TODAY</div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #f87171; margin: 4px 0;">{stats['due_today']}</div>
                <div style="font-size: 0.75rem; color: #64748b;">Needs urgent action</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f"""
            <div style="background-color: #1e293b; border-radius: 8px; padding: 16px; border: 1px solid rgba(255,255,255,0.08); text-align: center;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em;">THIS WEEK</div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #facc15; margin: 4px 0;">{stats['due_this_week']}</div>
                <div style="font-size: 0.75rem; color: #64748b;">Due in next 7 days</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c4:
        st.markdown(
            f"""
            <div style="background-color: #1e293b; border-radius: 8px; padding: 16px; border: 1px solid rgba(255,255,255,0.08); text-align: center;">
                <div style="font-size: 0.75rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em;">COMPLETED</div>
                <div style="font-size: 2.2rem; font-weight: 800; color: #4ade80; margin: 4px 0;">{stats['completed']}</div>
                <div style="font-size: 0.75rem; color: #64748b;">Finished deliverables</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    # Quick Digest Expander / Action Bar
    with st.expander("📬 Quick Deadline Digest Preview"):
        upcoming_items = service.get_upcoming_deadlines(ref_date)
        overdue_items = service.get_overdue_deadlines(ref_date)
        digest_text = DigestService.generate_text_digest(upcoming_items, overdue_items, student_name, ref_date)
        st.code(digest_text, language="markdown")

        c_send1, c_send2 = st.columns(2)
        with c_send1:
            if st.button("📤 Send Digest to Telegram", use_container_width=True):
                notif = NotificationService()
                success, msg = notif.send_telegram(digest_text)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
        with c_send2:
            if st.button("📧 Send Digest to Email", use_container_width=True):
                notif = NotificationService()
                success, msg = notif.send_email("📚 Deadline Tracker Digest", digest_text)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

    st.divider()

    # Urgency Sections (Section 7 & 18)
    overdue_deadlines = service.get_overdue_deadlines(ref_date)
    due_today_deadlines = service.get_due_today(ref_date)
    tomorrow_deadlines = service.get_due_tomorrow(ref_date)
    this_week_deadlines = service.get_due_this_week(ref_date)
    upcoming_deadlines = service.get_due_later(ref_date)

    total_pending = len(overdue_deadlines) + len(due_today_deadlines) + len(tomorrow_deadlines) + len(this_week_deadlines) + len(upcoming_deadlines)

    # Empty State (Section 29)
    if total_pending == 0:
        st.markdown(
            """
            <div style="text-align: center; padding: 48px 20px; background-color: #1e293b; border-radius: 12px; margin-top: 20px;">
                <div style="font-size: 3rem; margin-bottom: 12px;">🎉</div>
                <h3 style="color: #f8fafc; margin-bottom: 8px;">You're all caught up!</h3>
                <p style="color: #94a3b8; max-width: 500px; margin: 0 auto 20px auto;">
                    No pending academic deadlines found. Upload a syllabus, timetable, or assignment sheet to extract your upcoming dates.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # 1. ⚠️ Overdue Deadlines
    if overdue_deadlines:
        st.markdown(f"### ⚠️ Overdue ({len(overdue_deadlines)})")
        for dl in overdue_deadlines:
            render_deadline_card(dl, service, key_prefix="overdue")
        st.write("")

    # 2. 🔴 Due Today
    if due_today_deadlines:
        st.markdown(f"### 🔴 Due Today ({len(due_today_deadlines)})")
        for dl in due_today_deadlines:
            render_deadline_card(dl, service, key_prefix="today")
        st.write("")

    # 3. 🟠 Tomorrow
    if tomorrow_deadlines:
        st.markdown(f"### 🟠 Tomorrow ({len(tomorrow_deadlines)})")
        for dl in tomorrow_deadlines:
            render_deadline_card(dl, service, key_prefix="tomorrow")
        st.write("")

    # 4. 🟡 This Week
    if this_week_deadlines:
        st.markdown(f"### 🟡 This Week ({len(this_week_deadlines)})")
        for dl in this_week_deadlines:
            render_deadline_card(dl, service, key_prefix="this_week")
        st.write("")

    # 5. 🔵 Upcoming
    if upcoming_deadlines:
        st.markdown(f"### 🔵 Upcoming ({len(upcoming_deadlines)})")
        for dl in upcoming_deadlines:
            render_deadline_card(dl, service, key_prefix="upcoming")
