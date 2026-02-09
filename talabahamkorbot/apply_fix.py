
target = 'total_count = await HemisService.get_admin_student_count(admin_filters)'
replacement = '''# [NEW] Fetch from Admin API (List + Count)
        admin_items, total_count = await HemisService.get_admin_student_list(
            admin_filters, page=1, limit=500
        )
        
        students = []
        if total_count > 0:
            for item in admin_items:
                s = Student()
                s.id = item.get("id") 
                s.hemis_id = item.get("id")
                s.hemis_login = item.get("login")
                s.full_name = item.get("full_name") or f"{item.get('second_name', '')} {item.get('first_name', '')} {item.get('third_name', '')}".strip()
                s.image_url = item.get("image")
                dept = item.get("department", {})
                s.faculty_name = dept.get("name") if isinstance(dept, dict) else ""
                grp = item.get("group", {})
                s.group_number = grp.get("name") if isinstance(grp, dict) else ""
                lvl = item.get("level", {})
                s.level_name = lvl.get("name") if isinstance(lvl, dict) else ""
                ef = item.get("educationForm", {})
                s.education_form = ef.get("name") if isinstance(ef, dict) else ""
                et = item.get("educationType", {})
                s.education_type = et.get("name") if isinstance(et, dict) else ""
                students.append(s)'''

with open("api/management.py", "r") as f:
    content = f.read()

if target in content:
    new_content = content.replace(target, replacement)
    with open("api/management.py", "w") as f:
        f.write(new_content)
    print("Fix applied successfully.")
else:
    print("Target string not found!")
    # Debug info
    print("Searching for:")
    print(target)
