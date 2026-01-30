import streamlit as st
import sqlite3
import hashlib
import json
import os
import tempfile
import random
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
@st.cache_resource
def get_db_connection():
    db_path = os.path.join(os.getcwd(), "users.db")
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=20)
    return conn

conn = get_db_connection()
cur = conn.cursor()

try:
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
    conn.commit()
except sqlite3.OperationalError as e:
    st.error(f"Database Error: {e}")
    st.stop()

# --------------------------------------------------
# MIGRATION HELPER
# --------------------------------------------------
def add_column_if_missing(table, column, definition):
    try:
        cur.execute(f"SELECT {column} FROM {table} LIMIT 1")
    except sqlite3.OperationalError:
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            conn.commit()
        except:
            pass

add_column_if_missing("medicines", "med_name", "TEXT")
add_column_if_missing("medicines", "doses_json", "TEXT")

# --------------------------------------------------
# HELPERS & AUTH FUNCTIONS
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
# SESSION STATE & TRANSLATIONS
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
        "checklist": "📋 Today's Checklist", "settings": "⚙️ Settings", "add_med": "➕ Add Medicine",
        "logout": "🚪 Logout", "profile": "👤 Profile", "appearance": "🎨 Appearance",
        "save": "Save", "apply": "Apply", "status_taken": "Taken", "status_now": "Time to Take",
        "status_missed": "Missed", "status_upcoming": "Upcoming", "btn_taken": "Taken",
        "btn_edit": "Edit", "btn_del": "Delete", "no_meds_today": "No medicines today.",
        "adherence_score": "📊 Adherence Score", "btn_pdf": "Download Report",
        "lang_label": "Language", "age_label": "Age", "change_creds": "🔐 Change Credentials",
        "curr_username": "Current Username", "curr_password": "Current Password",
        "new_username": "New Username", "new_password": "New Password", "btn_update_auth": "Update Credentials",
        "pdf_report_title": "Medication Adherence Report", "patient": "Patient", "generated": "Generated",
        "col_date": "Date", "col_day": "Day", "col_med": "Medicine", "col_sched": "Scheduled", "col_taken": "Taken At", "col_status": "Status",
        "btn_download_pdf": "⬇️ Download PDF"
    },
    "Tamil": {
        "checklist": "📋 இன்றைய பட்டியல்", "settings": "⚙️ அமைப்புகள்", "add_med": "➕ மருந்து சேர்க்க",
        "logout": "🚪 வெளியேறு", "profile": "👤 சுயவிவரம்", "appearance": "🎨 தோற்றம்",
        "save": "சேமி", "apply": "தீம் மாற்றுக", "status_taken": "எடுத்துக்கொள்ளப்பட்டது", "status_now": "மருந்து எடுக்கும் நேரம்",
        "status_missed": "தவறியது", "status_upcoming": "வரவிருப்பது", "btn_taken": "எடுத்தேன்",
        "btn_edit": "திருத்து", "btn_del": "நீக்கு", "no_meds_today": "இன்று மருந்துகள் ஏதுமில்லை.",
        "adherence_score": "📊 பின்பற்றுதல் மதிப்பெண்", "btn_pdf": "PDF அறிக்கை",
        "lang_label": "மொழி", "age_label": "வயது", "change_creds": "🔐 சான்றுகளை மாற்றவும்",
        "curr_username": "தற்போதைய பயனர் பெயர்", "curr_password": "தற்போதைய கடவுச்சொல்",
        "new_username": "புதிய பயனர் பெயர்", "new_password": "புதிய கடவுச்சொல்", "btn_update_auth": "சான்றுகளைப் புதுப்பிக்கவும்",
        "pdf_report_title": "மருந்து பின்பற்றுதல் அறிக்கை", "patient": "நோயாளி", "generated": "உருவாக்கப்பட்டது",
        "col_date": "தேதி", "col_day": "நாள்", "col_med": "மருந்து", "col_sched": "நேரம்", "col_taken": "எடுத்த நேரம்", "col_status": "நிலை",
        "btn_download_pdf": "⬇️ PDF பதிவிறக்கம்"
    },
    "Hindi": {
        "checklist": "📋 आज की सूची", "settings": "⚙️ सेटिंग्स", "add_med": "➕ दवा जोड़ें",
        "logout": "🚪 लॉग आउट", "profile": "👤 प्रोफाइल", "appearance": "🎨 उपस्थिति",
        "save": "सहेजें", "apply": "थीम लागू करें", "status_taken": "लिया गया", "status_now": "दवा का समय",
        "status_missed": "छूट गया", "status_upcoming": "आगामी", "btn_taken": "ले लिया",
        "btn_edit": "संपादित करें", "btn_del": "हटाएं", "no_meds_today": "आज कोई दवा नहीं है।",
        "adherence_score": "📊 अनुपालन स्कोर", "btn_pdf": "PDF रिपोर्ट",
        "lang_label": "भाषा", "age_label": "आयु", "change_creds": "🔐 क्रेडेंशियल बदलें",
        "curr_username": "वर्तमान उपयोगकर्ता नाम", "curr_password": "वर्तमान पासवर्ड",
        "new_username": "नया उपयोगकर्ता नाम", "new_password": "नया पासवर्ड", "btn_update_auth": "क्रेडेंशियल अपडेट करें",
        "pdf_report_title": "दवा अनुपालन रिपोर्ट", "patient": "रोगी", "generated": "जनरेट किया गया",
        "col_date": "तारीख", "col_day": "दिन", "col_med": "दवा", "col_sched": "निर्धारित", "col_taken": "लिया गया समय", "col_status": "स्थिति",
        "btn_download_pdf": "⬇️ PDF डाउनलोड करें"
    },
    "Spanish": {
        "checklist": "📋 Lista de hoy", "settings": "⚙️ Ajustes", "add_med": "➕ Añadir medicina",
        "logout": "🚪 Salir", "profile": "👤 Perfil", "appearance": "🎨 Apariencia",
        "save": "Guardar", "apply": "Aplicar", "status_taken": "Tomado", "status_now": "Hora de tomar",
        "status_missed": "Omitido", "status_upcoming": "Próximo", "btn_taken": "Tomado",
        "btn_edit": "Editar", "btn_del": "Eliminar", "no_meds_today": "No hay medicinas para hoy.",
        "adherence_score": "📊 Puntuación de adherencia", "btn_pdf": "Informe PDF",
        "lang_label": "Idioma", "age_label": "Edad", "change_creds": "🔐 Cambiar credenciales",
        "curr_username": "Usuario actual", "curr_password": "Password actual",
        "new_username": "Nuevo usuario", "new_password": "Nuevo password", "btn_update_auth": "Actualizar datos",
        "pdf_report_title": "Informe de adherencia médica", "patient": "Paciente", "generated": "Generado",
        "col_date": "Fecha", "col_day": "Día", "col_med": "Medicina", "col_sched": "Programado", "col_taken": "Tomado a las", "col_status": "Estado",
        "btn_download_pdf": "⬇️ Descargar PDF"
    },
    "French": {
        "checklist": "📋 Liste du jour", "settings": "⚙️ Paramètres", "add_med": "➕ Ajouter médicament",
        "logout": "🚪 Déconnexion", "profile": "👤 Profil", "appearance": "🎨 Apparence",
        "save": "Enregistrer", "apply": "Appliquer", "status_taken": "Pris", "status_now": "C'est l'heure",
        "status_missed": "Manqué", "status_upcoming": "À venir", "btn_taken": "Pris",
        "btn_edit": "Modifier", "btn_del": "Supprimer", "no_meds_today": "Aucun médicament aujourd'hui.",
        "adherence_score": "📊 Score d'adhésion", "btn_pdf": "Rapport PDF",
        "lang_label": "Langue", "age_label": "Âge", "change_creds": "🔐 Changer identifiants",
        "curr_username": "Nom d'utilisateur actuel", "curr_password": "Mot de passe actuel",
        "new_username": "Nouveau nom", "new_password": "Nouveau mot de passe", "btn_update_auth": "Mettre à jour",
        "pdf_report_title": "Rapport d'observance", "patient": "Patient", "generated": "Généré",
        "col_date": "Date", "col_day": "Jour", "col_med": "Médicament", "col_sched": "Prévu", "col_taken": "Pris à", "col_status": "Statut",
        "btn_download_pdf": "⬇️ Télécharger PDF"
    },
    "German": {
        "checklist": "📋 Checkliste", "settings": "⚙️ Einstellungen", "add_med": "➕ Medizin hinzufügen",
        "logout": "🚪 Abmelden", "profile": "👤 Profil", "appearance": "🎨 Aussehen",
        "save": "Speichern", "apply": "Übernehmen", "status_taken": "Eingenommen", "status_now": "Zeit zur Einnahme",
        "status_missed": "Verpasst", "status_upcoming": "Anstehend", "btn_taken": "Eingenommen",
        "btn_edit": "Bearbeiten", "btn_del": "Löschen", "no_meds_today": "Keine Medikamente heute.",
        "adherence_score": "📊 Therapietreue", "btn_pdf": "PDF Bericht",
        "lang_label": "Sprache", "age_label": "Alter", "change_creds": "🔐 Zugangsdaten ändern",
        "curr_username": "Benutzername", "curr_password": "Passwort",
        "new_username": "Neuer Name", "new_password": "Neues Passwort", "btn_update_auth": "Aktualisieren",
        "pdf_report_title": "Medikationsbericht", "patient": "Patient", "generated": "Erstellt",
        "col_date": "Datum", "col_day": "Tag", "col_med": "Medikament", "col_sched": "Geplant", "col_taken": "Zeit", "col_status": "Status",
        "btn_download_pdf": "⬇️ PDF Herunterladen"
    },
    "Chinese": {
        "checklist": "📋 今日清单", "settings": "⚙️ 设置", "add_med": "➕ 添加药物",
        "logout": "🚪 登出", "profile": "👤 个人资料", "appearance": "🎨 外观",
        "save": "保存", "apply": "应用", "status_taken": "已服用", "status_now": "服药时间",
        "status_missed": "错过", "status_upcoming": "即将到来", "btn_taken": "已服",
        "btn_edit": "编辑", "btn_del": "删除", "no_meds_today": "今天没有药。",
        "adherence_score": "📊 服药依从性", "btn_pdf": "PDF 报告",
        "lang_label": "语言", "age_label": "年龄", "change_creds": "🔐 更改凭据",
        "curr_username": "当前用户名", "curr_password": "当前密码",
        "new_username": "新用户名", "new_password": "新密码", "btn_update_auth": "更新凭据",
        "pdf_report_title": "服药依从性报告", "patient": "患者", "generated": "生成日期",
        "col_date": "日期", "col_day": "星期", "col_med": "药物", "col_sched": "计划时间", "col_taken": "服用时间", "col_status": "状态",
        "btn_download_pdf": "⬇️ 下载 PDF"
    }
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
    if "notifications_done" not in st.session_state:
        st.session_state.notifications_done = set()

    for med in st.session_state.meds:
        for dose in med["doses"]:
            if dose["datetime"].date() == now.date() and not dose["taken"]:
                time_diff = (now - dose["datetime"]).total_seconds() / 60
                notification_key = f"{med['name']}_{dose['datetime'].strftime('%H:%M')}"
                if 0 <= time_diff < 1: 
                    if notification_key not in st.session_state.notifications_done:
                        st.toast(f"🔔 **Time for your medicine:** {med['name']}!", icon="💊")
                        st.session_state.notifications_done.add(notification_key)

