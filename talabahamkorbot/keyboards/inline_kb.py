from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# ============================================================
# 1) Rol tanlash (Xodim / Talaba)
# ============================================================

from config import DOMAIN

def get_start_role_inline_kb(tg_id: int = None) -> InlineKeyboardMarkup:
    oauth_url = f"https://{DOMAIN}/api/v1/oauth/login?source=bot"
    if tg_id:
        # We can pass tg_id via state but source=bot handles logic. 
        # Actually state should encode tg_id if we want to bind it.
        # But for now 'bot' source just redirects to bot start deep link.
        pass
        
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🌐 HEMIS orqali kirish (Tavsiya etiladi)",
                    url=oauth_url
                )
            ],
            [
                InlineKeyboardButton(
                    text="👤 Login bilan kirish",
                    callback_data="role_student"
                )
            ],
             [
                InlineKeyboardButton(
                    text="👨‍🏫 Xodim sifatida",
                    callback_data="role_staff"
                )
            ]
        ]
    )


def get_subscription_check_kb(channel_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Kanalga a'zo bo'lish", url=channel_url),
            ],
            [
                InlineKeyboardButton(text="✅ A'zo bo'ldim (Tekshirish)", callback_data="check_subscription"),
            ]
        ]
    )


# ============================================================
# 2) OWNER asosiy menyusi
# ============================================================

def get_owner_main_menu_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏫 Universitet qo‘shish",
                    callback_data="owner_add_university"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏛 OTM va fakultetlar",
                    callback_data="owner_universities",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Xodim / talaba importi",
                    callback_data="owner_import",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤖 AI Yordamchi",
                    callback_data="ai_assistant_main",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Umumiy e'lon yuborish",
                    callback_data="owner_broadcast",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👨‍💻 Developerlar boshqaruvi",
                    callback_data="owner_dev",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 Premium",
                    callback_data="owner_gifts_menu",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚙️ Bot sozlamalari",
                    callback_data="owner_settings",
                )
            ],
        ]
    )


# ============================================================
# 3) Xato → Qayta urinish / Bosh menyu
# ============================================================

def get_retry_or_home_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="♻️ Qayta urinish", callback_data="retry"),
                InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="go_home"),
            ]
        ]
    )


# ============================================================
# 4) Universal "Ortga" tugmasi
# ============================================================

def get_back_inline_kb(callback_to: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data=callback_to)]
        ]
    )


# ============================================================
# 5) Universitetni boshqarish menyusi
# ============================================================

def get_university_actions_kb(university_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 Shablon CSV fayllarini yuklab olish",
                    callback_data=f"download_csv_templates:{university_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📤 CSV fayllarni import qilish",
                    callback_data=f"uni_import_start:{university_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📌 Kanal majburiyatini sozlash",
                    callback_data=f"uni_channel_menu:{university_id}",
                )
            ],
            [
                InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_universities")
            ],
            [
                InlineKeyboardButton(text="🏠 Owner menyusi", callback_data="owner_menu")
            ],
        ]
    )


# ============================================================
# 6) 📥 IMPORTNI TASDIQLASH
# (faqat bitta versiya — shu qoladi)
# ============================================================

def get_import_confirm_kb(university_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Importni tasdiqlash",
                    callback_data=f"uni_import_confirm:{university_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Qayta yuklash",
                    callback_data=f"uni_import_start:{university_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Ortga",
                    callback_data="owner_universities"
                )
            ]
        ]
    )


# ============================================================
# 7) Import xatosi → qayta urinish
# ============================================================

def get_import_retry_kb(university_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="♻️ Qayta import boshlash",
                    callback_data=f"uni_import_start:{university_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📥 Shablonlarni qayta yuklab olish",
                    callback_data=f"uni_tpl:{university_id}",
                )
            ],
            [
                InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_universities")
            ],
        ]
    )


# ============================================================
# 8) Import tugagach → kanal majburiyatini qo‘shish savoli
# ============================================================

def get_channel_requirement_decision_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Kanal majburiyatini qo‘shish",
                    callback_data="channel_req_yes",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Keyinroq",
                    callback_data="channel_req_no",
                )
            ],
        ]
    )


def get_channel_add_confirm_kb() -> InlineKeyboardMarkup:
    return get_channel_requirement_decision_kb()


# ============================================================
# 9) Kanalni saqlashni tasdiqlash
# ============================================================

