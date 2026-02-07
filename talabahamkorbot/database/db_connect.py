from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from config import DATABASE_URL, LOG_LEVEL

# Agar DEBUG bo‘lsa SQL so‘rovlar loglanadi
echo_sql = LOG_LEVEL.upper() == "DEBUG"

engine = create_async_engine(
    DATABASE_URL,
    echo=echo_sql,
    future=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=60,
    pool_recycle=1800,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# Barcha modellarning asosiy bazasi
Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency-style session.
    FastAPI yoki middleware bilan ishlash uchun qulay.
    """
    async with AsyncSessionLocal() as session:
        yield session

# Alias for backward compatibility
get_db = get_session


def get_session_factory():
    """
    Middleware uchun Session maker.
    """
    return AsyncSessionLocal


async def create_tables():
    """
    Database jadvallarini yaratish.
    main.py on_startup paytida chaqiriladi.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
