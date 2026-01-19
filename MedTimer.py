import streamlit as st
import sqlite3
import hashlib
from datetime import datetime, date, time, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import tempfile

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Asclepius – MedTimer",
    page_icon="💊",
    layout="wide"
)

# --------------------------------------------------
# DATABASE
# --------------------------------------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    username TEXT UNIQUE,
    password_hash TEXT
)
""")
conn.commit()

# --------------------------------------------------
# AUTH HELPERS
# --------------------------------------------------
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def create_user(name, age, username, password):
    try:
        cur.execute(
            "INSERT INTO users (name, age, username, password_hash) VALUES (?, ?, ?, ?)",
            (name, age, username, hash_pw(password))
        )
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    cur.execute(
        "SELECT name, age FROM users WHERE username=? AND password_hash=?",
        (username, hash_pw(password))
    )
    return cur.fetchone()

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
defaults = {
    "logged": False,
    "user": "",
    "age": 0,
    "meds": [],
    "edit_med": None,
    "page": "Add Medicine"
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ------------------ NEW ---------------------------
# REMINDER TRACKING
# --------------------------------------------------
if "reminded_doses" not in st.session_state:
    st.session_state.reminded_doses = set()

# --------------------------------------------------
# REMINDER ENGINE (NEW)
# --------------------------------------------------
def check_medicine_reminders():
    now = datetime.now()
    WINDOW_SECONDS = 60

    for mi, med in enumerate(st.session_state.meds):
        for di, dose in enumerate(med["doses"]):
            reminder_id = f"{mi}_{di}"
            dose_time = dose["datetime"]

            if (
                not dose["taken"]
                and reminder_id not in st.session_state.reminded_doses
                and abs((dose_time - now).total_seconds()) <= WINDOW_SECONDS
            ):
                st.toast(
                    f"💊 Time to take {med['name']} ({dose_time.strftime('%H:%M')})",
                    icon="⏰"
                )
                st.session_state.reminded_doses.add(reminder_id)

# --------------------------------------------------
# AUTH UI
# --------------------------------------------------
if not st.session_state.logged:
    st.title("💊 Asclepius – MedTimer")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                res = login_user(u, p)
                if res:
                    st.session_state.logged = True
                    st.session_state.user = res[0]
                    st.session_state.age = res[1]
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    with tab2:
        with st.form("signup"):
            n = st.text_input("Full Name")
            a = st.number_input("Age", 1, 120)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Create Account"):
                if create_user(n, a, u, p):
                    st.success("Account created. Please login.")
                else:
                    st.error("Username already exists")

    st.stop()

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown(f"### 👤 Logged in as **{st.session_state.user}**")

# --------------------------------------------------
# ADD / EDIT MEDICINE
# --------------------------------------------------
if st.session_state.page == "Add Medicine":
    st.title("➕ Add / ✏️ Edit Medicine")

    edit_mode = st.session_state.edit_med is not None
    med = st.session_state.meds[st.session_state.edit_med] if edit_mode else None

    times_per_day = st.number_input(
        "Times per Day",
        1, 5,
        value=med["times_per_day"] if edit_mode else 1
    )

    with st.form("medicine_form"):
        name = st.text_input("Medicine Name", value=med["name"] if edit_mode else "")
        start_date = st.date_input("Start Date", value=med["start"] if edit_mode else date.today())
        days = st.number_input("Number of Days", 1, 365, value=med["days"] if edit_mode else 5)

        st.subheader("⏰ Dose Times")
        times = []
        for i in range(times_per_day):
            default = med["times"][i] if edit_mode and i < len(med["times"]) else time(9, 0)
            times.append(st.time_input(f"Time {i+1}", default))

        if st.form_submit_button("Save Medicine"):
            doses = []
            for d in range(days):
                for t in times:
                    doses.append({
                        "datetime": datetime.combine(start_date + timedelta(days=d), t),
                        "taken": False,
                        "taken_time": None
                    })

            data = {
                "name": name,
                "start": start_date,
                "days": days,
                "times_per_day": times_per_day,
                "times": times,
                "doses": doses
            }

            if edit_mode:
                st.session_state.meds[st.session_state.edit_med] = data
                st.session_state.edit_med = None
            else:
                st.session_state.meds.append(data)

            st.session_state.page = "Today's Checklist"
            st.rerun()

# --------------------------------------------------
# TODAY'S CHECKLIST
# --------------------------------------------------
if st.session_state.page == "Today's Checklist":
    st.title("📋 Today's Checklist")
    now = datetime.now()

    # -------- NEW REMINDER CALL ----------
    check_medicine_reminders()

    for mi, med in enumerate(st.session_state.meds):
        for di, dose in enumerate(med["doses"]):
            if dose["datetime"].date() == date.today():
                st.markdown(f"### 💊 {med['name']}")
                st.write(f"⏰ {dose['datetime'].strftime('%H:%M')}")

                if dose["taken"]:
                    st.success("Taken")
                elif now > dose["datetime"]:
                    st.error("Missed")
                else:
                    st.warning("Upcoming")

                c1, c2, c3 = st.columns(3)

                if c1.button("✅ Taken", key=f"take_{mi}_{di}"):
                    dose["taken"] = True
                    dose["taken_time"] = datetime.now()
                    st.rerun()

                if c2.button("✏️ Edit", key=f"edit_{mi}_{di}"):
                    st.session_state.edit_med = mi
                    st.session_state.page = "Add Medicine"
                    st.rerun()

                if c3.button("🗑 Delete", key=f"del_{mi}_{di}"):
                    med["doses"].pop(di)
                    if not med["doses"]:
                        st.session_state.meds.pop(mi)
                    st.rerun()

                st.divider()

    total = sum(len(m["doses"]) for m in st.session_state.meds)
    taken = sum(d["taken"] for m in st.session_state.meds for d in m["doses"])
    score = int((taken / total) * 100) if total else 0

    st.subheader("📊 Adherence Score")
    st.progress(score)
    st.write(f"{score}%")

    if st.button("📄 Download Adherence Report (PDF)"):
        styles = getSampleStyleSheet()
        elements = [
            Paragraph("<b>Medicine Adherence Report</b>", styles["Title"]),
            Paragraph(
                f"Patient: {st.session_state.user} | Age: {st.session_state.age}<br/>Generated: {date.today()}",
                styles["Normal"]
            )
        ]

        table_data = [["Date", "Day", "Medicine", "Scheduled", "Taken", "Status"]]
        TOL = 10

        for med in st.session_state.meds:
            for d in med["doses"]:
                sched = d["datetime"]
                taken_time = d["taken_time"]

                if taken_time:
                    diff = (taken_time - sched).total_seconds() / 60
                    status = "On Time" if abs(diff) <= TOL else "Late"
                    taken_str = taken_time.strftime("%H:%M")
                else:
                    status = "Not Taken"
                    taken_str = "-"

                table_data.append([
                    sched.strftime("%d-%m-%Y"),
                    sched.strftime("%A"),
                    med["name"],
                    sched.strftime("%H:%M"),
                    taken_str,
                    status
                ])

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("ALIGN", (0,0), (-1,-1), "CENTER")
        ]))

        elements.append(table)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        SimpleDocTemplate(tmp.name, pagesize=A4).build(elements)

        with open(tmp.name, "rb") as f:
            st.download_button("⬇️ Download PDF", f, "medicine_adherence_report.pdf")

    # -------- AUTO REFRESH (NEW) ----------
    st.markdown(
        """
        <script>
        setTimeout(function(){ window.location.reload(); }, 60000);
        </script>
        """,
        unsafe_allow_html=True
    )

# --------------------------------------------------
# BOTTOM NAV
# --------------------------------------------------
st.divider()
c1, c2, c3 = st.columns(3)

if c1.button("➕ Add Medicine"):
    st.session_state.page = "Add Medicine"
    st.rerun()

if c2.button("📋 Today's Checklist"):
    st.session_state.page = "Today's Checklist"
    st.rerun()

if c3.button("🚪 Logout"):
    for k in defaults:
        st.session_state[k] = defaults[k]
    st.rerun()