def get_channel_save_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlayman", callback_data="channel_save_yes"
                ),
                InlineKeyboardButton(
                    text="❌ Bekor qilish", callback_data="channel_save_no"
                ),
            ]
        ]
    )


# ============================================================
# 10) Kanalni o‘chirishni tasdiqlash
# ============================================================

def get_channel_remove_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Ha, o‘chirish", callback_data="channel_remove_yes"
                ),
                InlineKeyboardButton(
                    text="❌ Yo‘q, qoldirish", callback_data="channel_remove_no"
                ),
            ]
        ]
    )


# ============================================================
# 11) Kanal majburiyati menyusi
# ============================================================

def get_channel_menu_kb(university_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Kanal majburiyatini qo‘shish / yangilash",
                    callback_data=f"channel_menu_add:{university_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="➖ Kanal majburiyatini o‘chirish",
                    callback_data=f"channel_menu_del:{university_id}",
                )
            ],
            [
                InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_universities")
            ],
        ]
    )


# ============================================================
# 12) Forward xatosida → qayta urinish
# ============================================================

def get_retry_channel_forward_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="♻️ Qayta urinaman", callback_data="retry_forward"
                )
            ]
        ]
    )


# ============================================================
# TALABA ASOSIY MENYUSI
# ============================================================

def get_student_main_menu_kb(led_clubs: list = None) -> InlineKeyboardMarkup:
    # led_clubs: list of Club objects led by this student
    
    rows = [
        [
            InlineKeyboardButton(text="👤 Profilim", callback_data="student_profile"),
        ],
        [InlineKeyboardButton(text="🏛 Akademik bo'lim", callback_data="student_academic_menu")],
        [
            InlineKeyboardButton(text="🤖 AI Yordamchi", callback_data="ai_assistant_main"),
        ],
        [
            InlineKeyboardButton(text="📊 Faolliklarim", callback_data="student_activities"),
            InlineKeyboardButton(text="📄 Hujjatlar", callback_data="student_documents"),
        ],
        [
            InlineKeyboardButton(text="🎓 Sertifikatlar", callback_data="student_certificates"),
            InlineKeyboardButton(text="🎭 Klublar", callback_data="student_clubs_market"),
        ],
        [
            # InlineKeyboardButton(text="💎 Premium Obuna", callback_data="student_premium_menu"), # Disabled by request
            InlineKeyboardButton(text="📨 Murojaatlar", callback_data="student_feedback_menu")
        ],
    ]
    
    # If Student leads any clubs, add manage buttons at bottom
    if led_clubs:
        for c in led_clubs:
            rows.append([InlineKeyboardButton(text=f"📢 {c.name} (Boshqarish)", callback_data=f"leader_manage:{c.id}")])
            
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_student_profile_menu_kb(led_clubs: list = None) -> InlineKeyboardMarkup:
    """
    Profilim menusi (xuddi asosiy menyu kabi, lekin callbacklar :from_profile bilan tugaydi)
    """
    rows = [
        # Profilim o'zi bu yerda kerak emas, chunki biz zatan profildamiz.
        # Lekin UI bir xil turishi uchun "Profilim" o'rniga "Bosh menyu" ga qaytish tugmasi bo'lishi mumkin.
        # Yoki shunchaki Profilim buttoni olib tashlanadi.
        # User so'rovi: Profilim -> Hujjatlar -> Ortga -> Profilim
        # Demak bu yerdagi Hujjatlar tugmasi documents:profile ga o'tishi kerak.
        
        [InlineKeyboardButton(text="🏛 Akademik bo'lim", callback_data="student_academic_menu:profile")],
        [
            InlineKeyboardButton(text="📊 Faolliklarim", callback_data="student_activities:profile"),
            InlineKeyboardButton(text="📄 Hujjatlar", callback_data="student_documents:profile"),
        ],
        [
            InlineKeyboardButton(text="🎓 Sertifikatlar", callback_data="student_certificates:profile"),
            InlineKeyboardButton(text="🎭 Klublar", callback_data="student_clubs_market:profile"),
        ],
        [InlineKeyboardButton(text="📨 Murojaatlar", callback_data="student_feedback_menu:profile")],
        
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="go_student_home")]
    ]
    
    if led_clubs:
        for c in led_clubs:
            rows.append([InlineKeyboardButton(text=f"📢 {c.name} (Boshqarish)", callback_data=f"leader_manage:{c.id}")])
            
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_student_academic_kb(back_callback: str = "go_student_home") -> InlineKeyboardMarkup:
    """
    Talaba uchun akademik ma'lumotlar menyusi (xuddi ilovadagidek)
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Reyting (GPA)", callback_data="student_gpa"),
                InlineKeyboardButton(text="📈 O'zlashtirish", callback_data="student_grades"),
            ],
            [
                InlineKeyboardButton(text="⏱ Davomat", callback_data="student_attendance"),
                InlineKeyboardButton(text="📚 Fanlar", callback_data="student_subjects"),
            ],
            [
                InlineKeyboardButton(text="📅 Dars jadvali", callback_data="student_schedule"),
                InlineKeyboardButton(text="📝 Fanlardan vazifalar", callback_data="student_tasks"),
            ],

            [InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback)],
        ]
    )




# ============================================================
# TALABA FAOLLIKLARI MENYUSI (ASOSIY)
# ============================================================

def get_student_activities_kb(back_callback: str = "go_student_home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Batafsil", callback_data="student_activities_detail"),
                InlineKeyboardButton(text="📚 Kitobxonlik", callback_data="student_kitobxonlik_menu"),
            ],
            [InlineKeyboardButton(text="➕ Faollik qo‘shish", callback_data="student_activity_add")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback)],
        ]
    )


# ============================================================
# 📚 KITOBXONLIK MENYUSI
# ============================================================

def get_student_kitobxonlik_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Testni ishlash", callback_data="student_kitobxonlik_test")],
            [InlineKeyboardButton(text="📚 Kitoblar ro'yixati", callback_data="student_kitobxonlik_books")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_activities")],
        ]
    )


# ============================================================
# 🔍 FAOLLIKLAR → BATAFSIL MENYUSI
# ============================================================

def get_student_activities_detail_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🖼 Rasmlarni ko‘rish", callback_data="student_activities_images")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_activities")],
        ]
    )


# ============================================================
# FAOLLIK QO‘SHISH MENYUSI
# ============================================================

def get_activity_add_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="To‘garak", callback_data="act_add_togarak"),
                InlineKeyboardButton(text="Yutuqlar", callback_data="act_add_yutuq")
            ],
            [
                InlineKeyboardButton(text="Ma’rifat darslari", callback_data="act_add_marifat"),
                InlineKeyboardButton(text="Volontyorlik", callback_data="act_add_vol")
            ],
            [
                InlineKeyboardButton(text="Madaniy tashriflar", callback_data="act_add_madaniy"),
                InlineKeyboardButton(text="Sport", callback_data="act_add_sport")
            ],
            [InlineKeyboardButton(text="Boshqa", callback_data="act_add_boshqa")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_activities")],
        ]
    )


# ============================================================
# ⭐ HUJJATLAR MENYUSI
# ============================================================

def get_student_documents_kb(back_callback: str = "go_student_home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📂 Mening hujjatlarim", callback_data="student_my_documents")],
            [InlineKeyboardButton(text="➕ Hujjat qo‘shish", callback_data="student_document_add")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback)],
        ]
    )


def get_date_select_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Bugun", callback_data="date_today")]
        ]
    )


def get_student_documents_simple_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Hujjat qo‘shish", callback_data="student_document_add")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_documents")],
        ]
    )


def get_document_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Passport", callback_data="doc_type_passport")],
            [InlineKeyboardButton(text="Rezyume", callback_data="doc_type_rezyume")],
            [InlineKeyboardButton(text="Obyektivka", callback_data="doc_type_obyektivka")],
            [InlineKeyboardButton(text="Sertifikat", callback_data="doc_type_sertifikat")],
            [InlineKeyboardButton(text="Boshqa hujjat", callback_data="doc_type_boshqa")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_documents")],
        ]
    )


# ============================================================
# SERTIFIKATLAR MENYUSI
# ============================================================

def get_student_certificates_kb(back_callback: str = "go_student_home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📁 Sertifikatlarim", callback_data="student_cert_list")],
            [InlineKeyboardButton(text="➕ Sertifikat qo‘shish", callback_data="student_cert_add")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback)],
        ]
    )


def get_student_certificates_simple_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Sertifikat qo‘shish", callback_data="student_cert_add")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_certificates")],
        ]
    )


def get_certificate_actions_kb(cert_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 Yuklab olish",
                    callback_data=f"certificate_download:{cert_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ O‘chirish",
                    callback_data=f"certificate_delete:{cert_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Ortga",
                    callback_data="student_back"
                )
            ],
        ]
    )


# ============================================================
# XODIM ROLINI TANLASH TUGMASI (agar kerak bo‘lsa)
# ============================================================

def get_staff_role_select_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
        [InlineKeyboardButton(text="🏛 Rahbariyat", callback_data="staff_role_rahbariyat")],
            [InlineKeyboardButton(text="🏫 Dekanat", callback_data="staff_role_dekanat")],
            [InlineKeyboardButton(text="👨‍🏫 Tyutor", callback_data="staff_role_tyutor")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="go_home")],
        ]
    )


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ============================================================
# RAHBARIYAT ASOSIY MENYUSI
# ============================================================

def get_rahbariyat_main_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📣 Universitet bo‘yicha e’lon yuborish",
                callback_data="rahb_broadcast"
            )],
            [InlineKeyboardButton(
                text="📲 Mobile Push yuborish (Loyiha)",
                callback_data="rh_mobile_push"
            )],
            [InlineKeyboardButton(
                text="📨 Talaba murojaatlari",
                callback_data="rh_feedback"
            )],
            [InlineKeyboardButton(
                text="🎓 Talaba profili",
                callback_data="rh_student_lookup"
            )],
            [InlineKeyboardButton(
                text="👥 Tyutor Monitoring",
                callback_data="rahb_tyutor_monitoring"
            )],
            [InlineKeyboardButton(
                text="📝 Faolliklarni tasdiqlash",
                callback_data="rahb_activity_approve_menu"
            )],
            [InlineKeyboardButton(
                text="📂 Tyutor Ishlari (6 yo'nalish)",
                callback_data="rahb_tyutor_works"
            )],
            # [InlineKeyboardButton(text="🤖 AI Yordamchi", callback_data="ai_assistant_main")],
            [InlineKeyboardButton(text="📊 Statistika", callback_data="staff_stats")]
        ]
    )

def get_rahb_broadcast_back_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="rahb_menu")]
        ]
    )


def get_rahb_broadcast_confirm_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data="rahb_broadcast_confirm"
                ),
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="rahb_broadcast_cancel"
                )
            ],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="rahb_menu")]
        ]
    )
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_rahb_broadcast_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Ortga",
                    callback_data="rahb_menu"
                )
            ]
        ]
    )


# ============================================================
# RAHBARIYAT FAOLLIK TASDIQLASH MENYUSI
# ============================================================

def get_rahb_activity_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🎯 HEMIS orqali aniq talaba",
                callback_data="rahb_activity_by_hemis"
            )],
            [InlineKeyboardButton(
                text="🎲 Tasodifiy faolliklar",
                callback_data="rahb_activity_random"
            )],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="rahb_menu")]
        ]
    )


# ============================================================
# RAHBARIYAT – Feedback boshqarish tugmalari
# ============================================================

def get_rahb_feedback_control_kb(feedback_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="✍️ Javob berish",
                callback_data=f"staff_fb_reply:{feedback_id}"   # ✔ staff feedback reply format
            )],
            [InlineKeyboardButton(
                text="➡️ Keyingisi",
                callback_data=f"staff_fb_next:{feedback_id}"    # ✔ next format
            )],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="rahb_menu")]
        ]
    )


def get_student_lookup_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="rahb_menu")]
        ]
    )


# ============================================================
# DEKANAT ASOSIY MENYUSI
# ============================================================

def get_dekanat_main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📣 Fakultet bo‘yicha e’lon yuborish",
                callback_data="dek_broadcast"
            )],
            [InlineKeyboardButton(
                text="📲 Mobile Push yuborish (Loyiha)",
                callback_data="dk_mobile_push"
            )],
            [InlineKeyboardButton(
                text="📨 Talaba murojaatlari",
                callback_data="dk_feedback"   # ✔ standardized name
            )],
            [InlineKeyboardButton(
                text="🎓 Talaba profili",
                callback_data="dk_student_lookup"
            )],
            [InlineKeyboardButton(
                text="👥 Tyutor Monitoring",
                callback_data="dek_tyutor_monitoring"
            )],
            [InlineKeyboardButton(
                text="📝 Faolliklarni tasdiqlash",
                callback_data="dek_activity_approve_menu"
            )],
            [InlineKeyboardButton(
                text="📂 Tyutor Ishlari (6 yo'nalish)",
                callback_data="dek_tyutor_works"
            )],
            # [InlineKeyboardButton(text="🤖 AI Yordamchi", callback_data="ai_assistant_main")],
            [InlineKeyboardButton(text="📊 Statistika", callback_data="staff_stats")],

        ]
    )


def get_dek_activity_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🎯 HEMIS orqali aniq talaba",
                callback_data="dek_activity_by_hemis"
            )],
            [InlineKeyboardButton(
                text="🎲 Tasodifiy faolliklar",
                callback_data="dek_activity_random"
            )],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="dek_menu")]
        ]
    )


def get_dek_student_lookup_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="dek_menu")]
        ]
    )


# ============================================================
# TYUTOR ASOSIY MENYUSI
# ============================================================

# ============================================================
# TYUTOR ASOSIY MENYUSI
# ============================================================

def get_tutor_main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Tyutor Dashboard", callback_data="tyutor_dashboard"),
            ],
            [
                InlineKeyboardButton(text="📋 Murojaatlar", callback_data="tt_feedback"),
                InlineKeyboardButton(text="📂 Faolliklar", callback_data="tutor_activity_approve_menu"),
            ],
            [
                InlineKeyboardButton(text="🔎 Talaba qidirish (ID)", callback_data="tt_student_lookup"),
            ],
            [
                InlineKeyboardButton(text="✅ 6 yo'nalish", callback_data="tyutor_work_directions"),
            ],
            # [
            #     InlineKeyboardButton(text="🤖 AI Yordamchi", callback_data="ai_assistant_main"),
            # ],
            [
                InlineKeyboardButton(text="📢 E'lon yuborish", callback_data="tutor_broadcast"),
            ],
        ]
    )


def get_tutor_activity_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🎯 HEMIS orqali talaba",
                callback_data="tutor_activity_by_hemis"
            )],
            [InlineKeyboardButton(
                text="🎲 Tasodifiy faollik",
                callback_data="tutor_activity_random"
            )],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="tutor_menu")]
        ]
    )


def get_tutor_student_lookup_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="tutor_menu")]
        ]
    )


# ============================================================
# FAOLLIK TASDIQLASH TUGMALARI (barcha staff uchun umumiy)
# ============================================================

def get_activity_approve_kb(activity_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"activity_yes:{activity_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"activity_no:{activity_id}"
                ),
            ],
            [InlineKeyboardButton(text="➡️ Keyingisi", callback_data="activity_next")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="activity_back")]
        ]
    )


def get_activity_post_action_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Keyingisi", callback_data="activity_next")],
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="activity_back")]
        ]
    )


# ============================================================
# Xodim murojaatlari uchun tugmalar (Appeals)
# ============================================================

def get_staff_appeal_actions_kb(appeal_id: int, role: str = None, student_id: int = None) -> InlineKeyboardMarkup:
    # Common Buttons
    keyboard = [
        [
            InlineKeyboardButton(
                text="✍️ Javob berish",
                callback_data=f"appeal_reply:{appeal_id}"
            )
        ]
    ]

    # Role specific buttons
    if role == "rahbariyat":
        keyboard.append([
            InlineKeyboardButton(
                text="📤 Biriktirish",
                callback_data=f"rahb_assign:{appeal_id}"
            )
        ])

    # Navigation
    keyboard.append([
        InlineKeyboardButton(
            text="➡️ Keyingisi",
            callback_data="appeal_next"
        )
    ])
    
    # Back Button Logic
    if student_id:
        back_callback = f"staff_back_to_profile:{student_id}"
        back_text = "⬅️ Profilga qaytish"
    else:
        back_callback = "staff_menu"
        back_text = "⬅️ Bosh menyu"

    keyboard.append([
        InlineKeyboardButton(
            text=back_text,
            callback_data=back_callback
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)



# ============================================================
# 📊 IMPORT STATUS PANEli (matn helper)
# ============================================================

def get_import_status_text(data: dict) -> str:
    fac = "📘 Fakultetlar: " + ("✅ Yuklandi" if data.get("import_faculties") else "⏳ Kutilmoqda")
    staff = "🧑‍🏫 Xodimlar: " + ("✅ Yuklandi" if data.get("import_staff") else "⏳ Kutilmoqda")
    students = "🎓 Talabalar: " + ("✅ Yuklandi" if data.get("import_students") else "⏳ Kutilmoqda")

    return f"{fac}\n{staff}\n{students}"


# ============================================================
# TALABA AUTENTIFIKATSIYASI → MA’LUMOT TASDIQLASH
# ============================================================

def get_data_confirmation_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Ha, to‘g‘ri", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ Yo‘q, qayta kiritaman", callback_data="confirm_no"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_feedback_recipient_kb():
    """Murojaat kimga yuborilishini tanlash uchun klaviatura (Asosiy)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏛 Rahbariyat", callback_data="fb_menu:rahbariyat")],
            [InlineKeyboardButton(text="🏫 Dekanat", callback_data="fb_menu:dekanat")],
            [InlineKeyboardButton(text="📚 Kutubxona", callback_data="fb_recipient:kutubxona")],
            [InlineKeyboardButton(text="🔍 Inspektor", callback_data="fb_recipient:inspektor")],
            [InlineKeyboardButton(text="🧠 Psixolog", callback_data="fb_recipient:psixolog")],
            [InlineKeyboardButton(text="🧑‍🏫 Tyutor", callback_data="fb_recipient:tyutor")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_feedback_new")]
        ]
    )


