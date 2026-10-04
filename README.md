# 📚 Deadline Tracker

> **AI-Powered Academic Productivity Application for Students**  
> Convert syllabi, timetables, assignment sheets, and exam circulars into structured, actionable deadlines with Google Gemini multimodal AI.

---

## 1. The Problem

Students manage dense, scattered schedules across multiple courses and platforms:
- Course syllabi in PDF format
- Exam timetables posted on physical notice boards or circulars
- Assignment deadlines announced across university portals and WhatsApp chats
- Lab submission sheets and project milestones

Manually transcribing these dates into calendars or reminder apps is tedious, error-prone, and easily forgotten—leading to missed submissions and academic penalties.

---

## 2. The Solution

**Deadline Tracker** solves this by leveraging **Google Gemini multimodal AI**:
1. Students photograph or upload any academic document (PNG, JPG, PDF).
2. Gemini extracts every academic deadline, exam, quiz, and submission with high precision.
3. The extracted data is parsed into strict structured JSON and validated against date formats.
4. The student reviews, edits, and approves the extracted deadlines in an interactive review screen.
5. Confirmed deadlines are stored in a persistent SQLite database with duplicate detection.
6. The dashboard categorizes milestones by urgency (Overdue, Due Today, Tomorrow, This Week, Upcoming).
7. Concise upcoming deadline digests and reminders are dispatched via **Telegram** and **Email**.

---

## 3. Key Features

- **Multimodal AI Extraction**: Direct visual and document understanding using the official `google-genai` SDK (`gemini-2.5-flash`).
- **Human-in-the-Loop Verification**: Review table with confidence indicators (`High`, `Medium - Please verify date`, `Low`) to guarantee zero silent hallucinations.
- **Dynamic Urgency Dashboard**:
  - ⚠️ **Overdue**: Immediate visibility into past-due deliverables.
  - 🔴 **Due Today**: Items requiring urgent action.
  - 🟠 **Tomorrow**: Preparation for next-day submissions.
  - 🟡 **This Week**: Deadlines within the next 7 days.
  - 🔵 **Upcoming**: Future exams and milestone events.
- **Conflict & Workload Detection**: Automatic warning banner when 4+ deliverables are due within a 3-day window.
- **Duplicate Detection**: Prevents duplicate entries using normalized `title + subject + date` matching, providing options to keep or replace records.
- **Calendar Timeline View**: Chronological breakdown grouped by Month and Date.
- **AI Academic Assistant ("Ask Deadline Tracker")**: Natural language Q&A strictly grounded in the student's real database records.
- **Dual Notification Channels**:
  - **Telegram Bot API**: Direct instant messaging delivery.
  - **Email (SMTP)**: Clean digest formatting delivered to student inbox.
- **Extensible Architecture**: Service abstractions enable plugging in Twilio WhatsApp and PostgreSQL/Supabase without rewriting core business logic.

---

## 4. System Architecture

```
deadline-tracker/
├── app.py                      # Main Streamlit application and layout orchestration
├── requirements.txt            # Production dependencies
├── README.md                   # Complete documentation
├── .gitignore                  # Git ignore rules for secrets and databases
│
├── database/
│   ├── __init__.py
│   └── database.py             # SQLite connection, schema, indexes, and queries
│
├── models/
│   ├── __init__.py
│   └── deadline.py             # Data model, Urgency calculation, and Enums
│
├── prompts/
│   ├── __init__.py
│   └── prompts.py              # Strict Gemini extraction and assistant prompts
│
├── services/
│   ├── __init__.py
│   ├── gemini_service.py       # Google GenAI client, multimodal analysis, and Q&A
│   ├── deadline_service.py     # CRUD, filtering, stats, workload, and duplicate checks
│   ├── notification_service.py # Telegram and SMTP Email delivery abstraction
│   └── digest_service.py       # Plain text and markdown digest generator
│
├── utils/
│   ├── __init__.py
│   ├── date_utils.py           # Robust date parsing, formatting, and reminder offsets
│   └── validators.py           # Sanitization and dictionary validation
│
├── views/
│   ├── __init__.py
│   ├── dashboard_view.py       # Dashboard cards, urgency sections, and quick digest
│   ├── extract_view.py         # Upload/Camera, Gemini extraction, and review screen
│   ├── all_deadlines_view.py   # Search, filters, and manual deadline creation
│   ├── calendar_view.py        # Date-grouped timeline view
│   ├── notifications_view.py   # Channel preferences, test tools, and reminder tables
│   └── settings_view.py        # Profile, Gemini key setup, and AI Assistant
│
├── tests/
│   └── test_deadline_service.py # Pytest test suite for critical business logic
│
└── .streamlit/
    ├── config.toml             # Sleek dark theme configuration
    └── secrets.toml.example    # Template for API keys and notification credentials
```

