import asyncio
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.db_connect import engine

async def migrate_premium():
    async with engine.begin() as conn:
        print("Checking for Premium columns...")
        
        # 1. Update USERS table
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT FALSE"))
            print("Added is_premium to users")
        except Exception as e:
            print(f"Skipped is_premium (users): {e}")

        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN premium_expiry TIMESTAMP WITHOUT TIME ZONE"))
            print("Added premium_expiry to users")
        except Exception as e:
             print(f"Skipped premium_expiry (users): {e}")

        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN balance INTEGER DEFAULT 0"))
            print("Added balance to users")
        except Exception as e:
             print(f"Skipped balance (users): {e}")

        # 2. Update STUDENTS table
        try:
            await conn.execute(text("ALTER TABLE students ADD COLUMN is_premium BOOLEAN DEFAULT FALSE"))
            print("Added is_premium to students")
        except Exception as e:
            print(f"Skipped is_premium (students): {e}")

        try:
            await conn.execute(text("ALTER TABLE students ADD COLUMN premium_expiry TIMESTAMP WITHOUT TIME ZONE"))
            print("Added premium_expiry to students")
        except Exception as e:
             print(f"Skipped premium_expiry (students): {e}")
             
        try:
            await conn.execute(text("ALTER TABLE students ADD COLUMN balance INTEGER DEFAULT 0"))
            print("Added balance to students")
        except Exception as e:
             print(f"Skipped balance (students): {e}")

        # 3. Create PAYMENTS table
        print("Creating payments table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                amount INTEGER NOT NULL,
                currency VARCHAR(3) DEFAULT 'UZS',
                payment_system VARCHAR(20) NOT NULL,
                transaction_id VARCHAR(255) UNIQUE,
                status VARCHAR(20) DEFAULT 'pending',
                proof_url VARCHAR(255),
                comment VARCHAR(255),
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
                paid_at TIMESTAMP WITHOUT TIME ZONE
            )
        """))
        print("Payments table created/verified.")

if __name__ == "__main__":
    asyncio.run(migrate_premium())
