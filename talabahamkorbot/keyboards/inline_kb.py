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
            # [
            #     InlineKeyboardButton(
            #         text="🌐 HEMIS orqali kirish (Tavsiya etiladi)",
            #         url=oauth_url
            #     )
            # ],
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
                    text="🏛 OTM",
                    callback_data="owner_universities",
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
                    text="🖼 Bannerlar boshqaruvi",
                    callback_data="owner_banner_menu",
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
                    text="🗳 Saylovlarni boshqarish",
                    callback_data="admin_election_menu:global",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎭 Klublar Boshqaruvi",
                    callback_data="owner_clubs_menu",
                )
            ],
        ]
    )

def get_owner_announcement_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Yangi e'lon yuborish", callback_data="owner_broadcast"),
            ],
            [
                InlineKeyboardButton(text="📋 E'lonlarni boshqarish", callback_data="owner_ann_list"),
            ],
            [
                InlineKeyboardButton(text="🖼 Bannerlar boshqaruvi", callback_data="owner_banner_setup"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_menu"),
            ]
        ]
    )

def get_active_announcements_kb(announcements: list) -> InlineKeyboardMarkup:
    buttons = []
    for ann in announcements:
        # Title limit 30 chars
        title = ann.title[:30] + "..." if len(ann.title) > 30 else ann.title
        buttons.append([
            InlineKeyboardButton(text=f"📝 {title}", callback_data=f"owner_ann_view:{ann.id}")
        ])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_ann_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_announcement_actions_kb(ann_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"owner_ann_del:{ann_id}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_ann_list"),
            ]
        ]
    )

# ============================================================
# BANNERLAR BOSHQARUVI
# ============================================================

def get_owner_banner_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Yangi banner qo'shish", callback_data="owner_banner_add"),
            ],
            [
                InlineKeyboardButton(text="📋 Bannerlar ro'yxati", callback_data="owner_banner_list"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_menu"),
            ]
        ]
    )

def get_banner_list_kb(banners: list) -> InlineKeyboardMarkup:
    buttons = []
    for banner in banners:
        # Status indicator
        status = "✅" if banner.is_active else "❌"
        # ID or short info
        btn_text = f"{status} Banner #{banner.id}"
        if banner.link:
            btn_text += " (🔗)"
            
        buttons.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"owner_banner_view:{banner.id}")
        ])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_banner_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_banner_actions_kb(banner_id: int, is_active: bool) -> InlineKeyboardMarkup:
    rows = []
    
    # Toggle Active button
    if is_active:
        rows.append([InlineKeyboardButton(text="⏹ Nofaol qilish", callback_data=f"owner_banner_toggle:{banner_id}")])
    else:
        rows.append([InlineKeyboardButton(text="▶️ Faollashtirish", callback_data=f"owner_banner_toggle:{banner_id}")])
        
    rows.append([InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"owner_banner_del:{banner_id}")])
    rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_banner_list")])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_numbered_universities_kb(universities: list) -> InlineKeyboardMarkup:
    """
    Creates numeric buttons for a list of universities.
    [1] [2] [3]
    [4] [5] [6]
    """
    buttons = []
    current_row = []
    
    for i, uni in enumerate(universities, 1):
        current_row.append(
            InlineKeyboardButton(
                text=str(i),
                callback_data=f"owner_uni_select:{uni.id}"
            )
        )
        if len(current_row) == 5:
            buttons.append(current_row)
            current_row = []
            
    if current_row:
        buttons.append(current_row)
        
    # Back button
    buttons.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="owner_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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
# UTILS (ORTGA, QAYTA URINISH)
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

def get_back_inline_kb(callback_to: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Ortga", callback_data=callback_to)]
        ]
    )
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
# ELECTION KEYBOARDS
# ============================================================

def get_election_candidates_kb(candidates: list, back_callback: str = "go_home") -> InlineKeyboardMarkup:
    """
    Saylov nomzodlari ro'yxati (Admin ko'rishi uchun ham ishlatilishi mumkin)
    candidates: list of ElectionCandidate objects
    """
    rows = []
    for cand in candidates:
        rows.append([
            InlineKeyboardButton(
                text=f"👤 {cand.student.full_name}",
                callback_data=f"election_cand:{cand.id}"
            )
        ])
    
    rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_candidate_detail_kb(candidate_id: int, can_vote: bool = False, back_callback: str = "election_menu") -> InlineKeyboardMarkup:
    """
    Nomzod sahifasidagi tugmalar.
    """
    rows = []
    if can_vote:
        rows.append([
            InlineKeyboardButton(
                text="🗳 Ovoz berish",
                callback_data=f"election_vote:{candidate_id}"
            )
        ])
    
    rows.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)
