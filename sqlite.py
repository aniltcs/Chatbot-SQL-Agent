import sqlite3

# Connect to SQLite
connection = sqlite3.connect("student.db")
cursor = connection.cursor()

# Create STUDENT table (you already have this)
cursor.execute("""
CREATE TABLE IF NOT EXISTS STUDENT(
    STUDENT_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    NAME VARCHAR(25),
    CLASS VARCHAR(25),
    SECTION VARCHAR(25),
    MARKS INT
)
""")

# Insert records into STUDENT table
cursor.execute("INSERT INTO STUDENT(NAME, CLASS, SECTION, MARKS) VALUES('Krish','Data Science','A',90)")
cursor.execute("INSERT INTO STUDENT(NAME, CLASS, SECTION, MARKS) VALUES('John','Data Science','B',100)")
cursor.execute("INSERT INTO STUDENT(NAME, CLASS, SECTION, MARKS) VALUES('Mukesh','Data Science','A',86)")
cursor.execute("INSERT INTO STUDENT(NAME, CLASS, SECTION, MARKS) VALUES('Jacob','DEVOPS','A',50)")
cursor.execute("INSERT INTO STUDENT(NAME, CLASS, SECTION, MARKS) VALUES('Dipesh','DEVOPS','A',35)")

# Create STUDENT_INFO table
cursor.execute("""
CREATE TABLE IF NOT EXISTS STUDENT_INFO(
    INFO_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    STUDENT_ID INT,
    DOB DATE,
    ADDRESS VARCHAR(100),
    PHONE VARCHAR(15),
    FOREIGN KEY(STUDENT_ID) REFERENCES STUDENT(STUDENT_ID)
)
""")

# Insert records into STUDENT_INFO table (linking with STUDENT_ID)
cursor.execute("INSERT INTO STUDENT_INFO(STUDENT_ID, DOB, ADDRESS, PHONE) VALUES(1, '2000-01-15', '123 Street, City', '1234567890')")
cursor.execute("INSERT INTO STUDENT_INFO(STUDENT_ID, DOB, ADDRESS, PHONE) VALUES(2, '1999-05-22', '456 Avenue, City', '2345678901')")

# Display records from both tables
print("STUDENT Table Records:")
for row in cursor.execute("SELECT * FROM STUDENT"):
    print(row)

print("\nSTUDENT_INFO Table Records:")
for row in cursor.execute("SELECT * FROM STUDENT_INFO"):
    print(row)

# Commit and close
connection.commit()
connection.close()
