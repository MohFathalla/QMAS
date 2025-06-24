# 🕌 Quran Memorization Admission System (QMAS)

**QMAS** is a web-based platform designed to manage the admission and evaluation process for Quran memorization programs. It streamlines student registration, automates evaluation through MCQ testing, and enables administrators to monitor student progress and communicate via internal notifications.

---

## 🚀 Features

- 📥 Student self-registration
- ✅ Admin approval and status control (Pending / Accepted / Rejected)
- 🧪 Automatic MCQ qualification test (10 randomized questions)
- 📊 Student dashboard showing status, score history, and notifications
- 📢 Admin dashboard with student management and notification system
- 🔐 Role-based login system (Students / Admins)
- 📅 Retake option after failure (only after 7 days)

---

## 🛠️ Tech Stack

- **Frontend**: HTML, Bootstrap 5 (RTL support), Jinja2
- **Backend**: Python, Flask
- **Database**: SQLite
- **ORM**: SQLAlchemy

---

## 🗃️ Database Schema

Entities:
- Students
- Admins
- Test Results
- Notifications
- MCQ Questions
- User Sessions

Relational Design follows normalized structure with ERD mapping included in `/docs`.

---

## 📸 Screenshots

> Add screenshots in `/screenshots/` folder and reference them here (login page, dashboards, test view).

---

## 🧪 Running the Project Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/MohFathalla/QMAS
   cd qmas
