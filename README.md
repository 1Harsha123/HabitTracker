# Habit Tracker & Study Timer (Django)

A Django-based web application to help users build daily habits, track streaks, and manage a focused **study timer** with pause/resume functionality.

---

##  Features

###  User Authentication
- Signup, Login, Logout
- Forgot password (reset password)

###  Habit Tracking
- Create, edit, and delete habits
- Mark habits as **Done Today**
- Habit status: Completed / Pending
- Each user sees **only their own habits**

###  Streak System
- Automatically calculates streaks
- Shows previous streak even if today is not yet completed
- Streak increases when today’s habit is completed

### ⏱ Study Timer (Special Habit)
- Start / Stop / Resume timer
- Accumulates time across sessions
- One-hour daily study goal
- Prevents resetting time accidentally
- Shows remaining time if goal not completed

### Dashboard
- Today’s completed habits
- Pending habits
- Total habits
- Study progress message
- Visual status indicators

---

## 🛠 Tech Stack

- **Backend:** Python, Django
- **Frontend:** HTML, CSS, Bootstrap, JavaScript
- **Database:** SQLite (default)
- **Authentication:** Django Auth System

---

##  Project Structure

habit_tracker/
├── manage.py
├── README.md
├── habit_tracker/
│ ├── settings.py
│ ├── urls.py
│ └── ...
├── Home/
│ ├── views.py
│ ├── models.py
│ ├── templates/
│ └── ...
├── templates/
├── static/
└── db.sqlite3

---

##  Setup & Run

1. Clone the repository
```bash
git clone https://github.com/1Harsha123/HabitTracker.git
cd habit_tracker

2. python -m venv venv
venv\Scripts\activate

3. Install dependencies
pip install django

4. Run migrations
python manage.py migrate

5. Start server
python manage.py runserver

6. Open:
http://127.0.0.1:8000/



Author
Harsha Gupta
Junior Django Developer
India 🇮🇳
coder.harshaa@gmail.com
