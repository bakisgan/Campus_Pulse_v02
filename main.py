import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QDateTimeEdit, QStackedWidget, QMessageBox, QWidget, QTableWidget, QTableWidgetItem, QCheckBox, QLabel, QCalendarWidget, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QDate, QDateTime
from PyQt5.uic import loadUi

import re
from datetime import datetime
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QMessageBox
from passlib.hash import bcrypt
import psycopg2



os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"


# Database connection details
database_name = "db_campusv2"
user = "postgres"
# "MerSer01"
password = "MerSer01"
host = "localhost"
port = "5432"

global_user_id = None
# Construct the database URL
db_url = f"postgresql://{user}:{password}@{host}:{port}/{database_name}"


def create_tables():

    # List of CREATE TABLE statements
    create_table_queries = [
        """
        CREATE TABLE IF NOT EXISTS application (
        "application_id" SERIAL PRIMARY KEY,
        "email" VARCHAR(100) UNIQUE NOT NULL,
        "password" VARCHAR(60) NOT NULL,
        "first_name" VARCHAR(50),
        "last_name" VARCHAR(50),
        "phone" VARCHAR(15),
        "city" VARCHAR(30),
        "gender" VARCHAR(10),
        "birthdate" DATE,
        "status" BOOLEAN
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS usertable (
        "user_id" SERIAL PRIMARY KEY,
        "email" VARCHAR(100) UNIQUE NOT NULL,
        "password" VARCHAR(60) NOT NULL,
        "first_name" VARCHAR(50),
        "last_name" VARCHAR(50),
        "phone" VARCHAR(15),
        "city" VARCHAR(30),
        "gender" VARCHAR(10),
        "birthdate" DATE,
        "user_type" VARCHAR(20),
        "status" BOOLEAN,
        "application_id" INT,
        CONSTRAINT "fk_application_id" FOREIGN KEY ("application_id") REFERENCES "Application"("application_id")
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS lesson (
        "lesson_id" SERIAL PRIMARY KEY,
        "lesson_name" VARCHAR(50)
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS calendar (
        "calendar_id" SERIAL PRIMARY KEY,
        "lesson_id" INT,
        "teacher_id" INT,
        "creation_date" TIMESTAMP,
        "planned_date" TIMESTAMP,
        "student_id" INT,
        "status" BOOLEAN,
        CONSTRAINT fk_lesson FOREIGN KEY ("lesson_id") REFERENCES "Lesson"("lesson_id"),
        CONSTRAINT fk_teacher FOREIGN KEY ("teacher_id") REFERENCES "User"("user_id"),
        CONSTRAINT fk_student FOREIGN KEY ("student_id") REFERENCES "User"("user_id")
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS announcement (
        "announcement_id" SERIAL PRIMARY KEY,
        "teacher_id" INT,
        "text" VARCHAR(255),
        "date" TIMESTAMP,
        "deadline" DATE,
        CONSTRAINT fk_teacher_announcement FOREIGN KEY ("teacher_id") REFERENCES "User"("user_id")
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS task (
        "task_id" SERIAL PRIMARY KEY,
        "teacher_id" INT,
        "text" VARCHAR(255),
        "date" TIMESTAMP,
        "deadline" DATE,
        "status" BOOLEAN,
        "student_id" INT,
        CONSTRAINT fk_teacher_task FOREIGN KEY ("teacher_id") REFERENCES "User"("user_id"),
        CONSTRAINT fk_student_task FOREIGN KEY ("student_id") REFERENCES "User"("user_id")
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS logtable (
        "log_id" SERIAL PRIMARY KEY,
        "user_id" INT,
        "event_type" VARCHAR(50),
        "time_stamp" TIMESTAMP,
        "action" VARCHAR(255),
        "type" VARCHAR(50),
        CONSTRAINT fk_user_log FOREIGN KEY ("user_id") REFERENCES "User"("user_id")
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS chat (
        "chat_id" SERIAL PRIMARY KEY,
        "sender_id" INT,
        "receiver_id" INT,
        "text" VARCHAR(255),
        "date" TIMESTAMP,
        "status" BOOLEAN,
        CONSTRAINT fk_sender FOREIGN KEY ("sender_id") REFERENCES "User"("user_id"),
        CONSTRAINT fk_receiver FOREIGN KEY ("receiver_id") REFERENCES "User"("user_id")
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS hashedpasswords (
        "hash_id" SERIAL PRIMARY KEY,
        "user_id" INT UNIQUE NOT NULL,
        "hashed_password" VARCHAR(60) NOT NULL,
        FOREIGN KEY ("user_id") REFERENCES "User"("user_id") ON DELETE CASCADE
        )
        """
    ]


    # Connect to the PostgreSQL database
    conn = psycopg2.connect(db_url)

    # Create a cursor object to interact with the database
    cur = conn.cursor()

    try:
        # Execute each CREATE TABLE statement
        for query in create_table_queries:
            cur.execute(query)

        # Commit the changes to the database
        conn.commit()

        print("Tables created successfully!")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Close the cursor and connection
        cur.close()
        conn.close()



class Login(QMainWindow):
    """
    Class representing the login window of the application.

    Attributes:
    - signup_btn: Button for switching to the signup form.
    - contact_adm_btn: Button for switching to the contact admin form.
    - loginbutton: Button for initiating the login process.
    - email_LE: Line edit for entering the email.
    - password_LE: Line edit for entering the password.
    """
        
    def __init__(self):
        """
        Initializes the Login window.

        Connects signals to corresponding slots and loads the UI from 'login.ui'.  
        """
        super(Login, self).__init__()
        loadUi('login.ui', self)

        self.signup_btn.clicked.connect(self.switch_signupform)
        self.contact_adm_btn.clicked.connect(self.switch_adminform)
        self.loginbutton.clicked.connect(self.switch_student)



    def switch_signupform(self):
        """
        Switches to the signup form when the signup button is clicked.
        Clears line edits in the signup form.
        """
        stackedWidget.setCurrentIndex(1)
        signup.clear_line_edits_signupform()

    def switch_adminform(self):
        """
        Switches to the admin form when the contact admin button is clicked.
        Clears line edits in the contact admin form.
        """
        stackedWidget.setCurrentIndex(2)
        cont_admin.clear_line_edits_contactadmin()


    def switch_student(self):
        """
        Initiates the login process when the login button is clicked.

        Retrieves email and password, checks against stored accounts, and switches to
        corresponding user interfaces (Student, Teacher, Admin).
        Displays error messages for incorrect credentials or file-related issues.
        """
        email = self.email_LE.text()
        password = self.password_LE.text()
        global global_user_id
        global db_url

        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("SELECT password FROM usertable WHERE email = %s", (email,))

            stored_password_data = cur.fetchone()
            if stored_password_data:
                stored_hashed_password = stored_password_data[0]
                password_match = bcrypt.verify(password, stored_hashed_password)

                if password_match:
                    # Fetch user data
                    cur.execute("SELECT * FROM usertable WHERE email = %s", (email,))
                    user_data = cur.fetchone()

                    if user_data:
                        global_user_id = user_data[0]
                        account_type = user_data[9]
                        
                        userprofile.name_line.setText(user_data[3])
                        userprofile.surname_line.setText(user_data[4])
                        userprofile.telephone_line.setText(user_data[5])
                        userprofile.mail_line.setText(user_data[1])
                        userprofile.type_line.setText(user_data[9])
                        userprofile.gender_line.setText(user_data[7])
                        if user_data[8] == None:
                            userprofile.birthdate_line.setText("")
                        else:
                            userprofile.birthdate_line.setText(user_data[8].strftime('%Y-%m-%d'))
                        userprofile.city_line.setText(user_data[6])
                        student.label_2.setText("Welcome, " + user_data[3])
                        student.label.setText(user_data[3] + " " + user_data[4])

                        if account_type == "Student":
                            stackedWidget.setCurrentIndex(3)
                            # student.load_attendance()
                            # student.load_tasks()
                            # student.load_announcements()
                            student.load_calendar_events()
                            student.show_tasks()
                            student.populate_table()
                            student.show_announcements()

                        elif account_type == "Teacher":
                            stackedWidget.setCurrentIndex(4)
                            # teacher.task_manager.load_data()
                            # teacher.populate_students_list()
                            # teacher.populate_students_table()
                            
                            # teacher.connect_table_signals() 
                            stackedWidget.setCurrentIndex(4)
                            # teacher.fill_courses()
                            teacher.pushButton_switchadmin.hide()
                            teacher.label_Name.setText(f"Welcome {user_data[3]} {user_data[4]}")
                            teacher.fill_courses()
                            teacher.fill_students()

                        elif account_type == "Admin":
                            # teacher.task_manager.load_data()
                            # teacher.populate_students_list()
                            # teacher.populate_students_table()
                            # teacher.pushButton_switchadmin.show()
                            stackedWidget.setCurrentIndex(5)
                            teacher.label_Name.setText(f"Welcome {user_data[3]} {user_data[4]}")
                            admin.fill_table()
                            teacher.fill_courses()
                            teacher.fill_students()

                    else:
                        self.show_error_message("User not found.")
                else:
                    self.show_error_message("Incorrect password.")
            else:
                self.show_error_message("User not found.")

        except Exception as e:
            self.show_error_message(f"Error: {str(e)}")

        finally:
            # Close database connection
            if cur:
                cur.close()
            if conn:
                conn.close()


    def show_error_message(self, message): #error messages
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("Error")
        error_box.setText(message)
        error_box.exec_()

    def clear_line_edits_loginform(self):
        """
        Clears line edits in the login form.
        """
        self.email_LE.clear()
        self.password_LE.clear()


