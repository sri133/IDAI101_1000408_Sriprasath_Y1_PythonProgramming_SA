# 💊 Asclepius – MedTimer  
### Daily Medicine Companion for Adherence & Wellbeing

Asclepius – MedTimer is an interactive **Python-based web application** designed to help elderly users and individuals with chronic conditions manage their daily medication routines with ease, confidence, and reduced stress.

Built using **Streamlit**, the app transforms medication tracking from a stressful obligation into a calm, reassuring daily companion focused on accessibility, clarity, and social good.

---
## APP FLOW IN TEXT:
📌 Application Flow

App Start / Launch

User opens the MedTimer web application.

Welcome Screen

Displays a friendly greeting:
“Let’s take care of your health today.”

Add Medicine Screen

User inputs:

Medicine name

Scheduled time

Clicks Add Medicine button.

Data Storage Process

Medicine details are stored in a list/dictionary.

Default status is set to Upcoming.

Daily Medicine Checklist Screen

Displays all medicines scheduled for the current day.

Uses large fonts and clear spacing for readability.

Time Comparison Logic

Current time is compared with the scheduled medicine time.

Status conditions:

⏳ Upcoming → Time not reached (Yellow)

✅ Taken → User marked as taken (Green)

❌ Missed → Time passed and not taken (Red)

User Action: Mark as Taken

User checks a checkbox or clicks a button.

Medicine status updates instantly to Taken.

Weekly Adherence Calculation

Counts:

Total scheduled medicines

Total medicines taken

Calculates adherence percentage.

Adherence Score Display Screen

Shows weekly adherence score.

Includes a progress indicator.

Turtle Graphics Feedback

If adherence meets or exceeds a good threshold:

Displays turtle graphics (smiley face / trophy).

Shows an encouraging message.

Motivational Tips Screen

Displays a health tip or motivational quote.

Loop Flow

Application continues running:

Allows adding new medicines

Updates statuses dynamically.

End of Day / Continue Tomorrow

Day ends naturally.

Data continues for the next day’s tracking.

## Drive Link to view app flow image and app Screenshots: https://drive.google.com/drive/folders/1Tt6dp-HQPeD_E8dZAZjkc7vZGEQ003Vu?usp=drive_link

## 📘 Project Overview

Medication adherence is a major challenge for elderly users and patients with chronic illnesses. Missed or delayed doses can lead to anxiety, health risks, and reduced independence.

**Asclepius – MedTimer** addresses these challenges by offering:

- 🟢 Color-coded medication checklists  
- ⏰ Gentle, non-intrusive reminders  
- 📊 Visual adherence analytics  
- 💬 Motivational and encouraging messages  
- 📄 Downloadable medical reports for caregivers and doctors  

This project aligns with real-world healthcare needs and demonstrates the deployment of Python applications for meaningful social impact.

---

## 🎯 Problem Understanding & Design Planning

### 👥 Target Users
- Older adults  
- Patients with chronic illnesses  
- Users who value simplicity, clarity, and reassurance  

### ⚠️ Pain Points Addressed
- Forgetting medication doses  
- Anxiety around missed medicines  
- Confusing medication schedules  
- Lack of clear feedback on adherence  

### ❤️ Intended Emotional Experience
- Comfort and trust  
- Reduced stress  
- Empowerment and confidence  
- Gentle encouragement rather than pressure  

---

## 🖍️ Interface Design (Wireframe Concept)

- **Top Section:** Add / Edit medicines  
- **Center:** Today’s medication checklist (color-coded)  
- **Side / Below:** Adherence score & motivational feedback  
- **Footer:** Simple navigation controls  

### 🎨 Design Choices
- Large, readable fonts  
- Calm color palette (green, blue, neutral tones)  
- Minimal cognitive load  
- Friendly icons and human-centered language  

---

## ✔️ Features

### Core Features
- Add / Edit / Delete medicines  
- Color-coded checklist  
  - 🟢 Taken  
  - 🟡 Upcoming  
  - 🔴 Missed  
- Daily adherence score  
- Weekly adherence visualization  
- Motivational messages  

### Creative / Advanced Features
- Toast notifications  
- Multilingual support (7 languages)  
- PDF medical reports  
- UI personalization (font size, colors, layout)  

---

## 🧠 Python Logic & Data Design

