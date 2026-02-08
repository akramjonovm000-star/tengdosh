import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db_connect import Base


# ============================================================
# ENUM ROLLAR
# ============================================================

class StaffRole(str, enum.Enum):
    OWNER = "owner"
    DEVELOPER = "developer"
    RAHBARIYAT = "rahbariyat"
    DEKANAT = "dekanat"
    TYUTOR = "tyutor"
    # New roles
    TEACHER = "teacher"
    KAFEDRA_MUDIRI = "kafedra_mudiri"
    DEKAN = "dekan"
    DEKAN_ORINBOSARI = "dekan_orinbosari"
    DEKAN_YOSHLAR = "dekan_yoshlar"
    PROREKTOR = "prorektor"
    YOSHLAR_PROREKTOR = "yoshlar_prorektor"
    REKTOR = "rektor"
    BUXGALTER = "buxgalter"
    KUTUBXONA = "kutubxona"
    INSPEKTOR = "inspektor"
    PSIXOLOG = "psixolog"
    YOSHLAR_YETAKCHISI = "yoshlar_yetakchisi"
    KLUB_RAHBARI = "klub_rahbari"

# ============================================================
# OBUNA (FOLLOW) MODELI
# ============================================================
class StudentSubscription(Base):
    __tablename__ = "student_subscriptions"
    __table_args__ = (
        UniqueConstraint("follower_id", "target_id", name="uq_student_subscription"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    follower_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    follower: Mapped["Student"] = relationship("Student", foreign_keys=[follower_id], back_populates="following")
    target: Mapped["Student"] = relationship("Student", foreign_keys=[target_id], back_populates="followers")


# ============================================================
# PRIVATE CHAT SYSTEM
# ============================================================

class PrivateChat(Base):
    __tablename__ = "private_chats"
    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_private_chat_users"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user1_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    user2_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Metadata for list view
    last_message_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_message_time: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, index=True)
    
    user1_unread_count: Mapped[int] = mapped_column(Integer, default=0)
    user2_unread_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    user1: Mapped["Student"] = relationship("Student", foreign_keys=[user1_id])
    user2: Mapped["Student"] = relationship("Student", foreign_keys=[user2_id])
    messages: Mapped[list["PrivateMessage"]] = relationship("PrivateMessage", back_populates="chat", cascade="all, delete-orphan")


class PrivateMessage(Base):
    __tablename__ = "private_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("private_chats.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    chat: Mapped["PrivateChat"] = relationship("PrivateChat", back_populates="messages")
    sender: Mapped["Student"] = relationship("Student", foreign_keys=[sender_id])


class StudentStatus(str, enum.Enum):
    ACTIVE = "active"
    GRADUATED = "graduated"
    ACADEMIC_LEAVE = "academic_leave"
    EXPELLED = "expelled"



# ============================================================
# UNIFIED USER MODEL
# ============================================================

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("hemis_login", name="uq_users_hemis_login"),
        UniqueConstraint("username", name="uq_users_username"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hemis_login: Mapped[str] = mapped_column(String(128), nullable=False, index=True) # Personal ID
    username: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True) # Platform Username
    role: Mapped[str] = mapped_column(String(32), default="student") # student, staff, admin
    
    # Basic Profile
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    
    # HEMIS/System Data
    hemis_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hemis_token: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # Storing encrypted password or plain (as per existing logic for auto-scrape)
    hemis_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Academic/Work Context
    university_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("universities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    university_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    faculty_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True
    )
    faculty_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    specialty_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    group_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    level_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    semester_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    education_form: Mapped[str | None] = mapped_column(String(64), nullable=True)
    education_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payment_form: Mapped[str | None] = mapped_column(String(64), nullable=True)
    student_status: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Location
    province_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    district_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    accommodation_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    fcm_token: Mapped[str | None] = mapped_column(String(255), nullable=True) # [NEW] Firebase Token

    # --- Premium Features ---
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_expiry: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    balance: Mapped[int] = mapped_column(Integer, default=0)
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False)
    # ------------------------

    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.hemis_login} ({self.role})>"


# ============================================================
# UNIVERSITET MODELI
# ============================================================