def get_feedback_rahbariyat_menu_kb():
    """Rahbariyat tarkibi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎓 Rektor", callback_data="fb_recipient:rektor")],
            [InlineKeyboardButton(text="👔 O'quv ishlari prorektori", callback_data="fb_recipient:prorektor")],
            [InlineKeyboardButton(text="👔 Yoshlar ishlari prorektori", callback_data="fb_recipient:yoshlar_prorektor")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_feedback_recipient")] 
        ]
    )


def get_feedback_dekanat_menu_kb():
    """Dekanat tarkibi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Dekan", callback_data="fb_recipient:dekan")],
            [InlineKeyboardButton(text="👤 Dekan o'rinbosari", callback_data="fb_recipient:dekan_orinbosari")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_feedback_recipient")]
        ]
    )


def get_feedback_confirm_kb() -> InlineKeyboardMarkup:
    """Murojaatni tasdiqlash uchun"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Yuborish", callback_data="feedback_send_confirm")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="student_feedback_menu")]
        ]
    )


def get_feedback_cancel_kb() -> InlineKeyboardMarkup:
    """Murojaat yozishni bekor qilish"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="student_feedback_menu")]
        ]
    )

    # This part was a redundant return statement in the original code.
    # It is being replaced by the new functions as per the instruction.
    # return InlineKeyboardMarkup(
    #     inline_keyboard=[
    #         [InlineKeyboardButton(text="✅ Yuborish", callback_data="feedback_send")],
    #         [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="feedback_cancel")],
    #     ]
    # )