---

## 5. Local Setup & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.11)
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### Step 1: Clone or Navigate to the Repository
```bash
cd "deadline tracker"
```

### Step 2: Create and Activate a Virtual Environment
**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Secrets
Copy the sample secrets template:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```
Open `.streamlit/secrets.toml` and configure your credentials:
```toml
GEMINI_API_KEY="your-gemini-api-key"

# Optional Telegram notifications
TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
TELEGRAM_CHAT_ID="your-telegram-chat-id"

# Optional Email SMTP notifications
EMAIL_HOST="smtp.gmail.com"
EMAIL_PORT=587
EMAIL_USERNAME="your-email@gmail.com"
EMAIL_PASSWORD="your-app-password"
EMAIL_FROM="your-email@gmail.com"
```
*(Note: You can also configure the Gemini API key and Telegram/Email credentials directly within the application's **Settings** page at runtime).*

### Step 5: Run the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 6. Running the Unit Tests

Execute the automated test suite covering deadline creation, date parsing, urgency calculation, overdue detection, duplicate detection, and digest formatting:

```bash
pytest -v
```

All 13 core tests run against an isolated SQLite test database and mocked Twilio REST services.

---

## 7. Scheduled Reminders & Multi-Channel Dispatch

Streamlit runs on a reactive, request-driven loop. For production scheduled reminders:
1. **Calculation Layer**: The application includes `calculate_reminder_dates(deadline_date)` in `utils/date_utils.py` and a dedicated **Reminder Schedule** view calculating:
   - 7 days before due date
   - 3 days before due date
   - 1 day before due date
   - On the due date
2. **Background Dispatch**: In a production deployment, a lightweight scheduled runner (such as GitHub Actions cron, AWS Lambda, or a simple systemd / cron script) invokes:
   ```python
   from services.deadline_service import DeadlineService
   from services.digest_service import DigestService
   from services.notification_service import NotificationService

   service = DeadlineService()
   upcoming = service.get_upcoming_deadlines()
   overdue = service.get_overdue_deadlines()
   digest = DigestService.generate_text_digest(upcoming, overdue)

   notif = NotificationService()
   # Send via WhatsApp (Twilio)
   notif.send_whatsapp(digest, to_number="+918310905835")
   # Or Telegram / Email / SMS
   notif.send_telegram(digest)
   ```

---

## 8. Deployment to Streamlit Community Cloud

1. Push your repository to GitHub.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **"New App"** and select your repository and branch (`app.py` as entry point).
4. In the **Secrets** section under Advanced Settings, paste the content of your `.streamlit/secrets.toml`.
5. Click **Deploy**.

---

## 9. Future Roadmap

- 📅 **Two-Way Google Calendar Sync**: Export deadlines as `.ics` and OAuth sync with Google Calendar.
- 🗄️ **Supabase / PostgreSQL**: Seamlessly swap SQLite with hosted PostgreSQL using SQLAlchemy.
- 🔄 **Recurring Deadlines**: Support for weekly lab submissions and recurring tutorials.
- 🔐 **Multi-Student Authentication**: Student login with personalized schedules and course enrollments.

