from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import datetime
from models import db, Student, Admin, TestResult, Notification, Question

import os

# إعداد المسار الكامل للقاعدة
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'secret-key'  # مفتاح ضروري للـ flash messages


# إعداد قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'DB', 'DBfile.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تهيئة قاعدة البيانات
db.init_app(app)




# إنشاء الجداول
with app.app_context():
    db.create_all()

@app.route('/test/<int:student_id>', methods=['GET', 'POST'])
def take_test(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        answers = request.form
        correct = 0
        for qid, user_answer in answers.items():
            question = Question.query.get(int(qid))
            if question and question.correct_option == user_answer:
                correct += 1

        status = 'Pass' if correct >= 6 else 'Fail'
        result = TestResult(student_id=student.id, score=correct, status=status)
        db.session.add(result)
        db.session.commit()

        flash(f'تم تقديم الاختبار. الدرجة: {correct}/10 - {"ناجح" if status == "Pass" else "راسب"}', 'info')
        return redirect(url_for('dashboard', student_id=student.id))

    questions = Question.query.order_by(func.random()).limit(10).all()
    return render_template('test.html', questions=questions, student=student)



@app.route('/dashboard/<int:student_id>')
def dashboard(student_id):
    student = Student.query.get_or_404(student_id)
    test_result = TestResult.query.filter_by(student_id=student.id).order_by(TestResult.submission_date.desc()).first()
    all_results = TestResult.query.filter_by(student_id=student.id).order_by(TestResult.submission_date.desc()).all()
    notifications = Notification.query.filter_by(student_id=student.id).order_by(Notification.sent_at.desc()).all()
    return render_template('dashboard.html', student=student, test_result=test_result,
                           all_results=all_results, notifications=notifications)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        student = Student.query.filter_by(email=email, password_hash=password).first()
        if student:
            session['user_type'] = 'student'
            session['user_name'] = student.name
            session['student_id'] = student.id

            if student.status != 'Accepted':
                flash('Account is not activated yet.', 'warning')
                return redirect(url_for('login'))

            flash('Login successful!', 'success')
            return redirect(url_for('dashboard', student_id=student.id))
        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        admin = Admin.query.filter_by(email=email, password_hash=password).first()
        if admin:
            session['user_type'] = 'admin'
            session['user_name'] = admin.name
            session['admin_id'] = admin.id
            flash('Welcome, admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("تم تسجيل الخروج", "info")
    return redirect(url_for('home'))

@app.route('/')
def home():
    user_type = session.get('user_type')
    if user_type == 'student':
        student_id = session.get('student_id')
        return redirect(url_for('dashboard', student_id=student_id))
    elif user_type == 'admin':
        return redirect(url_for('admin_dashboard'))
    return render_template('index.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    students = Student.query.filter_by(status='Pending').all()
    return render_template('admin_dashboard.html', students=students)

@app.route('/admin/approve/<int:student_id>')
def approve_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.status = 'Accepted'
    db.session.commit()
    flash(f'Student {student.name} approved.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:student_id>')
def reject_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.status = 'Rejected'
    db.session.commit()
    flash(f'Student {student.name} rejected.', 'danger')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/notify', methods=['GET', 'POST'])
def send_notification():
    students = Student.query.filter_by(status='Accepted').all()

    if request.method == 'POST':
        student_id = int(request.form['student_id'])
        message = request.form['message']

        notification = Notification(student_id=student_id, message=message)
        db.session.add(notification)
        db.session.commit()

        flash('تم إرسال الإشعار بنجاح!', 'success')
        return redirect(url_for('admin_dashboard'))  # إعادة التوجيه بعد الإرسال

    return render_template('notifications.html', students=students)

@app.route('/admin/add-question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        question = Question(
            text=request.form['text'],
            option_a=request.form['option_a'],
            option_b=request.form['option_b'],
            option_c=request.form['option_c'],
            correct_option=request.form['correct_option']
        )
        db.session.add(question)
        db.session.commit()
        flash("تمت إضافة السؤال بنجاح", 'success')
        return redirect(url_for('add_question'))
    return render_template('add_question.html')


# Route: صفحة تسجيل الطالب
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']  # لاحقًا يتم تشفيره

        existing = Student.query.filter_by(email=email).first()
        if existing:
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))

        new_student = Student(
            name=name,
            email=email,
            phone=phone,
            password_hash=password
        )
        db.session.add(new_student)
        db.session.commit()

        flash('Registration successful! Your account is pending approval.', 'success')
        return redirect(url_for('register'))

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
