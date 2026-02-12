from aiogram.fsm.state import State, StatesGroup

# Predefined simple states
default_state = State()
any_state = State(state="*")


# ============================================================
#                  AUTH STATES (student + staff)
# ============================================================

class AuthStates(StatesGroup):
    choosing_role = State()
    entering_jshshir = State()
    entering_hemis_login = State()
    entering_hemis_password = State() # NEW
    confirm_data = State()
    entering_phone = State()


# ============================================================
#                     OWNER PANEL STATES
# ============================================================

class OwnerStates(StatesGroup):

    # Owner bosh menyu
    main_menu = State()
    owner_universities = State()

    # Universitet qo‘shish jarayoni
    entering_new_uni_code = State()   # YANGI Universitet kodi uchun
    entering_uni_code = State()       # MAVJUD Universitetni qidirish uchun
    entering_uni_name = State()       # owner.py shu nomni ishlatyapti
    entering_short_name = State()     # owner.py shu nomni ishlatyapti

    # Agar bor bo‘lsa: tasdiqlash
    confirming_university = State()   # ixtiyoriy, owner.py bo‘limida bo‘lishi mumkin

    # Universitet tanlangan
    university_selected = State()

    # CSV import
    importing_csv_files = State()
    confirming_import = State()

    # Kanal sozlamalari
    waiting_channel_add_decision = State()
    waiting_channel_forward = State()
    confirming_channel_save = State()
    confirming_channel_save = State()
    confirming_channel_delete = State()

    # Reklama tarqatish
    broadcasting_message = State()

    # Developerlik boshqaruvi
    waiting_dev_tg_id = State()

    # Banner Sozlash
    waiting_banner_image = State()
    waiting_banner_link = State()

class OwnerGifts(StatesGroup):
    waiting_user_id = State()
    selecting_duration = State()
    selecting_duration_all = State()
    waiting_revoke_id = State()
    
    # Balance Top-up
    waiting_topup_hemis_id = State()
    waiting_topup_amount = State()



# ============================================================
#                     STAFF STATES
# ============================================================

class StaffAuthStates(StatesGroup):
    entering_jshshir = State()
    entering_hemis_login = State()      # NEW
    entering_hemis_password = State()   # NEW


class StaffFeedbackStates(StatesGroup):
    reviewing = State()
    replying = State()


class StaffAppealStates(StatesGroup):
    viewing = State()
    reviewing = State()
    replying = State()


class StaffActivityStates(StatesGroup):
    waiting_hemis = State()


# ============================================================
#                     STUDENT STATES
# ============================================================

class ActivityAddStates(StatesGroup):
    CATEGORY = State()
    NAME = State()
    DESCRIPTION = State()
    DATE = State()
    PHOTOS = State()
    CONFIRM = State()


class ActivityEditStates(StatesGroup):
    waiting_name = State()
    waiting_description = State()
    waiting_date = State()


class DocumentAddStates(StatesGroup):
    TITLE = State() # NEW
    CATEGORY = State()
    FILE = State()
    WAIT_FOR_APP_FILE = State() # [NEW] Specifically for App-initiated flow

class CertificateAddStates(StatesGroup):
    TITLE = State()
    FILE = State()
    WAIT_FOR_APP_FILE = State() # [NEW] Specifically for App-initiated flow


class PhoneCollectState(StatesGroup):
    WAITING_PHONE = State()

class RequestSimpleStates(StatesGroup):
    WAITING_MESSAGE = State()

class FeedbackStates(StatesGroup):
    anonymity_choice = State()  # Anonimlik tanlash
    recipient_choice = State()  # Kimga yuborishni tanlash
    select_teacher = State()    # Yangi: O'qituvchini tanlash
    waiting_message = State()
    reappealing = State()
    WAIT_FOR_APP_FILE = State() # [NEW] Specifically for App-initiated flow


class RahbBroadcastStates(StatesGroup):
    WAITING_CONTENT = State()   # 📩 xabar kutish
    CONFIRM = State()           # ✅ tasdiqlash


class DekBroadcastStates(StatesGroup):
    WAITING_CONTENT = State()
    CONFIRM = State()


class TutorBroadcastStates(StatesGroup):
    WAITING_CONTENT = State()
    CONFIRM = State()

class MobilePushStates(StatesGroup):
    waiting_title = State()
    waiting_body = State()
    confirming = State()


class RahbAppealStates(StatesGroup):
    viewing = State()
    replying = State()

class DekanatAppealStates(StatesGroup):
    viewing = State()
    replying = State()


class StaffStudentLookupStates(StatesGroup):
    waiting_input = State()
    viewing_profile = State()
    sending_message = State()

class StaffActivityApproveStates(StatesGroup):
    reviewing = State()


# ============================================================
#                     TYUTOR STATES
# ============================================================

class TyutorWorkStates(StatesGroup):
    entering_title = State() # <--- NEW
    entering_description = State()
    entering_date = State() # <--- NEW
    uploading_photo = State() # <--- NEW

class TyutorMonitoringStates(StatesGroup):
    waiting_search_query = State()

# ============================================================
#                     AI ASSISTANT STATES
# ============================================================
class AIStates(StatesGroup):
    chatting = State()
    waiting_for_konspekt = State()
    viewing_credit_system = State() # NEW: To isolate user in this menu

class ActivityUploadState(StatesGroup):
    waiting_for_photo = State()

class StudentUpdateAuthStates(StatesGroup):
    waiting_for_new_password = State()

class StudentProfileStates(StatesGroup):
    waiting_for_password = State()

class StudentAcademicStates(StatesGroup):
    waiting_for_password = State()

class StudentSurveyStates(StatesGroup):
    taking = State()
