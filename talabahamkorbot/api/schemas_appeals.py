from pydantic import BaseModel
from typing import List, Optional, Dict
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
    id: Optional[int] = None
    faculty: str
    total: int
    resolved: int
    pending: int
    overdue: int = 0
    avg_response_time: float = 0.0 # In hours
    rate: float
    topics: Dict[str, int] = {} # { "Davomat": 5, ... }

class TopTarget(BaseModel):
    role: str
    count: int

class AppealStats(BaseModel):
    total: int
    counts: Dict[str, int]
    total_active: int
    total_resolved: int
    total_overdue: int = 0
    faculty_performance: List[FacultyPerformance]
    top_targets: List[TopTarget]