class University(Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uni_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(64), nullable=True)

    required_channel: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    faculties: Mapped[list["Faculty"]] = relationship("Faculty", back_populates="university")
    staff: Mapped[list["Staff"]] = relationship("Staff", back_populates="university")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="university")
    tutor_groups: Mapped[list["TutorGroup"]] = relationship("TutorGroup", back_populates="university")

    def __repr__(self):
        return f"<University {self.uni_code}>"


# ============================================================
# FAKULTET MODELI
# ============================================================

class Faculty(Base):
    __tablename__ = "faculties"
    __table_args__ = (
        UniqueConstraint("university_id", "faculty_code", name="uq_faculty_uni_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    university_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("universities.id", ondelete="CASCADE"), nullable=False
    )
    faculty_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    university: Mapped["University"] = relationship("University", back_populates="faculties")
    
    staff: Mapped[list["Staff"]] = relationship("Staff", back_populates="faculty")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="faculty")
    tutor_groups: Mapped[list["TutorGroup"]] = relationship("TutorGroup", back_populates="faculty")

    def __repr__(self):
        return f"<Faculty {self.faculty_code} - {self.name}>"


# ============================================================
# CACHE MODELI
# ============================================================
from sqlalchemy import JSON

class StudentCache(Base):
    __tablename__ = "student_cache"
    __table_args__ = (
        UniqueConstraint("student_id", "key", name="uq_student_cache_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(64), nullable=False) # e.g. "subjects_11", "attendance_11"
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    student: Mapped["Student"] = relationship("Student", backref="caches")

    def __repr__(self):
        return f"<Faculty {self.faculty_code}>"


# ============================================================
# XODIM MODELI
# ============================================================

class Staff(Base):
    __tablename__ = "staff"
    __table_args__ = (
        UniqueConstraint("jshshir", name="uq_staff_jshshir"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True) # [NEW] Added for OneID
    jshshir: Mapped[str] = mapped_column(String(20), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)

    role: Mapped[StaffRole] = mapped_column(String(32), nullable=False)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    hemis_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True) # HEMIS ID
    hemis_token: Mapped[str | None] = mapped_column(String(1024), nullable=True) # [NEW] Authorization Token

    university_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("universities.id", ondelete="SET NULL"), nullable=True
    )
    faculty_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True
    )

    # --- Premium Features ---
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_expiry: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    custom_badge: Mapped[str | None] = mapped_column(String(64), nullable=True)
    balance: Mapped[int] = mapped_column(Integer, default=0)
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # AI Limits for Staff
    ai_usage_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_limit: Mapped[int] = mapped_column(Integer, default=25)
    ai_last_reset: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    # ------------------------

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    university: Mapped["University"] = relationship("University", back_populates="staff")
    faculty: Mapped["Faculty"] = relationship("Faculty", back_populates="staff")
    tg_accounts: Mapped[list["TgAccount"]] = relationship("TgAccount", back_populates="staff")
    tutor_groups: Mapped[list["TutorGroup"]] = relationship("TutorGroup", back_populates="tutor")
    
    managed_clubs: Mapped[list["Club"]] = relationship(
        "Club",
        secondary="club_leaders",
        back_populates="leaders",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Staff {self.full_name}>"


class ResourceFile(Base):
    __tablename__ = "resource_files"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hemis_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ============================================================
# TALABA MODELI
# ============================================================

class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("hemis_login", name="uq_student_hemis"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hemis_id: Mapped[str | None] = mapped_column(String(64), nullable=True) # HEMIS specific ID
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    hemis_login: Mapped[str] = mapped_column(String(128), nullable=False)
    hemis_token: Mapped[str | None] = mapped_column(String(1024), nullable=True) # SAVING TOKEN FOR REFRESH
    hemis_password: Mapped[str | None] = mapped_column(String(255), nullable=True) # SAVING PASS FOR AUTO-SCRAPE
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    birth_date: Mapped[str | None] = mapped_column(String(32), nullable=True) # New Field (Age Calculation)

    university_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("universities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    university_name: Mapped[str | None] = mapped_column(String(255), nullable=True) # New Field

    faculty_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("faculties.id", ondelete="SET NULL"), nullable=True
    )
    faculty_name: Mapped[str | None] = mapped_column(String(255), nullable=True) # New Field
    specialty_name: Mapped[str | None] = mapped_column(String(255), nullable=True) # Yor'nalish
    
    group_number: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True) # Expanded length
    
    # --- New Profile Fields ---
    short_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    level_name: Mapped[str | None] = mapped_column(String(64), nullable=True) # 1-kurs
    semester_name: Mapped[str | None] = mapped_column(String(64), nullable=True) # 1-semestr
    education_form: Mapped[str | None] = mapped_column(String(64), nullable=True) # Kunduzgi
    education_type: Mapped[str | None] = mapped_column(String(64), nullable=True) # Bakalavr
    payment_form: Mapped[str | None] = mapped_column(String(64), nullable=True) # Davlat granti
    student_status: Mapped[str | None] = mapped_column(String(64), nullable=True) # O'qimoqda
    
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    province_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    district_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    accommodation_name: Mapped[str | None] = mapped_column(String(128), nullable=True) # Ijaradagi uyda
    
    missed_hours: Mapped[int] = mapped_column(Integer, default=0) 
    missed_hours_excused: Mapped[int] = mapped_column(Integer, default=0) # [NEW]
    missed_hours_unexcused: Mapped[int] = mapped_column(Integer, default=0) # [NEW]
    gpa: Mapped[float] = mapped_column(default=0.0) # GPA requires decimal precision
    fcm_token: Mapped[str | None] = mapped_column(String(255), nullable=True) # [NEW] Firebase Token
    username: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    hemis_role: Mapped[str | None] = mapped_column(String(50), nullable=True) # HEMIS role code (e.g. 'student', 'teacher')
    
    is_election_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # --- AI Context ---
    ai_context: Mapped[str | None] = mapped_column(Text, nullable=True) # Summarized info for AI
    last_context_update: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    
    # --- Premium Features ---
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_expiry: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    balance: Mapped[int] = mapped_column(Integer, default=0)
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # [NEW] Limits & Badge
    ai_usage_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_limit: Mapped[int] = mapped_column(Integer, default=25)
    ai_last_reset: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    custom_badge: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # ------------------------
    # --------------------------

    status: Mapped[StudentStatus] = mapped_column(String(32), default=StudentStatus.ACTIVE.value)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    university: Mapped["University"] = relationship("University", back_populates="students")
    faculty: Mapped["Faculty"] = relationship("Faculty", back_populates="students")
    tg_accounts: Mapped[list["TgAccount"]] = relationship("TgAccount", back_populates="student")

    activities: Mapped[list["UserActivity"]] = relationship(
        "UserActivity", back_populates="student", cascade="all, delete-orphan"
    )
    documents: Mapped[list["UserDocument"]] = relationship(
        "UserDocument", back_populates="student", cascade="all, delete-orphan"
    )


    certificates: Mapped[list["UserCertificate"]] = relationship(
        "UserCertificate", back_populates="student", cascade="all, delete-orphan"
    )
    feedbacks: Mapped[list["StudentFeedback"]] = relationship(
        "StudentFeedback", back_populates="student", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["StudentNotification"]] = relationship(
        "StudentNotification", back_populates="student", cascade="all, delete-orphan"
    )
    
    # --- Follow System ---
    followers: Mapped[list["StudentSubscription"]] = relationship(
        "StudentSubscription", 
        foreign_keys="[StudentSubscription.target_id]", 
        back_populates="target", 
        cascade="all, delete-orphan"
    )
    following: Mapped[list["StudentSubscription"]] = relationship(
        "StudentSubscription", 
        foreign_keys="[StudentSubscription.follower_id]", 
        back_populates="follower", 
        cascade="all, delete-orphan"
    )
    # ---------------------

    def __repr__(self):
        return f"<Student {self.full_name}>"



class TakenUsername(Base):
    __tablename__ = "taken_usernames"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    student: Mapped["Student"] = relationship("Student")

# ============================================================
# TELEGRAM ACCOUNT
# ============================================================

class TgAccount(Base):
    __tablename__ = "tg_accounts"
    __table_args__ = (
        UniqueConstraint("telegram_id", name="uq_tg_accounts_telegram_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    staff_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("staff.id", ondelete="SET NULL"), nullable=True
    )
    student_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True
    )

    current_role: Mapped[str | None] = mapped_column(String(32), nullable=True)
    channel_verified_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    last_active: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    staff: Mapped["Staff"] = relationship("Staff", back_populates="tg_accounts")
    student: Mapped["Student"] = relationship("Student", back_populates="tg_accounts")

    def __repr__(self):
        return f"<TgAccount {self.telegram_id}>"


# ============================================================
# FAOLLIKLAR
# ============================================================

class UserActivity(Base):
    __tablename__ = "user_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )

    category: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    date: Mapped[str | None] = mapped_column(String(32), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, index=True)

    student: Mapped["Student"] = relationship("Student", back_populates="activities")

    images: Mapped[list["UserActivityImage"]] = relationship(
        "UserActivityImage", back_populates="activity", cascade="all, delete-orphan"
    )


# ============================================================
# HUJJATLAR MODELI
# ============================================================

class UserDocument(Base):
    __tablename__ = "user_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )

    category: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), default="document")

    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    student: Mapped["Student"] = relationship("Student", back_populates="documents")


