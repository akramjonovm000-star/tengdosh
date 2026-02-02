import asyncio
from database.db_connect import engine, Base
from database.models import Election, ElectionCandidate, ElectionVote

async def create_election_tables():
    async with engine.begin() as conn:
        # This will create any missing tables defined in the models
        await conn.run_sync(Base.metadata.create_all)
    print("Election tables created successfully.")

if __name__ == "__main__":
    asyncio.run(create_election_tables())
