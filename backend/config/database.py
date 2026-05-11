from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from core.config import settings

# PostgreSQL database connection
connect_args = {}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True  # Good for PostgreSQL connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
