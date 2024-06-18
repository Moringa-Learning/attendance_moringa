from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['pin']
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
        else:
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
    students = Student.query.all()
    return render_template('list_students.html', students=students, noOfstudents=len(students))

@app.route('/check_attendance', methods=['GET', 'POST'])
@login_required
def check_attendance():
    not_attended = None
    if request.method == 'POST':
        attending_list = request.form['attending_list'].split()
        main_list = [student.email for student in Student.query.all()]
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

@app.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted successfully', 'success')
    return redirect(url_for('list_students'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
