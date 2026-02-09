
import asyncio
from sqlalchemy import select, or_
from database.db_connect import get_session
from database.models import Staff

async def check():
    async for db in get_session():
        try:
            stmt = select(Staff).where(
                or_(
                    Staff.role.ilike('%rektor%'),
                    Staff.position.ilike('%rektor%'),
                    Staff.full_name.ilike('%rektor%')
                )
            )
            results = (await db.execute(stmt)).scalars().all()
            with open("rektor.log", "w") as f:
                if results:
                    f.write(f"Found {len(results)} Rektor accounts:\n")
                    for r in results:
                        f.write(f"- {r.full_name} (Role: {r.role}, Position: {r.position})\n")
                else:
                    f.write("No Rektor accounts found.\n")
        except Exception as e:
            with open("rektor.log", "w") as f:
                f.write(f"Error: {e}\n")
        break

if __name__ == "__main__":
    asyncio.run(check())
