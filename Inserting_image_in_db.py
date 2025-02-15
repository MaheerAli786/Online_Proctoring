import mysql.connector
import requests

def insert_student_data(studentid, name, password, email, gender, year, contact):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="Exam"
        )
        cursor = conn.cursor()

        # Fetch the image from the URL
        url = f"https://intranet.rguktn.ac.in/SMS/usrphotos/user/{studentid.upper()}.jpg"
        response = requests.get(url)
        image = response.content  # Fixed: Removed ()

        # Corrected SQL Query
        sql = "INSERT INTO Student(studentid, name, password, email, gender, year, contact, image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        
        # Execute Query with Correct Parameters
        cursor.execute(sql, (studentid, name, password, email, gender, year, contact, image))
        conn.commit()

        print("Data inserted successfully!")

    except mysql.connector.Error as err:
        print("Error:", err)
    
    finally:
        cursor.close()
        conn.close()

# Calling function with correct arguments
insert_student_data("n200579", "Varshitha Ramavath", "Varshitha@123", "n200579@rguktn.ac.in", "Female", 3, "7989693716")
