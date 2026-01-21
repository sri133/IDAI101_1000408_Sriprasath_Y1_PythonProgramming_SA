import streamlit as st
import sqlite3
import hashlib
import json
import tempfile
from datetime import datetime, date, time, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Asclepius – MedTimer",
    page_icon="💊",
    layout="wide"
)

# --------------------------------------------------
# DATABASE INITIALIZATION
# --------------------------------------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER, username TEXT UNIQUE, password_hash TEXT)")
cur.execute('''CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                med_name TEXT,
                start_date TEXT,
                days INTEGER,
                times TEXT,
                doses_json TEXT)''')
cur.execute("CREATE TABLE IF NOT EXISTS user_settings (username TEXT PRIMARY KEY, language TEXT, bg_color TEXT, font_family TEXT, font_size INTEGER)")

def add_column_if_missing(table, column, definition):
    try:
        cur.execute(f"SELECT {column} FROM {table} LIMIT 1")
    except sqlite3.OperationalError:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        conn.commit()

add_column_if_missing("medicines", "med_name", "TEXT")
add_column_if_missing("medicines", "doses_json", "TEXT")
conn.commit()

# --------------------------------------------------
# HELPERS & AUTH
# --------------------------------------------------
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def create_user(name, age, username, password):
    try:
        cur.execute(
            "INSERT INTO users (name, age, username, password_hash) VALUES (?, ?, ?, ?)",
            (name, age, username, hash_pw(password))
        )
        cur.execute(
            "INSERT INTO user_settings VALUES (?, ?, ?, ?, ?)",
            (username, "English", "#ffffff", "sans-serif", 16)
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
    user_data = cur.fetchone()
    
    if user_data:
        cur.execute("SELECT language, bg_color, font_family, font_size FROM user_settings WHERE username=?", (username,))
        settings = cur.fetchone()
        if settings:
            st.session_state.language = settings[0]
            st.session_state.bg_color = settings[1]
            st.session_state.font_family = settings[2]
            st.session_state.font_size = settings[3]

        cur.execute("SELECT med_name, doses_json FROM medicines WHERE username=?", (username,))
        db_meds = cur.fetchall()
        
        st.session_state.meds = []
        for row in db_meds:
            m_name = row[0]
            m_doses = json.loads(row[1]) 
            for d in m_doses:
                d["datetime"] = datetime.strptime(d["datetime"], "%Y-%m-%d %H:%M:%S")
                if d.get("taken_time"):
                    d["taken_time"] = datetime.strptime(d["taken_time"], "%Y-%m-%d %H:%M:%S")
            st.session_state.meds.append({"name": m_name, "doses": m_doses})
            
    return user_data

def update_credentials(old_u, old_p, new_u, new_p):
    cur.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (old_u, hash_pw(old_p)))
    if cur.fetchone():
        try:
            cur.execute("UPDATE users SET username=?, password_hash=? WHERE username=?", (new_u, hash_pw(new_p), old_u))
            cur.execute("UPDATE user_settings SET username=? WHERE username=?", (new_u, old_u))
            cur.execute("UPDATE medicines SET username=? WHERE username=?", (new_u, old_u))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return "exists"
    return False