class Signup(QMainWindow):
    """
    Class representing the signup window of the application.

    Attributes:
    - sign_up_but: Button for initiating the signup process.
    - Back_Log_but: Button for switching back to the login form.
    - signup_email_LE: Line edit for entering the signup email.
    - signup_password_LE: Line edit for entering the signup password.
    - confirmpass_LE: Line edit for confirming the signup password.
    - name_LE: Line edit for entering the user's name.
    - surname_LE: Line edit for entering the user's surname.
    """
    def __init__(self):
        """
        Initializes the Signup window.

        Connects signals to corresponding slots and loads the UI from 'signup.ui'.
        """
        super(Signup, self).__init__()
        loadUi('signup.ui', self)
        self.sign_up_but.clicked.connect(self.signup_swt_login)
        self.Back_Log_but.clicked.connect(self.switch_loginform)

    def signup_swt_login(self):
        """
        Initiates the signup process when the signup button is clicked.

        Retrieves user input, checks for existing email, password matching,
        and password strength. If all conditions are met, adds the new account
        to usertable and switches to the login form.
        """
        email = self.signup_email_LE.text()
        plain_password = self.signup_password_LE.text()
        plain_password_conf= self.confirmpass_LE.text()
        first_name = self.name_LE.text()
        last_name = self.surname_LE.text()
        phone = self.phone_LE.text()
        city = self.city_LE.text()
        gender = None
        birthdate = None
        user_type = "Student"
        application_id = None
        good_to_go=False
        global db_url
        registration_successful=False


        try:
            # Check for existing user in the database
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM usertable WHERE email = %s", (email,))

            existing_user = cur.fetchone()
            
            # Validate input fields
            if not email or not plain_password or not first_name or not phone or not city:
                self.show_error_message("Please fill in all required fields.")
                return
            elif existing_user:
                self.show_error_message("The email address provided already exists in our records. If you have an existing account, please proceed to the login page.")
                return
            elif plain_password != plain_password_conf:
                self.show_error_message("The passwords entered do not match. Please ensure that the passwords are identical and try again.")
            elif not self.password_strength(plain_password):
                self.show_error_message("Please use at least 2 uppercase, 2 lowercase, and 2 special characters. Minimum length is 8 characters.")
            else:
                hashed_password = bcrypt.hash(plain_password)

                cur.execute("""
                    INSERT INTO usertable (
                        email, password, first_name, last_name, phone, city, gender, birthdate, user_type, status, application_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (email, hashed_password, first_name, last_name, phone, city, gender, birthdate, user_type, True, application_id))



                registration_successful = True


        
        except Exception as e:
            self.show_error_message(f"An unexpected error occurred: {str(e)}")

        finally:
            # Close database connection
            if cur:
                cur.close()
            if conn:
                conn.commit()
                conn.close()

                                            
        if registration_successful:
            try:
                stackedWidget.setCurrentIndex(0)
                login.clear_line_edits_loginform()

                # Check for existing user in the database
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                #Insert into logtable
                cur.execute("select user_id from usertable where email = %s",(email,))
                user_id=cur.fetchone()[0]

                cur.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Usertable', CURRENT_TIMESTAMP, 'Student Account is created', 'Creation')
                """, (user_id,))
                
            except Exception as e:
                self.show_error_message(f"An unexpected error occurred while saving the account information: {str(e)}")
            finally:
                # Close database connection
                if cur:
                    cur.close()
                if conn:
                    conn.commit()
                    conn.close()




    def switch_loginform(self):
        """
        Switches back to the login form when the 'Back to Login' button is clicked.
        Clears line edits in the login form.
        """
        stackedWidget.setCurrentIndex(0)
        login.clear_line_edits_loginform()

    
    def show_error_message(self, message): #error messages
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("Error")
        error_box.setText(message)
        error_box.exec_()
    
    def password_strength(self, psword):
        """
        Checks the strength of the password.

        Args:
        - psword: The password to be checked.

        Returns:
        - True if the password meets strength requirements, False otherwise.
        """
        if len(psword) < 8:
            return False

        num_of_uppercase = 0
        num_of_lowercase = 0
        num_of_specialchars = 0

        for i in psword:
            if i.isupper():
                num_of_uppercase += 1
            elif i.islower():
                num_of_lowercase += 1
            elif not i.isalnum():
                num_of_specialchars += 1

        if num_of_lowercase < 2 or num_of_uppercase < 2 or num_of_specialchars < 2:
            return False

        return True
    
    def clear_line_edits_signupform(self):
        """
        Clears line edits in the signup form.
        """
        self.signup_email_LE.clear()
        self.signup_password_LE.clear()
        self.confirmpass_LE.clear()
        self.name_LE.clear()
        self.surname_LE.clear()
    
class ContactAdmin(QMainWindow):
    """
    Class representing the contact admin window of the application.

    Attributes:
    - Back_to_login_but: Button for switching back to the login form.
    - Create_TA_but: Button for creating a TA (Teacher Assistant) account.
    - TA_email_LE: Line edit for entering the TA's email.
    - TA_password_LE: Line edit for entering the TA's password.
    - TA_confirmpass_LE: Line edit for confirming the TA's password.
    - TA_name_LE: Line edit for entering the TA's name.
    - TA_surname_LE: Line edit for entering the TA's surname.
    """
    def __init__(self):
        """
        Initializes the ContactAdmin window.

        Connects signals to corresponding slots and loads the UI from 'contactadmin.ui'.
        """
        super(ContactAdmin, self).__init__()
        loadUi('contactadmin.ui', self)
        self.Back_to_login_but.clicked.connect(self.switch_loginform)
        self.Create_TA_but.clicked.connect(self.send_TA_Account)

    def switch_loginform(self):
        """
        Switches back to the login form when the 'Back to Login' button is clicked.
        Clears line edits in the login form.
        """
        stackedWidget.setCurrentIndex(0)
        login.clear_line_edits_loginform()

    
    def password_strength(self, psword):
        if len(psword) < 8:
            return False

        num_of_uppercase = 0
        num_of_lowercase = 0
        num_of_specialchars = 0

        for i in psword:
            if i.isupper():
                num_of_uppercase += 1
            elif i.islower():
                num_of_lowercase += 1
            elif not i.isalnum():
                num_of_specialchars += 1

        if num_of_lowercase < 2 or num_of_uppercase < 2 or num_of_specialchars < 2:
            return False

        return True

    def show_error_message(self, message): #error messages
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("Error")
        error_box.setText(message)
        error_box.exec_()

    def show_success_message(self, message):  # Add this method
        success_box = QMessageBox()
        success_box.setIcon(QMessageBox.Information)
        success_box.setWindowTitle("Success")
        success_box.setText(message)
        success_box.exec_()

    def send_TA_Account(self):
        """
        Sends a request to create a Teacher Assistant (TA) account.

        Retrieves user input, checks for existing requests, existing accounts,
        password matching, and password strength. If all conditions are met,
        adds the new TA account request to the application table.
        """
        email = self.TA_email_LE.text()
        plain_password = self.TA_password_LE.text()
        plain_password_conf= self.TA_confirmpass_LE.text()
        first_name = self.TA_name_LE.text()
        last_name = self.TA_surname_LE.text()
        phone = self.TA_phone_LE.text()
        city = self.TA_city_LE.text()
        gender = None
        birthdate = None
        # user_type = "Teacher"
        global db_url
        registration_successful=False

        try:
            # Check for existing user in the database
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM usertable WHERE email = %s", (email,))
            existing_user_active = cur.fetchone()
            cur.execute("SELECT application_id FROM application WHERE email = %s", (email,))
            existing_user_pending = cur.fetchone()


            if not email or not plain_password or not first_name or not phone or not city:
                self.show_error_message("Please fill in all required fields.")
                return
            elif existing_user_pending:
                self.show_error_message("Your previous application is pending. It will be activated soon!") #status'u kontrol et, active olanlar. yer değiştir
            elif existing_user_active:
                self.show_error_message("The email address provided already exists in our records. If you have an existing account, please proceed to the login page.")
            elif plain_password != plain_password_conf:
                self.show_error_message("The passwords entered do not match. Please ensure that the passwords are identical and try again.")
            elif not self.password_strength(plain_password):
                self.show_error_message("Please use at least 2 uppercase, 2 lowercase, and 2 special characters. Minimum length is 8 characters.")
            else:
                hashed_password = bcrypt.hash(plain_password)

                cur.execute("""
                    INSERT INTO application (
                        email, password, first_name, last_name, phone, city, gender, birthdate, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (email, hashed_password, first_name, last_name, phone, city, gender, birthdate, None))

                registration_successful = True
                self.show_success_message("Your application is received. It will be activated after confirmation. Thank you.")
        
        except Exception as e:
            self.show_error_message(f"An unexpected error occurred: {str(e)}")

        finally:
            # Close database connection
            if cur:
                cur.close()
            if conn:
                conn.commit()
                conn.close()


        if registration_successful:
            try:

                # Check for existing user in the database
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                #Insert into logtable
                cur.execute("select application_id from application where email = %s",(email,))
                application_id=cur.fetchone()[0]
                
                cur.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Application', CURRENT_TIMESTAMP, 'Teacher Account is requested', 'Creation')
                """, (application_id,))
                
            except Exception as e:
                self.show_error_message(f"An unexpected error occurred while saving the account information: {str(e)}")
            finally:
                # Close database connection
                if cur:
                    cur.close()
                if conn:
                    conn.commit()
                    conn.close()



    def clear_line_edits_contactadmin(self):
        """
        Clears line edits in the contact admin form.
        """
        self.TA_email_LE.clear()
        self.TA_password_LE.clear()
        self.TA_confirmpass_LE.clear()
        self.TA_name_LE.clear()
        self.TA_surname_LE.clear()


# class Teacher(QMainWindow):
#     def __init__(self):
#         super(Teacher, self).__init__()
#         loadUi('teacher_page.ui', self)
#         self.Chatboard_but.clicked.connect(self.switch_chatboard)

        
#     def switch_loginform(self):
#         stackedWidget.setCurrentIndex(0)
    
#     def switch_chatboard(self):
#         stackedWidget.setCurrentIndex(6)
#         chatboard.fill_user_list2()

