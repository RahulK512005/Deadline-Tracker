"""Views package for Deadline Tracker."""
from views.dashboard_view import render_dashboard
from views.extract_view import render_extract_page
from views.all_deadlines_view import render_all_deadlines_page
from views.calendar_view import render_calendar_page
from views.notifications_view import render_notifications_page
from views.settings_view import render_settings_page

__all__ = [
    "render_dashboard",
    "render_extract_page",
    "render_all_deadlines_page",
    "render_calendar_page",
    "render_notifications_page",
    "render_settings_page",
]