### 🧩 Core Data Structures
- Lists for medicine schedules  
- Dictionaries for dose tracking:
  ```python
  {
    "datetime": datetime,
    "taken": bool,
    "taken_time": datetime | None
  }
JSON serialization for persistence

SQLite database for secure local storage

⏱ Time-Based Logic
Real-time comparison of current time vs scheduled dose

Automatic status classification:

🟢 Taken

🟡 Upcoming

🔴 Missed

📊 Adherence Calculation
Daily adherence percentage

Weekly aggregation (last 7 days)

Live recalculation after each interaction

🔐 Authentication
SHA-256 password hashing

Session-based login control

Secure credential updates

🧠 Modular Architecture
Authentication module

Reminder & timing logic

PDF generation module

UI state management

🖥 Interactive Streamlit Interface
🎛 UI Components
Forms (st.form)

Buttons, sliders, and select boxes

Columns and layout containers

Toast notifications

Interactive charts (Matplotlib & Plotly)

🎨 Visual Hierarchy
Clear headers for each medicine

Color-coded feedback:

Green = Taken

Yellow = Time to Take

Red = Missed

Icons and emojis for clarity

🔁 Live Interactivity
Checklist updates instantly

Adherence score updates live

Auto-refresh every 60 seconds

🌍 Accessibility
Multilingual UI (7 languages)

Adjustable font size

Custom background colors

Simple and intuitive navigation

🧪 Testing & Creative Enhancements
🔍 Testing Scenarios
Multiple medicines per day

Missed doses

Early and late intake

Weekly adherence tracking

Credential updates

Language switching

🎁 Creative Enhancements
Random motivational quotes after dose intake

Toast reminders at exact medication times

Personalized encouragement messages

Professional PDF medical reports

Visual adherence charts

🧑‍🤝‍🧑 Usability Focus
Large buttons

Simple wording

Minimal steps per action

Clear feedback after every interaction

📊 Adherence Analytics
Daily
Circular adherence indicator (%)

Weekly
Bar chart for last 7 days

These visuals help users and caregivers understand behavior patterns rather than just raw data.

📄 PDF Medical Report
The downloadable PDF report includes:

Patient name and age

Date-wise medication log

Scheduled vs actual intake time

Color-coded adherence status

Reports can be shared with doctors and family members to support informed healthcare decisions.

🌍 Social & Ethical Impact
Supports medication adherence for vulnerable populations

Reduces health risks caused by missed doses

Promotes independence for elderly users

Respects privacy (local database, no data selling)

Encourages responsible health behavior

🚀 Deployment
Requirements
streamlit
plotly
matplotlib
reportlab
streamlit run app.py
Cloud Deployment
GitHub Repository

Streamlit Cloud

Free public access

🔗 Live Links

Live App: https://1000408sriprasathy1pythonprogrammingsa-dhqr3wkoeobnxf5c9dvens.streamlit.app/

📁 Repository Structure
/
├── app.py
├── users.db
├── requirements.txt
⭐ Asclepius – MedTimer is built with empathy, simplicity, and real-world healthcare impact at its core.

## 📌 App Summary

| Assessment Criteria | Status |
|---------------------|--------|
| Understanding user needs & planning | ✅ |
| Python logic using lists, dictionaries & `datetime` | ✅ |
| Interactive Streamlit interface | ✅ |
| Color-coded medication checklist | ✅ |
| Adherence calculation & analytics | ✅ |
| Turtle graphics (creative feature) | ✅ |
| Testing & usability checks | ✅ |
| GitHub repository & documentation | ✅ |
| Live Streamlit deployment | ✅ |

---

## 🚀 Conclusion

**MedTimer** is a complete, user-centric medicine tracking application designed with **empathy, accessibility, and simplicity** at its core.

The project successfully fulfills **all compulsory requirements** of the Summative Assessment while going beyond the baseline through creative, motivational, and usability-focused enhancements.

This work demonstrates:

- Strong Python fundamentals  
- Effective and structured use of Streamlit  
- Real-world problem solving skills  
- Thoughtful UI/UX design aimed at social good  

MedTimer highlights how technology can be applied responsibly to improve everyday healthcare experiences.

---
Credits: 
1. Name:Sri Prasath. P
2. Grade: IBCP Year1
3. Course: Python Programming
4. Mentor: Syed Ali Beema.S

