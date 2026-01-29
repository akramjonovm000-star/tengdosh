ROLE_MAPPING = {
    "api": "API User",
    "tech": "ATM",
    "auditor": "Auditor",
    "accounting": "Buxgalteriya",
    "dean": "Dekan",
    "diploma_department": "Diplom bo'limi",
    "doctorate": "Doktorantura bo'limi",
    "user": "Talaba",
    "student": "Talaba", # Explicit student code
    "science": "Ilmiy bo'lim",
    "inspector": "Inspeksiya",
    "staff": "Kadrlar bo'limi",
    "department": "Kafedra mudiri",
    "minadmin": "Kichik Admin",
    "librarian": "Kutubxona",
    "marketing": "Marketing",
    "finance_control": "Moliya-nazorat",
    "teacher": "O'qituvchi",
    "academic_board": "O'quv bo'limi",
    "academic_vice_rector": "O'quv i.b. prorektor",
    "direction": "Rahbariyat",
    "registrator_office": "Registrator ofisi",
    "super_admin": "Super Admin",
    "tutor": "Tyutor",
    "dormitory": "Yotoqxona",
    "lawyer": "Yurist"
}

def get_role_label(code: str) -> str:
    """Returns the display name for a given role code."""
    if not code: return "Talaba"
    return ROLE_MAPPING.get(code.lower(), code.capitalize())
