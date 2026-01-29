from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FacultySchema(BaseModel):
    id: int
    name: str

class HemisLoginRequest(BaseModel):
    login: str
    password: str

class StudentProfileSchema(BaseModel):
    id: int
    full_name: str
    phone: Optional[str]
    hemis_login: str
    group_number: Optional[str] = None
    faculty_id: Optional[int] = None
    faculty_name: Optional[str] = None
    specialty_name: Optional[str] = None
    
    # Extended Profile
    first_name: Optional[str] = None
    short_name: Optional[str] = None
    image_url: Optional[str] = None
    level_name: Optional[str] = None
    semester_name: Optional[str] = None
    education_form: Optional[str] = None
    education_type: Optional[str] = None
    payment_form: Optional[str] = None
    student_status: Optional[str] = None
    
    email: Optional[str] = None
    province_name: Optional[str] = None
    district_name: Optional[str] = None
    accommodation_name: Optional[str] = None
    
    is_registered_bot: bool = False 
    username: Optional[str] = None # New Field
    hemis_role: Optional[str] = None # New Field
    role: str = "student" # Fix for Role Label on Mobile
    balance: int = 0
    trial_used: bool = False
    is_premium: bool = False # Premium Status
    premium_expiry: Optional[datetime] = None # NEW: Expiry date
    custom_badge: Optional[str] = None # NEW: Status Icon/Emoji

    created_at: datetime
    
    class Config:
        from_attributes = True

class UsernameUpdateSchema(BaseModel):
    username: str

class ActivityImageSchema(BaseModel):
    file_id: str
    file_type: str

class ActivityListSchema(BaseModel):
    id: int
    category: str
    name: str
    description: Optional[str]
    date: Optional[str]
    status: str
    images: list[ActivityImageSchema] = []

    class Config:
        from_attributes = True

class ActivityCreateSchema(BaseModel):
    category: str
    name: str
    description: str
    date: str

class StudentDashboardSchema(BaseModel):
    gpa: float = 0.0
    missed_hours: int = 0
    missed_hours_excused: int = 0
    missed_hours_unexcused: int = 0
    activities_count: int
    clubs_count: int
    activities_approved_count: int

class ClubSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    image_file_id: Optional[str]

    class Config:
        from_attributes = True

class ClubMembershipSchema(BaseModel):
    club: ClubSchema
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True

class FeedbackListSchema(BaseModel):
    id: int
    text: Optional[str]
    title: Optional[str] = None # NEW: Computed title for UI
    status: str
    assigned_role: Optional[str]
    created_at: datetime
    is_anonymous: bool = False
    
    class Config:
        from_attributes = True

class AppealStatsSchema(BaseModel):
    answered: int = 0
    pending: int = 0
    closed: int = 0

class AppealListResponseSchema(BaseModel):
    appeals: list[FeedbackListSchema]
    stats: AppealStatsSchema

class FeedbackCreateSchema(BaseModel):
    text: str
    role: str # 'rahbariyat', 'dekanat', etc.

class DocumentRequestSchema(BaseModel):
    id: int
    type: str # 'reference', 'transcript'
    status: str
    file_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class PostCreateSchema(BaseModel):
    content: str
    category_type: str # 'university', 'faculty', 'specialty'

class PostResponseSchema(BaseModel):
    id: int
    content: str
    category_type: str
    author_id: int
    author_name: str
    author_username: Optional[str] = None # NEW
    author_avatar: Optional[str] = None   # NEW
    author_image: Optional[str] = None    # NEW FALLBACK
    image: Optional[str] = None           # NEW FALLBACK
    author_role: str
    author_is_premium: bool = False # NEW
    author_custom_badge: Optional[str] = None # NEW
    created_at: datetime
    
    # Context (Debugging mostly, but useful)
    target_university_id: Optional[int]
    target_faculty_id: Optional[int]
    target_specialty_name: Optional[str]

    target_specialty_name: Optional[str]

    # Likes & Comments & Reposts
    likes_count: int = 0
    comments_count: int = 0
    reposts_count: int = 0
    is_liked_by_me: bool = False
    is_reposted_by_me: bool = False
    is_mine: bool = False

    class Config:
        from_attributes = True

class CommentCreateSchema(BaseModel):
    content: str
    reply_to_comment_id: Optional[int] = None

class CommentResponseSchema(BaseModel):
    id: int
    post_id: int
    content: str
    author_id: int
    author_name: str
    author_username: Optional[str] = None
    author_avatar: Optional[str] = None
    author_image: Optional[str] = None    # NEW FALLBACK
    image: Optional[str] = None           # NEW FALLBACK
    created_at: datetime
    
    # New Fields for Frontend UI
    likes_count: int = 0
    is_liked: bool = False
    is_liked_by_author: bool = False
    author_role: str = "Talaba"
    author_is_premium: bool = False # NEW
    author_custom_badge: Optional[str] = None # NEW
    
    # Reply info
    reply_to_comment_id: Optional[int] = None # NEW
    reply_to_username: Optional[str] = None
    reply_to_content: Optional[str] = None
    
    is_mine: bool = False
    
    class Config:
        from_attributes = True

class SubscriptionPlanSchema(BaseModel):
    id: int
    name: str
    duration_days: int
    price_uzs: int
    is_active: bool

    class Config:
        from_attributes = True

class PurchaseRequestSchema(BaseModel):
    plan_id: int

class GPASubjectResultSchema(BaseModel):
    subject_id: str
    name: str
    credit: float
    final_score: float
    grade: str
    grade_point: float
    included: bool
    reason_excluded: Optional[str] = None
    semester_id: Optional[str] = None

class GPAResultSchema(BaseModel):
    gpa: float
    total_credits: float
    total_points: float
    subjects: list[GPASubjectResultSchema]