# --------------------------------------------------
# SESSION STATE & TRANSLATION
# --------------------------------------------------
defaults = {
    "logged": False,
    "user": "",
    "age": 0,
    "meds": [],
    "edit_med": None,
    "page": "Add Medicine",
    "language": "English",
    "bg_color": "#ffffff",
    "font_family": "sans-serif",
    "font_size": 16,
    "reminded_doses": set()
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

LANG_DATA = {
    "English": {
        "title": "💊 Asclepius – MedTimer", "settings": "⚙️ Settings", "add_med": "➕ Add Medicine", 
        "checklist": "📋 Today's Checklist", "logout": "🚪 Logout", "status_taken": "Taken", 
        "status_now": "Time to Take", "status_missed": "Missed", "status_upcoming": "Upcoming", 
        "save": "Save", "apply": "Apply Theme", "profile": "👤 Profile", "appearance": "🎨 Appearance", 
        "lang_label": "Language", "age_label": "Age", "btn_taken": "Taken", "btn_edit": "Edit", 
        "btn_del": "Delete", "adherence_score": "📊 Adherence Score", "btn_pdf": "Download Adherence Report (PDF)", 
        "no_meds_today": "No medicines scheduled for today.", "btn_download_pdf": "⬇️ Download PDF"
    },
    "Tamil": {
        "title": "💊 அஸ்க்லெபியஸ் – மெட்டடைமர்", "settings": "⚙️ அமைப்புகள்", "add_med": "➕ மருந்து சேர்க்க", 
        "checklist": "📋 இன்றைய பட்டியல்", "logout": "🚪 வெளியேறு", "save": "சேமி", "apply": "தீம் மாற்றுக", 
        "status_taken": "எடுத்துக்கொள்ளப்பட்டது", "status_now": "மருந்து எடுக்கும் நேரம்", "status_missed": "தவறியது", 
        "status_upcoming": "வரவிருப்பது", "profile": "👤 சுயவிவரம்", "appearance": "🎨 தோற்றம்", 
        "lang_label": "மொழி", "age_label": "வயது", "btn_taken": "எடுத்தேன்", "btn_edit": "திருத்து", 
        "btn_del": "நீக்கு", "adherence_score": "📊 பின்பற்றுதல் மதிப்பெண்", "btn_pdf": "PDF அறிக்கை", 
        "no_meds_today": "இன்று மருந்துகள் ஏதுமில்லை.", "btn_download_pdf": "⬇️ PDF பதிவிறக்கம்"
    },
    "Hindi": { "title": "💊 एस्लेपियस - मेडटाइमर", "settings": "⚙️ सेटिंग्स", "add_med": "➕ दवा जोड़ें", "checklist": "📋 आज की सूची", "logout": "🚪 लॉग आउट", "save": "सहेजें", "apply": "थीम लागू करें", "profile": "👤 प्रोफाइल", "appearance": "🎨 उपस्थिति", "lang_label": "भाषा", "age_label": "आयु" },
    "Spanish": { "title": "💊 Asclepius", "settings": "⚙️ Ajustes", "add_med": "➕ Añadir", "checklist": "📋 Lista", "logout": "🚪 Salir", "save": "Guardar", "apply": "Aplicar" },
    "French": { "title": "💊 Asclepius", "settings": "⚙️ Paramètres", "add_med": "➕ Ajouter", "checklist": "📋 Liste", "logout": "🚪 Déconnexion", "save": "Enregistrer", "apply": "Appliquer" },
    "German": { "title": "💊 Asclepius", "settings": "⚙️ Einstellungen", "add_med": "➕ Hinzufügen", "checklist": "📋 Checkliste", "logout": "🚪 Abmelden", "save": "Speichern", "apply": "Anwenden" },
    "Chinese": { "title": "💊 Asclepius", "settings": "⚙️ 设置", "add_med": "➕ 添加药物", "checklist": "📋 今日清单", "logout": "🚪 登出", "save": "保存", "apply": "应用主题" }
}

def t(key):
    return LANG_DATA.get(st.session_state.language, LANG_DATA["English"]).get(key, key)

# --------------------------------------------------
# STYLING & REMINDERS
# --------------------------------------------------
st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {st.session_state.bg_color} !important; }}
    html, body, [class*="css"], .stMarkdown, p, h1, h2, h3, label {{
        font-family: '{st.session_state.font_family}', sans-serif !important;
        font-size: {st.session_state.font_size}px !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

def check_medicine_reminders():
    now = datetime.now()
    for mi, med in enumerate(st.session_state.meds):
        for di, dose in enumerate(med["doses"]):
            rid = f"{mi}_{di}"
            if (not dose["taken"] and rid not in st.session_state.reminded_doses and 
                abs((dose["datetime"] - now).total_seconds()) <= 60):
                st.toast(f"💊 Time to take {med['name']} ({dose['datetime'].strftime('%H:%M')})", icon="⏰")
                st.session_state.reminded_doses.add(rid)

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
                    st.session_state.user = u
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
# MAIN APP HEADER
# --------------------------------------------------
st.markdown(f"### 👤 Logged in as **{st.session_state.user}**")

# --------------------------------------------------
# PAGE: ADD / EDIT MEDICINE
# --------------------------------------------------
if st.session_state.page == "Add Medicine":
    st.title("➕ Add / ✏️ Edit Medicine")
    edit_mode = st.session_state.edit_med is not None
    med = st.session_state.meds[st.session_state.edit_med] if edit_mode else None
    times_per_day = st.number_input("Times per Day", 1, 5, value=med["times_per_day"] if edit_mode else 1)

    with st.form("medicine_form"):
        name = st.text_input("Medicine Name", value=med["name"] if edit_mode else "")
        start_date = st.date_input("Start Date", value=med["start"] if edit_mode else date.today())
        days = st.number_input("Number of Days", 1, 365, value=med["days"] if edit_mode else 5)
        times = []
        for i in range(times_per_day):
            default = med["times"][i] if edit_mode and i < len(med["times"]) else time(9, 0)
            times.append(st.time_input(f"Time {i+1}", default, step=60))

        if st.form_submit_button("Save Medicine"):
            doses = []
            for d in range(days):
                for t_val in times:
                    doses.append({
                        "datetime": datetime.combine(start_date + timedelta(days=d), t_val),
                        "taken": False, "taken_time": None
                    })
            data = {"name": name, "start": start_date, "days": days, "times_per_day": times_per_day, "times": times, "doses": doses}
            
            doses_json = json.dumps([{
                "datetime": d["datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                "taken": d["taken"],
                "taken_time": d["taken_time"].strftime("%Y-%m-%d %H:%M:%S") if d["taken_time"] else None
            } for d in doses])
            times_str = json.dumps([t_val.strftime("%H:%M") for t in times])

            if edit_mode:
                cur.execute("UPDATE medicines SET med_name=?, start_date=?, days=?, times=?, doses_json=? WHERE username=? AND med_name=?", 
                            (name, str(start_date), days, times_str, doses_json, st.session_state.user, med["name"]))
                st.session_state.meds[st.session_state.edit_med] = data
                st.session_state.edit_med = None
            else:
                cur.execute("INSERT INTO medicines (username, med_name, start_date, days, times, doses_json) VALUES (?, ?, ?, ?, ?, ?)", 
                            (st.session_state.user, name, str(start_date), days, times_str, doses_json))
                st.session_state.meds.append(data)
            conn.commit()
            st.session_state.page = "Today's Checklist"
            st.rerun()

# --------------------------------------------------
# PAGE: TODAY'S CHECKLIST
# --------------------------------------------------
if st.session_state.page == "Today's Checklist":
    st.title(t("checklist"))
    now = datetime.now()
    check_medicine_reminders()
    to_delete = None
    has_meds_today = False

    for mi, med in enumerate(st.session_state.meds):
        for di, dose in enumerate(med["doses"]):
            if dose["datetime"].date() == date.today():
                has_meds_today = True
                st.markdown(f"### 💊 {med['name']}")
                st.write(f"⏰ {dose['datetime'].strftime('%H:%M')}")
                time_diff = (now - dose["datetime"]).total_seconds() / 60
                
                if dose["taken"]: st.success(t("status_taken")) 
                elif abs(time_diff) <= 10: st.success(f"🌟 {t('status_now')}") 
                elif time_diff > 10: st.error(t("status_missed"))
                else: st.warning(t("status_upcoming"))

                c1, c2, c3 = st.columns(3)
                if c1.button(f"✅ {t('btn_taken')}", key=f"take_{mi}_{di}"):
                    dose["taken"] = True
                    dose["taken_time"] = datetime.now()
                    updated_json = json.dumps([{
                        "datetime": d["datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                        "taken": d["taken"],
                        "taken_time": d["taken_time"].strftime("%Y-%m-%d %H:%M:%S") if d["taken_time"] else None
                    } for d in med["doses"]])
                    cur.execute("UPDATE medicines SET doses_json=? WHERE username=? AND med_name=?", (updated_json, st.session_state.user, med["name"]))
                    conn.commit()
                    st.rerun()

                if c2.button(f"✏️ {t('btn_edit')}", key=f"edit_{mi}_{di}"):
                    st.session_state.edit_med = mi
                    st.session_state.page = "Add Medicine"
                    st.rerun()

                if c3.button(f"🗑 {t('btn_del')}", key=f"del_{mi}_{di}"):
                    to_delete = mi
                st.divider()

    if to_delete is not None:
        med_to_remove = st.session_state.meds[to_delete]["name"]
        cur.execute("DELETE FROM medicines WHERE username=? AND med_name=?", (st.session_state.user, med_to_remove))
        conn.commit()
        st.session_state.meds.pop(to_delete)
        st.rerun()

    if not has_meds_today: st.info(t("no_meds_today"))

    total = sum(len(m["doses"]) for m in st.session_state.meds)
    taken = sum(d["taken"] for m in st.session_state.meds for d in m["doses"])
    score = int((taken / total) * 100) if total else 0
    st.subheader(t("adherence_score"))
    st.progress(score)
    st.write(f"{score}%")

    if st.button(f"📄 {t('btn_pdf')}"):
        styles = getSampleStyleSheet()
        elements = [Paragraph(f"<b>Report</b>", styles["Title"])]
        table_data = [["Date", "Day", "Medicine", "Scheduled", "Taken", "Status"]]
        for med in st.session_state.meds:
            for d in med["doses"]:
                status = "Taken" if d["taken"] else "Not Taken"
                table_data.append([d["datetime"].strftime("%d-%m-%Y"), d["datetime"].strftime("%A"), med["name"], d["datetime"].strftime("%H:%M"), d["taken_time"].strftime("%H:%M") if d["taken_time"] else "-", status])
        table = Table(table_data)
        elements.append(table)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        doc = SimpleDocTemplate(tmp.name, pagesize=A4)
        doc.build(elements)
        with open(tmp.name, "rb") as f:
            st.download_button(t("btn_download_pdf"), f, file_name="report.pdf")

# --------------------------------------------------
# PAGE: SETTINGS
# --------------------------------------------------
if st.session_state.page == "Settings":
    st.title(t("settings"))
    st.subheader("👤 " + t("profile"))
    new_age = st.number_input(t("age_label"), 1, 120, value=st.session_state.age)
    lang_options = ["English", "Tamil", "Hindi", "Spanish", "French", "German", "Chinese"]
    lang = st.selectbox(t("lang_label"), lang_options, index=lang_options.index(st.session_state.language))

    if st.button(t("save")):
        cur.execute("UPDATE users SET age=? WHERE username=?", (new_age, st.session_state.user))
        cur.execute("UPDATE user_settings SET language=? WHERE username=?", (lang, st.session_state.user))
        conn.commit()
        st.session_state.age, st.session_state.language = new_age, lang
        st.rerun()

    st.divider()
    st.subheader("🎨 " + t("appearance"))
    bg = st.color_picker("Background", st.session_state.bg_color)
    font = st.selectbox("Font", ["Arial", "Verdana", "Courier New"], index=0)
    size = st.slider("Size", 12, 32, st.session_state.font_size)
    if st.button(t("apply")):
        cur.execute("UPDATE user_settings SET bg_color=?, font_family=?, font_size=? WHERE username=?", (bg, font, size, st.session_state.user))
        conn.commit()
        st.session_state.bg_color, st.session_state.font_family, st.session_state.font_size = bg, font, size
        st.rerun()

    st.divider()
    st.subheader("🔐 Security")
    with st.form("change_auth"):
        curr_u = st.text_input("Current Username", value=st.session_state.user)
        curr_p = st.text_input("Current Password", type="password")
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password", type="password")
        if st.form_submit_button("Update Credentials"):
            res = update_credentials(curr_u, curr_p, new_u, new_p)
            if res == True: st.success("Updated! Log in again."); st.session_state.logged = False; st.rerun()
            else: st.error("Error updating credentials")

# --------------------------------------------------
# NAVIGATION FOOTER
# --------------------------------------------------
st.divider()
c1, c2, c3, c4 = st.columns(4)
if c1.button(t("add_med")): st.session_state.page = "Add Medicine"; st.rerun()
if c2.button(t("checklist")): st.session_state.page = "Today's Checklist"; st.rerun()
if c3.button(t("settings")): st.session_state.page = "Settings"; st.rerun()
if c4.button(t("logout")): st.session_state.logged = False; st.rerun()

st.markdown("""<script>setTimeout(function(){window.location.reload();}, 60000);</script>""", unsafe_allow_html=True)