# ============================================================
# SERTIFIKATLAR
# ============================================================

class UserCertificate(Base):
    __tablename__ = "user_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_id: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    student: Mapped["Student"] = relationship("Student", back_populates="certificates")


# ============================================================
# FAOLLIK RASMLARI
# ============================================================

class UserActivityImage(Base):
    __tablename__ = "user_activity_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_activities.id", ondelete="CASCADE"), nullable=False, index=True
    )

    file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), default="photo")

    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    activity: Mapped["UserActivity"] = relationship("UserActivity", back_populates="images")


# ============================================================
# TALABA MUROJAATLARI
# ============================================================

class StudentFeedback(Base):
    __tablename__ = "student_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    assigned_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assigned_staff_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_hemis_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True) # ID of staff in Hemis (if not in DB)
    file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # AI Analysis Snapshot (Sync with bot)
    ai_topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ai_sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Snapshot Data
    student_full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    student_group: Mapped[str | None] = mapped_column(String(255), nullable=True)
    student_faculty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    student_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("student_feedback.id"), nullable=True)

    student: Mapped["Student"] = relationship("Student", back_populates="feedbacks")
    replies: Mapped[list["FeedbackReply"]] = relationship("FeedbackReply", back_populates="feedback")
    children: Mapped[list["StudentFeedback"]] = relationship("StudentFeedback", back_populates="parent")
    parent: Mapped["StudentFeedback"] = relationship("StudentFeedback", back_populates="children", remote_side=[id])