def get_rahb_broadcast_confirm_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash va yuborish", callback_data="rahb_broadcast_confirm")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="rahb_broadcast_cancel")]
        ]
    )


# Dekanat Broadcast Keyboards
def get_dek_broadcast_back_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="dek_menu")]
        ]
    )

def get_dek_broadcast_confirm_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash va yuborish", callback_data="dek_broadcast_confirm")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="dek_broadcast_cancel")]
        ]
    )


# Tutor Broadcast Keyboards
def get_tutor_broadcast_back_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="tutor_menu")]
        ]
    )

def get_tutor_broadcast_confirm_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash va yuborish", callback_data="tutor_broadcast_confirm")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="tutor_broadcast_cancel")]
        ]
    )

def get_feedback_anonymity_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 Shaxsiy (Ochiq)", callback_data="feedback_mode_public"),
                InlineKeyboardButton(text="🕵️‍♂️ Anonim (Yashirin)", callback_data="feedback_mode_anon"),
            ],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_feedback_menu")],
        ]
    )



from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_staff_feedback_kb(feedback_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Javob berish",
                    callback_data=f"staff_fb_reply:{feedback_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➡️ Keyingisi",
                    callback_data=f"staff_fb_next:{feedback_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Ortga",
                    callback_data="staff_fb_back"
                )
            ]
        ]
    )

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_rh_feedback_kb(appeal_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏫 Dekanatga yuborish",
                    callback_data=f"rahb_assign_dekanat:{appeal_id}"
                ),
                InlineKeyboardButton(
                    text="👨‍🏫 Tyutorga yuborish",
                    callback_data=f"rahb_assign_tutor:{appeal_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➡️ Keyingisi",
                    callback_data="rahb_appeal_next"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Rahbariyat menyusi",
                    callback_data="rahb_menu"
                )
            ]
        ]
    )

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



