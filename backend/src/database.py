"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://scout:safe_scouting_2026@localhost:5435/scout_architect"
)

# Use NullPool for containerized environments to avoid connection issues
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create tables"""
    from src.models import Base
    Base.metadata.create_all(bind=engine)
    
    # Import all models to ensure they're registered
    from src.models import Section, OASSkill, Badge, Activity, Location, TermPlan, MeetingPlan, SafetyProtocol, UserPreference