class FeedbackReply(Base):
    __tablename__ = "feedback_replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feedback_id: Mapped[int] = mapped_column(Integer, ForeignKey("student_feedback.id", ondelete="CASCADE"))
    staff_id: Mapped[int] = mapped_column(Integer, ForeignKey("staff.id", ondelete="SET NULL"), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=True) # Text can be null if file is present
    file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    feedback: Mapped["StudentFeedback"] = relationship("StudentFeedback", back_populates="replies")
    staff: Mapped["Staff"] = relationship("Staff")


class UserAppeal(Base):
    __tablename__ = "user_appeals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )

    file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    text: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    student: Mapped["Student"] = relationship("Student")



# ============================================================
# TUTOR GROUP — TYUTOR → GURUHLAR
# ============================================================

class TutorGroup(Base):
    __tablename__ = "tutor_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    tutor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("staff.id", ondelete="SET NULL"),
        nullable=True, index=True
    )

    university_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("universities.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    faculty_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("faculties.id", ondelete="SET NULL"),
        nullable=True, index=True
    )

    group_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    tutor: Mapped["Staff"] = relationship("Staff", back_populates="tutor_groups")
    university: Mapped["University"] = relationship("University", back_populates="tutor_groups")
    faculty: Mapped["Faculty"] = relationship("Faculty", back_populates="tutor_groups")

    __table_args__ = (
        UniqueConstraint("tutor_id", "group_number", name="uq_tutor_group"),
    )