def get_rahb_assign_choice_kb(appeal_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏫 Dekanatga biriktirish",
                    callback_data=f"rahb_assign_dekanat:{appeal_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👨‍🏫 Tyutorga biriktirish",
                    callback_data=f"rahb_assign_tyutor:{appeal_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Ortga",
                    callback_data="rh_feedback"
                )
            ]
        ]
    )


def get_rahb_appeal_actions_kb(appeal_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Javob berish",
                    callback_data=f"rahb_reply:{appeal_id}"
                ),
                InlineKeyboardButton(
                    text="🤖 AI Javob",
                    callback_data=f"staff_ai_reply:{appeal_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📤 Biriktirish",
                    callback_data=f"rahb_assign:{appeal_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➡️ Keyingisi",
                    callback_data=f"rahb_appeal_next:{appeal_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Bosh menyu",
                    callback_data="rahb_menu"
                )
            ]
        ]
    )

def get_rahb_post_reply_kb(appeal_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➡️ Keyingisi",
                    callback_data=f"rahb_appeal_next:{appeal_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Bosh menyu",
                    callback_data="rahb_menu"
                )
            ]
        ]
    )

def get_student_feedback_reply_kb(feedback_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="✅ Murojaat yopildi",
                    callback_data=f"feedback_close:{feedback_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Qayta murojaat",
                    callback_data=f"feedback_reappeal:{feedback_id}"
                )
            ]
        ]
    )


