import asyncio
from vanna_setup import get_vanna_components
from vanna.core.tool import ToolContext
from vanna.core.user.models import User

async def seed_training_data():
    """
    Adds schema documentation and high-quality Question-SQL pairs to the Agent's memory.
    This enhances the Agent's ability to generate accurate SQL for the specific dataset.
    """
    agent, memory, runner = get_vanna_components()
    print("--- Seeding Vanna Agent Memory ---")

    # Create dummy user and context for the new API requirement
    dummy_user = User(id="setup_user", email="setup@local")
    context = ToolContext(
        user=dummy_user,
        conversation_id="setup",
        request_id="setup",
        agent_memory=memory
    )

    # 1. Add schema docs/DDL to memory to help the LLM understand relationships
    schema_info = """
    We have an SQLite database for a medical clinic. Database Schema:
    1. patients(id, first_name, last_name, email, phone, date_of_birth, gender, city, registered_date)
    2. doctors(id, name, specialization, department, phone)
    3. appointments(id, patient_id, doctor_id, appointment_date, status, notes)
    4. treatments(id, appointment_id, treatment_name, cost, duration_minutes)
    5. invoices(id, patient_id, invoice_date, total_amount, paid_amount, status)
    
    Notes:
    - appointments.status can be 'Scheduled', 'Completed', 'Cancelled', 'No Show'.
    - invoices.status can be 'Paid', 'Pending', 'Overdue'.
    """
    try:
        await memory.save_text_memory(schema_info, context=context)
        print("- Added Schema documentation.")
    except Exception as e:
        print(f"Error saving text memory: {e}")

    # 2. Add 15 High-Quality Question-SQL Pairs covering schema and business cases
    qa_pairs = [
        # Basic Counts
        ("How many patients are registered in the clinic?", "SELECT count(id) FROM patients;"),
        ("List all doctors in the Cardiology department.", "SELECT name FROM doctors WHERE department = 'Cardiology';"),
        
        # Financials / Revenue
        ("What is the average cost of treatments?", "SELECT avg(cost) FROM treatments;"),
        ("Show me the top 5 most expensive treatments.", "SELECT treatment_name, cost FROM treatments ORDER BY cost DESC LIMIT 5;"),
        ("What was the total revenue generated last month?", "SELECT sum(paid_amount) FROM invoices WHERE strftime('%Y-%m', invoice_date) = strftime('%Y-%m', 'now', '-1 month');"),
        ("List the names of patients who have unpaid invoices.", "SELECT p.first_name, p.last_name FROM patients p JOIN invoices i ON p.id = i.patient_id WHERE i.status != 'Paid';"),
        
        # Scheduling
        ("How many appointments are scheduled for today?", "SELECT count(id) FROM appointments WHERE date(appointment_date) = date('now');"),
        ("Which doctor has the most appointments?", "SELECT d.name, COUNT(a.id) as appt_count FROM doctors d JOIN appointments a ON d.id = a.doctor_id GROUP BY d.id ORDER BY appt_count DESC LIMIT 1;"),
        ("How many appointments were cancelled in the last 30 days?", "SELECT count(id) FROM appointments WHERE status = 'Cancelled' AND date(appointment_date) >= date('now', '-30 days');"),
        ("Show the total duration of treatments for patient ID 1", "SELECT sum(t.duration_minutes) FROM treatments t JOIN appointments a ON t.appointment_id = a.id WHERE a.patient_id = 1;"),
        
        # Demographics
        ("Who is the youngest patient?", "SELECT first_name, last_name, date_of_birth FROM patients ORDER BY date_of_birth DESC LIMIT 1;"),
        ("How many male patients are from New York?", "SELECT count(id) FROM patients WHERE gender = 'Male' AND city = 'New York';"),
        ("List the top 3 cities with the most registered patients.", "SELECT city, count(id) as patient_count FROM patients GROUP BY city ORDER BY patient_count DESC LIMIT 3;"),
        ("What is the average age of patients in years?", "SELECT avg((julianday('now') - julianday(date_of_birth))/365.25) FROM patients;"),
        
        # Other connections
        ("Provide the contact details for the Oncology department doctors.", "SELECT name, phone FROM doctors WHERE department = 'Oncology';")
    ]

    success_count = 0
    for q, s in qa_pairs:
        try:
            # Memory class generally supports adding SQL pairs for few-shot learning
            await memory.save_tool_usage(
                question=q,
                tool_name="run_sql",  # Usually standard in Vanna 2.x
                args={"sql": s},
                context=context
            )
            success_count += 1
        except Exception as e:
            print(f"Error adding memory for question '{q}': {e}")

    print(f"- Successfully seeded {success_count} Question-SQL training pairings!")

if __name__ == "__main__":
    asyncio.run(seed_training_data())
