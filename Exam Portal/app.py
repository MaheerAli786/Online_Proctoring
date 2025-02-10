import sqlite3
from flask import Flask, render_template, request, redirect, flash ,url_for, session
import random
from datetime import datetime, timedelta
import json
import cv2
import base64
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'Venky@123'
# Function to create the database and tables
def create_db():
    connection = sqlite3.connect('Exam Portal/instance1.db')
    cursor = connection.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Unique ID for each student
    full_name TEXT NOT NULL,                     -- Full name of the student
    mobile TEXT NOT NULL,                        -- Mobile number of the student
    branch TEXT NOT NULL,                        -- Branch/Department of the student (e.g., "CSE", "ECE")
    year INTEGER NOT NULL,                       -- Year of study (e.g., 1, 2, 3, 4)
    gender TEXT NOT NULL,                        -- Gender of the student (e.g., "Male", "Female", "Other")
    photo BLOB,                                  -- Student's photo stored as a BLOB (Binary Large Object)
    abc_id TEXT UNIQUE NOT NULL,                 -- Unique ABC ID for the student
    mail TEXT UNIQUE NOT NULL,                   -- Email address of the student
    password TEXT NOT NULL,                      -- Encrypted password for authentication
    role TEXT NOT NULL CHECK (role IN ('student', 'faculty', 'admin')) -- Role: 'student' or 'admin'
);
    
    ''')

    # Commit the changes and close the connection
    connection.commit()
    connection.close()

create_db()
# Function to convert image to binary data
def convert_to_binary(filename):
    with open(filename, 'rb') as file:
        return file.read()


def get_db_connection():
    conn = sqlite3.connect('Exam Portal/instance1.db')  # Timeout to avoid lock
    conn.row_factory = sqlite3.Row
    return conn

user_data = {
    'student_id': None,
    'full_name': None,
    'mobile': None,
    'branch': None,
    'year': None,
    'gender': None,
    'abc_id': None,
    'email': None,
    'photo': None
}
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
            global user_data
            cursor = conn.cursor()
            cursor.execute("""
                    SELECT * FROM students WHERE (full_name = ? OR mail = ?) AND password = ?
                """, (username,username, password))
            user = cursor.fetchone()
            print(user)

            if user:
                # Extract user details and set session variables
                session['student_id'] = user[0]
                session['full_name'] = user[1]
                session['mobile'] = user[2]
                session['branch'] = user[3]
                session['year'] = user[4]
                session['gender'] = user[5]
                session['abc_id'] = user[7]
                session['email'] = user[8]
                session['role'] = user[9]

                #storing in global 
                user_data['student_id'] = session['student_id']
                user_data['full_name'] = session['full_name']
                user_data['mobile'] = session['mobile']
                user_data['branch'] = session['branch']
                user_data['year'] = session['year']
                user_data['gender'] = session['gender']
                user_data['abc_id'] = session['abc_id']
                user_data['email'] = session['email']
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT photo FROM students WHERE student_id = ?
                    """, (session['student_id'],))
                    photo_data = cursor.fetchone()

                    if photo_data and photo_data[0]:
                        # Convert binary data to base64 string
                        base64_image = base64.b64encode(photo_data[0]).decode('utf-8')
                        user_data['photo'] = base64_image
                    else:
                        user_data['photo'] = None
                return render_template('Homepage.html',user = user_data)
            else:
                flash("Invalid username",'danger')
                return render_template('Login.html')
    return render_template('Login.html')

@app.route('/index')
def index():
    return render_template('Homepage.html',user = user_data)


@app.route('/details',methods=['POST'])
def details():
    if request.method == 'POST':
        user = request.form['user']
        password = request.form['password']
        print(user,password)
        return render_template('Homepage.html')
    return render_template('Login.html')

@app.route('/view_profile')
def view_profile():
    # Retrieve data from session
    user_data = {
        'student_id': session.get('student_id'),
        'full_name': session.get('full_name'),
        'mobile': session.get('mobile'),
        'branch': session.get('branch'),
        'year': session.get('year'),
        'gender': session.get('gender'),
        'abc_id': session.get('abc_id'),
        'email': session.get('email'),
        'role': session.get('role')
    }
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT photo FROM students WHERE student_id = ?
        """, (session['student_id'],))
        photo_data = cursor.fetchone()

        if photo_data and photo_data[0]:
            # Convert binary data to base64 string
            base64_image = base64.b64encode(photo_data[0]).decode('utf-8')
            user_data['photo'] = base64_image
        else:
            user_data['photo'] = None

    
    # Render the template and pass the user data
    return render_template('viewprofile.html', user=user_data)

# Route to create the database and tables (you can call this when setting up)
@app.route('/create_db')
def setup_db():
    create_db()
    return 'Database and tables created successfully!'

@app.route('/Exams')
def exams():
    return render_template('Exam.html',user = user_data)

@app.route('/Maths_Exam')
def maths_exam():
    return render_template('Maths.html')

@app.route('/Results')
def results():
    return render_template('Results.html',user = user_data)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