def get_dekanat_appeal_actions_kb(appeal_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Javob berish",
                    callback_data=f"dekan_reply:{appeal_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➡️ Keyingisi",
                    callback_data="dekan_next"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Yopish",
                    callback_data=f"dekan_close:{appeal_id}"
                )
            ]
        ]
    )


# ============================================================
# TALABA MUROJAATLARI MENYUSI (Yangi)
# ============================================================

def get_student_feedback_menu_kb(back_callback: str = "go_student_home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📨 Yuborilgan murojaatlar", callback_data="student_feedback_list")],
            [InlineKeyboardButton(text="✍️ Murojaat yuborish", callback_data="student_feedback_new")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback)],
        ]
    )

def get_student_feedback_list_kb(feedbacks: list) -> InlineKeyboardMarkup:
    """
    Talabaning murojaatlari ro'yxati.
    feedbacks: List[StudentFeedback] objects
    """
    rows = []
    
    status_emoji = {
        "pending": "⏳",
        "answered": "✅",
        "closed": "🔒",
        "dekanat": "🏫",
        "tyutor": "👨‍🏫",
        "dekan": "👤",
        "dekan_orinbosari": "👤",
        "kafedra_mudiri": "🏫",
        "kafedra": "🏫",
        "teacher": "👨‍🏫",
        "inspektor": "🔍",
        "buxgalter": "💰",
        "psixolog": "🧠",
        "rahbariyat": "🏢",
        "reappeal": "🔄"
    }

    for fb in feedbacks:
        # Statusga qarab emoji
        if fb.status == "answered":
            emoji = "✅"
        elif fb.status == "closed":
            emoji = "🔒"
        elif fb.status == "rejected":
            emoji = "❌"
        else:
            # pending, assigned_*, etc. -> Kutilmoqda
            emoji = "⏳"

        # Recipient Role Mapping
        role_map = {
            "dekanat": "Dekanat",
            "tyutor": "Tyutor",
            "buxgalter": "Buxgalteriya",
            "psixolog": "Psixolog",
            "rahbariyat": "Rahbariyat",
            "rector": "Rektor",
            "prorector": "Prorektor",
            "teacher": "O'qituvchi",
            "inspektor": "Inspektor",
            "kafedra": "Kafedra",
            "kafedra_mudiri": "Kafedra mudiri",
            "dekan": "Dekan",
            "dekan_orinbosari": "Dekan o'rinbosari"
        }
        
        # Get readable role or capitalize fallback
        role_key = fb.assigned_role or "unknown"
        role_name = role_map.get(role_key, role_key.capitalize())
        
        # Qisqartirish (agar ro'l nomi juda uzun bo'lsa)
        if len(role_name) > 12:
            role_name = role_name[:10] + "."

        date_str = fb.created_at.strftime("%d.%m")
        # Textdan qisqacha fragment (15 ta belgi)
        short_text = (fb.text[:15] + "...") if fb.text else "[Media]"
        
        btn_text = f"{emoji} {date_str} | {role_name} | {short_text}"
        
        rows.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=f"student_feedback_view:{fb.id}"
            )
        ])
        
    # Footer
    rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_feedback_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_student_feedback_detail_kb(feedback_id: int, is_closed: bool = False) -> InlineKeyboardMarkup:
    rows = []
    
    if not is_closed:
        rows.append([
            InlineKeyboardButton(
                text="🔄 Qayta murojaat yozish", 
                callback_data=f"feedback_reappeal:{feedback_id}"
            )
        ])
        rows.append([
            InlineKeyboardButton(
                text="✅ Murojaatni yopish", 
                callback_data=f"feedback_close:{feedback_id}"
            )
        ])
        
    rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="student_feedback_list")])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ============================================================
