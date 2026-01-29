import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
import csv
import os
import zipfile
from io import StringIO

# Define template structures
TEMPLATES = {
    "faculties.csv": [
        ["faculty_code", "faculty_name"],
        ["F01", "Axborot Texnologiyalari"],
        ["F02", "Iqtisodiyot"],
    ],
    "staff.csv": [
        ["faculty_code", "full_name", "role", "jshshir", "phone", "position", "tutor_groups"],
        ["F01", "Admin Adminov", "rahbariyat", "12345678901234", "+998901234567", "Yoshlar ishlari bo'yicha prorektor", ""],
        ["F01", "Dean Deanov", "dekanat", "12345678901235", "+998901234568", "Fakultet dekani", ""],
        ["F01", "Tutor Tutorov", "tyutor", "12345678901236", "+998901234569", "Guruh tyutori", "210-21; 211-21"],
    ],
    "students.csv": [
        ["faculty_code", "full_name", "hemis_login", "group_number", "phone"],
        ["F01", "Aliyev Vali", "392211100001", "210-21", "+998911234567"],
        ["F01", "Valiyev Ali", "392211100002", "210-21", "+998911234568"],
    ]
}

UPLOAD_DIR = "/var/www/talabahamkorbot/uploads"
ZIP_PATH = os.path.join(UPLOAD_DIR, "templates.zip")

def create_csv_string(data):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(data)
    return output.getvalue()

def main():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    with zipfile.ZipFile(ZIP_PATH, 'w') as zipf:
        for filename, data in TEMPLATES.items():
            content = create_csv_string(data)
            zipf.writestr(filename, content)
            print(f"Added {filename} to {ZIP_PATH}")

    print(f"Successfully created {ZIP_PATH}")

if __name__ == "__main__":
    main()
