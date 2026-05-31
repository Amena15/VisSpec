from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

# Async PostgreSQL engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,           # Permanent connections
    max_overflow=20,        # Extra connections when busy
    pool_pre_ping=True,     # Verify connection before using
    echo=False,             # Set True for SQL logging
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db():
    """Dependency to get async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