# ============================================================
# TYUTOR MODULI
# ============================================================

class TyutorWorkLog(Base):
    """6 yo'nalish bo'yicha tyutor ishlari"""
    __tablename__ = "tyutor_work_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tyutor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("staff.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=True
    )
    
    direction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # normativ, darsdan_tashqari, manaviy, profilaktika, turar_joy, ota_ona
    
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    completion_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="completed")
    points: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)


class TyutorKPI(Base):
    """Tyutor KPI hisoblash"""
    __tablename__ = "tyutor_kpi"
    __table_args__ = (
        UniqueConstraint("tyutor_id", "quarter", "year", name="uq_tyutor_kpi_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tyutor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("staff.id", ondelete="CASCADE"), nullable=False
    )
    
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3, 4
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    
    coverage_score: Mapped[float] = mapped_column(Integer, default=0)  # 30%
    risk_detection_score: Mapped[float] = mapped_column(Integer, default=0)  # 25%
    activity_score: Mapped[float] = mapped_column(Integer, default=0)  # 20%
    parent_contact_score: Mapped[float] = mapped_column(Integer, default=0)  # 15%
    discipline_score: Mapped[float] = mapped_column(Integer, default=0)  # 10%
    
    total_kpi: Mapped[float] = mapped_column(Integer, default=0)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)


class StudentRiskAssessment(Base):
    """Talaba xavf darajasi"""
    __tablename__ = "student_risk_assessment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    # low, medium, high, critical
    
    risk_factors: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON string: {"attendance": "low", "activity": "none", "grades": "poor"}
    
    last_assessed: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)


class ParentContactLog(Base):
    """Ota-ona bilan aloqa"""
    __tablename__ = "parent_contact_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    tyutor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("staff.id", ondelete="CASCADE"), nullable=False
    )
    
    contact_date: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    contact_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # phone, visit, meeting
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

# ============================================================
# KLUB MODELLARI
# ============================================================

class ClubLeader(Base):
    __tablename__ = "club_leaders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    club_id: Mapped[int] = mapped_column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    staff_id: Mapped[int] = mapped_column(Integer, ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    appointed_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Club(Base):
    __tablename__ = "clubs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    statute_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    channel_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    spreadsheet_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    leader_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("staff.id", ondelete="SET NULL"), nullable=True)
    
    # Deprecating single leader relationship in favor of list
    # leader: Mapped["Staff"] = relationship("Staff", foreign_keys=[leader_id], lazy="selectin")
    
    # New relationship: Multiple Leaders
    leaders: Mapped[list["Staff"]] = relationship(
        "Staff", 
        secondary="club_leaders",
        back_populates="managed_clubs", # Need to add this to Staff model too
        lazy="selectin"
    )
    # Shared Auth Implementation
    # - [x] Design strategy for Bot-App sync
    # - [x] Update Bot to store HEMIS passwords
    # - [x] Implement production `/api/auth/check` endpoint
    # - [x] Test Telegram login flow on emulator
    memberships: Mapped[list["ClubMembership"]] = relationship("ClubMembership", back_populates="club")

    @property
    def leader(self):
        """Backward compatibility: returns first leader or None"""
        return self.leaders[0] if self.leaders else None

class ClubMembership(Base):
    __tablename__ = "club_memberships"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    club_id: Mapped[int] = mapped_column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    
    student: Mapped["Student"] = relationship("Student")
    club: Mapped["Club"] = relationship("Club", back_populates="memberships")


# ============================================================
# AI SUHBAT LOGLARI
# ============================================================
class StudentAILog(Base):
    __tablename__ = "student_ai_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    
    # Snapshot of student info (for analytics even if student changes)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    university_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    faculty_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    group_number: Mapped[str | None] = mapped_column(String(255), nullable=True) # Increased from 64
    
    user_query: Mapped[str] = mapped_column(Text, nullable=False)
    ai_response: Mapped[str] = mapped_column(Text, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    student: Mapped["Student"] = relationship("Student")

# ============================================================
# PENDING UPLOAD (TELEGRAM-FIRST FLOW)
# ============================================================

class PendingUpload(Base):
    __tablename__ = "pending_uploads"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True) # UUID from App
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True) # e.g. 'passport', 'boshqa'
    title: Mapped[str | None] = mapped_column(String(128), nullable=True) # Custom title for 'Other'
    file_ids: Mapped[str] = mapped_column(Text, default="") # Comma-separated list of file_ids
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    student: Mapped["Student"] = relationship("Student")