class User_Profile(QMainWindow):
    def __init__(self):
        super(User_Profile, self).__init__()
        loadUi('user_profile_information.ui', self)
        self.save_pushButton.clicked.connect(self.save_profile)
        self.Back_Button.clicked.connect(self.switch_previous_form)

    def save_profile(self):
        global global_user_id
        try:
            global db_url
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("""
                        UPDATE usertable
                        SET first_name = %s, last_name = %s, phone = %s, gender = %s, birthdate = %s, city = %s
                        WHERE user_id = %s
                    """, (
                        self.name_line.text(),
                        self.surname_line.text(),
                        self.telephone_line.text(),
                        self.gender_line.text(),
                        self.birthdate_line.text(),
                        self.city_line.text(),
                        global_user_id
                    ))
            cur.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Usertable', CURRENT_TIMESTAMP, 'User profile has been updated', 'Update')
                """, (global_user_id,))
            conn.commit()
        except Exception as e:
            # Handle the exception (show error message, log, etc.)
            print(f"Error: {str(e)}")
        finally:
            cur.close()
            conn.close()

    def switch_previous_form(self):
        global global_user_id
        try:
            global db_url
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("SELECT * FROM usertable WHERE user_id = %s", (global_user_id,))
            user_data = cur.fetchone()
            account_type = user_data[9]
            # Fetch the existing user data from the database
            if account_type == "Student":
                stackedWidget.setCurrentIndex(3)
            elif account_type == "Teacher":
                stackedWidget.setCurrentIndex(4)
            elif account_type == "Admin":
                stackedWidget.setCurrentIndex(5)
        except Exception as e:
            print(f"Error: {str(e)}")
            self.show_error_message(f"Error: {str(e)}")
        finally:
            cur.close()
            conn.close()

    def show_error_message(self, message):  # error messages
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Critical)
        error_box.setWindowTitle("Error")
        error_box.setText(message)
        error_box.exec_()

    def show_success_message(self, message):  # Add this method
        success_box = QMessageBox()
        success_box.setIcon(QMessageBox.Information)
        success_box.setWindowTitle("Success")
        success_box.setText(message)
        success_box.exec_()



class Admin(QMainWindow):
    """
    Class representing the admin window of the application.

    Attributes:
    - Back_Log_but: Button for switching back to the login form.
    - Approve_but: Button for approving selected accounts.
    - Discard_but: Button for discarding selected accounts.
    - tableWidget: Table widget for displaying pending TA accounts.
    """
    def __init__(self):
        """
        Initializes the Admin window.

        Connects signals to corresponding slots, sets up the table, and fills it with data.
        """
        super(Admin, self).__init__()
        loadUi('admin.ui', self)

        self.Back_Log_but.clicked.connect(self.switch_teacherform)
        self.Chatboard_but.clicked.connect(self.switch_chatboard)
        self.Approve_but.clicked.connect(self.approve_account)
        self.Discard_but.clicked.connect(self.discard_account)
        self.tableWidget.setColumnWidth(0,50)
        self.tableWidget.setColumnWidth(1,150)
        self.tableWidget.setColumnWidth(2,150)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels([ "Select", "Email", "Name", "Surname"])
        self.populate_user_combobox()
        self.populate_transaction_combobox()
        self.filter_button.clicked.connect(self.fill_logdata)

        self.fill_table()


    def fill_table(self):
        """
        Fills the table with pending TA account data.
        """
        global db_url
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()

             # Fetch the count of pending accounts
            cur.execute("SELECT count(*) FROM application WHERE status IS NULL;")
            number_of_accounts = cur.fetchone()[0]
            row = 0
            self.tableWidget.setRowCount(number_of_accounts)

            # Fetch the data for pending accounts
            cur.execute("SELECT application_id, email, first_name, last_name FROM application WHERE status IS NULL;")
            pending_user_data = cur.fetchall()

            for i in range(number_of_accounts):
                checkbox = QCheckBox()
                application_id = pending_user_data[i][0]
                email = pending_user_data[i][1]
                first_name= pending_user_data[i][2]
                last_name = pending_user_data[i][3]
                self.tableWidget.setCellWidget(row, 0, checkbox)
                self.tableWidget.setItem(row, 1, QTableWidgetItem(email))
                self.tableWidget.setItem(row, 2, QTableWidgetItem(first_name))
                self.tableWidget.setItem(row, 3, QTableWidgetItem(last_name))
                row += 1
        except Exception as e:
           print(f"Error loading data: {e}")
        finally:
            cur.close()
            conn.close()


    def approve_account(self):
        """
        Approves selected accounts and updates the tables accordingly.
        """
        global db_url
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            conn.autocommit = False
            cur.execute("SELECT * FROM application WHERE status IS NULL;")
            pending_user_data = cur.fetchall()
            for row in range(self.tableWidget.rowCount()):
                checkbox = self.tableWidget.cellWidget(row, 0)
                email_item = self.tableWidget.item(row, 1)
                if email_item is not None:
                    email_key = email_item.text()
                if checkbox.isChecked():
                    cur.execute("UPDATE application SET status = TRUE WHERE email = %s",(email_key,))
                    cur.execute("SELECT * FROM application WHERE email = %s",(email_key,))
                    selected_user_data = cur.fetchone()
                    cur.execute("""
                    INSERT INTO usertable (
                        email, password, first_name, last_name, phone, city, gender, birthdate, user_type, status, application_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (selected_user_data[1], selected_user_data[2], selected_user_data[3], selected_user_data[4], selected_user_data[5], selected_user_data[6], selected_user_data[7], selected_user_data[8], "Teacher", True, selected_user_data[0]))
                    
                    cur.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Usertable', CURRENT_TIMESTAMP, 'Teacher Account is created', 'Creation')
                """, (global_user_id,))
                    
                    cur.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Application', CURRENT_TIMESTAMP, 'Teacher Account is approved', 'Update')
                """, (global_user_id,))                   
                    
            conn.commit()
        except Exception as e:
            # Rollback the transaction in case of an error
            conn.rollback()
            print(f"Error: {str(e)}")
            self.show_error_message(f"Error: {str(e)}")
        finally:
            conn.autocommit = True
            cur.close()
            conn.close()             
            self.tableWidget.clearContents()
            self.fill_table()

    def discard_account(self):
        """
        Discards selected accounts and updates the tables accordingly.
        """
        global db_url
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            conn.autocommit = False
            cur.execute("SELECT * FROM application WHERE status IS NULL;")
            pending_user_data = cur.fetchall()
            for row in range(self.tableWidget.rowCount()):
                checkbox = self.tableWidget.cellWidget(row, 0)
                email_item = self.tableWidget.item(row, 1)
                if email_item is not None:
                    email_key = email_item.text()
                if checkbox.isChecked():
                    cur.execute("UPDATE application SET status = FALSE WHERE email = %s",(email_key,))
                    cur.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Application', CURRENT_TIMESTAMP, 'Teacher Account is not approved', 'Update')
                """, (global_user_id,))
            conn.commit()
        except Exception as e:
            # Rollback the transaction in case of an error
            conn.rollback()
            print(f"Error: {str(e)}")
            self.show_error_message(f"Error: {str(e)}")
        finally:
            conn.autocommit = True
            cur.close()
            conn.close()             
            self.tableWidget.clearContents()
            self.fill_table()

    def switch_teacherform(self):
        stackedWidget.setCurrentIndex(4)

    def switch_chatboard(self):
        stackedWidget.setCurrentIndex(6)
        chatboard.fill_user_list2()

    def populate_user_combobox(self):
            # Populate the combo box with user emails from usertable
            global db_url
            try:
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                cur.execute("SELECT email FROM usertable;")
                user_emails = cur.fetchall()
                self.Users_combo.addItem("None")
                for email in user_emails:
                    self.Users_combo.addItem(email[0])
            except Exception as e:
                print(f"Error populating user combo box: {e}")
            finally:
                cur.close()
                conn.close()
    
    def populate_transaction_combobox(self):
            # Populate the combo box with user emails from usertable
            global db_url
            try:
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                cur.execute("SELECT DISTINCT event_type FROM logtable;")
                transactions = cur.fetchall()
                self.Transaction_combo.addItem("None")
                for transaction in transactions:
                    self.Transaction_combo.addItem(transaction[0])
            except Exception as e:
                print(f"Error populating user combo box: {e}")
            finally:
                cur.close()
                conn.close()
    
    def fill_logdata(self):
        """
        Fills the table with log data
        """
        global db_url
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()

            selected_email = self.Users_combo.currentText()
            cur.execute("SELECT user_id FROM usertable WHERE email = %s", (selected_email,))
            selected_user = cur.fetchone()[0] if cur.rowcount > 0 else None

            selected_transaction = self.Transaction_combo.currentText()
            selected_date = self.logcalendarWidget.date().toString(Qt.ISODate)

            conditions = []

            if selected_user:
                conditions.append(f"logtable.user_id = '{selected_user}'")

            if selected_transaction != "None":
                conditions.append(f"logtable.event_type = '{selected_transaction}'")

            if selected_date != "2024-01-01":
                conditions.append(f"DATE(logtable.time_stamp) = '{selected_date}'")

            # Construct the SQL query
            where_clause = " AND ".join(conditions)
            query = f"""
                SELECT usertable.first_name, usertable.last_name, logtable.event_type, logtable.time_stamp, logtable.action, logtable.type
                FROM logtable
                LEFT JOIN usertable ON logtable.user_id = usertable.user_id
                {"WHERE" if conditions else ""}
                {where_clause};
            """

            cur.execute(query)
            log_records = cur.fetchall()
            number_of_records = len(log_records)

            self.logtablewidget.setColumnCount(5)
            self.logtablewidget.setHorizontalHeaderLabels(["Name", "Event", "Date", "Action", "Type"])
            self.logtablewidget.setColumnWidth(0, 150)
            self.logtablewidget.setColumnWidth(1, 150)
            self.logtablewidget.setColumnWidth(2, 150)
            self.logtablewidget.setColumnWidth(3, 150)
            self.logtablewidget.setColumnWidth(4, 150)

            self.logtablewidget.setRowCount(number_of_records)

            row = 0
            for i in range(number_of_records):
                name = log_records[i][0] + " " + log_records[i][1]
                event = log_records[i][2]
                date = str(log_records[i][3])
                action = log_records[i][4]
                tip = log_records[i][5]

                self.logtablewidget.setItem(row, 0, QTableWidgetItem(name))
                self.logtablewidget.setItem(row, 1, QTableWidgetItem(event))
                self.logtablewidget.setItem(row, 2, QTableWidgetItem(date))
                self.logtablewidget.setItem(row, 3, QTableWidgetItem(action))
                self.logtablewidget.setItem(row, 4, QTableWidgetItem(tip))

                row += 1

        except Exception as e:
            print(f"Error loading data: {e}")
        finally:
            cur.close()
            conn.close()

        # Clear the date selection in the logcalendarWidget
        self.logcalendarWidget.setDate(QDate(2024, 1, 1))


    
class Chatboard(QMainWindow):
    """
    Class representing the chatboard window of the application.

    Attributes:
    - Back_TF_but: Button for switching back to the teacher form.
    - Send_but: Button for sending a message.
    - usertableWidget: Table widget for displaying user information.
    - history_LE: Line edit for displaying chat history.
    - send_TE: Text edit for typing and sending messages.
    """
    def __init__(self):
        """
        Initializes the Chatboard window.

        Connects signals to corresponding slots, sets up the user table, and initializes UI elements.
        """
        super(Chatboard, self).__init__()
        loadUi('chatbot.ui', self)
        # self.usertableWidget.setColumnWidth(0,10)
        self.usertableWidget.setColumnWidth(0,400)
        # self.usertableWidget.setColumnCount(2)
        # self.usertableWidget.setHorizontalHeaderLabels([ "","Name"])
        self.usertableWidget.setColumnCount(2)
        self.usertableWidget.setHorizontalHeaderLabels(["Name","User_id"])
        self.Back_TF_but.clicked.connect(self.switch_previous_form)
        self.Send_but.clicked.connect(self.send_message)
        self.usertableWidget.itemSelectionChanged.connect(self.selection)
        self.history_LE.setReadOnly(True)
        # Connect Enter key press event to send_message method
        self.send_TE.installEventFilter(self)
        


    def fill_user_list2(self):
        """
        Fills the user table with user information and unread message counts.
        """
        global db_url
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()

             # Fetch the count of pending accounts
            cur.execute("SELECT count(*) FROM usertable WHERE status IS TRUE;")
            number_of_accounts = cur.fetchone()[0]

            unread_query= f"""
            SELECT sender_id, COUNT(*) AS message_count
            FROM chat
            WHERE status = false AND receiver_id = {global_user_id}
            GROUP BY sender_id, receiver_id;
            """
            cur.execute(unread_query)
            unread_data = cur.fetchall()
            
            # Create a dictionary to store sender_id and message_count
            sender_id_data = dict()

            for i in unread_data:
                sender_id_data[i[0]] = i[1]


            cur.execute("SELECT user_id, first_name, last_name, email FROM usertable WHERE status IS TRUE;")
            active_user_data = cur.fetchall()
            row=0

            self.usertableWidget.setRowCount(number_of_accounts)  # Set the row count

            for i in range(number_of_accounts):

                user_id = active_user_data[i][0]

                if user_id not in sender_id_data:
                    self.usertableWidget.setItem(
                        row,
                        0,
                        QTableWidgetItem(active_user_data[i][2]+ ", " + active_user_data[i][1]),
                    )
                    self.usertableWidget.setItem(row, 1, QTableWidgetItem(str(user_id)))

                else:
                    self.usertableWidget.setItem(row, 1, QTableWidgetItem(str(user_id)))
                    self.usertableWidget.setItem(
                        row,
                        0,
                        QTableWidgetItem(active_user_data[i][2]+ ", " + active_user_data[i][1]+", " + str(sender_id_data.get(user_id, 0))),
                    )
                    self.usertableWidget.item(row, 0).setBackground(QColor(255, 0, 0))
                    

                self.usertableWidget.setColumnWidth(0, 185)
                self.usertableWidget.setColumnWidth(1, 0)
                row += 1

        except Exception as e:
            # Rollback the transaction in case of an error
            conn.rollback()
            print(f"Error: {str(e)}")
        finally:
            cur.close()
            conn.close()             

    def selection(self):
        """
        Handles user selection from the user table and displays the chat history.
        """
        global db_url
        global global_user_id

        selected_items = self.usertableWidget.selectedItems()


        self.history_LE.setText("")

        if not selected_items:
            return
        selected_row=selected_items[0].row()
        recipient=int(self.usertableWidget.item(selected_row,1).text())

        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()

             # Fetch name of the user and receiver
            cur.execute("SELECT first_name FROM usertable WHERE user_id=%s",(global_user_id,))
            name_of_sender = cur.fetchone()[0]
            cur.execute("SELECT first_name FROM usertable WHERE user_id=%s",(recipient,))
            name_of_recepient = cur.fetchone()[0]
            chat_query = f"""
            SELECT sender_id, text, date, status
            FROM chat
            WHERE (sender_id = {global_user_id} AND receiver_id = {recipient}) OR (sender_id = {recipient} AND receiver_id = {global_user_id})
            ORDER BY date;
            """
            cur.execute(chat_query)
            chat_data=cur.fetchall()

            if not chat_data:
                self.history_LE.setText("")
                return
            
            # Update chat status
            cur.execute("UPDATE chat SET status = TRUE WHERE receiver_id=%s and sender_id=%s",(global_user_id,recipient))


            formatted_date1 = chat_data[0][2].strftime("%A, %B %d")
            padding = "-" * ((50 - len(formatted_date1)) // 2)
            self.history_LE.insertPlainText(padding + formatted_date1 + padding+"\n")

            for i in chat_data:
                formatted_time=i[2].strftime("%H:%M")
                formatted_date2 = i[2].strftime("%A, %B %d")
                if formatted_date1==formatted_date2:
                    message= i[1]
                    if i[0]==global_user_id:
                        self.history_LE.append(name_of_sender + " : " + str(formatted_time) + "\n" + message + "\n")
                    else:
                        self.history_LE.append(name_of_recepient+ " : " + str(formatted_time) + "\n" + message + "\n")
                    formatted_date1=formatted_date2
                else:
                    message= i[1]
                    padding = "-" * ((50 - len(formatted_date1)) // 2)
                    self.history_LE.append(padding + formatted_date2 + padding+"\n")
                    if i[0]==global_user_id:
                        self.history_LE.append(name_of_sender + " : " + str(formatted_time) + "\n" + message + "\n")
                    else:
                        self.history_LE.append(name_of_recepient+ " : " + str(formatted_time) + "\n" + message + "\n")   
                    formatted_date1=formatted_date2                 

        except Exception as e:
            print(f"Error: {str(e)}")
        finally:        
            cur.close()
            conn.commit()
            conn.close() 
            self.fill_user_list2()


    def send_message(self):
        """
        Sends a message to the selected recipient and updates the chat entries.
        """
        global global_user_id
        global db_url

        message=self.send_TE.toPlainText()
        selected_items = self.usertableWidget.selectedItems()
        # user_email = login.email_LE.text()

        if not selected_items:
            return
        
        selected_row=selected_items[0].row()
        recipient=int(self.usertableWidget.item(selected_row,1).text())
        current_time = datetime.now()
        time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO chat (
                    sender_id, receiver_id, text, date, status
                ) VALUES (%s, %s, %s, %s, %s)
            """, (global_user_id, recipient, message, time, False))


        except Exception as e:
            print(f"Error: {str(e)}")
        finally:        
            cur.close()
            conn.commit()
            conn.close() 

        self.send_TE.setText("")
        self.selection()

    def eventFilter(self, obj, event):
        if obj is self.send_TE and event.type() == event.KeyPress and event.key() == Qt.Key_Return:
            self.send_message()
            return True  # Event handled
        return super().eventFilter(obj, event)

    def switch_previous_form(self):
        global global_user_id
        try:
            global db_url
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("SELECT * FROM usertable WHERE user_id = %s", (global_user_id,))
            user_data = cur.fetchone()
            account_type = user_data[9]
            # Fetch the existing user data from the database
            if account_type == "Student":
                stackedWidget.setCurrentIndex(3)
            elif account_type == "Teacher":
                stackedWidget.setCurrentIndex(4)
            elif account_type == "Admin":
                stackedWidget.setCurrentIndex(5)
        except Exception as e:
            print(f"Error: {str(e)}")
            self.show_error_message(f"Error: {str(e)}")
        finally:
            cur.close()
            conn.close()

    
    def switch_chatboard(self):
        stackedWidget.setCurrentIndex(6)
        chatboard.fill_user_list2()





