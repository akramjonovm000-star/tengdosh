# ============================================================
#                   BASE STATE SYSTEM (Aiogram 3)
# ============================================================

import inspect
from typing import Any, Optional, Type, no_type_check
from aiogram.types import TelegramObject


class State:
    """Single state object"""

    def __init__(self, state: Optional[str] = None, group_name: Optional[str] = None):
        self._state = state
        self._group_name = group_name
        self._group: Optional[Type["StatesGroup"]] = None

    @property
    def group(self):
        if not self._group:
            raise RuntimeError("State has no group!")
        return self._group

    @property
    def state(self):
        if self._state is None or self._state == "*":
            return self._state

        if self._group_name is None and self._group:
            group = self._group.__full_group_name__
        elif self._group_name:
            group = self._group_name
        else:
            group = "@"

        return f"{group}:{self._state}"

    def set_parent(self, group):
        from models.states import StatesGroup  # circular fix
        if not issubclass(group, StatesGroup):
            raise ValueError("Parent must be StatesGroup child")
        self._group = group

    def __set_name__(self, owner, name):
        if self._state is None:
            self._state = name
        self.set_parent(owner)

    def __call__(self, event: TelegramObject, raw_state: Optional[str] = None):
        if self.state == "*":
            return True
        return raw_state == self.state

    def __eq__(self, other):
        if isinstance(other, State):
            return self.state == other.state
        if isinstance(other, str):
            return self.state == other
        return False

    def __hash__(self):
        return hash(self.state)

    def __str__(self):
        return f"<State '{self.state}'>"

    __repr__ = __str__


class StatesGroupMeta(type):

    @no_type_check
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace)

        states = []
        childs = []

        for key, arg in namespace.items():
            if isinstance(arg, State):
                states.append(arg)
            elif inspect.isclass(arg) and issubclass(arg, StatesGroup):
                childs.append(arg)
                arg.__parent__ = cls

        cls.__parent__ = None
        cls.__childs__ = tuple(childs)
        cls.__states__ = tuple(states)
        cls.__state_names__ = tuple(s.state for s in states)

        return cls

    @property
    def __full_group_name__(cls):
        if cls.__parent__:
            return cls.__parent__.__full_group_name__ + "." + cls.__name__
        return cls.__name__

    @property
    def __all_childs__(cls):
        result = cls.__childs__
        for c in cls.__childs__:
            result += c.__all_childs__
        return result

    @property
    def __all_states__(cls):
        result = cls.__states__
        for c in cls.__childs__:
            result += c.__all_states__
        return result

    @property
    def __all_states_names__(cls):
        return tuple(s.state for s in cls.__all_states__ if s.state)

    def __contains__(cls, item):
        if isinstance(item, str):
            return item in cls.__all_states_names__
        if isinstance(item, State):
            return item in cls.__all_states__
        return False


class StatesGroup(metaclass=StatesGroupMeta):
    pass


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
    confirming_channel_delete = State()

    # Reklama tarqatish
    broadcasting_message = State()

class OwnerGifts(StatesGroup):
    waiting_user_id = State()
    selecting_duration = State()
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


class DocumentAddStates(StatesGroup):
    TITLE = State() # NEW
    CATEGORY = State()
    FILE = State()
    WAIT_FOR_APP_FILE = State() # [NEW] Specifically for App-initiated flow

class CertificateAddStates(StatesGroup):
    TITLE = State()
    FILE = State()
    WAIT_FOR_APP_FILE = State() # [NEW] Specifically for App-initiated flow

from aiogram.fsm.state import State, StatesGroup

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

from aiogram.fsm.state import StatesGroup, State


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

from aiogram.fsm.state import StatesGroup, State

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
