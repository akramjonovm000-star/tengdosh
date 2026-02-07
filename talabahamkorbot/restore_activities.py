import asyncio
from sqlalchemy import text
from database.db_connect import AsyncSessionLocal
from datetime import datetime
import os

BACKUP_PATH = "/home/user/talabahamkor/latest_full_db_backup.sql"

def parse_dt(s):
    if not s or s == "\\N":
        return None
    # Handle space separator
    s = s.replace(" ", "T")
    # Handle irregular microseconds (e.g. .94564 -> .945640)
    if "." in s:
        base, ms = s.split(".")
        ms = (ms + "000000")[:6]
        s = f"{base}.{ms}"
    return datetime.fromisoformat(s)

def parse_copy_block(file_path, table_name):
    lines = []
    in_block = False
    with open(file_path, "r") as f:
        for line in f:
            if line.startswith(f"COPY public.{table_name}"):
                in_block = True
                continue
            if in_block:
                if line.strip() == "\\.":
                    break
                lines.append(line.strip())
    return lines

async def main():
    print("🚀 Starting Restoration (Robust)...")
    
    act_lines = parse_copy_block(BACKUP_PATH, "user_activities")
    img_lines = parse_copy_block(BACKUP_PATH, "user_activity_images")
    
    print(f"Parsed {len(act_lines)} activities and {len(img_lines)} images from backup.")
    
    async with AsyncSessionLocal() as session:
        # Restore Activities
        restored_count = 0
        for line in act_lines:
            parts = line.split("\t")
            if len(parts) < 8: continue
            
            # (id, student_id, category, name, description, date, status, created_at)
            aid, sid, cat, name, desc, date, status, created = parts
            
            if len(name) < 3: continue
            if name.lower() in ["test", "skaj", "jsak", "ajkdfjds", "fdsjia", "fdsfdsfd"]: 
                continue

            exists = await session.execute(text("SELECT 1 FROM user_activities WHERE id = :id"), {"id": int(aid)})
            if exists.scalar():
                continue
            
            created_dt = parse_dt(created)
            
            await session.execute(
                text("INSERT INTO user_activities (id, student_id, category, name, description, date, status, created_at) "
                     "VALUES (:id, :sid, :cat, :name, :desc, :date, :status, :created)"),
                {
                    "id": int(aid), "sid": int(sid), "cat": cat, "name": name, 
                    "desc": desc if desc != "\\N" else None, 
                    "date": date if date != "\\N" else None, 
                    "status": status, "created": created_dt
                }
            )
            restored_count += 1
        
        print(f"Restored {restored_count} activities.")
        
        # Restore Images
        img_restored = 0
        for line in img_lines:
            parts = line.split("\t")
            if len(parts) < 5: continue
            
            iid, aid, fid, ftype, created = parts
            
            act_exists = await session.execute(text("SELECT 1 FROM user_activities WHERE id = :aid"), {"aid": int(aid)})
            if not act_exists.scalar():
                continue
                
            exists = await session.execute(text("SELECT 1 FROM user_activity_images WHERE id = :id"), {"id": int(iid)})
            if exists.scalar():
                continue

            created_dt = parse_dt(created)
            await session.execute(
                text("INSERT INTO user_activity_images (id, activity_id, file_id, file_type, created_at) "
                     "VALUES (:id, :aid, :fid, :ftype, :created)"),
                {"id": int(iid), "aid": int(aid), "fid": fid, "ftype": ftype, "created": created_dt}
            )
            img_restored += 1
            
        print(f"Restored {img_restored} activity images.")
        
        if restored_count > 0:
            await session.execute(text("SELECT setval('user_activities_id_seq', (SELECT MAX(id) FROM user_activities))"))
        if img_restored > 0:
            await session.execute(text("SELECT setval('user_activity_images_id_seq', (SELECT MAX(id) FROM user_activity_images))"))
        
        await session.commit()
        print("✨ Restoration complete!")

if __name__ == "__main__":
    asyncio.run(main())
