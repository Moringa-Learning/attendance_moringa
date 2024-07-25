from flask import Flask, request, render_template, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import datetime
from dotenv import load_dotenv
from sqlalchemy.sql import text
from sqlalchemy import exc

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')

if 'sqlite' in db_uri:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri.replace('postgresql://', 'postgresql+psycopg2://')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
bcrypt = Bcrypt(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    students = db.relationship('Student', backref='owner', lazy=True)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Extras
def fetch_emails_from_db(user_id):
    try:
        with db.engine.connect() as connection:
            query = text(f"SELECT email FROM student WHERE user_id={user_id}")
            result = connection.execute(query)
            emails = [row[0] for row in result.fetchall()]
        return emails
    except exc.SQLAlchemyError as error:
        print(error)
        return []
    
def create_pdf_template(output_filename, num_days, emails):
    if not 1 <= num_days <= 6:
        raise ValueError("Number of days must be between 1 and 6")

    def build_headers(num_days):
        top_header = ['Email']
        second_header = ['']
        for i in range(num_days):
            top_header.extend([f'Day {i + 1}', ''])
            second_header.extend(['Time In', 'Sign'])
        return [top_header, second_header]

    headers = build_headers(num_days)
    data = headers + [[email] + [''] * (len(headers[0]) - 1) for email in emails]

    pdf = SimpleDocTemplate(output_filename, pagesize=A4)
    table = Table(data)
    style = TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 2), (0, -1), 'LEFT'),
    ])
    col_start = 1
    for i in range(num_days):
        col_end = col_start + 1
        style.add('SPAN', (col_start, 0), (col_end, 0))
        col_start += 2

    table.setStyle(style)
    pdf.build([table])

# Routes
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['pin']
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please log in.', 'warning')
            return redirect(url_for('login'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/add_students', methods=['GET', 'POST'])
@login_required
def add_students():
    if request.method == 'POST':
        emails = request.form['emails'].split()
        for email in emails:
            if email:
                existing_student = Student.query.filter_by(email=email, user_id=current_user.id).first()
                if not existing_student:
                    new_student = Student(email=email, owner=current_user)
                    db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('list_students'))
    return render_template('add_students.html')

@app.route('/list_students')
@login_required
def list_students():
    if current_user.is_authenticated:
        students = Student.query.filter_by(user_id=current_user.id).all()
        return render_template('list_students.html', students=students, noOfstudents=len(students))
    return "Unauthorized", 401

@app.route('/check_attendance', methods=['GET', 'POST'])
@login_required
def check_attendance():
    not_attended = None
    if request.method == 'POST':
        attending_list = request.form['attending_list'].split()
        main_list = [student.email for student in Student.query.filter_by(user_id=current_user.id).all()]
        not_attended = [email for email in main_list if email not in attending_list]
    return render_template('check_attendance.html', not_attended=not_attended)

@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        new_email = request.form['new_email']
        student.email = new_email
        db.session.commit()
        flash('Student updated successfully', 'success')
        return redirect(url_for('list_students'))
    return render_template('edit_student.html', student=student)

@app.route('/delete_student/<int:student_id>', methods=['GET', 'DELETE'])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash(f'{student.email} deleted successfully', 'info')
    return redirect(url_for('list_students'))

@app.route('/attendance_preview', methods=['GET', 'POST'])
@login_required
def attendance_preview():
    if request.method == 'POST':
        num_days = int(request.form['num_days'])
        emails = fetch_emails_from_db(current_user.id)
        return render_template('attendance_preview.html', num_days=num_days, emails=emails)
    return render_template('generate_pdf.html')

@app.route('/generate_pdf', methods=['POST'])
@login_required
def generate_pdf():
    num_days = int(request.form['num_days'])
    emails = fetch_emails_from_db(current_user.id)
    output_filename = f'attendance/attendance_template-{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.pdf'
    create_pdf_template(output_filename, num_days, emails)
    return send_file(output_filename, as_attachment=True)

@app.route('/manage_files', methods=['GET'])
@login_required
def manage_files():
    files = os.listdir('attendance')
    files = [f for f in files if f.endswith('.pdf')]
    return render_template('manage_files.html', files=files)

@app.route('/view_file/<filename>', methods=['GET'])
@login_required
def view_file(filename):
    return send_file(os.path.join('attendance', filename))

@app.route('/delete_file/<filename>', methods=['GET', 'POST', 'DELETE'])
@login_required
def delete_file(filename):
    file_path = os.path.join('attendance', filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f'{filename} has been deleted.', 'success')
    else:
        flash(f'{filename} does not exist.', 'danger')
    return redirect(url_for('manage_files'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
