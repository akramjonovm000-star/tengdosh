import asyncio
import csv
import os
import sys
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

# We assume we are running from talabahamkorbot directory
# So we can import directly
try:
    from database.db_connect import AsyncSessionLocal
    from database.models import StudentFeedback
    # from config import UPLOAD_DIR (not found)
except ImportError:
    # Fallback if running from parent
    sys.path.append(os.getcwd())
    from talabahamkorbot.database.db_connect import AsyncSessionLocal
    from talabahamkorbot.database.models import StudentFeedback
    # from talabahamkorbot.config import UPLOAD_DIR

async def export_appeals():
    print("Connecting to database...")
    async with AsyncSessionLocal() as db:
        print("Querying StudentFeedback...")
        stmt = (
            select(StudentFeedback)
            .options(selectinload(StudentFeedback.replies))
            .order_by(desc(StudentFeedback.created_at))
        )
        result = await db.execute(stmt)
        appeals = result.scalars().all()

        print(f"Found {len(appeals)} appeals.")

        # Define CSV file path
        filename = f"murojaatlar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        # Save to static/uploads
        # UPLOAD_DIR should be defined in config, usually 'static/uploads'
        output_dir = "static/uploads"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        filepath = os.path.join(output_dir, filename)

        print(f"Writing to {filepath}...")
        
        with open(filepath, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            
            # Header
            header = [
                "ID", "Student Name", "Group", "Faculty", "Phone", 
                "Role (Recipient)", "Status", "Date", "Text", 
                "Anonymous", "File ID", "Replies Count", "Last Reply"
            ]
            writer.writerow(header)

            for appeal in appeals:
                # Text cleanup (remove newlines for CSV safety)
                text_clean = appeal.text.replace("\n", " ").replace("\r", "")
                
                # Last reply text
                last_reply = ""
                if appeal.replies:
                    last_reply = appeal.replies[-1].text or "[File]"
                    last_reply = last_reply.replace("\n", " ").replace("\r", "")

                row = [
                    appeal.id,
                    appeal.student_full_name or "N/A",
                    appeal.student_group or "N/A",
                    appeal.student_faculty or "N/A",
                    appeal.student_phone or "N/A",
                    appeal.assigned_role or "General",
                    appeal.status,
                    appeal.created_at.strftime("%Y-%m-%d %H:%M:%S") if appeal.created_at else "",
                    text_clean,
                    "Yes" if appeal.is_anonymous else "No",
                    appeal.file_id or "",
                    len(appeal.replies),
                    last_reply
                ]
                writer.writerow(row)

        print(f"Successfully exported to: {filepath}")
        # Print actual absolute path for user
        print(f"FILE_PATH={os.path.abspath(filepath)}")

if __name__ == "__main__":
    try:
        asyncio.run(export_appeals())
    except KeyboardInterrupt:
        print("Export cancelled.")
    except Exception as e:
        print(f"Error: {e}")