# ============================================================
# AI CHAT HISTORY (PERSISTENT)
# ============================================================
class AiMessage(Base):
    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    
    role: Mapped[str] = mapped_column(String(20), nullable=False) # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    student: Mapped["Student"] = relationship("Student")


# ============================================================
# CHOYXONA (COMMUNITY)
# ============================================================

class ChoyxonaPost(Base):
    __tablename__ = "choyxona_posts"

    # ID va User
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Kategoriya (universitet | fakultet | yonalish)
    category_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True) 
    
    # Target Context (Access Control)
    # Qaysi auditoriya uchun mo'ljallangan?
    target_university_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("universities.id", ondelete="CASCADE"), nullable=True, index=True)
    target_faculty_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("faculties.id", ondelete="CASCADE"), nullable=True, index=True)
    target_specialty_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True) # Direction ID o'rniga name ishlatilmoqda chunki alohida jadval yo'q

    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, index=True)
    
    # Denormalized Counts for Performance
    likes_count: Mapped[int] = mapped_column(Integer, default=0)
    comments_count: Mapped[int] = mapped_column(Integer, default=0)
    reposts_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    student: Mapped["Student"] = relationship("Student")
    university: Mapped["University"] = relationship("University")
    faculty: Mapped["Faculty"] = relationship("Faculty")
    
    comments: Mapped[list["ChoyxonaComment"]] = relationship("ChoyxonaComment", back_populates="post", cascade="all, delete-orphan")
    likes: Mapped[list["ChoyxonaPostLike"]] = relationship("ChoyxonaPostLike", back_populates="post", cascade="all, delete-orphan")
    reposts: Mapped[list["ChoyxonaPostRepost"]] = relationship("ChoyxonaPostRepost", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChoyxonaPost {self.id} by {self.student_id} ({self.category_type})>"


class ChoyxonaComment(Base):
    __tablename__ = "choyxona_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("choyxona_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    
    content: Mapped[str] = mapped_column(Text, nullable=False)
    reply_to_comment_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("choyxona_comments.id", ondelete="SET NULL"), nullable=True)
    reply_to_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, index=True)
    
    likes_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    post: Mapped["ChoyxonaPost"] = relationship("ChoyxonaPost", back_populates="comments")
    student: Mapped["Student"] = relationship("Student", foreign_keys=[student_id])
    reply_to_user: Mapped["Student"] = relationship("Student", foreign_keys=[reply_to_user_id])
    parent_comment: Mapped["ChoyxonaComment"] = relationship("ChoyxonaComment", remote_side=[id], backref="replies", foreign_keys=[reply_to_comment_id])
    likes: Mapped[list["ChoyxonaCommentLike"]] = relationship("ChoyxonaCommentLike", back_populates="comment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Comment {self.id} on Post {self.post_id}>"


class ChoyxonaCommentLike(Base):
    __tablename__ = "choyxona_comment_likes"
    __table_args__ = (UniqueConstraint('comment_id', 'student_id', name='_user_comment_like_uc'),)
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    comment_id: Mapped[int] = mapped_column(Integer, ForeignKey("choyxona_comments.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    
    comment: Mapped["ChoyxonaComment"] = relationship("ChoyxonaComment", back_populates="likes")

    def __repr__(self):
        return f"<ChoyxonaCommentLike {self.id} on Comment {self.comment_id}>"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recipient_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    
    type: Mapped[str] = mapped_column(String(32), nullable=False) # 'reply', 'like', 'system'
    related_id: Mapped[int | None] = mapped_column(Integer, nullable=True) # comment_id or post_id
    
    title: Mapped[str] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(String(1024), nullable=False)
    
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    recipient: Mapped["Student"] = relationship("Student", foreign_keys=[recipient_id])
    sender: Mapped["Student"] = relationship("Student", foreign_keys=[sender_id])

    def __repr__(self):
        return f"<Notification {self.id} To: {self.recipient_id} Type: {self.type}>"


class ChoyxonaPostLike(Base):
    __tablename__ = "choyxona_post_likes"
    __table_args__ = (UniqueConstraint('post_id', 'student_id', name='_user_post_like_uc'),)
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("choyxona_posts.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    
    post: Mapped["ChoyxonaPost"] = relationship("ChoyxonaPost", back_populates="likes")

    def __repr__(self):
        return f"<ChoyxonaPostLike {self.id} on Post {self.post_id} by Student {self.student_id}>"

class ChoyxonaPostRepost(Base):
    __tablename__ = "choyxona_post_reposts"
    __table_args__ = (UniqueConstraint('post_id', 'student_id', name='_user_post_repost_uc'),)
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("choyxona_posts.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    
    post: Mapped["ChoyxonaPost"] = relationship("ChoyxonaPost", back_populates="reposts")

    def __repr__(self):
        return f"<ChoyxonaPostRepost {self.id} on Post {self.post_id} by Student {self.student_id}>"


# ============================================================
# TALABA BOZORI (MARKET)
# ============================================================

class MarketCategory(str, enum.Enum):
    BOOKS = "books"       # Kitoblar
    TECH = "tech"         # Texnika
    HOUSING = "housing"   # Kvartira / Ijaraga sherik
    JOBS = "jobs"         # Ish / Vakansiya
    LOST_FOUND = "lost"   # Yo'qolgan buyumlar
    OTHER = "other"       # Boshqa

class MarketItem(Base):
    __tablename__ = "market_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[str] = mapped_column(String(128), nullable=True) # "100.000 so'm" or "Kelishilgan"
    category: Mapped[str] = mapped_column(String(32), default=MarketCategory.OTHER.value, index=True)
    
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, index=True)

    # Relationships
    student: Mapped["Student"] = relationship("Student")

    def __repr__(self):
        return f"<MarketItem {self.id} {self.title}>"


# ============================================================
# NOTIFICATIONS
# ============================================================

class StudentNotification(Base):
    __tablename__ = "student_notifications"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="info") # 'grade', 'info', 'alert'
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow, index=True)
    
    student: Mapped["Student"] = relationship("Student", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.id} for {self.student_id}>"


# ============================================================
# TOLOVLAR (PAYMENTS)
# ============================================================

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    
    amount: Mapped[int] = mapped_column(Integer, nullable=False) # Tiylin or Sum (Use Sum for simplicity if Click returns Sum, usually Click is Sum)
    currency: Mapped[str] = mapped_column(String(3), default="UZS")
    
    payment_system: Mapped[str] = mapped_column(String(20), nullable=False) # click, payme, manual, telegram_stars
    transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True) # External ID
    
    status: Mapped[str] = mapped_column(String(20), default="pending") # pending, paid, cancelled, rejected
    
    proof_url: Mapped[str | None] = mapped_column(String(255), nullable=True) # For manual payments
    comment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    student: Mapped["Student"] = relationship("Student")


# ============================================================
# TO'LOVLAR (TRANSACTIONS)
# ============================================================

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False) # Internal ID (prem_123_...)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    
    amount: Mapped[int] = mapped_column(Integer, nullable=False) # Tiyin
    state: Mapped[int] = mapped_column(Integer, default=1) 
    # 1: Created (Waiting)
    # 2: Completed (Performed)
    # -1: Canceled (before complete)
    # -2: Canceled (after complete)

    create_time: Mapped[int] = mapped_column(BigInteger, default=lambda: int(datetime.utcnow().timestamp() * 1000))
    perform_time: Mapped[int] = mapped_column(BigInteger, default=0)
    cancel_time: Mapped[int] = mapped_column(BigInteger, default=0)
    reason: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    payme_trans_id: Mapped[str | None] = mapped_column(String(64), nullable=True) # External ID from Payme
    click_trans_id: Mapped[str | None] = mapped_column(String(64), nullable=True) # External ID from Click
    uzum_trans_id: Mapped[str | None] = mapped_column(String(64), nullable=True) # External ID from Uzum
    provider: Mapped[str] = mapped_column(String(20), default="payme") # payme, click, uzum


    
    student: Mapped["Student"] = relationship("Student")