class Main_Window(QMainWindow):
    def __init__(self):
        super(Main_Window, self).__init__()

        loadUi('student.ui', self)  
        self.pushButton.clicked.connect(self.switch_chatboard)
        self.pushButton_2.clicked.connect(self.switch_userprofile)
        self.back_button.clicked.connect(self.switch_login)
        self.setFixedSize(900,600)
        self.setWindowTitle('Campus Pulse')


        self.note_edit = self.findChild(QLabel, 'note_edit')  # Find the element named note_edit in the UI file.
        self.calendar = self.findChild(QCalendarWidget, 'calendarWidget')  # Find the element named calendarWidget in the UI file.
        self.mission_complete = self.findChild(QPushButton, 'self.mission_complete')  # Find the element named mission_complete in the UI file.


        self.calendar.clicked.connect(self.load_calendar_events)
        self.comboBox_2.currentIndexChanged.connect(self.populate_table)
        self.comboBox_3.currentIndexChanged.connect(self.populate_table)
        
#meeting calendar
    def load_calendar_events(self):
        
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        try:
            cur.execute('SELECT lesson_id, planned_date FROM calendar')
            date_show=cur.fetchall()

            if date_show:
                
                for date_str in date_show:
                    date = QDate.fromString(str(date_str[1]), Qt.ISODate)
                    #If there is a date value and the lesson ID is 1 (if it is a mentor meeting), go to format1 for calendar coloring.
                    if date.isValid() and (str(date_str[0])!="1"): 
                        self.calendar.setDateTextFormat(date, self.get_calendar_event_format1())
                    else:
                        self.calendar.setDateTextFormat(date, self.get_calendar_event_format2())
            
                selected_date = self.calendar.selectedDate().toString(Qt.ISODate)
                
                #Extract the time information from the 'planned_date' variable and take only the date information.
                sql = "SELECT lesson_id, planned_date FROM calendar WHERE date_trunc('day', planned_date)::date = %s;"
                cur.execute(sql, (datetime.strptime(selected_date, "%Y-%m-%d").date(),))
                lesson_show=cur.fetchall()

                if lesson_show == []:
                    self.note_edit.clear() 
                #Show the event and time on the selected date in the calendar.
                else:   
                    cur.execute(f"SELECT lesson_name FROM lesson where lesson_id = '{lesson_show[0][0]}'")
                    nameles = cur.fetchone()
                    les=nameles[0]
                    time=lesson_show[0][1].strftime("%H:%M")
                    text=f"Event: {les}, Time:{time}"
                    self.note_edit.setText(text)
                    
                
            else:
                pass

            conn.commit()

        except Exception as e:
            print(f"Error: {e}")

        finally:
            cur.close()
            conn.close()


    def get_calendar_event_format1(self):
        format = self.calendar.dateTextFormat(self.calendar.selectedDate())
        font = format.font()
        font.setBold(True)  # Text bold
        format.setFont(font)
        format.setForeground(Qt.red)
        format.setBackground(Qt.green)
        return format
    
    def get_calendar_event_format2(self):
        format = self.calendar.dateTextFormat(self.calendar.selectedDate())
        font = format.font()
        font.setBold(True)  # Text bold
        format.setFont(font)
        format.setForeground(Qt.green)
        format.setBackground(Qt.red)
        return format   

#status of attendance
    def populate_table(self):
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        try:
            #Remove all table items for news.
            for i in range(self.tableWidget.rowCount() - 1, -1, -1):
                is_row_empty = all(self.tableWidget.item(i, j) is None or self.tableWidget.item(i, j).text() == '' for j in range(self.tableWidget.columnCount()))
                if not is_row_empty:
                    self.tableWidget.removeRow(i)

            #Assign the statuses in the ComboBox to a variable.
            filter_statu1 = self.comboBox_2.currentText()
            filter_statu2 = self.comboBox_3.currentText()

            #Filter the data from the database based on the selection in the ComboBox.
            if filter_statu1=='Mentor Meetings': 
                cur.execute(f'SELECT lesson_id, planned_date, status FROM calendar WHERE student_id={global_user_id} and lesson_id =1 order by planned_date asc')
                event_show=cur.fetchall()
                cur.execute(f'SELECT lesson_name FROM lesson WHERE lesson_id = 1')
                lesname=cur.fetchall()  
                x_name = str(lesname[0])     
            else:
                cur.execute(f'SELECT lesson_id, planned_date, status FROM calendar WHERE student_id={global_user_id} and lesson_id !=1 order by planned_date asc')
                event_show=cur.fetchall()
                cur.execute(f'SELECT lesson_name FROM lesson WHERE lesson_id != 1')
                lesname=cur.fetchall()  
                
            i=0
            for a in event_show:
                if len(lesname)>1:
                    x_name = str(lesname[i][0]) #Loop for lesson_name.
                    i+=1
                else:
                    x_name = str(lesname[0][0]) 
                if a[2]==False:
                    value='Not Attended'
                else:
                    value='Attended'

                postgre_date=a[1]    
                qdate = QDate(postgre_date.year, postgre_date.month, postgre_date.day) #Convert the date from SQL to QDate format.
                current_date = QDate.currentDate()

                if value==filter_statu2 and qdate <= current_date:
                    row_position = self.tableWidget.rowCount()
                    self.tableWidget.insertRow(row_position)
                    item_date = QTableWidgetItem(qdate.toString("yyyy-MM-dd")) # Print the date as a string.
                    item_value = QTableWidgetItem(str(value))
                    item_event = QTableWidgetItem(x_name)
                    self.tableWidget.setItem(row_position, 0, item_event)
                    self.tableWidget.setItem(row_position, 1, item_value)
                    self.tableWidget.setVerticalHeaderItem(row_position, item_date)

                if filter_statu2=='Make Your Choice' and (filter_statu1=='Mentor Meetings' or filter_statu1=='Lessons') and qdate <= current_date:
                    row_position = self.tableWidget.rowCount()
                    self.tableWidget.insertRow(row_position)
                    item_date = QTableWidgetItem(qdate.toString("yyyy-MM-dd"))
                    item_value = QTableWidgetItem(str(value))
                    item_event = QTableWidgetItem(x_name)
                    self.tableWidget.setItem(row_position, 0, item_event)
                    self.tableWidget.setItem(row_position, 1, item_value)
                    self.tableWidget.setVerticalHeaderItem(row_position, item_date)

            conn.commit()
        
        
        except Exception as e:
            print(f"Error: {e}")

        finally:
            cur.close()
            conn.close()

