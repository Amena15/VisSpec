"""
Database engine and session configuration for the VisSpec backend.

Uses async SQLAlchemy with PostgreSQL and connection pooling.
All database interactions in the application are asynchronous.
"""

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.core.config import settings

# -----------------------------------------------------------------------------
# Async PostgreSQL Engine
# -----------------------------------------------------------------------------
# Create an asynchronous engine with connection pooling.
# - pool_size: number of persistent connections kept open.
# - max_overflow: additional connections that can be opened beyond pool_size.
# - pool_pre_ping: verifies connection liveness before checkout.
# - echo: set to True only for detailed SQL logging during development.
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)

# Async session factory – produces database sessions that are awaitable.
# expire_on_commit=False prevents attribute expiration after commit,
# which simplifies working with objects outside of a transaction.
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for all declarative ORM models.
Base = declarative_base()

# -----------------------------------------------------------------------------
# Dependency: Get Async DB Session
# -----------------------------------------------------------------------------
async def get_db():
    """
    FastAPI dependency that provides an async database session.

    Yields an AsyncSession instance, which is automatically closed
    when the request ends. Use this dependency in all async route handlers.
    """
    async with AsyncSessionLocal() as session:
        yield session

# -----------------------------------------------------------------------------
# Lifespan Helper: Cleanly Close Connections on Shutdown
# -----------------------------------------------------------------------------
@asynccontextmanager
async def lifespan_db():
    """
    Context manager to be used in FastAPI's lifespan handler.
    Ensures the engine is properly disposed when the application shuts down.
    """
    try:
        yield
    finally:
        await engine.dispose()