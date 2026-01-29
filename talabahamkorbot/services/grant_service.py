from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import UserActivity, Student
from services.hemis_service import HemisService

# Mapping of categories to their Regulation Max Points
# Note: "min(count, 7) / 7" formula applies to these max points.
CATEGORY_POINTS_MAP = {
    # Existing Bot Categories
    "togarak": 20,       # 2. "5 muhim tashabbus" to'garak
    "yutuqlar": 10,      # 5. Musobaqalar / Yutuqlar
    "marifat": 10,       # 7. Ma'rifat darslari
    "volontyorlik": 5,   # 8. Volontyorlik
    "madaniy": 5,        # 9. Madaniy tashriflar (Teatr, muzey...)
    "sport": 5,          # 10. Sport
    "boshqa": 5,         # 11. Boshqa (Ma'naviy-ma'rifiy...)
    
    # Not in Bot yet (Scored as 0)
    # "kitobxonlik": 20, # 1. Kitobxonlik
    # "akademik": 0,     # 3. GPA replaces this
    # "intizom": 0,      # 4. User said IGNORE
    # "davomat": 0,      # 6. User said IGNORE
}

async def calculate_grant_score(student: Student, session: AsyncSession, hemis_service: HemisService):
    """
    Calculates the predicted grant score based on GPA and Activities.
    Returns a dict with breakdown.
    """
    
    # 1. Get GPA
    # Use existing helper to calculate GPA
    gpa = 0.0
    try:
        # We want overall GPA likely, so pass no semester? Or loop?
        # get_student_performance calculates based on "subject-list" which usually returns all subjects or current semester.
        # Let's try fetching without semester_code to get all/default.
        gpa = await hemis_service.get_student_performance(student.hemis_token)
    except Exception as e:
        print(f"Error fetching GPA for grant: {e}")
        
    # User Formula: GPA * 16 (Max 80)
    # If GPA is > 5.0 (e.g. 100 scale), we might need normalization? 
    # Usually Hemis GPA is 2.0 - 5.0. 
    # If GPA is 0, score is 0.
    academic_score = gpa * 16
    if academic_score > 80: academic_score = 80 # Cap just in case
    
    # 2. Get Activities
    # Fetch approved activities grouped by category
    result = await session.execute(
        select(UserActivity.category, func.count(UserActivity.id))
        .where(UserActivity.student_id == student.id)
        .where(UserActivity.status == "approved")
        .group_by(UserActivity.category)
    )
    rows = result.all() # [(category, count), ...]
    
    activity_counts = {cat: 0 for cat in CATEGORY_POINTS_MAP.keys()}
    for cat, count in rows:
        if cat in activity_counts:
            activity_counts[cat] = count
            
    # Calculate Activity Score
    # Formula: (min(count, 7) / 7) * max_points
    total_activity_raw = 0.0
    details = []
    
    for cat, max_pts in CATEGORY_POINTS_MAP.items():
        count = activity_counts.get(cat, 0)
        eff_count = min(count, 7)
        points = (eff_count / 7) * max_pts
        total_activity_raw += points
        
        details.append({
            "category": cat,
            "count": count,
            "max_points": max_pts,
            "earned": points
        })
        
    # User Formula: Total Raw / 5 (Max 20)
    # Example: If perfect everywhere (60 raw available in bot categories), 
    # score = 60 / 5 = 12. 
    # Note: Since we are missing Kitobxonlik (20pts), max possible raw in bot is 60.
    # Max final score = 12. 
    # This is consistent with "bori bilan ishlansin".
    
    social_score = total_activity_raw / 5
    if social_score > 20: social_score = 20 # Cap
    
    total_score = academic_score + social_score
    
    return {
        "gpa": gpa,
        "academic_score": round(academic_score, 2),
        "activity_counts": activity_counts,
        "activity_raw_total": round(total_activity_raw, 2),
        "social_score": round(social_score, 2),
        "total_score": round(total_score, 2),
        "details": details
    }