# to do list
    def show_tasks(self):

        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        try:
            cur.execute(f"SELECT * FROM task WHERE student_id = {global_user_id} order by deadline asc")
            task_show=cur.fetchall()


            if task_show:
                self.check_boxes = []

                #Show task, deadline, and task assignee information to the database.
                for task_row in task_show:
                    cur.execute(f"SELECT first_name, last_name FROM usertable WHERE user_id = {str(task_row[1])};")
                    teacher_show=cur.fetchall()
                    row_position = self.table_todolist.rowCount()
                    self.table_todolist.insertRow(row_position)
                    self.table_todolist.setItem(row_position, 1, QTableWidgetItem(str(task_row[2])))
                    self.table_todolist.setItem(row_position, 2, QTableWidgetItem(str(task_row[4])))
                    self.table_todolist.setItem(row_position, 3, QTableWidgetItem(str(teacher_show[0][0])+' '+str(teacher_show[0][1])))
                   
                    # Show the statuses of tasks in the database.
                    self.check_box = QCheckBox()
                    if task_row[5] == True:
                        self.check_box.setChecked(True)
                    else:
                        self.check_box.setChecked(False)

                    self.table_todolist.setCellWidget(row_position,0, self.check_box)
                    self.check_boxes.append(self.check_box)

                # Set the column width.
                self.table_todolist.setColumnWidth(0,30)
                self.table_todolist.setColumnWidth(1,325)
                self.table_todolist.setColumnWidth(2,90)
                self.table_todolist.setColumnWidth(3,90)
        
                self.connect_check_boxes()
            else:
                pass
            conn.commit()

            print("Tasks showed successfully!")

        except Exception as e:
            print(f"Error: {e}")

        finally:
            cur.close()
            conn.close()

# to do list check
    def connect_check_boxes(self):
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()    

        try:
        
            for row, check_box in enumerate(self.check_boxes):
                check_box.stateChanged.connect(lambda state, r=row: self.onCheckBoxStateChanged(state, r))
        
            conn.commit()

        except Exception as e:
            print(f"Error: {e}")

        finally:
            cur.close()
            conn.close()

    def onCheckBoxStateChanged(self, state, row):
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        global global_user_id
        

        try:

            cur.execute(f"SELECT * FROM task WHERE student_id = {global_user_id} order by deadline asc")
            task_show=cur.fetchall()
            if state == 2:  # Qt.Checked
                cur.execute(f"UPDATE task SET status = TRUE WHERE task_id={task_show[row][0]}")
                cur.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Task', CURRENT_TIMESTAMP, 'Task is completed', 'Update')
                """, (global_user_id,))

            else:
                cur.execute(f"UPDATE task SET status = FALSE WHERE task_id={task_show[row][0]}")
                cur.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Task', CURRENT_TIMESTAMP, 'Task is undone', 'Update')
                """, (global_user_id,))

            conn.commit()

        except Exception as e:
            print(f"Error: {e}")

        finally:
            cur.close()
            conn.close()


# announcements  
    def show_announcements(self):
            
        self.announcement_i = 0  # Index of the next announcement.

        #Create a QTimer.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.up_announcements)
        self.timer.start(1500)  # Check every 5 seconds    
        self.up_announcements()  # Run at the beginning as well.

 # Update announcement
    def up_announcements(self):
       
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        try:
            cur.execute(f"SELECT * FROM announcement order by deadline asc")
            ann_show=cur.fetchall()
            self.announcement_textedit.setToolTip("\n".join(str(a[2]) for a in ann_show))
            
            if self.announcement_i < len(ann_show):
                
                    postgre_date=ann_show[self.announcement_i][4]    
                    last_date = QDate(postgre_date.year, postgre_date.month, postgre_date.day) #sql den gelen date i QDate formatina cevir
                    current_date = QDate.currentDate()
                    
                    if last_date >= current_date:
                        self.announcement_textedit.setText('')
                        self.announcement_textedit.setText(f' 📢❗🚨 {ann_show[self.announcement_i][2]}   Deadline: {ann_show[self.announcement_i][4]} 📢❗🚨') #ekranda sola bitisik yazmasin
            
                    # Move on to the next announcement.
                    self.announcement_i += 1
            else:
            # When the end of the announcement list is reached, go back to the beginning.
                self.announcement_i = 0
            
            conn.commit()
            
        except Exception as e:
            print(f"Error: {e}")

        finally:
            cur.close()
            conn.close()

    
    def switch_chatboard(self):
        stackedWidget.setCurrentIndex(6)
        chatboard.fill_user_list2()

    def switch_login(self):
        stackedWidget.setCurrentIndex(0)
        login.clear_line_edits_loginform()
    
    def switch_userprofile(self):
        stackedWidget.setCurrentIndex(7)

