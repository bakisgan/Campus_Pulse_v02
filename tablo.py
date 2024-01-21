import psycopg2

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
        CONSTRAINT "fk_application_id" FOREIGN KEY ("application_id") REFERENCES "application"("application_id")
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
        CONSTRAINT fk_lesson FOREIGN KEY ("lesson_id") REFERENCES "lesson"("lesson_id"),
        CONSTRAINT fk_teacher FOREIGN KEY ("teacher_id") REFERENCES "usertable"("user_id"),
        CONSTRAINT fk_student FOREIGN KEY ("student_id") REFERENCES "usertable"("user_id")
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS announcement (
        "announcement_id" SERIAL PRIMARY KEY,
        "teacher_id" INT,
        "text" VARCHAR(255),
        "date" TIMESTAMP,
        "deadline" DATE,
        CONSTRAINT fk_teacher_announcement FOREIGN KEY ("teacher_id") REFERENCES "usertable"("user_id")
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
        CONSTRAINT fk_teacher_task FOREIGN KEY ("teacher_id") REFERENCES "usertable"("user_id"),
        CONSTRAINT fk_student_task FOREIGN KEY ("student_id") REFERENCES "usertable"("user_id")
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
        CONSTRAINT fk_user_log FOREIGN KEY ("user_id") REFERENCES "usertable"("user_id")
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
        CONSTRAINT fk_sender FOREIGN KEY ("sender_id") REFERENCES "usertable"("user_id"),
        CONSTRAINT fk_receiver FOREIGN KEY ("receiver_id") REFERENCES "usertable"("user_id")
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS hashedpasswords (
        "hash_id" SERIAL PRIMARY KEY,
        "user_id" INT UNIQUE NOT NULL,
        "hashed_password" VARCHAR(60) NOT NULL,
        FOREIGN KEY ("user_id") REFERENCES "usertable"("user_id") ON DELETE CASCADE
        )
        """
    ]

database_name = "db_campusv2"
user = "postgres"
password = "MerSer01"
host = "localhost"
port = "5432"

global_user_id = None
# Construct the database URL
db_url = f"postgresql://{user}:{password}@{host}:{port}/{database_name}"

# Veritabanı bağlantısı kurulması
try:
    connection = psycopg2.connect(
        database=database_name,
        user=user,
        password=password,
        host=host,
        port=port
    )

    cursor = connection.cursor()

    # Tabloların oluşturulması
    for query in create_table_queries:
        cursor.execute(query)
        connection.commit()

    print("Tablolar başarıyla oluşturuldu.")

except Exception as e:
    print(f"Hata: {e}")

finally:
    if connection:
        cursor.close()
        connection.close()
        print("Veritabanı bağlantısı kapatıldı.")
