import glob
import os

files_to_fix = [
    "api/student.py",
    "api/chat.py",
    "api/notifications.py",
    "api/academic.py"
]

for f in files_to_fix:
    if os.path.exists(f):
        with open(f, "r") as file:
            content = file.read()
        
        # Replace the dependency
        content = content.replace("Depends(get_current_student)", "Depends(get_student_or_staff)")
        
        # Add get_student_or_staff to imports if not there
        if "get_student_or_staff" not in content:
            content = content.replace("get_current_student", "get_current_student, get_student_or_staff")

        with open(f, "w") as file:
            file.write(content)
        print(f"Updated {f}")
