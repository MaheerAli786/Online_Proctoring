import sqlite3
from flask import Flask, render_template, request, redirect, flash ,url_for, session
from faker import Faker
import random
from datetime import datetime, timedelta
import json
import cv2

# # Initialize Faker for realistic data generation
# fake = Faker()

# def populate_db():
#     connection = sqlite3.connect('exam_portal.db')
#     cursor = connection.cursor()

#     # Insert Users (Admins and Students)
#     users = []
#     for _ in range(5):  # Admins
#         users.append((fake.name(), fake.email(), fake.password(), 'admin'))
#     for _ in range(15):  # Students
#         users.append((fake.name(), fake.email(), fake.password(), 'student'))
#     cursor.executemany("""
#         INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)""", users)
    
#     # Fetch inserted user IDs
#     cursor.execute("SELECT user_id FROM users WHERE role='admin'")
#     admin_ids = [row[0] for row in cursor.fetchall()]
#     cursor.execute("SELECT user_id FROM users WHERE role='student'")
#     student_ids = [row[0] for row in cursor.fetchall()]
    
#     # Insert Exams
#     subjects = ['Mathematics', 'Physics', 'Chemistry', 'Computer Science', 'Biology']
#     exams = []
#     for _ in range(10):
#         exams.append((
#             fake.sentence(nb_words=3),
#             fake.date_time_between(start_date='-30d', end_date='+30d').strftime('%Y-%m-%d %H:%M:%S'),
#             random.randint(30, 180),
#             random.choice(subjects),
#             random.choice(admin_ids)
#         ))
#     cursor.executemany("""
#         INSERT INTO exams (exam_name, exam_date, duration, subject, created_by) VALUES (?, ?, ?, ?, ?)""", exams)
    
#     # Fetch inserted exam IDs
#     cursor.execute("SELECT exam_id FROM exams")
#     exam_ids = [row[0] for row in cursor.fetchall()]
    
#     # Insert Questions
#     questions = []
#     for exam_id in exam_ids:
#         for _ in range(5):  # 5 questions per exam
#             question_type = random.choice(['mcq', 'descriptive'])
#             options = json.dumps([fake.word() for _ in range(4)]) if question_type == 'mcq' else None
#             correct_answer = random.choice(json.loads(options)) if options else fake.sentence()
#             questions.append((exam_id, fake.sentence(), question_type, options, correct_answer))
#     cursor.executemany("""
#         INSERT INTO questions (exam_id, question_text, question_type, options, correct_answer) VALUES (?, ?, ?, ?, ?)""", questions)
    
#     # Fetch inserted question IDs
#     cursor.execute("SELECT question_id, options FROM questions")
#     question_data = cursor.fetchall()
    
#     # Insert Responses
#     responses = []
#     for student_id in student_ids:
#         for exam_id in random.sample(exam_ids, k=5):  # Each student takes 5 exams
#             for question_id, options in random.sample(question_data, k=3):  # Each student answers 3 questions per exam
#                 if options:
#                     option_list = json.loads(options)
#                     selected_option = random.choice(option_list)
#                     response_text = None
#                 else:
#                     selected_option = None
#                     response_text = fake.sentence()
#                 responses.append((exam_id, student_id, question_id, response_text, selected_option))
#     cursor.executemany("""
#         INSERT INTO responses (exam_id, user_id, question_id, response_text, selected_option) VALUES (?, ?, ?, ?, ?)""", responses)
    
#     # Insert Results
#     results = []
#     for student_id in student_ids:
#         for exam_id in random.sample(exam_ids, k=5):
#             results.append((exam_id, student_id, random.randint(0, 100), random.randint(600, 5400)))
#     cursor.executemany("""
#         INSERT INTO results (exam_id, user_id, total_score, time_taken) VALUES (?, ?, ?, ?)""", results)
    
#     # Commit and close connection
#     connection.commit()
#     connection.close()

# populate_db()
# print("Database populated successfully!")

app = Flask(__name__)
app.secret_key = 'Venky@123'
# Function to create the database and tables
def create_db():
    connection = sqlite3.connect('exam_portal.db')
    cursor = connection.cursor()

    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT CHECK(role IN ('admin', 'student')) NOT NULL
        )
    ''')

    # Create Exams table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_name TEXT NOT NULL,
            exam_date DATETIME NOT NULL,
            duration INTEGER NOT NULL,
            subject TEXT NOT NULL,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        )
    ''')

    # Create Questions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            question_text TEXT NOT NULL,
            question_type TEXT CHECK(question_type IN ('mcq', 'descriptive')) NOT NULL,
            options TEXT,  -- For storing options as JSON (optional)
            correct_answer TEXT NOT NULL,
            FOREIGN KEY (exam_id) REFERENCES exams(exam_id)
        )
    ''')

    # Create Responses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            response_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            user_id INTEGER,
            question_id INTEGER,
            response_text TEXT,
            selected_option TEXT,
            FOREIGN KEY (exam_id) REFERENCES exams(exam_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (question_id) REFERENCES questions(question_id)
        )
    ''')

    # Create Results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            user_id INTEGER,
            total_score INTEGER NOT NULL,
            time_taken INTEGER NOT NULL,  -- Time in seconds
            FOREIGN KEY (exam_id) REFERENCES exams(exam_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')

    # Commit the changes and close the connection
    connection.commit()
    connection.close()

def get_db_connection():
    conn = sqlite3.connect('exam_portal.db')  # Timeout to avoid lock
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['user']
        password = request.form['password']
        user = ''

        if  not username or not password:
            flash('Please provide all required fields (username, password, role).', 'danger')
            return render_template('Login.html')

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                    SELECT * FROM users WHERE (full_name = ? OR email = ?) AND password_hash = ?
                """, (username,username, password))
            user = cursor.fetchone()
            print(user)

            if user:
                # Extract user details and set session variables
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['email'] = user[2]
                session['role'] = user[4]
                print(session['user_id'],session['username'],session['email'],session['role'])
                return render_template('Homepage.html')
            else:
                flash("Invalid username",'danger')
                return render_template('Login.html')
    return render_template('Login.html')

@app.route('/index')
def index():
    return render_template('Homepage.html')


@app.route('/details',methods=['POST'])
def details():
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']
        print(user,password)
        return render_template('Homepage.html')
    return render_template('Login.html')

@app.route('/signup')
def signup():
    return render_template('SignUp.html')

@app.route('/view_profile')
def view_profile():
    user = {'username':session['username'],'email':session['email'] ,'role':session['role']}
    return render_template('viewprofile.html',user = user)

# Route to create the database and tables (you can call this when setting up)
@app.route('/create_db')
def setup_db():
    create_db()
    return 'Database and tables created successfully!'

@app.route('/Exams')
def exams():
    return render_template('Exam.html')

@app.route('/Maths_Exam')
def maths_exam():
    return render_template('Maths.html')

@app.route('/Results')
def results():
    return render_template('Results.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
