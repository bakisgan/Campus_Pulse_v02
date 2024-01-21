import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QDateTimeEdit, QStackedWidget, QMessageBox, QWidget, QTableWidget, QTableWidgetItem, QCheckBox, QLabel, QCalendarWidget, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QDate, QDateTime
from PyQt5.uic import loadUi
import json
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
        CREATE TABLE IF NOT EXISTS "Application" (
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
        CREATE TABLE IF NOT EXISTS "User" (
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
        CREATE TABLE IF NOT EXISTS "Lesson" (
        "lesson_id" SERIAL PRIMARY KEY,
        "lesson_name" VARCHAR(50)
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS "Calendar" (
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
        CREATE TABLE IF NOT EXISTS "Announcement" (
        "announcement_id" SERIAL PRIMARY KEY,
        "teacher_id" INT,
        "text" VARCHAR(255),
        "date" TIMESTAMP,
        "deadline" DATE,
        CONSTRAINT fk_teacher_announcement FOREIGN KEY ("teacher_id") REFERENCES "User"("user_id")
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS "Task" (
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
        CREATE TABLE IF NOT EXISTS "Log" (
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
        CREATE TABLE IF NOT EXISTS "Chat" (
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
        CREATE TABLE IF NOT EXISTS "HashedPasswords" (
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
                        userprofile.birthdate_line.setText(user_data[8].strftime('%Y-%m-%d'))
                        userprofile.city_line.setText(user_data[6])
                        student.label_2.setText("Welcome, " + user_data[3])
                        student.label.setText(user_data[3] + " " + user_data[4])

                        if account_type == "Student":
                            stackedWidget.setCurrentIndex(3)
                            student.load_attendance()
                            student.load_tasks()
                            student.load_announcements()
                            student.load_calendar_events()
                            student.show_tasks()
                            student.populate_table()
                            student.show_announcements()

                        elif account_type == "Teacher":
                            stackedWidget.setCurrentIndex(4)
                            # teacher.task_manager.load_data()
                            # teacher.populate_students_list()
                            # teacher.populate_todo_list()
                            # teacher.populate_students_table()
                            # teacher.populate_attendance_table()
                            # teacher.populate_mentor_attendance_table()
                            # teacher.connect_table_signals() 
                            stackedWidget.setCurrentIndex(4)
                            # teacher.pushButton_switchadmin.hide()
                            teacher.label_Name.setText(f"Welcome {user_data[2]} {user_data[3]}")

                        elif account_type == "Admin":
                            # teacher.task_manager.load_data()
                            # teacher.populate_students_list()
                            # teacher.populate_todo_list()
                            # teacher.populate_students_table()
                            # teacher.populate_attendance_table()
                            # teacher.populate_mentor_attendance_table()
                            # teacher.pushButton_switchadmin.show()
                            stackedWidget.setCurrentIndex(5)
                            teacher.label_Name.setText(f"Welcome {user_data[2]} {user_data[3]}")
                            # admin.fill_table()

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
        to the 'accounts.json' file and switches to the login form.
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


        try:
            # Check for existing user in the database
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM usertable WHERE email = %s", (email,))
            existing_user = cur.fetchone()
            if existing_user:
                self.show_error_message("The email address provided already exists in our records. If you have an existing account, please proceed to the login page.")
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

                good_to_go = True
        
        except Exception as e:
            self.show_error_message(f"An unexpected error occurred: {str(e)}")

        finally:
            # Close database connection
            if cur:
                cur.close()
            if conn:
                conn.commit()
                conn.close()

                                            
        if good_to_go:
            try:
                stackedWidget.setCurrentIndex(0)
                login.clear_line_edits_loginform()
            except Exception as e:
                self.show_error_message(f"An unexpected error occurred while saving the account information: {str(e)}")




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
        adds the new TA account request to the 'TA_tobecreated.json' file.
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
        good_to_go=False

        try:
            # Check for existing user in the database
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM usertable WHERE email = %s", (email,))
            existing_user_active = cur.fetchone()
            cur.execute("SELECT application_id FROM application WHERE email = %s", (email,))
            existing_user_pending = cur.fetchone()
            if existing_user_pending:
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
                """, (email, hashed_password, first_name, last_name, phone, city, gender, birthdate, False))

                good_to_go = True
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

    def clear_line_edits_contactadmin(self):
        """
        Clears line edits in the contact admin form.
        """
        self.TA_email_LE.clear()
        self.TA_password_LE.clear()
        self.TA_confirmpass_LE.clear()
        self.TA_name_LE.clear()
        self.TA_surname_LE.clear()


class Teacher(QMainWindow):
    def __init__(self):
        super(Teacher, self).__init__()
        loadUi('teacher_page.ui', self)
        self.Chatboard_but.clicked.connect(self.switch_chatboard)

        
    def switch_loginform(self):
        stackedWidget.setCurrentIndex(0)
    
    def switch_chatboard(self):
        stackedWidget.setCurrentIndex(6)
        chatboard.fill_user_list2()

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

            conn.commit()
        except Exception as e:
            # Handle the exception (show error message, log, etc.)
            print(f"Error: {str(e)}")
        finally:
            cur.close()
            conn.close()

    def switch_previous_form(self):
        try:
            # Fetch the existing user data from the database
            with self.db_trans as db:
                user_data = db.fetch_data("SELECT * FROM usertable WHERE user_id = %s", (global_user_id,))
                if user_data and user_data[0][9] == "Student":
                    stackedWidget.setCurrentIndex(3)
                elif user_data and user_data[0][9] == "Teacher":
                    stackedWidget.setCurrentIndex(4)
                elif user_data and user_data[0][9] == "Admin":
                    stackedWidget.setCurrentIndex(5)
        except Exception as e:
            print(f"Error: {str(e)}")
            self.show_error_message(f"Error: {str(e)}")

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
        self.fill_table()


    def fill_table(self):
       """
        Fills the table with pending TA account data.
        """
       try:
          with open("TA_tobecreated.json", "r") as pendinginfo:
                pending_accounts = json.load(pendinginfo)
                row = 0
                self.tableWidget.setRowCount(len(pending_accounts))
                for emails in pending_accounts:
                    checkbox = QCheckBox()
                    self.tableWidget.setCellWidget(row, 0, checkbox)
                    self.tableWidget.setItem(row, 1, QTableWidgetItem(emails))
                    self.tableWidget.setItem(row, 2, QTableWidgetItem(pending_accounts[emails]["name"]))
                    self.tableWidget.setItem(row, 3, QTableWidgetItem(pending_accounts[emails]["surname"]))

                    row += 1
       except Exception as e:
           print(f"Error loading data: {e}")


    def approve_account(self):
        """
        Approves selected accounts and updates the tables accordingly.
        """
        pendinginfo = open("TA_tobecreated.json", "r")
        pending_accounts = json.load(pendinginfo)
        userinfo = open("accounts.json", "r")
        accounts = json.load(userinfo)
        pending_accounts_rest=dict()
        for row in range(self.tableWidget.rowCount()):
            checkbox = self.tableWidget.cellWidget(row, 0)
            email_item = self.tableWidget.item(row, 1)
            email_key = email_item.text() if email_item else None
            if checkbox.isChecked():
                if email_key in pending_accounts:
                    accounts[email_key] = {
                        "password": pending_accounts[email_key]["password"],
                        "Account_Type": "Teacher",
                        "name": pending_accounts[email_key]["name"],
                        "surname": pending_accounts[email_key]["surname"]
                    }
            else:
                pending_accounts_rest[email_key] = {
                    "password": pending_accounts[email_key]["password"],
                    "Account_Type": "Teacher",
                    "name": pending_accounts[email_key]["name"],
                    "surname": pending_accounts[email_key]["surname"]
                 }

                
        pendinginfo.close()
        userinfo.close()
        with open("accounts.json", "w") as userinfo:
                json.dump(accounts, userinfo, indent=2)
        with open("TA_tobecreated.json", "w") as pendinginfo:
                json.dump(pending_accounts_rest, pendinginfo, indent=2)
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(len(pending_accounts_rest))
        row = 0
        for emails in pending_accounts_rest:
            checkbox = QCheckBox()
            self.tableWidget.setCellWidget(row, 0, checkbox)
            self.tableWidget.setItem(row, 1, QTableWidgetItem(emails))
            self.tableWidget.setItem(row, 2, QTableWidgetItem(pending_accounts_rest[emails]["name"]))
            self.tableWidget.setItem(row, 3, QTableWidgetItem(pending_accounts_rest[emails]["surname"]))
            row += 1            

    def discard_account(self):
        """
        Discards selected accounts and updates the tables accordingly.
        """
        pendinginfo = open("TA_tobecreated.json", "r")
        pending_accounts = json.load(pendinginfo)
        pending_accounts_rest=dict()
        for row in range(self.tableWidget.rowCount()):
            checkbox = self.tableWidget.cellWidget(row, 0)
            email_item = self.tableWidget.item(row, 1)
            email_key = email_item.text() if email_item else None
            if not checkbox.isChecked():
                if email_key in pending_accounts:
                    pending_accounts_rest[email_key] = {
                        "password": pending_accounts[email_key]["password"],
                        "Account_Type": "Teacher",
                        "name": pending_accounts[email_key]["name"],
                        "surname": pending_accounts[email_key]["surname"]
                    }
             
        pendinginfo.close()
        with open("TA_tobecreated.json", "w") as pendinginfo:
                json.dump(pending_accounts_rest, pendinginfo, indent=2)
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(len(pending_accounts_rest))
        row = 0
        for emails in pending_accounts_rest:
            checkbox = QCheckBox()
            self.tableWidget.setCellWidget(row, 0, checkbox)
            self.tableWidget.setItem(row, 1, QTableWidgetItem(emails))
            self.tableWidget.setItem(row, 2, QTableWidgetItem(pending_accounts_rest[emails]["name"]))
            self.tableWidget.setItem(row, 3, QTableWidgetItem(pending_accounts_rest[emails]["surname"]))
            row += 1   

    def switch_teacherform(self):
        stackedWidget.setCurrentIndex(4)

    def switch_chatboard(self):
        stackedWidget.setCurrentIndex(6)
        chatboard.fill_user_list2()
    
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
        self.usertableWidget.setHorizontalHeaderLabels(["Name","Email"])
        # self.fill_user_list2()
        self.Back_TF_but.clicked.connect(self.switch_previous_form)
        self.Send_but.clicked.connect(self.send_message)
        self.usertableWidget.itemSelectionChanged.connect(self.selection)
        self.history_LE.setReadOnly(True)


    def fill_user_list2(self):
        """
        Fills the user table with user information and unread message counts.
        """
        try:
            with open("chats.json", "r") as chatinfo:
                chat_entries = json.load(chatinfo)
        except Exception as e:
            print(f"Error loading data: {e}")
            return
        
        try:
            with open("accounts.json", "r") as userinfo:
                user_accounts = json.load(userinfo)
        except Exception as e:
            print(f"Error loading data: {e}")
            return

        unread_list=dict()

        user_email = login.email_LE.text()


        try:
            for i in user_accounts:
                unread_count = 0
                msg_count = 1
                if i not in chat_entries[user_email]:
                    unread_list[i] = 0
                else:
                    for j in chat_entries[user_email][i]:
                        messageid = "message" + str(msg_count)
                        if (
                            messageid in chat_entries[user_email][i]
                            and chat_entries[user_email][i][messageid]["read"] == 0
                            and chat_entries[user_email][i][messageid]["Status"] == "Received"
                        ):
                            unread_count += 1
                        msg_count += 1
                    unread_list[i] = unread_count
        except Exception as e:
            print(f"Error loading data: {e}")
        
        row = 0
        self.usertableWidget.setRowCount(len(user_accounts))
        self.usertableWidget.setColumnWidth(0, 185)
        self.usertableWidget.setColumnWidth(1, 0)


#Emailin chats.jsonda yer almaması durumunda hata veriyor. Düzeltilmesi gerekiyor.
        

        for email, data in user_accounts.items():
            unread_count = unread_list.get(email, 0)
            if unread_count > 0:
                self.usertableWidget.setItem(
                    row,
                    0,
                    QTableWidgetItem(data["surname"] + ", " + data["name"] + " (" + str(unread_list[email]) + ")"),
                )
                self.usertableWidget.item(row, 0).setBackground(QColor(255, 0, 0))
            else:
                self.usertableWidget.setItem(row, 0, QTableWidgetItem(data["surname"] + ", " + data["name"]))
            self.usertableWidget.setItem(row, 1, QTableWidgetItem(email))
            row += 1

    def selection(self):
        """
        Handles user selection from the user table and displays the chat history.
        """
        selected_items = self.usertableWidget.selectedItems()

        if not selected_items:
            return
        selected_row=selected_items[0].row()
        recipient=self.usertableWidget.item(selected_row,1).text()

        user_email = login.email_LE.text()


        with open("accounts.json", "r") as userinfo:
            accounts=json.load(userinfo)
            name_of_sender=accounts[user_email]["name"]
            name_of_recepient=accounts[recipient]["name"]

        with open("chats.json", "r") as chatinfo:
            chat_entries=json.load(chatinfo)

            # Check if user_email and recipient exist in chat_entries
        if user_email not in chat_entries or recipient not in chat_entries[user_email]:
            if hasattr(self, 'history_LE'):
                self.history_LE.setText("")
            return


        for key in chat_entries[user_email][recipient]:
            inner_dict = chat_entries[user_email][recipient][key]
            inner_dict["read"]=1

        with open("chats.json", "w") as chatinfo:
            json.dump(chat_entries, chatinfo, indent=2)
        

        count=0

        chat_recipient = chat_entries[user_email].get(recipient, {})

        if not chat_recipient:
            if hasattr(self, 'history_LE'):
                self.history_LE.setText("")
            return

        for i in chat_entries[user_email][recipient]:
            if count==0:
                time1=chat_entries[user_email][recipient][i]["Time"]
                sender=chat_entries[user_email][recipient][i]["Status"]
                message=chat_entries[user_email][recipient][i]["Message"]
                formatted_date1 = datetime.fromtimestamp(time1).strftime("%A, %B %d")
                formatted_time=datetime.fromtimestamp(time1).strftime("%H:%M")
                padding = "-" * ((50 - len(formatted_date1)) // 2)
                if hasattr(self, 'history_LE'):
                    self.history_LE.setText(padding + formatted_date1 + padding + "\n")
                    if sender == "Sent":
                        self.history_LE.append("you : " + formatted_time + "\n" + message + "\n")
                    else:
                        self.history_LE.insertPlainText(name_of_recepient+ " : " + formatted_time + "\n" + message + "\n")

                count+=1
            else:
                time2=chat_entries[user_email][recipient][i]["Time"]
                sender=chat_entries[user_email][recipient][i]["Status"]
                message=chat_entries[user_email][recipient][i]["Message"]
                formatted_date2 = datetime.fromtimestamp(time2).strftime("%A, %B %d")
                formatted_time=datetime.fromtimestamp(time2).strftime("%H:%M")
                if formatted_date1==formatted_date2:
                    if sender=="Sent":
                        self.history_LE.append("you : " + formatted_time + "\n" + message+"\n")

                    else:
                        self.history_LE.append(name_of_recepient + " : " + formatted_time + "\n" + message+"\n")

                else:
                    padding = "-" * ((50 - len(formatted_date2)) // 2)

                    self.history_LE.append(padding + formatted_date2 + padding+"\n")
                    if sender=="Sent":
                        self.history_LE.append("you : " + formatted_time + "\n" + message+"\n")

                    else:
                        self.history_LE.append(name_of_recepient + " : " + formatted_time + "\n" + message+"\n")

                count+=1
                formatted_date1=formatted_date2        

        count=0
        self.fill_user_list2()
    
    def send_message(self):
        """
        Sends a message to the selected recipient and updates the chat entries.
        """
        message=self.send_TE.toPlainText()
        # user_email=login.email_LE.text()
        selected_items = self.usertableWidget.selectedItems()
        user_email = login.email_LE.text()

        if not selected_items:
            return
        
        selected_row=selected_items[0].row()
        recipient=self.usertableWidget.item(selected_row,1).text()
        
        with open("chats.json", "r") as chat_file:
            chat_entries = json.load(chat_file)
        
        if user_email not in chat_entries:
            chat_entries[user_email] = {}
        
        chat_entries.setdefault(user_email, {})
        chat_entries.setdefault(recipient, {})
        
        time=datetime.now().timestamp()
        new_message_key_user = f"message{len(chat_entries[user_email].get(recipient, {})) + 1}"
        new_message_key_recipient = f"message{len(chat_entries[recipient].get(user_email, {})) + 1}"
        # new_message_key = f"message{len(chat_entries[user_email][recipient]) + 1}"

        chat_entries[user_email].setdefault(recipient, {})[new_message_key_user] = {
        "Time": time,
        "Status": "Sent",
        "read": 1,
        "Message": message
        }

        chat_entries[recipient].setdefault(user_email, {})[new_message_key_recipient] = {
        "Time": time,
        "Status": "Received",
        "read": 0,
        "Message": message
        }

        with open("chats.json", "w") as chat_file:
            json.dump(chat_entries, chat_file, indent=2) 
        
        self.send_TE.setText("")
        self.selection()

        
    def switch_previous_form(self):
        with open("accounts.json", "r") as userinfo:
            accounts = json.load(userinfo)
        if accounts[login.email_LE.text()]["Account_Type"]=="Student":
            stackedWidget.setCurrentIndex(3)
        elif accounts[login.email_LE.text()]["Account_Type"]=="Teacher":
            stackedWidget.setCurrentIndex(4)
        elif accounts[login.email_LE.text()]["Account_Type"]=="Admin":
            stackedWidget.setCurrentIndex(5)
    
    def switch_chatboard(self):
        stackedWidget.setCurrentIndex(6)
        chatboard.fill_user_list2()


class Main_Window(QMainWindow):
    def __init__(self):
        super(Main_Window, self).__init__()


        loadUi('student.ui', self)  # UI dosyasını yükle
        # loadUi(r'C:\Users\Gebruiker\Desktop\Python\PYQT5\calendar\student - Kopya (2).ui', self)  # UI dosyasını yükle
        self.pushButton.clicked.connect(self.switch_chatboard)
        self.pushButton_2.clicked.connect(self.switch_userprofile)
        self.back_button.clicked.connect(self.switch_login)
        self.setFixedSize(900,600)
        self.setWindowTitle('Campus Pulse')


        self.note_edit = self.findChild(QLabel, 'note_edit')  # UI dosyasındaki note_edit adlı öğeyi bul
        self.calendar = self.findChild(QCalendarWidget, 'calendarWidget')  # UI dosyasındaki calendarWidget adlı öğeyi bul
        self.mission_complete = self.findChild(QPushButton, 'self.mission_complete') 


        self.calendar.clicked.connect(self.load_calendar_events)
        self.comboBox_2.currentIndexChanged.connect(self.populate_table)
        self.comboBox_3.currentIndexChanged.connect(self.populate_table)
        

#load file

    def load_attendance(self):
        try:
            with open('attendance.json', 'r') as file_2:
                self.attendance = json.load(file_2)
        except FileNotFoundError:
            self.attendance = {}

    def load_tasks(self):
        try:
            with open('tasks.json', 'r') as file_3:
                self.tasks = json.load(file_3)
        except FileNotFoundError:
            self.tasks = {}

    def load_announcements(self):
        try:
            with open('announcements.json', 'r') as file_4:
                self.announcements = json.load(file_4)
        except FileNotFoundError:
            self.announcements = {}

#meeting calendar
    def load_calendar_events(self):
        self.mail = login.email_LE.text()

        if self.mail in self.attendance:
            meeting = self.attendance[self.mail]
            mentor = meeting["Mentor Meeting"]
            data_science = meeting["Data Science"]
        
            for date_str in mentor.keys():
                date = QDate.fromString(str(date_str), Qt.ISODate)
                if date.isValid():  #and result1==['Mentor']:
                    self.calendar.setDateTextFormat(date, self.get_calendar_event_format1())

            for date_str in data_science.keys():
                date = QDate.fromString(str(date_str), Qt.ISODate)
                if date.isValid():  #and result2==['Data Science']:
                    self.calendar.setDateTextFormat(date, self.get_calendar_event_format2())

            selected_date = self.calendar.selectedDate().toString(Qt.ISODate)
            if selected_date in data_science:
                self.note_edit.setText('Data Science Course')
            elif selected_date in mentor:
                self.note_edit.setText('Mentor Meeting')
            else:
                self.note_edit.clear()
        else:
            pass


    def get_calendar_event_format1(self):
        format = self.calendar.dateTextFormat(self.calendar.selectedDate())
        font = format.font()
        font.setBold(True)  # Metni bold yap
        format.setFont(font)
        format.setForeground(Qt.red)
        format.setBackground(Qt.green)
        return format
    
    def get_calendar_event_format2(self):
        format = self.calendar.dateTextFormat(self.calendar.selectedDate())
        font = format.font()
        font.setBold(True)  # Metni bold yap
        format.setFont(font)
        format.setForeground(Qt.green)
        format.setBackground(Qt.red)
        return format   

#status of attendance
    def populate_table(self):
        self.mail = login.email_LE.text()

        if self.mail in self.attendance:
      
            for i in range(self.tableWidget.rowCount() - 1, -1, -1):
                is_row_empty = all(self.tableWidget.item(i, j) is None or self.tableWidget.item(i, j).text() == '' for j in range(self.tableWidget.columnCount()))
                if not is_row_empty:
                    self.tableWidget.removeRow(i)

            filter_statu1 = self.comboBox_2.currentText()
            filter_statu2 = self.comboBox_3.currentText()

            dates = self.attendance[self.mail]
            result = dates[filter_statu1]
            for date, value in result.items():

                if value==filter_statu2 and QDate.fromString(date, "yyyy-MM-dd") <= QDate.currentDate():
                    row_position = self.tableWidget.rowCount()
                    self.tableWidget.insertRow(row_position)
                    item_date = QTableWidgetItem(date)
                    item_value = QTableWidgetItem(str(value))
                    self.tableWidget.setItem(row_position, 0, item_value)
                    self.tableWidget.setVerticalHeaderItem(row_position, item_date)
                if filter_statu2=='Make your choice' and (filter_statu1=='Mentor Meeting' or filter_statu1=='Data Science') and QDate.fromString(date, "yyyy-MM-dd") <= QDate.currentDate():
                    row_position = self.tableWidget.rowCount()
                    self.tableWidget.insertRow(row_position)
                    item_date = QTableWidgetItem(date)
                    item_value = QTableWidgetItem(str(value))
                    self.tableWidget.setItem(row_position, 0, item_value)
                    self.tableWidget.setVerticalHeaderItem(row_position, item_date)
        else:
            pass

                # value_str = str(value)
                # symbol = '\u2717'
                # value_with_symbol = f"{value_str} {symbol}"

                # # QTableWidgetItem oluştur ve tabloya ekle
                # item_value = QTableWidgetItem(value_with_symbol)
                # self.tableWidget.setItem(row_position, 0, item_value)
                # self.tableWidget.setVerticalHeaderItem(row_position, item_date)

# to do list
    def show_tasks(self):
        self.mail = login.email_LE.text()

        if self.mail in self.tasks:

            assignment=self.tasks[self.mail]
            self.mission=assignment['tasks']
            self.check_boxes = []

        
            for i in self.mission:
                row_position = self.table_todolist.rowCount()
            
                self.table_todolist.insertRow(row_position)
                self.table_todolist.setItem(row_position, 1, QTableWidgetItem(str(i['task'])))
                self.table_todolist.setItem(row_position, 2, QTableWidgetItem(i['deadline']))
                self.table_todolist.setVerticalHeaderItem(row_position, QTableWidgetItem(str(i['id'])))
            
                self.check_box = QCheckBox()
                if self.mission[row_position]['status'] == True:
                    self.check_box.setChecked(True)
                else:
                    self.check_box.setChecked(False)
                self.table_todolist.setCellWidget(row_position,0, self.check_box)

                self.check_boxes.append(self.check_box)

        

            self.table_todolist.setColumnWidth(0,30)
            self.table_todolist.setColumnWidth(1,415)
            self.table_todolist.setColumnWidth(2,100)
     

            self.connect_check_boxes()
        else:
            pass

# to do list check
    def connect_check_boxes(self):
        for row, check_box in enumerate(self.check_boxes):
            check_box.stateChanged.connect(lambda state, r=row: self.onCheckBoxStateChanged(state, r))

    def onCheckBoxStateChanged(self, state, row):
        self.mail = login.email_LE.text()
        if self.mail in self.tasks:
            self.assignment=self.tasks[self.mail]

            if state == 2:  # Qt.Checked
                self.mission[row]['status'] = True   
            else:
                self.mission[row]['status'] = False 

            with open('tasks.json', 'w') as json_file:
                    json.dump(self.tasks, json_file, indent=2)
        else:
            pass
        # print(self.mission[row]['status'])
            


# # announcements  
    def show_announcements(self):
        # content=self.announcements["content"]
        # print(t)
        # for k in self.announcements:
            # row = self.announcement_widget.rowCount()
            
            # self.announcement_widget.insertRow(row)
            # self.announcement_widget.setItem(row, 0, QTableWidgetItem(k["content"]))
            # self.announcement_widget.setVerticalHeaderItem(row_position, QTableWidgetItem(str(i['id'])))
            
        self.announcement_index = 0  # Sıradaki anonsun indeksi

        # QTimer oluştur
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_announcements)
        self.timer.start(1500)  # 5 saniyede bir kontrol et     
        self.update_announcements()  # Başlangıçta da çalıştır

    def update_announcements(self):
        # Anonsları güncelle
        self.announcement_textedit.setToolTip("\n".join(str(announcement.get("content", "")) for announcement in self.announcements))
        if self.announcement_index < len(self.announcements):
            announcement = self.announcements[self.announcement_index]
            last_date = announcement.get("last_date")
            current_date = datetime.now().strftime("%Y-%m-%d")
            if last_date >= current_date:
                self.announcement_textedit.setText('')
                self.announcement_textedit.setText('  \u2605  ' + announcement['content']) #ekranda sola bitisik yazmasin

            # Bir sonraki anonsa geç
            self.announcement_index += 1
        else:
            # Anons listesinin sonuna gelindiğinde başa dön
            self.announcement_index = 0
    
    def switch_chatboard(self):
        stackedWidget.setCurrentIndex(6)
        chatboard.fill_user_list2()

    def switch_login(self):
        stackedWidget.setCurrentIndex(0)
        login.clear_line_edits_loginform()
    
    def switch_userprofile(self):
        stackedWidget.setCurrentIndex(7)

class MyMainWindow(QMainWindow):
    def __init__(self):
        super(MyMainWindow, self).__init__()
        #self.setupUi(self)
        loadUi("teacher_page.ui", self)
        self.setWindowTitle('Campus Pulse')
        self.task_manager = TaskManager()
        # self.populate_students_list()
        # self.populate_todo_list()
        # self.populate_students_table()
        # self.populate_attendance_table()
        # self.populate_mentor_attendance_table()
        # self.connect_table_signals() 
        
    
        self.pushButton_chatbox.clicked.connect(student.switch_chatboard)
        self.pushButton_profile.clicked.connect(student.switch_userprofile)
        self.pushButton_backtologin.clicked.connect(student.switch_login)
        self.pushButton_switchadmin.clicked.connect(self.switch_to_admin)

        self.pushButton_schedule.clicked.connect(lambda: self.MainPage.setCurrentIndex(1))
        self.pushButton_announcement.clicked.connect(lambda: self.MainPage.setCurrentIndex(1))

        self.pushButton_SchSave.clicked.connect(self.save_attendance)
        self.tableWidget_Students.setColumnWidth(0,100)
        self.tableWidget_Students.setColumnWidth(1,150)
        self.tableWidget_Students.setColumnWidth(2,250)
        self.tableWidget_Students.setColumnWidth(3,335)

        self.tableWidget_ToDoList.setColumnWidth(0, 50)  # 0. sütunun genişliği
        self.tableWidget_ToDoList.setColumnWidth(1, 635)  # 1. sütunun genişliği
        self.tableWidget_ToDoList.setColumnWidth(2, 150)
        
        # Create Task butonuna tıklandığında
        self.pushButton_CreateTask.clicked.connect(self.create_task)

        # Send Announcement butonuna tıklandığında
        self.pushButton_SendAnnouncement.clicked.connect(self.send_announcement)

        self.announcements = self.task_manager.get_all_announcements()
        self.announcement_index = 0  # Sıradaki anonsun indeksi

        # QTimer oluştur
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_announcements)
        self.timer.start(5000)  # 5 saniyede bir kontrol et
        self.update_announcements()  # Başlangıçta da çalıştır
        self.textEdit_AnnouncementView.setToolTip("\n".join(str(announcement.get("content", "")) for announcement in self.announcements))


    def switch_to_chatboard(self):
        stackedWidget.setCurrentIndex(6)
    
    def switch_to_admin(self):
        email=login.email_LE.text()
        with open('accounts.json', 'r') as f:
            self.accounts_data = json.load(f)
            if self.accounts_data[email]["Account_Type"]=="Admin":
                stackedWidget.setCurrentIndex(5)
            else:
                pass


            
    def populate_attendance_table(self):
        # Get students and dates from your data
        students = self.task_manager.get_students()
        dates = self.get_distinct_dates_from_attendance()
        # print("Tarihler:", dates)
        
        # Set the row and column counts
        self.tableWidget_cattendencetable.setRowCount(len(students) + 1)  # +1 for the header row
        self.tableWidget_cattendencetable.setColumnCount(len(dates) + 3)  # +1 for the student names column
        self.tableWidget_cattendencetable.horizontalHeader().setVisible(True)

        # Set the headers
        headers = ["Name","Surname","Email"] + dates
        # print("Başlıklar:", headers)

        self.tableWidget_cattendencetable.setHorizontalHeaderLabels(headers)

        # Populate the table with data
        for row, student in enumerate(students):
            # Set the student name
            name = student.get("name", "")
            surname = student.get("surname", "")
            email = student.get("Email", "")
            self.tableWidget_cattendencetable.setItem(row, 0, QTableWidgetItem(name))
            self.tableWidget_cattendencetable.setItem(row, 1, QTableWidgetItem(surname))
            self.tableWidget_cattendencetable.setItem(row, 2, QTableWidgetItem(email))

            # Set attendance for each date
            for col, date in enumerate(dates):
                email = student['Email']
                status = self.get_attendance_status(email, date, "Data Science")
                self.tableWidget_cattendencetable.setItem(row, col + 3, QTableWidgetItem(status))
            

    def populate_mentor_attendance_table(self):
            # Get students with account type 'Student' from accounts.json
            students = [data for data in self.task_manager.accounts_data.values() if data.get("Account_Type") == "Student"]

            # Get distinct dates from Mentor Meeting attendance in attendance.json
            dates = self.get_distinct_dates_from_mentor_attendance()
            # print("Tarihler:", dates)
            # Set the row and column counts
            self.tableWidget_mattendencetable.setRowCount(len(students))
            self.tableWidget_mattendencetable.setColumnCount(len(dates) + 3)  # +3 for Name, Surname, Email columns
            self.tableWidget_mattendencetable.horizontalHeader().setVisible(True)

            # Set the headers
            headers = ["Name", "Surname", "Email"] + dates
            # print("Başlıklar:", headers)

            self.tableWidget_mattendencetable.setHorizontalHeaderLabels(headers)

            # Populate the table with data
            for row, student in enumerate(students):
                name = student.get("name", "")
                surname = student.get("surname", "")
                email = student.get("Email", "")

                # Set the Name, Surname, and Email columns
                self.tableWidget_mattendencetable.setItem(row, 0, QTableWidgetItem(name))
                self.tableWidget_mattendencetable.setItem(row, 1, QTableWidgetItem(surname))
                self.tableWidget_mattendencetable.setItem(row, 2, QTableWidgetItem(email))

                # Set attendance for each date
                for col, date in enumerate(dates):
                    status = self.get_attendance_status(email, date, "Mentor Meeting")
                    self.tableWidget_mattendencetable.setItem(row, col + 3, QTableWidgetItem(status))


    def get_distinct_dates_from_attendance(self):
        # Get distinct dates from attendance_data
        all_dates = []
        for student_attendance in self.task_manager.attendance_data.values():
            for course_dates in student_attendance.values():
                all_dates.extend(course_dates.keys())
        sorted_dates = sorted(set(all_dates))
        return sorted_dates

    def get_attendance_status(self, email, date, meeting_type):
            # Get attendance status for the given email, date, and meeting type
            if email in self.task_manager.attendance_data:
                if meeting_type in self.task_manager.attendance_data[email]:
                    if date in self.task_manager.attendance_data[email][meeting_type]:
                        return self.task_manager.attendance_data[email][meeting_type][date]

            return "-"



    def get_distinct_dates_from_mentor_attendance(self):
        # Get distinct dates from Mentor Meeting attendance in attendence.json
        all_dates = []
        for student_attendance in self.task_manager.attendance_data.values():
            if "Mentor Meeting" in student_attendance:
                all_dates.extend(student_attendance["Mentor Meeting"].keys())

        return list(set(all_dates))
                 
    def update_announcements(self):
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
            
    def populate_students_list(self):
        # Öğrenci listesini doldur
        students = self.task_manager.get_students()
        for student in students:
            email = student.get("Email", "")
            name = student.get("name", "")
            surname = student.get("surname", "")
            self.listWidget_AssignList.addItem(f"{name} {surname} ({email})")
            self.listWidget_studentlist.addItem(f"{name} {surname} ({email})")
            
    def create_task(self):
        # Yeni görev oluştur
        task_text = self.plainTextEdit_NewTask.toPlainText()

        deadlinecontrol = self.dateTimeEdit_Deadline.date()
        if  deadlinecontrol < QDate.currentDate():
            QMessageBox.warning(self, "Warning", "Selected date can not be before the current date.")
            return  
        deadline = deadlinecontrol.toString("yyyy-MM-dd")
        # Seçilen öğrenci e-postalarını al
        selected_items = self.listWidget_AssignList.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select at least one student.")
            return        
        
        assigned_emails = [item.text().split("(")[-1].split(")")[0] for item in selected_items]

        # Görev yöneticisine görev oluşturma işlemini yapması için bildir
        self.task_manager.create_task(assigned_emails, task_text, deadline)
        QMessageBox.information(self, "Success", "Task created successfully!")

        # Görev oluşturulduktan sonra formu temizle
        self.plainTextEdit_NewTask.clear()
        self.dateTimeEdit_Deadline.clear()
        self.populate_todo_list()
        self.update_table()

    def send_announcement(self):
        # Yeni anons oluştur ve görev yöneticisine bildir
        announcement_text = self.textEdit_announcementtext.toPlainText()
        if not announcement_text:
            QMessageBox.warning(self, "Warning", "Announcement text cannot be empty.")
            return        
        
        last_date_control = self.dateEdit_lastdateofannouncement.date()
        if  last_date_control < QDate.currentDate():
            QMessageBox.warning(self, "Warning", "Selected date can not be before the current date.")
            return  
        last_date = last_date_control.toString("yyyy-MM-dd")   
        
        self.task_manager.create_announcement(announcement_text, last_date)
        QMessageBox.information(self, "Success", "Announcement created successfully!")

        # Anons oluşturulduktan sonra formu temizle
        self.textEdit_announcementtext.clear()
        self.dateEdit_lastdateofannouncement.clear()

    def populate_todo_list(self):
        self.tableWidget_ToDoList.setRowCount(0)  # Önceki verileri temizle

        tasks = self.task_manager.get_all_tasks()

        for task in tasks:
            row_position = self.tableWidget_ToDoList.rowCount()
            self.tableWidget_ToDoList.insertRow(row_position)

            self.tableWidget_ToDoList.setItem(row_position, 0, QTableWidgetItem(str(task["id"])))
            self.tableWidget_ToDoList.setItem(row_position, 1, QTableWidgetItem(task["task"]))
            self.tableWidget_ToDoList.setItem(row_position, 2, QTableWidgetItem(task["deadline"]))

    def populate_students_table(self):
        # Students tablosunu güncelle
        students = self.task_manager.get_students()
        self.tableWidget_Students.setRowCount(len(students))

        for row, student in enumerate(students):
            email = student.get("Email", "")
            name = student.get("name", "")
            surname = student.get("surname", "")
            tasks = self.task_manager.get_student_tasks(email)

            # Satırı eklemek için rowCount kullanmamıza gerek yok
            self.tableWidget_Students.insertRow(row)

            self.tableWidget_Students.setItem(row, 2, QTableWidgetItem(email))
            self.tableWidget_Students.setItem(row, 0, QTableWidgetItem(name))
            self.tableWidget_Students.setItem(row, 1, QTableWidgetItem(surname))

            # Görevleri birleştirip metin oluştur
            tasks_text = ", ".join(f"{task.get('id')}={'✅' if task.get('status') else '❌'}" for task in tasks)

            # Doğru sütuna QTableWidgetItem ekleyin
            self.tableWidget_Students.setItem(row, 3, QTableWidgetItem(tasks_text))

    def save_attendance(self):
        # PushButton_SchSave butonuna tıklandığında çalışacak işlemler
        selected_items = self.listWidget_studentlist.selectedItems()

        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select at least one student.")
            return

        selected_date1 = self.dateTimeEdit_sch.date()
        if  selected_date1 < QDate.currentDate():
            QMessageBox.warning(self, "Warning", "Selected date can not be before the current date.")
            return        
        selected_date=selected_date1.toString("yyyy-MM-dd")
        
        selected_item = self.listWidget_coursemeet.currentItem()
        if not selected_item or not selected_item.text():
            QMessageBox.warning(self, "Warning", "Please select at least one Schedule Type.")
            return

        selected_course = selected_item.text()

        for item in selected_items:
            student_info = item.text().split("(")
            student_email = student_info[-1].split(")")[0]

            if student_email in self.task_manager.attendance_data:
                if selected_course not in self.task_manager.attendance_data[student_email]:
                    self.task_manager.attendance_data[student_email][selected_course] = {}

                self.task_manager.attendance_data[student_email][selected_course][selected_date] = "Not Attended"
            else:
                self.task_manager.attendance_data[student_email] = {
                    selected_course: {selected_date: "Not Attended"}
                }

        # attendence.json dosyasını güncelle
        with open('attendance.json', 'w') as f:
            json.dump(self.task_manager.attendance_data, f, indent=2)

        QMessageBox.information(self, "Success", "Attendance records saved successfully!")


    def connect_table_signals(self):
            # Connect cellChanged signal for both tables to the update_attendance function
            self.tableWidget_mattendencetable.cellChanged.connect(self.update_attendance)
            self.tableWidget_cattendencetable.cellChanged.connect(self.update_attendance)

    def update_attendance(self, row, col):

        # Get the email from the respective table
        email_col = 2  # Assuming Email column is at index 2
        email_m = self.tableWidget_mattendencetable.item(row, email_col).text()
        email_c = self.tableWidget_cattendencetable.item(row, email_col).text()

        # Check if the column corresponds to a date (skip Name, Surname, and Email columns)
        if col > 2:
            # Get the date from the respective table
            date_m = self.get_date_from_table(self.tableWidget_mattendencetable, col) if email_m else None
            date_c = self.get_date_from_table(self.tableWidget_cattendencetable, col) if email_c else None

            # Get the new attendance status from the table cell
            status_m_item = self.tableWidget_mattendencetable.item(row, col)
            status_m = status_m_item.text() if status_m_item is not None else None

            status_c_item = self.tableWidget_cattendencetable.item(row, col)
            status_c = status_c_item.text() if status_c_item is not None else None

            # Update attendance data only if all necessary information is available
            if email_m and date_m and status_m:
                self.task_manager.update_attendance_data(email_m, "Mentor Meeting", date_m, status_m)

            if email_c and date_c and status_c:
                self.task_manager.update_attendance_data(email_c, "Data Science", date_c, status_c)

    def get_date_from_table(self, table_widget, col):
        # Get the date from the respective table
        header_item = table_widget.horizontalHeaderItem(col)
        if header_item is not None:
            return header_item.text()
        return None

    def update_table(self):
        # Students tablosunu güncelle
        students = self.task_manager.get_students()
        self.tableWidget_Students.setRowCount(len(students))




        for row, student in enumerate(students):
            email = student.get("Email", "")
            name = student.get("name", "")
            surname = student.get("surname", "")
            tasks = self.task_manager.get_student_tasks(email)

            # Satırı eklemek için rowCount kullanmamıza gerek yok
            self.tableWidget_Students.insertRow(row)

            self.tableWidget_Students.setItem(row, 2, QTableWidgetItem(email))
            self.tableWidget_Students.setItem(row, 0, QTableWidgetItem(name))
            self.tableWidget_Students.setItem(row, 1, QTableWidgetItem(surname))

            # Görevleri birleştirip metin oluştur
            tasks_text = ", ".join(f"{task.get('id')}={'✅' if task.get('status') else '❌'}" for task in tasks)

            # Doğru sütuna QTableWidgetItem ekleyin
            self.tableWidget_Students.setItem(row, 3, QTableWidgetItem(tasks_text))

class TaskManager:
    def __init__(self):
        self.load_data()

    def load_data(self):
        # accounts.json, tasks.json ve announcements.json dosyalarını oku
        
        with open('accounts.json', 'r') as f:
            self.accounts_data = json.load(f)

        with open('tasks.json', 'r') as f:
            self.tasks_data = json.load(f)

        try:    
            with open('attendance.json', 'r') as f:
                self.attendance_data = json.load(f)    
        except (FileNotFoundError, json.JSONDecodeError):
            self.attendance_data = {}

        try:
            with open('announcements.json', 'r') as f:
                self.announcements_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.announcements_data = []


    def populate_students_list(self):
        # accounts.json dosyasındaki 'Student' olan öğrencileri listWidget_StudentList'e ekle
        students = [data for data in self.accounts_data.values() if data.get("Account_Type") == "Student"]
        for student in students:
            email = student.get("Email", "")
            name = student.get("name", "")
            surname = student.get("surname", "")
            self.listWidget_studentlist.addItem(f"{name} {surname} ({email})")


    def save_data(self):
        # accounts.json, tasks.json ve announcements.json dosyalarına verileri yaz
        with open('accounts.json', 'w') as f:
            json.dump(self.accounts_data, f, indent=2)

        with open('tasks.json', 'w') as f:
            json.dump(self.tasks_data, f, indent=2)

        with open('announcements.json', 'w') as f:
            json.dump(self.announcements_data, f, indent=2)

        # attendance.json dosyasına verileri yaz
        with open('attendance.json', 'w') as f:
            json.dump(self.attendance_data, f, indent=2)
            
    def get_all_tasks(self):
        # Tüm görevleri al ve ID'ye göre sırala
        all_tasks = [task for tasks in self.tasks_data.values() for task in tasks.get("tasks", [])]
        unique_tasks = {task["id"]: task for task in all_tasks}
        sorted_tasks = sorted(unique_tasks.values(), key=lambda x: int(x["id"]), reverse=True)
        return sorted_tasks

    def get_students(self):
        # accounts.json dosyasındaki öğrenci bilgilerini getir
        students = [data for data in self.accounts_data.values() if data.get("Account_Type") == "Student"]
        return students

    def get_student_tasks(self, email):
        # Öğrenciye ait görevleri getir
        if email in self.tasks_data:
            return self.tasks_data[email].get("tasks", [])
        return []

    def create_task(self, assigned_emails, task_text, deadline):
        # En yüksek task ID'sini bul
        max_task_id = max(
            (int(task["id"]) for email_tasks in self.tasks_data.values() for task in email_tasks.get("tasks", [])),
            default=0)

        # Yeni task ID'sini oluştur
        new_task_id = str(max_task_id + 1)

        # Yeni bir görev oluştur
        new_task = {
            "id": new_task_id,
            "task": task_text,
            "status": False,
            "deadline": deadline
        }

        # Görevi belirtilen e-posta adreslerine ata
        for email in assigned_emails:
            if email in self.tasks_data:
                # Ensure the "tasks" key exists for the email
                if "tasks" not in self.tasks_data[email]:
                    self.tasks_data[email]["tasks"] = []
                self.tasks_data[email]["tasks"].append(new_task)

        # tasks.json dosyasını güncelle
        self.save_data()
        
        

    def create_announcement(self, announcement_text, last_date):
        # Yeni bir anons oluştur
        new_announcement = {
            "content": announcement_text,
            "last_date": last_date
        }

        # Announcements listesine ekle
        self.announcements_data.append(new_announcement)

        # announcements.json dosyasını güncelle
        self.save_data()

    def get_all_announcements(self):
        # Tüm anonsları al, last_date'e göre sırala
        sorted_announcements = sorted(self.announcements_data, key=lambda x: x["last_date"])
        return sorted_announcements

    def update_attendance_data(self, email, meeting_type, date, status):
        if email not in self.attendance_data:
            self.attendance_data[email] = {}

        if meeting_type not in self.attendance_data[email]:
            self.attendance_data[email][meeting_type] = {}

            # Sadece durumu "N/A" değilse güncelle
        if status != "N/A":
            # Update attendance data for the specified meeting type
            self.attendance_data[email][meeting_type][date] = status

        # Update attendence.json file
        with open('attendance.json', 'w') as f:
            json.dump(self.attendance_data, f, indent=2)

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