########################################################################################################################################    
class MyMainWindow(QMainWindow):
    def __init__(self):
        super(MyMainWindow, self).__init__()
        #self.setupUi(self)
        loadUi("teacher_page.ui", self)
        self.setWindowTitle('Campus Pulse')
        self.task_manager = TaskManager()
        self.pushButton_LessonSave.clicked.connect(self.save_lesson)
        self.announcements = self.fetch_announcements_from_database() 
        self.announcement_index = 0
        self.populate_students_list()
        self.populate_students_table()
        self.populate_task_combobox()
        self.display_upcoming_tasks()
        self.populate_coursemeet_list()
        self.populate_announcements()
        self.populate_calendar_combobox()
        self.update_announcements()
        self.pushButton_SchSave.clicked.connect(self.save_schedule)
        self.pushButton_EditLesson.clicked.connect(self.edit_lesson_plan)
        self.pushButton_DeleteLesson.clicked.connect(self.delete_selected_lesson)
        self.pushButton_edit_announcement.clicked.connect(self.edit_announcement)
        self.pushButton_DeleteAnnouncement_6.clicked.connect(self.delete_announcement)
        self.comboBox_announcement.currentIndexChanged.connect(self.display_selected_announcement)
        self.pushButton_chatbox.clicked.connect(student.switch_chatboard)
        self.pushButton_profile.clicked.connect(student.switch_userprofile)
        self.pushButton_backtologin.clicked.connect(student.switch_login)
        self.pushButton_switchadmin.clicked.connect(self.switch_to_admin)
        self.pushButton_Edit_Task.clicked.connect(self.edit_task)
        self.pushButton_Delete_Task.clicked.connect(self.delete_task)
        self.pushButton_schedule.clicked.connect(lambda: self.MainPage.setCurrentIndex(1))
        self.pushButton_announcement.clicked.connect(lambda: self.MainPage.setCurrentIndex(1))
        self.courseWidget.itemSelectionChanged.connect(self.fill_students)
        self.comboBox_tasks.currentIndexChanged.connect(self.onComboBoxIndexChanged)

        
        self.tableWidget_Students.setColumnWidth(0,150)
        self.tableWidget_Students.setColumnWidth(1,250)
        self.tableWidget_Students.setColumnWidth(2,335)

        self.tableWidget_ToDoList.setColumnWidth(0, 100)  # 0. sütunun genişliği
        self.tableWidget_ToDoList.setColumnWidth(1, 100)  # 1. sütunun genişliği
        self.tableWidget_ToDoList.setColumnWidth(2, 200)
        #self.gecici.clicked.connect(self.fill_courses)
        
        # Create Task butonuna tıklandığında
        self.pushButton_CreateTask.clicked.connect(self.create_task)

        # Send Announcement butonuna tıklandığında
        self.pushButton_SendAnnouncement.clicked.connect(self.send_announcement)
        self.announcement_index = 0  # Sıradaki anonsun indeksi

        # QTimer oluştur
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_announcements)
        self.timer.start(5000)  # 5 saniyede bir kontrol et
        self.update_announcements()  # Başlangıçta da çalıştır
        self.textEdit_AnnouncementView.setToolTip("\n".join(str(announcement.get("content", "")) for announcement in self.announcements))

    def fill_courses(self):
        """
        Fills the courses with course/mentor name and dates.
        """
        global db_url

        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()

             # Fetch the number of distinct planned courses
            
            cur.execute("select count (distinct planned_date) from calendar;")
            number_of_planned_courses = cur.fetchone()[0]

            courses_query= f"""
            select DISTINCT planned_date, lesson_name from calendar
            left join lesson
            on calendar.lesson_id=lesson.lesson_id
            order by planned_date
            """
            cur.execute(courses_query)
            course_data = cur.fetchall()

            row=0

            self.courseWidget.setRowCount(number_of_planned_courses)  # Set the row count
            self.courseWidget.setColumnCount(2)
            self.courseWidget.setHorizontalHeaderLabels([ "Date", "Name"])
            self.courseWidget.setColumnWidth(0, 150)
            self.courseWidget.setColumnWidth(1, 150)

            for i in course_data:

                self.courseWidget.setItem(row, 0, QTableWidgetItem(i[0].strftime('%Y-%m-%d %H:%M:%S')))
                self.courseWidget.setItem(row, 1, QTableWidgetItem(str(i[1])))


                self.courseWidget.setColumnWidth(0, 120)
                self.courseWidget.setColumnWidth(1, 120)
                row += 1

        except Exception as e:
            # Rollback the transaction in case of an error
            conn.rollback()
            print(f"Error: {str(e)}")
        finally:
            cur.close()
            conn.close()    
    
    def fill_students(self):
        """
        Fills the table with assigned students.
        """
        global db_url
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()

            # Fetch the count of pending accounts
            selected_items = self.courseWidget.selectedItems()
            if not selected_items:
                return
            selected_row=selected_items[0].row()
            lessondate=self.courseWidget.item(selected_row,0).text()
            lessonname=self.courseWidget.item(selected_row,1).text()
          

            # lessondate = '2024-01-25 00:00:00'
            # lessonname = 'Mathematics'

            self.studentWidget.setColumnCount(2)
            self.studentWidget.setHorizontalHeaderLabels(["Attendance", "Name"])
            self.studentWidget.setColumnWidth(0, 100)
            self.studentWidget.setColumnWidth(1, 300)

            # Fetch number of students assigned to the lesson
            query1 = f'''SELECT COUNT(student_id) FROM calendar
                        LEFT JOIN lesson ON calendar.lesson_id = lesson.lesson_id
                        WHERE planned_date = '{lessondate}' AND lesson_name = '{lessonname}';
                    '''
            cur.execute(query1)
            number_of_students = cur.fetchone()[0]

            row = 0
            self.studentWidget.setRowCount(number_of_students)

            # Fetch data of students assigned to the lesson
            query2 = f'''SELECT calendar.student_id, calendar.status, usertable.first_name, usertable.last_name, calendar.lesson_id
                        FROM calendar
                        LEFT JOIN lesson ON calendar.lesson_id = lesson.lesson_id
                        LEFT JOIN usertable ON calendar.student_id = usertable.user_id
                        WHERE calendar.planned_date = '{lessondate}' AND lesson.lesson_name = '{lessonname}';
                    '''

            # Fetch the data for students
            cur.execute(query2)
            student_data = cur.fetchall()

            for i in range(number_of_students):
                checkbox = QCheckBox()
                studentid = student_data[i][0]
                attendance_status = student_data[i][1]
                firstname = student_data[i][2]
                lastname = student_data[i][3]
                lessonid=student_data[i][4]
                checkbox.setChecked(attendance_status)
                # Connect the stateChanged signal of the checkbox to the update_calendar_status method
                checkbox.stateChanged.connect(lambda state, sid=studentid: self.update_calendar_status(sid, lessonid, lessondate, state == Qt.Checked))

                self.studentWidget.setCellWidget(row, 0, checkbox)
                self.studentWidget.setItem(row, 1, QTableWidgetItem(f"{firstname} {lastname}"))
                row += 1
        except Exception as e:
            print(f"Error loading data: {e}")
        finally:
            cur.close()
            conn.close()

    def update_calendar_status(self, student_id, lessonid, planneddate, new_status):
        """
        Update the status in the calendar database.
        """
        global db_url
        try:
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()

            # Convert planneddate to string and enclose it in single quotes
            planneddate_str = str(planneddate)

            # Update the status in the calendar table
            update_query = f'''
                UPDATE calendar
                SET status = {new_status}
                WHERE student_id = {student_id} AND lesson_id = '{lessonid}' AND planned_date = '{planneddate_str}';
            '''
            cur.execute(update_query)
            cur.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Calendar', CURRENT_TIMESTAMP, 'Attendance has been updated', 'Update')
                """, (student_id,))
            conn.commit()

        except Exception as e:
            print(f"Error updating calendar status: {e}")
        finally:
            cur.close()
            conn.close()

    def populate_coursemeet_list(self):
        # Ders adlarını çek
        lessons = self.task_manager.get_lessons()

        # ListWidget'ı doldur
        self.listWidget_coursemeet.clear()
        self.listWidget_coursemeet.addItems(lessons)
        self.listWidget_coursemeet_2.addItems(lessons)
        
        
    def fetch_announcements_from_database(self):
        announcements = []
        try:
            conn = psycopg2.connect(db_url)
            # Veritabanından anonsları çek
            with conn.cursor() as cursor:
                cursor.execute("SELECT teacher_id, text, deadline FROM announcement")
                result = cursor.fetchall()

            for row in result:
                announcement = {
                    "teacher_id": row[0],
                    "content": row[1],
                    "last_date": row[2].strftime("%Y-%m-%d") if row[2] else None
                }
                announcements.append(announcement)

        except Exception as e:
            print(f"Hata: Veritabanından anonsları çekerken bir sorun oluştu. Hata: {e}")

        return announcements

    def update_announcements_from_database(self):
        
        # Anonsları güncelle
        if self.announcement_index < len(self.announcements):
            announcement = self.announcements[self.announcement_index]
            last_date = announcement.get("last_date")
            current_date = datetime.now().strftime("%Y-%m-%d")
            if last_date >= current_date:
                self.textEdit_AnnouncementView.clear()
                self.textEdit_AnnouncementView.append(
                    f"📢❗🚨   {announcement['content']}   🚨❗📢")

            # Bir sonraki anonsa geç
            self.announcement_index += 1
        else:
            # Anons listesinin sonuna gelindiğinde başa dön
            self.announcement_index = 0

    def populate_announcements(self):
        try:
            # Bugünün tarihini al
            current_date = QDate.currentDate()
            conn=psycopg2.connect(db_url)
            # announcement_id'leri ve announcement_text'leri çek (deadline bugünden büyük olanlar)
            with conn.cursor() as cursor:
                cursor.execute("SELECT announcement_id, text FROM announcement WHERE deadline >= %s", (current_date.toString("yyyy-MM-dd"),))
                announcements = cursor.fetchall()

            # comboBox_announcement'ı doldur
            self.comboBox_announcement.clear()  # Combobox'ı temizle
            for announcement_id, text in announcements:
                self.comboBox_announcement.addItem(f"{announcement_id}: {text}")

        except Exception as e:
            print(f"Hata: announcement_id'leri ve announcement_text'leri çekerken bir sorun oluştu. Hata: {e}")
        # Seçilen announcement'ın text'ini göstermek için


    def display_selected_announcement(self):
        selected_text = self.comboBox_announcement.currentText()
        announcement_text = selected_text.split(": ")[1]
        self.textEdit_announcementtext_5.setPlainText(announcement_text)

    # Announcement'ı düzenlemek için
    def edit_announcement(self):
        new_date = self.dateEdit_lastdateofannouncement_5.date().toString("yyyy-MM-dd")
        new_text = self.textEdit_announcementtext_5.toPlainText()
        selected_id = int(self.comboBox_announcement.currentText().split(": ")[0])
        teacher_id = global_user_id
        current_date = QDate.currentDate().toString("yyyy-MM-dd")

        # Tarih seçimini kontrol et
        if QDate.fromString(new_date, "yyyy-MM-dd") < QDate.currentDate():
            QMessageBox.warning(self, "Warning", "Selected date cannot be before the current date.")
            return

        # new_text alanını kontrol et
        if not new_text.strip():
            QMessageBox.warning(self, "Warning", "Please enter a new announcement text.")
            return

        try:
            conn = psycopg2.connect(db_url)
            # announcement'ı güncelle
            with conn.cursor() as cursor:
                cursor.execute("UPDATE announcement SET deadline = %s, text = %s, teacher_id = %s, date = CURRENT_TIMESTAMP WHERE announcement_id = %s",
                            (new_date, new_text, teacher_id, selected_id))
                cursor.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Calendar', CURRENT_TIMESTAMP, 'Attendance has been updated', 'Update')
                """, (global_user_id,))
                conn.commit()

            QMessageBox.information(self, "Success", "Announcement updated successfully!")

        except Exception as e:
            print(f"Hata: announcement güncellenirken bir sorun oluştu. Hata: {e}")

    # Announcement'ı silmek için
    def delete_announcement(self):
        selected_id = int(self.comboBox_announcement.currentText().split(": ")[0])

        try:
            conn = psycopg2.connect(db_url)
            # announcement'ı sil
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM announcement WHERE announcement_id = %s", (selected_id,))
                conn.commit()
            

                # comboBox_announcement'ı güncelle (silinen kaydı kaldır)
                self.comboBox_announcement.removeItem(self.comboBox_announcement.currentIndex())

                # Silme işlemi tamamlandıktan sonra text alanlarını temizle
                self.textEdit_announcementtext_5.clear()
                self.dateEdit_lastdateofannouncement_5.clear()
            QMessageBox.information(self, "Success", "Announcement deleted successfully!")

        except Exception as e:
            print(f"Hata: announcement silinirken bir sorun oluştu. Hata: {e}")
            # Anons listesinin sonuna gelindiğinde başa dön
            self.announcement_index = 0


    def save_lesson(self):
        # Kullanıcı tarafından girilen ders adını al
        lesson_name = self.textEdit_lesson_2.toPlainText()

        # Ders adını kontrol et
        if not lesson_name:
            QMessageBox.warning(self, 'Uyarı', 'Ders adı boş olamaz.')
            return

        # Ders adının daha önce eklenip eklenmediğini kontrol et
        if self.is_lesson_exists(lesson_name):
            QMessageBox.warning(self, 'Uyarı', 'Bu ders zaten var. Lütfen yeni bir ders giriniz.')
            return

        # Ders adını veritabanına eklemek için fonksiyonu çağır
        self.insert_lesson_to_database(lesson_name)
        QMessageBox.information(self, 'Bilgi', 'Ders başarıyla kaydedildi.')

    def is_lesson_exists(self, lesson_name):
        try:
            # Veritabanına bağlantı
            connection = psycopg2.connect(db_url)

            # Ders adını kontrol et
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM lesson WHERE lesson_name = %s", (lesson_name,))
                result = cursor.fetchone()

            return result is not None

        except Exception as e:
            print(f"Hata: Veritabanında sorgu yaparken bir sorun oluştu. Hata: {e}")
            return False

        finally:
            # Bağlantıyı kapat
            if connection:
                connection.close()


    def insert_lesson_to_database(self, lesson_name):
        try:
            # Veritabanına bağlantı
            connection = psycopg2.connect(db_url)

            # Ders adını eklemek için sorgu
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO lesson (lesson_name) VALUES (%s)", (lesson_name,))

            # Değişiklikleri kaydet
            connection.commit()

        except Exception as e:
            print(f"Hata: Veritabanına yeni kayıt eklerken bir sorun oluştu. Hata: {e}")

        finally:
            # Bağlantıyı kapat
            connection.close()

    def switch_to_chatboard(self):
        stackedWidget.setCurrentIndex(6)
    
    def switch_to_admin(self):

        stackedWidget.setCurrentIndex(5)

            

                 
    def update_announcements(self):
        
        self.textEdit_announcementtext.setToolTip("\n".join(str(announcement.get("content", "")) for announcement in self.announcements))
        
        # Anonsları güncelle
        if self.announcement_index < len(self.announcements):
            announcement = self.announcements[self.announcement_index]
            last_date = announcement.get("last_date")
            current_date = datetime.now().strftime("%Y-%m-%d")
            if last_date and last_date >= current_date:
                self.textEdit_AnnouncementView.clear()
                self.textEdit_AnnouncementView.append(
                    f"📢❗🚨   {announcement['content']}   🚨❗📢")

            # Bir sonraki anonsa geç
            self.announcement_index += 1
        else:
            # Anons listesinin sonuna gelindiğinde başa dön
            self.announcement_index = 0
            
    def populate_students_list(self):
        # Öğrenci listesini doldur
        students = self.task_manager.get_students()
        for student in students:
            email = student.get("Email", "")
            id=student.get("user_id", "")
            name = student.get("name", "")
            surname = student.get("surname", "")
            self.listWidget_AssignList.addItem(f"{id}: {name} {surname}")
            self.listWidget_studentlist.addItem(f"{id}: {name} {surname}")   
            self.listWidget_AssignList_2.addItem(f"{id}: {name} {surname}")
            self.listWidget_studentlist_2.addItem(f"{id}: {name} {surname}")   

    def populate_task_combobox(self):
        try:
            conn = psycopg2.connect(db_url)
            with conn.cursor() as cursor:
                current_date = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("SELECT DISTINCT text FROM task WHERE deadline > %s", (current_date,))
                task_names = cursor.fetchall()

            # Extract unique task names from the result
            unique_task_names = set(task_name for (task_name,) in task_names)

            # Clear and populate the combobox
            self.comboBox_tasks.clear()
            for task_name in unique_task_names:
                self.comboBox_tasks.addItem(task_name)

        except Exception as e:
            print(f"Hata: Görevler çekilirken bir sorun oluştu. Hata: {e}")



            
    def create_task(self):
        # Yeni görev oluştur
        task_text = self.plainTextEdit_NewTask.toPlainText()
        
        # plainTextEdit_NewTask alanını kontrol et
        if not task_text.strip():  # Boşluksuz bir metin kontrolü yapılıyor
            QMessageBox.warning(self, "Warning", "Please enter a task text.")
            return

        deadlinecontrol = self.dateTimeEdit_Deadline.date()
        if deadlinecontrol < QDate.currentDate():
            QMessageBox.warning(self, "Warning", "Selected date cannot be before the current date.")
            return
        deadline = deadlinecontrol.toString("yyyy-MM-dd")

        # Seçilen öğrenci e-postalarını al
        selected_items = self.listWidget_AssignList.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select at least one student.")
            return

        assigned_students = [item.text().split(":")[0] for item in selected_items]

        # Görevi belirtilen öğrencilere ata ve veritabanına ekle
        try:
            conn = psycopg2.connect(db_url)
            # Veritabanına yeni görev ekle
            with conn.cursor() as cursor:
                for student_id in assigned_students:
                    cursor.execute("""
                        INSERT INTO task (teacher_id, text, date, deadline, status, student_id)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, %s, FALSE, %s)
                    """, (global_user_id, task_text, deadline, int(student_id)))
                cursor.execute("""
                INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                VALUES (%s, 'Task', CURRENT_TIMESTAMP, 'Task has been created', 'Create')
            """, (global_user_id,))
                conn.commit()   

        except Exception as e:
            print(f"Hata: Görev eklenirken bir sorun oluştu. Hata: {e}")

        QMessageBox.information(self, "Success", "Task created successfully!")

        # Görev oluşturulduktan sonra formu temizle
        self.plainTextEdit_NewTask.clear()
        self.dateTimeEdit_Deadline.clear()

        self.populate_task_combobox()
        self.listWidget_AssignList.clearSelection()
        self.listWidget_AssignList_2.clearSelection()
        self.populate_students_list()

    def onComboBoxIndexChanged(self, Index):
        selected_task_text = self.comboBox_tasks.currentText()
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT deadline FROM task WHERE text = %s", (selected_task_text,))
        deadline = cursor.fetchall()
   
        try:
            self.dateTimeEdit_Deadline_2.setDate(QDate(deadline[0][0]))
        except:
            print("hata")

        conn.close()


    def edit_task(self):
        # Get the selected task text from comboBox_tasks
        selected_task_text = self.comboBox_tasks.currentText()
        global global_user_id

        # Get the new task information from listWidget_AssignList_2, plainTextEdit_NewTask_2, and dateTimeEdit_Deadline_2
        new_assigned_students = [item.text().split(":")[0] for item in self.listWidget_AssignList_2.selectedItems()]
        # listWidget_AssignList_2'den kişi seçilip seçilmediğini kontrol et
        if not new_assigned_students:
            QMessageBox.warning(self, "Warning", "Please select at least one student.")
            return
        # self.logcalendarWidget.setDate(QDate(2024, 1, 1))

        new_task_text = self.plainTextEdit_NewTask_2.toPlainText()
        
        # plainTextEdit_NewTask_2 alanını kontrol et
        if not new_task_text.strip():  # Boşluksuz bir metin kontrolü yapılıyor
            QMessageBox.warning(self, "Warning", "Please enter a new task text.")
            return

        new_deadline_control = self.dateTimeEdit_Deadline_2.date()
        if new_deadline_control < QDate.currentDate():
            QMessageBox.warning(self, "Warning", "Selected date cannot be before the current date.")
            return
        new_deadline = new_deadline_control.toString("yyyy-MM-dd")

        try:
            conn = psycopg2.connect(db_url)
            with conn.cursor() as cursor:
                # Find all task records with the given text
                cursor.execute("SELECT task_id, student_id FROM task WHERE text = %s", (selected_task_text,))
                task_records = cursor.fetchall()

                # Delete existing task records with the given text
                for task_id, old_student_id in task_records:
                    cursor.execute("DELETE FROM task WHERE task_id = %s", (task_id,))

                # Create new task records with the new information
                for _ in new_assigned_students:
                    cursor.execute("""
                        INSERT INTO task (teacher_id, text, date, deadline, status, student_id)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, %s, FALSE, %s)
                    """, (global_user_id, new_task_text, new_deadline, int(_)))
                    cursor.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Task', CURRENT_TIMESTAMP, 'Task has been edited', 'Update')
                """, (global_user_id,))

                conn.commit()
                QMessageBox.information(self, "Success", "Task edited successfully!")

        except Exception as e:
            print(f"Hata: Görev düzenlenirken bir sorun oluştu. Hata: {e}")

        finally:
            self.populate_task_combobox()

            conn.close()
            
        self.plainTextEdit_NewTask.clear()
        self.dateTimeEdit_Deadline.clear()
        self.populate_task_combobox()
        self.listWidget_AssignList.clearSelection()
        self.listWidget_AssignList_2.clearSelection()        
        self.populate_students_list()

    def delete_task(self):
        # Get the selected task text from comboBox_tasks
        selected_task_text = self.comboBox_tasks.currentText()
        global global_user_id

        try:
            conn = psycopg2.connect(db_url)
            with conn.cursor() as cursor:
                # Find all task records with the given text
                cursor.execute("SELECT task_id FROM task WHERE text = %s", (selected_task_text,))
                task_ids = [record[0] for record in cursor.fetchall()]

                # Delete existing task records with the given text
                for task_id in task_ids:
                    cursor.execute("DELETE FROM task WHERE task_id = %s", (task_id,))
                    cursor.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Task', CURRENT_TIMESTAMP, 'Task has been deleted', 'Delete')
                """, (global_user_id,))

                conn.commit()
                QMessageBox.information(self, "Success", "Task deleted successfully!")

        except Exception as e:
            print(f"Error during delete_task: {e}")

        finally:
            conn.close()

        # Refresh the combobox after deleting the task
        self.plainTextEdit_NewTask.clear()
        self.dateTimeEdit_Deadline.clear()
        self.populate_task_combobox()
        self.listWidget_AssignList.clearSelection()
        self.listWidget_AssignList_2.clearSelection()
        self.populate_students_list()



    def send_announcement(self):
        try:
            # Yeni anons oluştur ve görev yöneticisine bildir
            announcement_text = self.textEdit_announcementtext.toPlainText()
            if not announcement_text:
                QMessageBox.warning(self, "Warning", "Announcement text cannot be empty.")
                return

            last_date_control = self.dateEdit_lastdateofannouncement.date()
            if last_date_control < QDate.currentDate():
                QMessageBox.warning(self, "Warning", "Selected date cannot be before the current date.")
                return
            last_date = last_date_control.toString("yyyy-MM-dd")

            self.task_manager.create_announcement(announcement_text, last_date)
            QMessageBox.information(self, "Success", "Announcement created successfully!")

            # Anons oluşturulduktan sonra formu temizle
            self.textEdit_announcementtext.clear()
            self.dateEdit_lastdateofannouncement.clear()

        except Exception as e:
            print(f"Hata: Anons gönderilirken bir sorun oluştu. Hata: {e}")


    def display_upcoming_tasks(self):
        try:
            conn = psycopg2.connect(db_url)

            today = datetime.now().date()

            # Bugünden sonraki tarihli görevleri çek
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT ON (task.text) task.text, task.deadline, usertable.first_name, usertable.last_name
                    FROM task
                    INNER JOIN usertable ON task.teacher_id = usertable.user_id
                    WHERE task.deadline > %s
                    ORDER BY task.text, task.deadline
                """, (today,))

                result = cursor.fetchall()

            # Tabloyu güncelle
            self.tableWidget_ToDoList.setRowCount(len(result))

            for row, task in enumerate(result):
                text, deadline, teacher_first_name, teacher_last_name = task

                # Satırı eklemek için rowCount kullanmamıza gerek yok
                self.tableWidget_ToDoList.insertRow(row)

                self.tableWidget_ToDoList.setItem(row, 0, QTableWidgetItem(text))
                self.tableWidget_ToDoList.setItem(row, 1, QTableWidgetItem(str(deadline)))
                self.tableWidget_ToDoList.setItem(row, 2, QTableWidgetItem(f"{teacher_first_name} {teacher_last_name}"))

        except Exception as e:
            print(f"Hata: Görev bilgileri çekilirken bir sorun oluştu. Hata: {e}")
        finally:
            if conn:
                conn.close()


    def populate_students_table(self):
        # Students tablosunu güncelle
        students = self.get_students()
        self.tableWidget_Students.setRowCount(len(students))

        for row, student in enumerate(students):
            user_id = student.get("user_id", "")
            name = student.get("name", "")
            surname = student.get("surname", "")
            tasks = self.get_student_tasks(user_id)

            # Satırı eklemek için rowCount kullanmamıza gerek yok
            self.tableWidget_Students.insertRow(row)

            self.tableWidget_Students.setItem(row, 0, QTableWidgetItem(name))
            self.tableWidget_Students.setItem(row, 1, QTableWidgetItem(surname))

            # Görevleri birleştirip metin oluştur
            tasks_text = ", ".join(f"{task.get('id')}={'✅' if task.get('status') else '❌'}" for task in tasks)

            # Doğru sütuna QTableWidgetItem ekleyin
            self.tableWidget_Students.setItem(row, 2, QTableWidgetItem(tasks_text))

    def get_students(self):
        students = []
        try:
            conn = psycopg2.connect(db_url)
            
            # Veritabanından öğrenci bilgilerini ve görev sayılarını çek
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        usertable.user_id,
                        usertable.first_name,
                        usertable.last_name,
                        COUNT(task.task_id) as task_count
                    FROM usertable
                    LEFT JOIN task ON usertable.user_id = task.student_id
                    WHERE usertable.user_type = 'Student'
                    GROUP BY usertable.user_id
                """)
                result = cursor.fetchall()

            for row in result:
                student = {
                    "user_id": row[0],
                    "name": row[1],
                    "surname": row[2],
                    "task_count": row[3],
                }
                students.append(student)

        except Exception as e:
            print(f"Hata: Öğrenci bilgileri çekilirken bir sorun oluştu. Hata: {e}")

        return students
    
    def get_student_tasks(self, user_id):
        tasks = []
        try:
            conn = psycopg2.connect(db_url)

            # Öğrenciye ait görev bilgilerini çek
            with conn.cursor() as cursor:
                cursor.execute("SELECT task_id, status FROM task WHERE student_id = %s", (user_id,))
                result = cursor.fetchall()

            for row in result:
                task = {
                    "id": row[0],
                    "status": row[1],
                }
                tasks.append(task)

        except Exception as e:
            print(f"Hata: Öğrenci görev bilgileri çekilirken bir sorun oluştu. Hata: {e}")

        return tasks    


    def save_schedule(self):
        selected_students = [item.text().split(":")[0] for item in self.listWidget_studentlist.selectedItems()]
        
        # Kontrol ekleniyor
        selected_lesson_item = self.listWidget_coursemeet.currentItem()
        if selected_lesson_item is None:
            QMessageBox.warning(self, "Warning", "Lütfen bir ders seçin.")
            return

        selected_lesson_name = selected_lesson_item.text()
        planned_date = self.dateTimeEdit_sch.dateTime().toString("yyyy-MM-dd hh:mm:ss")

        if not selected_students or not selected_lesson_name:
            QMessageBox.warning(self, "Warning", "Lütfen öğrenci ve ders seçimi yapın.")
            return

        try:
            conn = psycopg2.connect(db_url)
            with conn.cursor() as cursor:
                # lesson_id'yi lesson tablosundan al
                cursor.execute("SELECT lesson_id FROM lesson WHERE lesson_name = %s", (selected_lesson_name,))
                lesson_id = cursor.fetchone()[0]

                for student_id in selected_students:
                    cursor.execute("""
                        INSERT INTO calendar (lesson_id, teacher_id, creation_date, planned_date, student_id, status)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, FALSE)
                    """, (lesson_id, global_user_id, planned_date, student_id))
                    cursor.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Calendar', CURRENT_TIMESTAMP, 'A lesson plan has been added', 'Create')
                """, (global_user_id,))

            conn.commit()
            self.populate_calendar_combobox()
            self.listWidget_coursemeet.clearSelection()
            self.listWidget_studentlist.clearSelection()
            QMessageBox.warning(self, "Success", "Ders planlama başarıyla kaydedildi.")

        except Exception as e:
            print(f"Hata: Ders planlama kaydedilirken bir sorun oluştu. Hata: {e}")

        finally:
            if conn:
                conn.close()

                
                
    def populate_calendar_combobox(self):
        try:
            conn = psycopg2.connect(db_url)
            with conn.cursor() as cursor:
                # calendar tablosundan ilgili bilgileri çek
                cursor.execute("""
                    SELECT DISTINCT ON (u.first_name, u.last_name, l.lesson_name, c.planned_date)
                        c.calendar_id, u.first_name || ' ' || u.last_name AS teacher_name, l.lesson_name, c.planned_date
                    FROM calendar c
                    JOIN usertable u ON c.teacher_id = u.user_id
                    JOIN lesson l ON c.lesson_id = l.lesson_id
                """)
                calendar_data = cursor.fetchall()

                # comboBox'ı doldur
                self.comboBox.clear()  # Combobox'ı temizle
                for calendar_id, teacher_name, lesson_name, planned_date in calendar_data:
                    self.comboBox.addItem(f"{teacher_name} - {lesson_name} - {planned_date}")

        except Exception as e:
            print(f"Hata: Combobox doldurulurken bir sorun oluştu. Hata: {e}")

        finally:
            if conn:
                conn.close()            
 
 
    def edit_lesson_plan(self):

        global global_user_id
        
        selected_item_text = self.comboBox.currentText()
        if not selected_item_text:
            print("Lütfen silinecek bir ders planı seçin.")
            return

        try:
            conn = psycopg2.connect(db_url)
            with conn.cursor() as cursor:
                # Seçilen ders planının bilgilerini ayrıştır
                parts = selected_item_text.split(" - ")
                if len(parts) != 3:
                    print("Hatalı ders planı formatı.")
                    return

                teacher_name, lesson_name, planned_date = parts

                # Ders planlarını sil
                cursor.execute("""
                    DELETE FROM calendar
                    WHERE teacher_id = (SELECT user_id FROM usertable WHERE CONCAT(first_name, ' ', last_name) = %s)
                    AND lesson_id = (SELECT lesson_id FROM lesson WHERE lesson_name = %s)
                    AND planned_date = %s
                """, (teacher_name, lesson_name, planned_date))
                cursor.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Calendar', CURRENT_TIMESTAMP, 'Lessonplan has been edited', 'Update')
                """, (global_user_id,))

            conn.commit()

            # Silme işleminden sonra comboBox'ı yeniden doldur
            self.populate_calendar_combobox()

        except Exception as e:
            print(f"Hata: Ders planları silinirken bir sorun oluştu. Hata: {e}")

        finally:
            if conn:
                conn.close()

        # Daha sonra yeni ders planlarını ekleyerek güncelle
        self.edit_schedule() 
        
        self.listWidget_studentlist_2.clearSelection()
        self.listWidget_coursemeet_2.clearSelection()


    def get_student_info_from_item(self, item_text):
        try:
            # Öğrenci verisini ":" karakterinden ayır
            parts = item_text.split(":")
            if len(parts) != 2:
                print(f"Hatalı öğrenci verisi formatı: {item_text}")
                return None, None

            # Öğrenci ID'sini ve adını al
            student_id = int(parts[0].strip())
            student_name = parts[1].strip()

            return student_id, student_name

        except ValueError as ve:
            print(f"Hata: Öğrenci ID'si sayıya dönüştürülemedi. Hata: {ve}")
            return None, None

    def edit_schedule(self):
        global global_user_id
        selected_students = self.listWidget_studentlist_2.selectedItems()
        selected_course_item  = self.listWidget_coursemeet_2.currentItem()
        planned_date = self.dateTimeEdit_sch_2.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        teacher_id = global_user_id

        # Eğer currentItem varsa devam et, yoksa uyarı ver ve işlemi sonlandır
        if selected_course_item is None:
            QMessageBox.warning(self, "Warning", "Lütfen bir ders seçin.")
            return
        
        selected_course = selected_course_item.text()

        try:
            conn = psycopg2.connect(db_url)
            with conn.cursor() as cursor:
                for student_item in selected_students:
                    # Öğrenci bilgisini al
                    student_id, student_name = self.get_student_info_from_item(student_item.text())
                    if student_id is None:
                        continue

                    # Ders bilgilerini al
                    cursor.execute("SELECT lesson_id FROM lesson WHERE lesson_name = %s", (selected_course,))
                    lesson_row = cursor.fetchone()
                    if not lesson_row:
                        print(f"Ders bulunamadı: {selected_course}")
                        continue

                    lesson_id = lesson_row[0]

                    # Ders planını kaydet
                    cursor.execute("""
                        INSERT INTO calendar (lesson_id, teacher_id, creation_date, planned_date, student_id, status)
                        VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s, FALSE)
                    """, (lesson_id, teacher_id, planned_date, student_id))
                    cursor.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Calendar', CURRENT_TIMESTAMP, 'Schedule has been edited', 'Edit')
                """, (global_user_id,))

                conn.commit()
                QMessageBox.information(self, "Success", "Ders planları başarıyla kaydedildi.")

        except Exception as e:
            print(f"Hata: Ders planları kaydedilirken bir sorun oluştu. Hata: {e}")
            QMessageBox.warning(self, "Warning", f"Ders planları kaydedilirken bir hata oluştu:\n{e}")

        finally:
            if conn:
                conn.close()
        
        self.populate_calendar_combobox()                

    def delete_selected_lesson(self):
        selected_item_text = self.comboBox.currentText()
        if not selected_item_text:
            print("Lütfen silinecek bir ders planı seçin.")
            return

        try:
            conn = psycopg2.connect(db_url)
            with conn.cursor() as cursor:
                # Seçilen ders planının bilgilerini ayrıştır
                parts = selected_item_text.split(" - ")
                if len(parts) != 3:
                    print("Hatalı ders planı formatı.")
                    return

                teacher_name, lesson_name, planned_date = parts

                # Ders planlarını sil
                cursor.execute("""
                    DELETE FROM calendar
                    WHERE teacher_id = (SELECT user_id FROM usertable WHERE CONCAT(first_name, ' ', last_name) = %s)
                    AND lesson_id = (SELECT lesson_id FROM lesson WHERE lesson_name = %s)
                    AND planned_date = %s
                """, (teacher_name, lesson_name, planned_date))

                cursor.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Calendar', CURRENT_TIMESTAMP, 'Lesson has been deleted', 'Delete')
                """, (global_user_id,))

            conn.commit()
            QMessageBox.warning(self, "Success", "Ders planlama başarıyla silindi.")

            # Silme işleminden sonra comboBox'ı yeniden doldur
            self.populate_calendar_combobox()

        except Exception as e:
            print(f"Hata: Ders planları silinirken bir sorun oluştu. Hata: {e}")

        finally:
            if conn:
                conn.close()







