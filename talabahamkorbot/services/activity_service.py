from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import logging

from database.models import ActivityLog, ActivityType, Student, DailyActivityStats

logger = logging.getLogger(__name__)

class ActivityService:
    @staticmethod
    async def log_activity(
        db: AsyncSession,
        user_id: int, 
        role: str, # 'student' or 'staff'
        activity_type: ActivityType,
        ref_id: int = None,
        meta_data: dict = None
    ):
        """
        Logs a user activity and updates the user's last_active_at timestamp.
        Designed to be fire-and-forget or awaited.
        """
        try:
            # 1. Create Log Entry
            log = ActivityLog(
                activity_type=activity_type,
                reference_id=ref_id,
                meta_data=meta_data,
                created_at=datetime.utcnow()
            )
            
            is_student = role == 'student'
            is_staff = role == 'staff'
            
            if is_student:
                log.student_id = user_id
                # Fetch student to get faculty_id for aggregation
                student = await db.get(Student, user_id)
                if student:
                    log.faculty_id = student.faculty_id
                    
                    # 2. Update Student Activity Metrics
                    # We use direct update to avoid race conditions on count
                    stmt = (
                        update(Student)
                        .where(Student.id == user_id)
                        .values(
                            last_active_at=datetime.utcnow(),
                            total_activity_count=Student.total_activity_count + 1
                        )
                    )
                    await db.execute(stmt)
            elif is_staff:
                log.staff_id = user_id
                # Staff metrics logic can be added here if needed

            db.add(log)
            # We don't commit here immediately if part of a larger transaction, 
            # but usually activity logging is side-effect.
            # Assuming the caller handles commit or we do it here.
            # Ideally, the caller (API endpoint) commits.
            
            # If we want to ensure it's saved regardless of main transaction success,
            # we'd need a separate session, but for now we attach to current session.
            
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")

    @staticmethod
    async def aggregate_daily_stats(db: AsyncSession, date: datetime = None):
        """
        Aggregates logs into DailyActivityStats.
        Should be called by a cron job or scheduled task.
        """
        if not date:
            date = datetime.utcnow().date()
            
        # Implementation of aggregation logic...
        # For now, we focus on real-time logging.
        pass