# ============================================================
# SUBSCRIPTION MODELS
# ============================================================

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    price_uzs: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class SubscriptionPurchase(Base):
    __tablename__ = "subscription_purchases"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscription_plans.id", ondelete="CASCADE"), nullable=False)
    amount_paid: Mapped[int] = mapped_column(Integer, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(), nullable=False)

    student: Mapped["Student"] = relationship("Student")
    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan")


# ============================================================
# ELECTION MODELS
# ============================================================

class Election(Base):
    __tablename__ = "elections"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    university_id: Mapped[int] = mapped_column(Integer, ForeignKey("universities.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft") # draft, active, finished
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    university: Mapped["University"] = relationship("University")
    candidates: Mapped[list["ElectionCandidate"]] = relationship("ElectionCandidate", back_populates="election", cascade="all, delete-orphan")
    votes: Mapped[list["ElectionVote"]] = relationship("ElectionVote", back_populates="election", cascade="all, delete-orphan")

class ElectionCandidate(Base):
    __tablename__ = "election_candidates"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    election_id: Mapped[int] = mapped_column(Integer, ForeignKey("elections.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_id: Mapped[int] = mapped_column(Integer, ForeignKey("faculties.id", ondelete="CASCADE"), nullable=False, index=True)
    
    campaign_text: Mapped[str] = mapped_column(Text, nullable=True) # Saylovoldi dasturi
    photo_id: Mapped[str | None] = mapped_column(String(255), nullable=True) # Nomzod rasmi
    order: Mapped[int] = mapped_column(Integer, default=0) # Tartib raqami
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    election: Mapped["Election"] = relationship("Election", back_populates="candidates")
    student: Mapped["Student"] = relationship("Student")
    faculty: Mapped["Faculty"] = relationship("Faculty")
    votes: Mapped[list["ElectionVote"]] = relationship("ElectionVote", back_populates="candidate", cascade="all, delete-orphan")

class ElectionVote(Base):
    __tablename__ = "election_votes"
    __table_args__ = (
        UniqueConstraint("election_id", "voter_id", name="uq_election_voter"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    election_id: Mapped[int] = mapped_column(Integer, ForeignKey("elections.id", ondelete="CASCADE"), nullable=False, index=True)
    voter_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id: Mapped[int] = mapped_column(Integer, ForeignKey("election_candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

    election: Mapped["Election"] = relationship("Election", back_populates="votes")
    voter: Mapped["Student"] = relationship("Student")
    candidate: Mapped["ElectionCandidate"] = relationship("ElectionCandidate", back_populates="votes")


# ============================================================
# NOTICE BOARD (ANNOUNCEMENTS)
# ============================================================

class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    link: Mapped[str | None] = mapped_column(String(512), nullable=True) # External or Internal link
    
    priority: Mapped[int] = mapped_column(Integer, default=0) # Higher = more priority (Superadmin = 100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    university_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("universities.id", ondelete="SET NULL"), nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)

    def __repr__(self):
        return f"<Announcement {self.title}>"


class AnnouncementRead(Base):
    __tablename__ = "announcement_read_status"
    __table_args__ = (
        UniqueConstraint("user_id", "announcement_id", name="uq_announcement_read"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    announcement_id: Mapped[int] = mapped_column(Integer, ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False, index=True)
    
    read_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)

# ============================================================
# HOME SCREEN BANNER
# ============================================================

class Banner(Base):
    __tablename__ = "banners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    image_file_id: Mapped[str] = mapped_column(String(255), nullable=False) # Telegram File ID
    link: Mapped[str | None] = mapped_column(String(512), nullable=True) # Optional Action Link
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=datetime.utcnow)
    
    views: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self):
        return f"<Banner {self.id} - Active: {self.is_active}>"
