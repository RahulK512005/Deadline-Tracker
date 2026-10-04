"""Calendar view grouping deadlines by month and date."""
import streamlit as st
from datetime import datetime, date
from collections import defaultdict
from services.deadline_service import DeadlineService
from utils.date_utils import format_display_date
from models.deadline import UrgencyLevel


def render_calendar_page(service: DeadlineService):
    st.markdown(
        """
        <div style="margin-bottom: 24px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #f8fafc;">Calendar View</h1>
            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 1.05rem;">
                Timeline of upcoming and past academic milestones organized chronologically.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_flt1, col_flt2 = st.columns([3, 1])
    with col_flt1:
        include_completed = st.checkbox("Include completed deadlines in calendar", value=True)

    deadlines = service.get_all_deadlines(include_completed=include_completed, sort_order="ASC")

    if not deadlines:
        st.info("No deadlines scheduled in your calendar.")
        return

    # Group by Month-Year, then by Date
    calendar_tree = defaultdict(lambda: defaultdict(list))
    for dl in deadlines:
        dt = dl.get_parsed_date()
        if dt:
            month_key = dt.strftime("%B %Y")
            date_key = dt.strftime("%Y-%m-%d")
            calendar_tree[month_key][date_key].append(dl)

    ref = date.today()

    for month_name, dates_dict in calendar_tree.items():
        st.markdown(
            f"""
            <div style="background-color: #0f172a; padding: 10px 16px; border-radius: 8px; margin: 20px 0 12px 0; border-left: 4px solid #3b82f6;">
                <h3 style="margin: 0; color: #60a5fa; font-size: 1.3rem;">🗓️ {month_name}</h3>
            </div>
            """,
            unsafe_allow_html=True
        )

        for date_str, items in sorted(dates_dict.items()):
            display_date = format_display_date(date_str, include_weekday=True)
            try:
                dt_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
                diff = (dt_obj - ref).days
                if diff == 0:
                    rel_label = "<span style='color: #f87171; font-weight: 700;'>(Today)</span>"
                elif diff == 1:
                    rel_label = "<span style='color: #fb923c;'>(Tomorrow)</span>"
                elif diff < 0:
                    rel_label = f"<span style='color: #94a3b8;'>({abs(diff)}d ago)</span>"
                else:
                    rel_label = f"<span style='color: #94a3b8;'>({diff}d away)</span>"
            except Exception:
                rel_label = ""

            st.markdown(f"**{display_date}** {rel_label}", unsafe_allow_html=True)

            for itm in items:
                urg = itm.get_urgency(ref)
                type_color = {
                    "Assignment": "#38bdf8",
                    "Exam": "#f87171",
                    "Quiz": "#fb923c",
                    "Project": "#a855f7",
                    "Lab": "#34d399",
                }.get(itm.type, "#94a3b8")

                done_decor = "text-decoration: line-through; opacity: 0.6;" if itm.completed else ""

                st.markdown(
                    f"""
                    <div style="background-color: #1e293b; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px; margin-left: 18px; border: 1px solid rgba(255,255,255,0.06); {done_decor}">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="background-color: rgba(255,255,255,0.08); color: {type_color}; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-right: 8px;">
                                    {itm.type}
                                </span>
                                <strong style="color: #f8fafc;">{itm.title}</strong>
                                <span style="color: #94a3b8; font-size: 0.85rem; margin-left: 8px;">[{itm.subject}]</span>
                            </div>
                            <span style="font-size: 0.8rem; color: #cbd5e1;">
                                {'✓ Done' if itm.completed else (f'⏰ {itm.deadline_time}' if itm.deadline_time else '')}
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        st.write("")
