import sys, os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
"""
Tyutor Module Migration Script
Adds 4 new tables for Tyutor Intelligence Management System
"""

import asyncio
from sqlalchemy import text
from database.db_connect import engine


async def add_tyutor_tables():
    async with engine.begin() as conn:
        # 1. Tyutor Work Log
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tyutor_work_log (
                id SERIAL PRIMARY KEY,
                tyutor_id INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                direction_type VARCHAR(50) NOT NULL,
                description TEXT,
                status VARCHAR(20) DEFAULT 'completed',
                points INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """))
        
        # 2. Tyutor KPI
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS tyutor_kpi (
                id SERIAL PRIMARY KEY,
                tyutor_id INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
                quarter INTEGER NOT NULL,
                year INTEGER NOT NULL,
                coverage_score FLOAT DEFAULT 0,
                risk_detection_score FLOAT DEFAULT 0,
                activity_score FLOAT DEFAULT 0,
                parent_contact_score FLOAT DEFAULT 0,
                discipline_score FLOAT DEFAULT 0,
                total_kpi FLOAT DEFAULT 0,
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(tyutor_id, quarter, year)
            );
        """))
        
        # 3. Student Risk Assessment
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS student_risk_assessment (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL UNIQUE REFERENCES students(id) ON DELETE CASCADE,
                risk_level VARCHAR(20) DEFAULT 'low',
                risk_factors TEXT,
                last_assessed TIMESTAMP DEFAULT NOW()
            );
        """))
        
        # 4. Parent Contact Log
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS parent_contact_log (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                tyutor_id INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
                contact_date TIMESTAMP NOT NULL,
                contact_type VARCHAR(50) NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """))
        
        print("✅ Tyutor module tables created successfully!")


if __name__ == "__main__":
    asyncio.run(add_tyutor_tables())
