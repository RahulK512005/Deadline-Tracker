"""Notification settings, testing, and scheduled reminder preview view."""
import streamlit as st
from datetime import date
from services.deadline_service import DeadlineService
from services.digest_service import DigestService
from services.notification_service import NotificationService
from database.database import get_setting, set_setting
from utils.date_utils import calculate_reminder_dates, format_display_date


def render_notifications_page(service: DeadlineService):
    st.markdown(
        """
        <div style="margin-bottom: 24px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #f8fafc;">Notifications & Reminders</h1>
            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 1.05rem;">
                Configure automated alerts via Telegram and Email to never miss a submission.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Load persistent settings
    from services.notification_service import get_secret_or_env
    saved_channel = get_setting("notif_channel", "WhatsApp")
    if saved_channel == "Both":
        saved_channel = "All"
    saved_freq = get_setting("digest_freq", "Daily")
    saved_r7 = get_setting("remind_7d", "true") == "true"
    saved_r3 = get_setting("remind_3d", "true") == "true"
    saved_r1 = get_setting("remind_1d", "true") == "true"
    saved_rdue = get_setting("remind_due", "true") == "true"

    saved_tg_token = get_setting("telegram_bot_token", "")
    saved_tg_chat = get_setting("telegram_chat_id", "")
    saved_email_host = get_setting("email_host", "smtp.gmail.com")
    saved_email_port = get_setting("email_port", "587")
    saved_email_user = get_setting("email_user", "")
    saved_email_pass = get_setting("email_pass", "")
    saved_email_to = get_setting("email_to", "")

    # Twilio persistent credentials
    saved_twilio_sid = get_setting("twilio_account_sid", "") or get_secret_or_env("TWILIO_ACCOUNT_SID", "")
    saved_twilio_token = get_setting("twilio_auth_token", "") or get_secret_or_env("TWILIO_AUTH_TOKEN", "")
    saved_twilio_from = get_setting("twilio_from_number", "") or get_secret_or_env("TWILIO_PHONE_NUMBER", "+14155238886")
    saved_twilio_to = get_setting("twilio_to_number", "") or get_secret_or_env("TWILIO_TO_NUMBER", "+918310905835")

    tab_config, tab_test, tab_schedule = st.tabs(["⚙️ Notification Preferences", "🧪 Test Channels", "⏰ Reminder Schedule"])

    with tab_config:
        st.markdown("##### Delivery Channels & Frequency")
        c_ch, c_fr = st.columns(2)
        with c_ch:
            channel_opts = ["WhatsApp", "Telegram", "Email", "SMS", "All", "None"]
            ch_idx = channel_opts.index(saved_channel) if saved_channel in channel_opts else 0
            channel = st.selectbox("Preferred Channel", channel_opts, index=ch_idx)
        with c_fr:
            freq_opts = ["Daily", "Weekly"]
            fr_idx = freq_opts.index(saved_freq) if saved_freq in freq_opts else 0
            frequency = st.selectbox("Digest Frequency", freq_opts, index=fr_idx)

        st.markdown("##### Reminder Timing Triggers")
        r_c1, r_c2, r_c3, r_c4 = st.columns(4)
        with r_c1:
            r7 = st.checkbox("7 days before", value=saved_r7)
        with r_c2:
            r3 = st.checkbox("3 days before", value=saved_r3)
        with r_c3:
            r1 = st.checkbox("1 day before", value=saved_r1)
        with r_c4:
            rdue = st.checkbox("On due date", value=saved_rdue)

        st.markdown("##### 💬 Twilio (WhatsApp & SMS) Configuration")
        st.caption("Deliver automated deadline alerts directly to your WhatsApp or phone via Twilio API.")
        c_tw1, c_tw2 = st.columns(2)
        with c_tw1:
            tw_sid = st.text_input("Twilio Account SID", value=saved_twilio_sid, type="password", placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        with c_tw2:
            tw_token = st.text_input("Twilio Auth Token", value=saved_twilio_token, type="password", placeholder="your_auth_token")

        c_tw3, c_tw4 = st.columns(2)
        with c_tw3:
            tw_from = st.text_input("Twilio Sender Number", value=saved_twilio_from, placeholder="+14155238886 (WhatsApp Sandbox) or your Twilio Number")
        with c_tw4:
            tw_to = st.text_input("Recipient WhatsApp / Phone Number", value=saved_twilio_to, placeholder="+918310905835")

        st.info("💡 **Twilio WhatsApp Sandbox Setup**: If using the Twilio WhatsApp Sandbox, send your sandbox activation text (e.g. `join <word>`) from WhatsApp (+91 83109 05835) to **+1 415 523 8886** before dispatching messages.")

        st.markdown("##### ✈️ Telegram Bot Configuration")
        c_tg1, c_tg2 = st.columns(2)
        with c_tg1:
            tg_token = st.text_input("Telegram Bot Token", value=saved_tg_token, type="password", placeholder="123456789:ABCdefGhIJKlmNoPQRstuVWxYZ")
        with c_tg2:
            tg_chat = st.text_input("Telegram Chat ID", value=saved_tg_chat, placeholder="e.g. 123456789 or @yourchannel")

        st.markdown("##### 📧 Email SMTP Configuration")
        c_em1, c_em2, c_em3 = st.columns(3)
        with c_em1:
            em_host = st.text_input("SMTP Host", value=saved_email_host)
        with c_em2:
            em_port = st.text_input("SMTP Port", value=saved_email_port)
        with c_em3:
            em_to = st.text_input("Recipient Email", value=saved_email_to, placeholder="student@university.edu")

        c_em4, c_em5 = st.columns(2)
        with c_em4:
            em_user = st.text_input("SMTP Username / Sender", value=saved_email_user)
        with c_em5:
            em_pass = st.text_input("SMTP App Password", value=saved_email_pass, type="password")

        if st.button("💾 Save Preferences", type="primary"):
            set_setting("notif_channel", channel)
            set_setting("digest_freq", frequency)
            set_setting("remind_7d", "true" if r7 else "false")
            set_setting("remind_3d", "true" if r3 else "false")
            set_setting("remind_1d", "true" if r1 else "false")
            set_setting("remind_due", "true" if rdue else "false")

            set_setting("twilio_account_sid", tw_sid)
            set_setting("twilio_auth_token", tw_token)
            set_setting("twilio_from_number", tw_from)
            set_setting("twilio_to_number", tw_to)

            set_setting("telegram_bot_token", tg_token)
            set_setting("telegram_chat_id", tg_chat)
            set_setting("email_host", em_host)
            set_setting("email_port", em_port)
            set_setting("email_user", em_user)
            set_setting("email_pass", em_pass)
            set_setting("email_to", em_to)

            st.success("Notification preferences and Twilio settings saved successfully!")
            st.rerun()

    with tab_test:
        st.markdown("##### Test Channel Connections")
        st.caption("Verify your credentials by sending test messages right now.")

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown("###### 💬 WhatsApp Test (Twilio)")
            if st.button("Send Test WhatsApp Message", use_container_width=True):
                notif = NotificationService()
                success, msg = notif.send_whatsapp(
                    "🔔 *Deadline Tracker WhatsApp Alert*\n\nYour Twilio WhatsApp integration is operational and ready to send deadline reminders!",
                    to_number=tw_to or None,
                    from_number=tw_from or None,
                    account_sid=tw_sid or None,
                    auth_token=tw_token or None
                )
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

            st.markdown("###### 📨 SMS Test (Twilio)")
            if st.button("Send Test SMS", use_container_width=True):
                notif = NotificationService()
                success, msg = notif.send_sms(
                    "Deadline Tracker: Test SMS notification. Your Twilio SMS integration is working properly!",
                    to_number=tw_to or None,
                    from_number=tw_from or None,
                    account_sid=tw_sid or None,
                    auth_token=tw_token or None
                )
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

        with col_t2:
            st.markdown("###### ✈️ Telegram Test")
            if st.button("Send Test Message via Telegram", use_container_width=True):
                notif = NotificationService()
                success, msg = notif.send_telegram(
                    "🔔 *Deadline Tracker Test Message*\n\nYour Telegram bot is successfully connected and ready to send deadline reminders!",
                    bot_token=tg_token or None,
                    chat_id=tg_chat or None
                )
                if success:
                    st.success("Telegram connected successfully.")
                else:
                    st.error(msg)

            st.markdown("###### 📧 Email Test")
            if st.button("Send Test Email", use_container_width=True):
                notif = NotificationService()
                success, msg = notif.send_email(
                    subject="Deadline Tracker: Test Email Notification",
                    body_text="Hello,\n\nThis is a test notification from your Deadline Tracker application.\nYour email SMTP configuration is functioning properly!",
                    to_email=em_to or None,
                    host=em_host or None,
                    port=int(em_port) if em_port.isdigit() else 587,
                    username=em_user or None,
                    password=em_pass or None,
                )
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

        st.divider()
        st.markdown("###### Dispatch Current Digest On-Demand")
        if st.button("📤 Send Current Academic Digest Now", type="primary"):
            ref = date.today()
            student_name = get_setting("student_name", "Student")
            upcoming = service.get_upcoming_deadlines(ref)
            overdue = service.get_overdue_deadlines(ref)
            digest = DigestService.generate_text_digest(upcoming, overdue, student_name, ref)

            notif = NotificationService()
            results = []
            if channel in ("WhatsApp", "All"):
                wa_ok, wa_m = notif.send_whatsapp(
                    digest,
                    to_number=tw_to or None,
                    from_number=tw_from or None,
                    account_sid=tw_sid or None,
                    auth_token=tw_token or None
                )
                results.append(f"WhatsApp: {wa_m}")
            if channel in ("SMS", "All"):
                short_sms = f"Deadline Tracker: You have {len(upcoming)} upcoming and {len(overdue)} overdue deadlines. Visit your dashboard for details."
                sms_ok, sms_m = notif.send_sms(
                    short_sms,
                    to_number=tw_to or None,
                    from_number=tw_from or None,
                    account_sid=tw_sid or None,
                    auth_token=tw_token or None
                )
                results.append(f"SMS: {sms_m}")
            if channel in ("Telegram", "All", "Both"):
                tg_ok, tg_m = notif.send_telegram(digest, bot_token=tg_token or None, chat_id=tg_chat or None)
                results.append(f"Telegram: {tg_m}")
            if channel in ("Email", "All", "Both"):
                em_ok, em_m = notif.send_email(
                    "📚 Upcoming Deadlines Digest",
                    digest,
                    to_email=em_to or None,
                    host=em_host or None,
                    port=int(em_port) if em_port.isdigit() else 587,
                    username=em_user or None,
                    password=em_pass or None
                )
                results.append(f"Email: {em_m}")

            for r in results:
                st.info(r)

    with tab_schedule:
        st.markdown("##### Calculated Reminder Trigger Dates")
        st.caption("Here is the exact schedule when alerts are computed for all active deadlines:")

        ref = date.today()
        upcoming = service.get_upcoming_deadlines(ref)
        if not upcoming:
            st.info("No active deadlines to schedule.")
        else:
            schedule_table = []
            for d in upcoming:
                reminders = calculate_reminder_dates(d.deadline_date)
                schedule_table.append({
                    "Title": d.title,
                    "Subject": d.subject,
                    "Due Date": format_display_date(d.deadline_date),
                    "7-Day Alert": format_display_date(reminders["7_days_before"]),
                    "3-Day Alert": format_display_date(reminders["3_days_before"]),
                    "1-Day Alert": format_display_date(reminders["1_day_before"]),
                })
            st.dataframe(schedule_table, use_container_width=True, hide_index=True)
