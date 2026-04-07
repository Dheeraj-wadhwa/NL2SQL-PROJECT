import sqlite3
import random
from datetime import datetime, timedelta

try:
    from faker import Faker
except ImportError:
    print("Faker library not found. Please install it using: pip install faker")
    exit(1)

fake = Faker()

def create_database(db_name="clinic.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Drop tables if they exist for clean setup
    tables = ["invoices", "treatments", "appointments", "doctors", "patients"]
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    # 1. patients
    cursor.execute('''
        CREATE TABLE patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            date_of_birth DATE,
            gender TEXT,
            city TEXT,
            registered_date DATE
        )
    ''')

    # 2. doctors
    cursor.execute('''
        CREATE TABLE doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT,
            department TEXT,
            phone TEXT
        )
    ''')

    # 3. appointments
    cursor.execute('''
        CREATE TABLE appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            appointment_date DATETIME,
            status TEXT,
            notes TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id),
            FOREIGN KEY(doctor_id) REFERENCES doctors(id)
        )
    ''')

    # 4. treatments
    cursor.execute('''
        CREATE TABLE treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER,
            treatment_name TEXT,
            cost REAL,
            duration_minutes INTEGER,
            FOREIGN KEY(appointment_id) REFERENCES appointments(id)
        )
    ''')

    # 5. invoices
    cursor.execute('''
        CREATE TABLE invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            invoice_date DATE,
            total_amount REAL,
            paid_amount REAL,
            status TEXT,
            FOREIGN KEY(patient_id) REFERENCES patients(id)
        )
    ''')

    conn.commit()
    return conn

def insert_dummy_data(conn):
    cursor = conn.cursor()

    print("Generating 200 patients...")
    genders = ['Male', 'Female', 'Other']
    for _ in range(200):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = fake.email()
        phone = fake.phone_number()
        dob = fake.date_of_birth(minimum_age=1, maximum_age=90).isoformat()
        gender = random.choice(genders)
        city = fake.city()
        registered_date = fake.date_between(start_date='-5y', end_date='today').isoformat()
        
        cursor.execute('''
            INSERT INTO patients (first_name, last_name, email, phone, date_of_birth, gender, city, registered_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, phone, dob, gender, city, registered_date))

    print("Generating 15 doctors...")
    specializations_depts = [
        ('Cardiology', 'Cardiologist'),
        ('Orthopedics', 'Orthopedic Surgeon'),
        ('Pediatrics', 'Pediatrician'),
        ('Neurology', 'Neurologist'),
        ('Dermatology', 'Dermatologist'),
        ('General Practice', 'General Practitioner'),
        ('Oncology', 'Oncologist')
    ]
    for _ in range(15):
        name = "Dr. " + fake.name()
        dept, spec = random.choice(specializations_depts)
        phone = fake.phone_number()
        cursor.execute('''
            INSERT INTO doctors (name, specialization, department, phone)
            VALUES (?, ?, ?, ?)
        ''', (name, spec, dept, phone))

    print("Generating 500 appointments...")
    status_choices = ['Scheduled', 'Completed', 'Cancelled', 'No Show']
    for _ in range(500):
        patient_id = random.randint(1, 200)
        doctor_id = random.randint(1, 15)
        
        appt_datetime = fake.date_time_between(start_date='-2y', end_date='+30d')
        status = random.choices(status_choices, weights=[0.1, 0.7, 0.1, 0.1])[0]
        notes = fake.sentence() if random.random() > 0.5 else ""
        
        cursor.execute('''
            INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (patient_id, doctor_id, appt_datetime.isoformat(), status, notes))

    print("Generating 350 treatments...")
    treatment_options = [
        ("Routine Checkup", 50.0, 30),
        ("Blood Test", 25.0, 15),
        ("X-Ray", 120.0, 45),
        ("Physical Therapy", 80.0, 60),
        ("Vaccination", 35.0, 15),
        ("MRI Scan", 400.0, 90),
        ("Surgery - Minor", 1500.0, 120)
    ]
    
    cursor.execute("SELECT id FROM appointments WHERE status = 'Completed'")
    completed_appts = [row[0] for row in cursor.fetchall()]
    
    # Generate treatments and link to completed appointments
    if not completed_appts:
        # Fallback if no completed appointments
        completed_appts = [random.randint(1, 500)]
        
    for _ in range(350):
        appointment_id = random.choice(completed_appts)
        t_name, t_cost, t_duration = random.choice(treatment_options)
        
        # Add random variance to cost (+- 10%)
        actual_cost = round(t_cost * random.uniform(0.9, 1.1), 2)
        
        cursor.execute('''
            INSERT INTO treatments (appointment_id, treatment_name, cost, duration_minutes)
            VALUES (?, ?, ?, ?)
        ''', (appointment_id, t_name, actual_cost, t_duration))

    print("Generating 300 invoices...")
    invoice_status_choices = ['Paid', 'Pending', 'Overdue']
    for _ in range(300):
        patient_id = random.randint(1, 200)
        invoice_date = fake.date_between(start_date='-2y', end_date='today').isoformat()
        total_amount = round(random.uniform(50.0, 2000.0), 2)
        
        status = random.choices(invoice_status_choices, weights=[0.8, 0.15, 0.05])[0]
        
        if status == 'Paid':
            paid_amount = total_amount
        elif status == 'Pending':
            paid_amount = 0.0
        else: # Overdue
            paid_amount = round(total_amount * random.uniform(0.0, 0.5), 2)
            
        cursor.execute('''
            INSERT INTO invoices (patient_id, invoice_date, total_amount, paid_amount, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (patient_id, invoice_date, total_amount, paid_amount, status))

    conn.commit()

def print_summary(conn):
    cursor = conn.cursor()
    
    tables = ["patients", "doctors", "appointments", "treatments", "invoices"]
    print("\n--- DATABASE SUMMARY ---")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Total {table.capitalize()}: {count}")
    print("------------------------\n")

if __name__ == "__main__":
    print("Starting database setup...")
    conn = create_database()
    insert_dummy_data(conn)
    print_summary(conn)
    conn.close()
    print("Database setup complete. SQLite DB 'clinic.db' generated successfully.")