# 10) Dashboard Statistika Navigatsiyasi (Drill-down)
# ============================================================

def get_rahb_stat_menu_kb() -> InlineKeyboardMarkup:
    """Universitet darajasidagi statistika menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏢 Fakultetlar kesimida", callback_data="stat_faculty_list")],
            [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="rahb_menu")]
        ]
    )

def get_faculties_stat_list_kb(faculties: list) -> InlineKeyboardMarkup:
    """Fakultetlar ro'yxati (statistika uchun)"""
    rows = []
    for fac in faculties:
        rows.append([
            InlineKeyboardButton(
                text=f"{fac.name} ({fac.faculty_code})",
                callback_data=f"stat_faculty:{fac.id}"
            )
        ])
    rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="staff_stats")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_faculty_stat_menu_kb(faculty_id: int) -> InlineKeyboardMarkup:
    """Fakultet statistikasi menyusi (Guruhlarga o'tish)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Guruhlar kesimida", callback_data=f"stat_group_list:{faculty_id}")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="stat_faculty_list")]
        ]
    )

def get_dek_stat_menu_kb(faculty_id: int) -> InlineKeyboardMarkup:
    """Dekanat statistikasi menyusi (Guruhlarga o'tish)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Guruhlar kesimida", callback_data=f"stat_group_list:{faculty_id}")],
            [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="dek_menu")]
        ]
    )