# --------------------------------------------------
# AUTHENTICATION UI
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
# APP HEADER
# --------------------------------------------------
st.markdown(f"### 👤 Logged in as **{st.session_state.user}**")

# --------------------------------------------------
# PAGE: ADD / EDIT MEDICINE
# --------------------------------------------------
if st.session_state.page == "Add Medicine":
    st.title("➕ Add / ✏️ Edit Medicine")

    # ✅ SAFE edit mode check (FIXES IndexError)
    edit_mode = (
        st.session_state.edit_med is not None
        and isinstance(st.session_state.edit_med, int)
        and 0 <= st.session_state.edit_med < len(st.session_state.meds)
    )

    med = st.session_state.meds[st.session_state.edit_med] if edit_mode else None

    times_per_day = st.number_input(
        "Times per Day",
        1,
        5,
        value=med["times_per_day"] if edit_mode else 1
    )

    with st.form("medicine_form"):
        name = st.text_input(
            "Medicine Name",
            value=med["name"] if edit_mode else ""
        )

        start_date = st.date_input(
            "Start Date",
            value=med["start"] if edit_mode else date.today()
        )

        days = st.number_input(
            "Number of Days",
            1,
            365,
            value=med["days"] if edit_mode else 5
        )

        times = []
        for i in range(times_per_day):
            default_time = (
                med["times"][i]
                if edit_mode and i < len(med["times"])
                else time(9, 0)
            )
            times.append(
                st.time_input(f"Time {i+1}", default_time, step=60)
            )

        if st.form_submit_button("Save Medicine"):
            doses = []
            for d in range(days):
                for t_val in times:
                    doses.append({
                        "datetime": datetime.combine(
                            start_date + timedelta(days=d),
                            t_val
                        ),
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

            doses_json = json.dumps([
                {
                    "datetime": d["datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                    "taken": d["taken"],
                    "taken_time": (
                        d["taken_time"].strftime("%Y-%m-%d %H:%M:%S")
                        if d["taken_time"] else None
                    )
                }
                for d in doses
            ])

            times_str = json.dumps(
                [t_val.strftime("%H:%M") for t_val in times]
            )

            if edit_mode:
                cur.execute(
                    """
                    UPDATE medicines
                    SET med_name=?, start_date=?, days=?, times=?, doses_json=?
                    WHERE username=? AND med_name=?
                    """,
                    (
                        name,
                        str(start_date),
                        days,
                        times_str,
                        doses_json,
                        st.session_state.user,
                        med["name"]
                    )
                )

                st.session_state.meds[st.session_state.edit_med] = data
                st.session_state.edit_med = None
            else:
                cur.execute(
                    """
                    INSERT INTO medicines
                    (username, med_name, start_date, days, times, doses_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        st.session_state.user,
                        name,
                        str(start_date),
                        days,
                        times_str,
                        doses_json
                    )
                )

                st.session_state.meds.append(data)

            conn.commit()
            st.session_state.page = "Today's Checklist"
            st.rerun()

# --------------------------------------------------
# PAGE: TODAY'S CHECKLIST
# --------------------------------------------------
if st.session_state.page == "Today's Checklist":
    st.title(t("checklist"))
    check_medicine_reminders()
    
    if "motivation_quote" not in st.session_state:
        st.session_state.motivation_quote = "Every pill taken on time is a victory for your health! 🌟"
    
    st.info(f"✨ **Daily Motivation:** {st.session_state.motivation_quote}")
    
    now = datetime.now()
    to_delete = None
    has_meds_today = False

    for mi, med in enumerate(st.session_state.meds):
        for di, dose in enumerate(med["doses"]):
            if dose["datetime"].date() == date.today():
                has_meds_today = True
                st.markdown(f"### 💊 {med['name']}")
                st.write(f"⏰ {dose['datetime'].strftime('%H:%M')}")
                time_diff = (now - dose["datetime"]).total_seconds() / 60
                
                if dose["taken"]: 
                    st.success(t("status_taken")) 
                elif abs(time_diff) <= 10: 
                    st.success(f"🌟 {t('status_now')}") 
                elif time_diff > 10: 
                    st.error(t("status_missed"))
                else: 
                    st.warning(t("status_upcoming"))

                c1, c2, c3 = st.columns(3)
                if c1.button(f"✅ {t('btn_taken')}", key=f"take_{mi}_{di}"):
                    dose["taken"] = True
                    dose["taken_time"] = datetime.now()
                    
                    MOTIVATION_QUOTES = [
                        "Excellent job! Your health is your wealth. 💪",
                        "Consistency is key! You're doing great. ✨",
                        "One step at a time, you're looking after yourself well! ❤️",
                        "Way to go! Keeping up with your health is a big win today. 🏆",
                        "You're doing a fantastic job staying on track! 🌈",
                        "Your future self will thank you for being so diligent. 💖",
                        "Keep it up! Small habits lead to big results. 🚀"
                    ]
                    st.session_state.motivation_quote = random.choice(MOTIVATION_QUOTES)
                    
                    updated_json = json.dumps([{
                        "datetime": d["datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                        "taken": d["taken"],
                        "taken_time": d["taken_time"].strftime("%Y-%m-%d %H:%M:%S") if d.get("taken_time") else None
                    } for d in med["doses"]])
                    
                    cur.execute("UPDATE medicines SET doses_json=? WHERE username=? AND med_name=?", 
                               (updated_json, st.session_state.user, med["name"]))
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

    if not has_meds_today: 
        st.info(t("no_meds_today"))

    # Adherence Score
    total = sum(len(m["doses"]) for m in st.session_state.meds)
    taken = sum(d["taken"] for m in st.session_state.meds for d in m["doses"])
    score = int((taken / total) * 100) if total else 0
    st.subheader(t("adherence_score"))
    st.progress(score)
    st.write(f"{score}%")

    # PDF Generation
    if st.button(f"📄 {t('btn_pdf')}"):
        styles = getSampleStyleSheet()
        status_style = styles["Normal"].clone("StatusStyle")
        status_style.alignment = 1 
        
        elements = []
        elements.append(Paragraph(f"<b>{t('pdf_report_title')}</b>", styles["Title"]))
        elements.append(Paragraph(f"<b>Patient:</b> {st.session_state.user} | <b>Age:</b> {st.session_state.age}", styles["Normal"]))
        elements.append(Paragraph(f"<b>Generated on:</b> {date.today().strftime('%d-%m-%Y')}", styles["Normal"]))
        elements.append(Paragraph("<br/><br/>", styles["Normal"]))

        table_data = [[t("col_date"), t("col_day"), t("col_med"), t("col_sched"), t("col_taken"), t("col_status")]]
        TOLERANCE = 15

        for med in st.session_state.meds:
            for d in med["doses"]:
                sched_dt = d["datetime"]
                taken_dt = d["taken_time"]
                
                if d["taken"] and taken_dt:
                    diff = (taken_dt - sched_dt).total_seconds() / 60
                    taken_str = taken_dt.strftime("%H:%M")
                    if abs(diff) <= TOLERANCE:
                        status_text, status_color = "Taken on time", "green"
                    else:
                        status_text, status_color = "Taken early/late", "#CCCC00"
                else:
                    status_text, status_color, taken_str = "Not taken", "red", "-"

                colored_status = Paragraph(f'<b><font color="{status_color}">{status_text}</font></b>', status_style)
                table_data.append([sched_dt.strftime("%d-%m-%Y"), sched_dt.strftime("%A"), med["name"], sched_dt.strftime("%H:%M"), taken_str, colored_status])

        report_table = Table(table_data, colWidths=[75, 85, 90, 70, 70, 120])
        report_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(report_table)

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        doc = SimpleDocTemplate(tmp.name, pagesize=A4)
        doc.build(elements)

        with open(tmp.name, "rb") as f:
            st.download_button(label=t("btn_download_pdf"), data=f, file_name=f"Medical_Report_{st.session_state.user}.pdf", mime="application/pdf")

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
            if res == True: 
                st.success("Updated! Log in again.")
                st.session_state.logged = False
                st.rerun()
            else: 
                st.error("Error updating credentials")

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

