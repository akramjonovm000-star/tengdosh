class RoleMapper {
  static const Map<String, String> _roles = {
    "api": "API User",
    "tech": "ATM",
    "auditor": "Auditor",
    "accounting": "Buxgalteriya",
    "dean": "Dekan",
    "diploma_department": "Diplom bo'limi",
    "doctorate": "Doktorantura bo'limi",
    "user": "Talaba",
    "student": "Talaba",
    "science": "Ilmiy bo'lim",
    "inspector": "Inspektor",
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
    "super_admin": "Super Administrator",
    "tutor": "Tyutor",
    "dormitory": "Yotoqxona",
    "lawyer": "Yurist",
    "talaba": "Talaba", // Safety fallback
    "rahbariyat": "Rahbariyat",
  };

  static String getLabel(String? code) {
    if (code == null || code.isEmpty) return "Foydalanuvchi";
    return _roles[code.toLowerCase()] ?? "Foydalanuvchi";
  }
}
