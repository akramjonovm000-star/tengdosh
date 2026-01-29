from keyboards.inline_kb import get_import_status_text, get_import_confirm_kb
# handlers/owner_import.py  (yoki sizda import kodlari qayerda bo‘lsa o‘sha fayl)
import logging
from pathlib import Path
import csv
from io import StringIO

logger = logging.getLogger(__name__)

# === 🆕 SHU YERGA QO‘YILADI ===================================
def make_progress_bar(loaded_count: int, total: int = 3) -> str:
    filled = "■" * loaded_count
    empty = "□" * (total - loaded_count)
    percent = int((loaded_count / total) * 100)
    return f"[{filled}{empty}] {percent}%"


def make_import_status_text(data: dict) -> tuple[str, int]:
    fac = bool(data.get("import_faculties"))
    staff = bool(data.get("import_staff"))
    students = bool(data.get("import_students"))

    loaded = sum([fac, staff, students])

    text = (
        f"📘 Fakultetlar: {'✔️' if fac else '⏳'}\n"
        f"🧑‍🏫 Xodimlar: {'✔️' if staff else '⏳'}\n"
        f"🎓 Talabalar: {'✔️' if students else '⏳'}"
    )

    return text, loaded
# ===============================================================
