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
    
    # Remove all non-digit characters for safety
    import re
    clean_login = re.sub(r'\D', '', str(hemis_login))
    
    return clean_login in MODERATOR_LOGINS
