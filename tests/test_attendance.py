import unittest
from flask_bcrypt import Bcrypt
from app import app, db, User, Student, create_pdf_template
import os
from dotenv import load_dotenv

bcrypt = Bcrypt(app)
load_dotenv()


class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
            'SQLALCHEMY_DATABASE_URI_TEST')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def create_user(self, username='testuser', password='testpassword'):
        with app.app_context():
            hashed_password = bcrypt.generate_password_hash(
                password).decode('utf-8')
            user = User(username=username, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            return user

    def test_home_page_requires_login(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)

    def test_user_registration(self):
        response = self.app.post('/register', data={
            'username': 'newuser',
            'pin': 'password'
        }, follow_redirects=True)
        self.assertIn(b'Your account has been created!', response.data)

    def test_user_login(self):
        self.create_user()
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertIn(b'Logout', response.data)

    def test_add_students(self):
        with app.app_context():
            user = self.create_user()

            response = self.app.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword'
            }, follow_redirects=True)

            with db.session.no_autoflush:
                response = self.app.post('/add_students', data={
                    'emails': 'student1@example.com student2@example.com'
                }, follow_redirects=True)
                self.assertEqual(response.status_code, 200)

                user = User.query.filter_by(username='testuser').first()
                students = Student.query.filter_by(user_id=user.id).all()
                self.assertEqual(len(students), 2)

    def test_create_pdf_template(self):
        emails = ['student1@example.com', 'student2@example.com']
        output_filename = 'test.pdf'
        num_days = 3

        create_pdf_template(output_filename, num_days, emails)
        self.assertTrue(os.path.exists(output_filename))
        os.remove(output_filename)


if __name__ == '__main__':
    unittest.main()
