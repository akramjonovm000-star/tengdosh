import re

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Add get_student_or_staff to imports from api.dependencies
    content = re.sub(r'(from api\.dependencies import .*?get_current_student.*?)\n', r'\1, get_student_or_staff\n', content)
    
    # Replace Depends(get_current_student) with Depends(get_student_or_staff)
    content = content.replace("Depends(get_current_student)", "Depends(get_student_or_staff)")

    with open(filepath, 'w') as f:
        f.write(content)

for filepath in ["api/student.py", "api/chat.py", "api/notifications.py", "api/academic.py"]:
    try:
        fix_file(filepath)
        print(f"Fixed {filepath}")
    except Exception as e:
        print(f"Failed {filepath}: {e}")
