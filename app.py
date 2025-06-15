from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# إعداد المسار الكامل للقاعدة
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'secret-key'  # مفتاح ضروري للـ flash messages


# إعداد قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'DB', 'DBfile.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تهيئة قاعدة البيانات
db = SQLAlchemy(app)

# تعريف النماذج
class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)

    test_results = db.relationship('TestResult', backref='student', cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='student', cascade="all, delete-orphan")

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TestResult(db.Model):
    __tablename__ = 'test_results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

# إنشاء الجداول
with app.app_context():
    db.create_all()

@app.route('/test/<int:student_id>', methods=['GET', 'POST'])
def take_test(student_id):
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        total_score = 0
        for i in range(1, 11):
            answer = int(request.form.get(f'q{i}', 0))
            total_score += answer

        status = 'Pass' if total_score >= 6 else 'Fail'

        result = TestResult(student_id=student.id, score=total_score, status=status)
        db.session.add(result)
        db.session.commit()

        flash(f'Test submitted! You scored {total_score}/10 ({status})', 'info')
        return redirect(url_for('dashboard', student_id=student.id))

    return render_template('test.html')


@app.route('/dashboard/<int:student_id>')
def dashboard(student_id):
    student = Student.query.get_or_404(student_id)
    test_result = TestResult.query.filter_by(student_id=student.id).first()
    notifications = Notification.query.filter_by(student_id=student.id).all()

    return render_template('dashboard.html', student=student, test_result=test_result, notifications=notifications)


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