def get_groups_stat_list_kb(groups: list, faculty_id: int) -> InlineKeyboardMarkup:
    """Guruhlar ro'yxati (statistika uchun)"""
    rows = []
    # 2 qatorli grid qilish mumkin, lekin hozircha oddiy list
    for gr in groups:
        rows.append([
            InlineKeyboardButton(
                text=str(gr.group_number),
                callback_data=f"stat_group:{gr.id}" # Bu yerda ID yo'q bo'lsa group_number ishlatiladi
            )
        ])
    
    rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"stat_faculty:{faculty_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_group_stat_menu_kb(faculty_id: int) -> InlineKeyboardMarkup:
    """Guruh statistikasidan qaytish"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"stat_group_list:{faculty_id}")]
        ]
    )

def get_student_profile_actions_kb(student_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📂 Faolliklari", callback_data=f"staff_review_activities:{student_id}"),
                InlineKeyboardButton(text="📨 Murojaatlari", callback_data=f"staff_view_appeals:{student_id}")
            ],
            [
                InlineKeyboardButton(text="✉️ Xabar yuborish", callback_data=f"staff_send_msg:{student_id}")
            ],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="staff_profile_back")]
        ]
    )

def get_staff_student_lookup_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data="go_home")]
        ]
    )


def get_staff_activity_history_kb(student_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🖼 Rasmlarni ko'rish", callback_data=f"staff_activity_images:{student_id}")],
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"staff_review_activities:{student_id}")]
        ]
    )

def get_staff_activity_images_back_kb(student_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data=f"staff_activity_history:{student_id}")]
        ]
    )

def get_yetakchi_main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏛 Klublar Boshqaruvi", callback_data="admin_clubs_menu")],
            # [InlineKeyboardButton(text="🤖 AI Yordamchi", callback_data="ai_assistant_main")],
            [InlineKeyboardButton(text="📢 E'lon yuborish", callback_data="yetakchi_broadcast_menu")],
        ]
    )
