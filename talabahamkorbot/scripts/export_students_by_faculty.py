import os
import sys
import csv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import datetime

# Adjust path to find config and models when run from talabahamkorbot directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from database.models import Student, Faculty, University
    from config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
except ImportError:
    # Fallback for different execution contexts
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from talabahamkorbot.database.models import Student, Faculty, University
    from talabahamkorbot.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

# Synchronous Database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def export_students():
    engine = create_engine(DATABASE_URL)
    
    with Session(engine) as session:
        stmt = (
            select(
                Student.full_name,
                Student.hemis_login,
                Faculty.name.label("faculty_name"),
                University.name.label("university_name"),
                Student.created_at
            )
            .join(Faculty, Student.faculty_id == Faculty.id)
            .join(University, Faculty.university_id == University.id)
            .order_by(University.name, Faculty.name, Student.full_name)
        )
        
        results = session.execute(stmt).all()
        
        if not results:
            print("Talabalar topilmadi.")
            return

        filename = f"students_by_faculty_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        # Save to a reachable location
        filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'exports', filename))
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['F.I.SH', 'HEMIS Login', 'Fakultet', 'Universitet', 'Ro\'yxatdan o\'tgan vaqti'])
            for row in results:
                writer.writerow([
                    row.full_name,
                    row.hemis_login,
                    row.faculty_name,
                    row.university_name,
                    row.created_at.strftime('%Y-%m-%d %H:%M:%S') if row.created_at else ''
                ])
        
        print(f"Hisobot yaratildi: {filepath}")
        print(f"Jami talabalar soni: {len(results)}")

if __name__ == "__main__":
    export_students()
