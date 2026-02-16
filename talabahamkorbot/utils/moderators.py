# Moderator Logins
# Bu foydalanuvchilar "Choyxona" (Community) qismida:
# 1. Barcha universitetlar
# 2. Barcha fakultetlar
# 3. Barcha yo'nalishlar
# postlarini ko'rish imkoniyatiga ega (Global View).

MODERATOR_LOGINS = [
    '395251101412',
    '395251101397'
]

def is_global_moderator(hemis_login: str) -> bool:
    """
    Berilgan login egasi global moderator ekanligini tekshiradi.
    """
    if not hemis_login:
        return False
    return str(hemis_login).strip() in MODERATOR_LOGINS