class TaskManager:
    def __init__(self):
        pass

   



    def get_lessons(self):
        lessons = []
        try:
            conn = psycopg2.connect(db_url)

            # Veritabanından ders adlarını çek
            with conn.cursor() as cursor:
                cursor.execute("SELECT lesson_name FROM lesson")
                result = cursor.fetchall()

            for row in result:
                lesson_name = row[0]
                lessons.append(lesson_name)

        except Exception as e:
            print(f"Hata: Ders adları çekilirken bir sorun oluştu. Hata: {e}")

        return lessons
            


    def get_students(self):
        students = []
        try:
            conn = psycopg2.connect(db_url)
            
            # Veritabanından öğrenci bilgilerini çek
            with conn.cursor() as cursor:
                cursor.execute("SELECT user_id, first_name, last_name, email FROM usertable WHERE user_type = 'Student'")
                result = cursor.fetchall()

            for row in result:
                student = {
                    "user_id": row[0],
                    "name": row[1],
                    "surname": row[2],
                    "Email": row[3]
                    # Eğer daha fazla alan varsa buraya ekleyebilirsiniz
                }
                students.append(student)

        except Exception as e:
            print(f"Hata: Öğrenci bilgileri çekilirken bir sorun oluştu. Hata: {e}")

        return students



        

    def create_announcement(self, announcement_text, last_date):
        global global_user_id
        try:
            conn = psycopg2.connect(db_url)
            # Veritabanına anonsu ekle
            teacher_id = global_user_id  # Bu değeri global_user_id olarak aldık
            date_created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO announcement (teacher_id, text, date, deadline) VALUES (%s, %s, %s, %s)",
                    (teacher_id, announcement_text, date_created, last_date)
                )
                cursor.execute("""
                    INSERT INTO logtable (user_id, event_type, time_stamp, action, type)
                    VALUES (%s, 'Announcement', CURRENT_TIMESTAMP, 'Announcement has been created', 'Create')
                """, (global_user_id,))
            conn.commit()

        except Exception as e:
            print(f"Hata: Anons oluşturulurken bir sorun oluştu. Hata: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)

    stackedWidget = QStackedWidget()
    database_name = "db_campusv2"
    user = "postgres"
    password = "MerSer01"
    host = "localhost"
    port = "5432"

    # Construct the database URL
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{database_name}"
    create_tables()

    login = Login()
    signup = Signup()
    cont_admin = ContactAdmin()
    student=Main_Window()
    teacher=MyMainWindow()
    admin=Admin()
    chatboard=Chatboard()
    userprofile=User_Profile()



    login.setFixedSize(900, 600)  
    signup.setFixedSize(900, 600)
    cont_admin.setFixedSize(900, 600)
    student.setFixedSize(900, 600)
    teacher.setFixedSize(900, 600)
    admin.setFixedSize(900, 600)
    chatboard.setFixedSize(900, 600)
    userprofile.setFixedSize(900, 600)





    stackedWidget.addWidget(login)
    stackedWidget.addWidget(signup)
    stackedWidget.addWidget(cont_admin)
    stackedWidget.addWidget(student)
    stackedWidget.addWidget(teacher)
    stackedWidget.addWidget(admin)
    stackedWidget.addWidget(chatboard)
    stackedWidget.addWidget(userprofile)



    stackedWidget.show()
    sys.exit(app.exec_())
