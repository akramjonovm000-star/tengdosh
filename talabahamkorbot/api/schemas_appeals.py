from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AppealItem(BaseModel):
    id: int
    text: str
    status: str
    student_name: str
    student_faculty: str
    student_group: Optional[str] = None
    student_phone: Optional[str] = None
    ai_topic: Optional[str] = None
    created_at: str  # ISO string
    assigned_role: str
    is_anonymous: bool

class FacultyPerformance(BaseModel):
    faculty: str
    total: int
    resolved: int
    rate: float

class AppealStats(BaseModel):
    total_active: int
    total_resolved: int
    faculty_performance: List[FacultyPerformance]
