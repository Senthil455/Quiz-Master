# 🎓 Quiz Master

A role‑based web platform for quiz creation, participation, and performance tracking, designed for **students, teachers, and admins** in academic or training environments.

---

## 🧠 Overview

**Quiz Master** is a full‑stack web application built with **HTML, CSS, JavaScript, Python (Flask), and PostgreSQL**. It enables:

- Secure user authentication and role‑based access.  
- Teachers to create, manage, and schedule quizzes.  
- Students to participate in quizzes and view results.  
- Admins to oversee users, assignments, and performance analytics.  

This project serves as a clean, portfolio‑grade example of a **data‑driven educational platform** with backend logic, relational modeling, and structured UI workflows.

---

## 🛠️ Tech Stack

- **Frontend**  
  - HTML5, CSS3, JavaScript (vanilla).  
  - Simple, responsive layouts for dashboards and forms.  

- **Backend**  
  - **Python** with **Flask** for routing and business logic.  
  - **PostgreSQL** for relational data storage (users, quizzes, questions, results).  

- **Security**  
  - **bcrypt** for secure password hashing.  
  - Role‑based access control (Student / Teacher / Admin).  

- **Deployment‑ready basics**  
  - Pure Python + Flask, easy to containerize or host on lightweight platforms.

---

## ✨ Key Features

### User Roles & Authentication

- Three roles: **Student**, **Teacher**, and **Admin**.  
- Secure login and registration with **bcrypt‑hashed passwords**.  
- Role‑based dashboards with tailored menus and views.

### Quiz Management

- **Teachers** can:
  - Create quizzes with multiple questions (MCQ / text‑based).  
  - Set time limits, difficulty, and visibility.  
  - Assign quizzes to specific students or classes.  

- **Admins** can:
  - Approve or delete quizzes.  
  - View overall quiz statistics and usage.

### Quiz Participation

- **Students** can:
  - See assigned quizzes with status (upcoming / active / completed).  
  - Start and submit quizzes within the time limit.  
  - View immediate feedback or review answers (configurable).  

### Result Tracking & Analytics

- Individual results per quiz (score, percentage, time taken).  
- Leaderboard‑style dashboards for high performers.  
- Centralized view for admins and teachers to track class‑level performance.

### Role‑Based Dashboards

- **Student Dashboard**  
  - Active quizzes, results, and upcoming assessments.  

- **Teacher Dashboard**  
  - Quiz creation, question bank, scoring, and student performance.  

- **Admin Dashboard**  
  - User management, role assignment, overall system metrics.

---

## 📂 Project Structure

```text
Quiz-Master/
├── static/              # CSS, JS, and static assets
│   ├── css/             # Stylesheets
│   └── js/              # Client‑side scripts
├── templates/           # HTML templates (Jinja2)
│   ├── base.html        # Base layout
│   ├── login.html
│   ├── register.html
│   ├── student/
│   ├── teacher/
│   └── admin/
├── app.py               # Flask application (routes, models, auth)
└── README.md            # This file
```

Developed and maintained by **Senthil Raja R** — Full Stack Developer | AI Automation Enthusiast.  
🔗 GitHub: [https://github.com/Senthil455/Quiz-Master](https://github.com/Senthil455/Quiz-Master)  
🔗 Profile: [https://github.com/Senthil455](https://github.com/Senthil455)

---

## ⚙️ Getting Started

### Prerequisites

- Python 3.8+  
- PostgreSQL installed or access to a PostgreSQL instance  
- `pip` for Python package management  

### 1. Clone the repository

```bash
git clone https://github.com/Senthil455/Quiz-Master.git
cd Quiz-Master
```

### 2. Install dependencies

```bash
pip install -r requirements.txt   # if a requirements.txt file exists
```

If there’s no `requirements.txt`, at minimum you’ll need:

```bash
pip install flask psycopg2-binary bcrypt
```

### 3. Configure database

- Create a PostgreSQL database (e.g., `quiz_master`).  
- Update connection details in `app.py` or a config file if you add one:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost:5432/quiz_master'
```

(Adjust `username`, `password`, and `host` as needed.)

### 4. Initialize the app

The current `app.py` already contains routes and simple database logic. You can run it directly:

```bash
python app.py
```

- Default: `http://localhost:5000` (adjust port in `app.py` if needed).

---

## 🔐 Security & Data Modeling

- **Password security** via **bcrypt** (hashed, salted passwords).  
- **Role‑based authorization** built into route logic (no direct access between roles).  
- **PostgreSQL normalization** for:
  - Users (with role flags).  
  - Quizzes and questions.  
  - Results and score tracking.  

This structure makes it easy to extend with **additional roles, permissions, or analytics** in the future.

---

## 🚀 Where This Project Excels (Portfolio Value)

- **Educational platform pattern**: Mimics real‑world LMS‑style flows (assignment, grading, dashboards).  
- **Relational design showcase**: Clean separation of users, quizzes, questions, and results.  
- **Role‑based access demonstration**: Great for junior‑to‑mid‑level interviews.  
- **Extensible base**: Easy to add:
  - Timer‑based sessions.  
  - Question‑bank import/export.  
  - PDF result reports.  
  - Token‑based login or OAuth.

---

## 📫 Let’s Connect

- 📧 **Email**: [senthilrajasen637@gmail.com](mailto:senthilrajasen637@gmail.com)  
- 🔗 **GitHub Profile**: [https://github.com/Senthil455](https://github.com/Senthil455)  

---

Build with 💡 using **Flask, PostgreSQL, HTML, CSS, and JavaScript**  
A solid, role‑based quiz platform ready for extension and experimentation.  
