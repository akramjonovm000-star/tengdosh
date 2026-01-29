import logging
from typing import List, Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class GPASubjectResult(BaseModel):
    subject_id: str
    name: str
    credit: float
    final_score: float
    grade: str
    grade_point: float
    included: bool
    reason_excluded: Optional[str] = None
    semester_id: Optional[str] = None

class GPAResult(BaseModel):
    gpa: float
    total_credits: float
    total_points: float
    subjects: List[GPASubjectResult]

class GPACalculator:
    # 3. Grade Mapping Configuration (Uzbekistan 5-Point System)
    GRADE_MAP = [
        {"min": 86, "max": 100, "grade": "5", "point": 5.0},
        {"min": 71, "max": 85,  "grade": "4", "point": 4.0},
        {"min": 56, "max": 70,  "grade": "3", "point": 3.0},
        {"min": 0,  "max": 55,  "grade": "2", "point": 2.0}
    ]

    @staticmethod
    def _map_grade(score: float):
        # If score is already in 5-point scale logic (e.g. 3, 4, 5)
        # We assume it is the point itself.
        if 0 < score <= 5:
            return str(int(score)), float(score)

        for rule in GPACalculator.GRADE_MAP:
            if rule["min"] <= score <= rule["max"]:
                return rule["grade"], rule["point"]
        return "2", 0.0

    @staticmethod
    def calculate_gpa(subjects: List[Dict], exclude_in_progress=True) -> GPAResult:
        """
        Calculates Weighted GPA for a list of raw subject data from HEMIS.
        """
        processed_subjects = []
        total_credits = 0.0
        total_points = 0.0

        for item in subjects:
            # Extract basic info
            # HEMIS data structure varies, we try robust extraction
            subject_info = item.get("curriculumSubject", {}) or item.get("subject", {}) or {}
            subj_name = subject_info.get("name") or subject_info.get("subject", {}).get("name") or "Nomsiz fan"
            subj_id = str(subject_info.get("id") or item.get("subject", {}).get("id") or "")
            
            # Extract Credit
            # Usually in curriculumSubject -> credit, or just credit
            try:
                credit = float(item.get("credit") or subject_info.get("credit") or 0)
            except: credit = 0.0

            # Extract Score
            # usually overallScore -> grade
            overall = item.get("overallScore")
            final_score = 0.0
            if isinstance(overall, dict):
                final_score = float(overall.get("grade") or 0)
            elif isinstance(overall, (int, float)):
                final_score = float(overall)
            
            # Extract Status
            # status -> code usually 11 (active), ?? (finished)
            # We rely on final_score > 0 as "finished" or check explicity
            # 4. Edge Cases logic
            
            included = True
            reason = None

            # Policy: Credit 0 -> Exclude
            if credit <= 0:
                included = False
                reason = "No credits"

            # Policy: In Progress -> Exclude (if score is 0)
            if exclude_in_progress and final_score == 0:
                included = False
                reason = "In progress / No score"

            # Map Grade
            grade_letter, grade_point = GPACalculator._map_grade(final_score)

            # If F and policy says exclude failed? Usually F is included in GPA as 0.
            # But user said "pass/fail" boolean subjects should be optional.
            # We assume standard graded subjects here.

            if included:
                total_credits += credit
                total_points += (grade_point * credit)

            processed_subjects.append(GPASubjectResult(
                subject_id=subj_id,
                name=subj_name,
                credit=credit,
                final_score=final_score,
                grade=grade_letter,
                grade_point=grade_point,
                included=included,
                reason_excluded=reason,
                semester_id=str(item.get("semester", {}).get("code") or "")
            ))

        gpa = 0.0
        if total_credits > 0:
            gpa = round(total_points / total_credits, 2)

        return GPAResult(
            gpa=gpa,
            total_credits=total_credits,
            total_points=total_points,
            subjects=processed_subjects
        )

    @staticmethod
    def calculate_cumulative(all_subjects: List[Dict], retake_policy="latest") -> GPAResult:
        """
        Calculates Cumulative GPA handling retakes.
        retake_policy: 'latest' (most recent attempt) or 'best' (highest score).
        """
        # Group by Subject ID
        grouped = {}
        for item in all_subjects:
            # Extract Subject ID
            # IMPORTANT: Retakes usually have same Subject ID but different semester
            s_info = item.get("curriculumSubject", {}) or item.get("subject", {}) or {}
            sid = str(s_info.get("id") or item.get("subject", {}).get("id") or "unknown")
            
            if sid == "unknown": continue # Skip malformed

            if sid not in grouped:
                grouped[sid] = []
            grouped[sid].append(item)

        final_list = []
        
        for sid, attempts in grouped.items():
            if len(attempts) == 1:
                final_list.append(attempts[0])
            else:
                # Resolve Retake
                if retake_policy == "best":
                     # Sort by grade desc
                     attempts.sort(key=lambda x: float(x.get("overallScore", {}).get("grade") or 0), reverse=True)
                     final_list.append(attempts[0])
                else: # latest
                     # Sort by semester code desc (assuming higher code = later)
                     # Or id desc
                     attempts.sort(key=lambda x: int(x.get("semester", {}).get("code") or 0), reverse=True)
                     final_list.append(attempts[0])

        return GPACalculator.calculate_gpa(final_list)
