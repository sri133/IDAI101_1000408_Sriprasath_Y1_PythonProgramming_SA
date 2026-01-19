# IDAI101_1000408_Sriprasath_Y1_PythonProgramming_SA
# Asclepius – MedTimer

**Asclepius – MedTimer** is a personal medication adherence tracking application built with Python and Streamlit. It allows users to schedule medicines, track daily intake, visualize adherence scores, and generate detailed PDF reports for medical records.

## Features

* **User Authentication:** Secure Login and Sign-up system using SHA-256 password hashing.
* **Medication Management:**
    * Add, Edit, and Delete medication schedules.
    * Set custom frequencies (up to 5 times per day) and specific dosage times.
    * Define treatment duration (days).
* **Daily Checklist:**
    * Interactive dashboard showing today's scheduled doses.
    * Mark doses as "Taken" with a single click.
    * Visual status indicators (Upcoming, Missed, Taken).
* **Adherence Analytics:**
    * Real-time adherence score calculation (percentage).
    * **Visual Feedback:** Uses Python `turtle` graphics to draw a pill visualization that fills up based on your adherence score.
* **PDF Reporting:**
    * Generates a downloadable PDF report using `ReportLab`.
    * Tracks exact timing deviations (Early, Late, On Time) based on a 10-minute tolerance window.

## Tech Stack

* **Language:** Python 3.x
* **Frontend/Framework:** [Streamlit](https://streamlit.io/)
* **Database:** SQLite (Embedded, no setup required)
* **PDF Generation:** ReportLab
* **Visualization:** Python Turtle Graphics (Standard Library)

## Prerequisites

Ensure you have Python installed on your machine. You will need to install the following external libraries:

* `streamlit`
* `reportlab`

## Installation

1.  **Clone the repository** (or place `MedTimer.py` in a folder):
    ```bash
    git clone <your-repo-url>
    cd medtimer
    ```

2.  **Install Dependencies:**
    Run the following command in your terminal:
    ```bash
    pip install streamlit reportlab
    ```
    *(Note: `sqlite3`, `hashlib`, `turtle`, `threading`, and `datetime` are part of the Python standard library and do not need installation.)*

## Usage

1.  **Run the Application:**
    Navigate to the project folder and run:
    ```bash
    streamlit run MedTimer.py
    ```

2.  **Access the App:**
    Streamlit will automatically open the app in your default web browser (usually at `http://localhost:8501`).

3.  **Workflow:**
    * **Sign Up:** Create a new account.
    * **Add Medicine:** Click "Add Medicine" to set up your schedule.
    * **Track:** Go to "Today's Checklist" to mark medicines as taken.
    * **Report:** Click "Download Adherence Report" to get your PDF summary.

## 📂 Project Structure

```text
.
├── MedTimer.py       # The main application code
├── users.db          # SQLite database (Auto-generated on first run)
└── README.md         # Project documentation
