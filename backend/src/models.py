"""
SQLAlchemy models for Scout Leader Lesson Architect
"""

from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    ARRAY,
    Numeric,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

try:
    from pgvector.sqlalchemy import Vector as VECTOR
except ImportError:
    # Fallback if pgvector not installed - use a placeholder
    from sqlalchemy import TypeDecorator, Text

    class VECTOR(TypeDecorator):
        impl = Text
        cache_ok = True

        def __init__(self, dim=None):
            super().__init__()
            self.dim = dim


from pydantic import BaseModel

Base = declarative_base()


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    min_age = Column(Integer, nullable=False)
    max_age = Column(Integer, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    badges = relationship("Badge", back_populates="section")
    oas_skills = relationship("OASSkill", back_populates="section")
    term_plans = relationship("TermPlan", back_populates="section")


class OASSkill(Base):
    __tablename__ = "oas_skills"

    id = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey("sections.id"))
    category = Column(String(50), nullable=False)
    skill_name = Column(String(100), nullable=False)
    levels = Column(JSONB, nullable=False)  # All 9 levels as JSON array
    prerequisites = Column(ARRAY(String))
    # embedding - disabled until pgvector is installed
    # embedding = Column(VECTOR(1536))
    created_at = Column(DateTime, default=datetime.utcnow)

    section = relationship("Section", back_populates="oas_skills")


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey("sections.id"))
    badge_name = Column(String(100), nullable=False)
    category = Column(String(50))
    requirements = Column(JSONB, nullable=False)
    prerequisites = Column(ARRAY(Integer))
    image_url = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    section = relationship("Section", back_populates="badges")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer)
    min_age = Column(Integer)
    max_age = Column(Integer)
    sections = Column(ARRAY(Integer))
    badges = Column(ARRAY(Integer))
    oas_skills = Column(ARRAY(Integer))
    materials = Column(ARRAY(String))
    location_type = Column(String(20))  # indoor, outdoor, both
    safety_notes = Column(Text)
    instructions = Column(Text)
    # embedding - disabled until pgvector is installed
    # embedding = Column(VECTOR(1536))
    created_at = Column(DateTime, default=datetime.utcnow)


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    city = Column(String(50))
    province = Column(String(50))
    country = Column(String(50), default="Canada")
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    timezone = Column(String(50))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    term_plans = relationship("TermPlan", back_populates="location")


class TermPlan(Base):
    __tablename__ = "term_plans"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"))
    location_id = Column(Integer, ForeignKey("locations.id"))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_weeks = Column(Integer, nullable=False)
    focus_badges = Column(ARRAY(Integer))
    focus_skills = Column(ARRAY(Integer))
    target_levels = Column(ARRAY(Integer))  # e.g., [3, 4, 5]
    theme = Column(String(100))
    notes = Column(Text)
    status = Column(String(20), default="draft")
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    section = relationship("Section", back_populates="term_plans")
    location = relationship("Location", back_populates="term_plans")
    meetings = relationship(
        "MeetingPlan", back_populates="term_plan", cascade="all, delete-orphan"
    )


class MeetingPlan(Base):
    __tablename__ = "meeting_plans"

    id = Column(Integer, primary_key=True)
    term_plan_id = Column(Integer, ForeignKey("term_plans.id", ondelete="CASCADE"))
    week_number = Column(Integer, nullable=False)
    meeting_date = Column(Date, nullable=False)
    title = Column(String(200))
    duration_minutes = Column(Integer, default=90)
    objectives = Column(JSONB)
    activities = Column(JSONB)
    materials_needed = Column(ARRAY(String))
    safety_briefing = Column(Text)
    weather_contingency = Column(Text)
    badges_covered = Column(ARRAY(Integer))
    skills_covered = Column(ARRAY(Integer))
    generated_plan = Column(Text)
    pdf_path = Column(String(500))
    status = Column(String(20), default="planned")
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    term_plan = relationship("TermPlan", back_populates="meetings")


class SafetyProtocol(Base):
    __tablename__ = "safety_protocols"

    id = Column(Integer, primary_key=True)
    activity_type = Column(String(50))
    title = Column(String(100), nullable=False)
    severity = Column(String(20))
    prevention = Column(Text)
    response = Column(Text)
    required_equipment = Column(ARRAY(String))
    certifications_needed = Column(ARRAY(String))
    # embedding - disabled until pgvector is installed
    # embedding = Column(VECTOR(1536))
    created_at = Column(DateTime, default=datetime.utcnow)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)


class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, default=1)
    key = Column(String(100), nullable=False)
    value = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Pydantic models for API
class SectionCreate(BaseModel):
    name: str
    min_age: int
    max_age: int
    description: Optional[str] = None


class LocationCreate(BaseModel):
    name: str
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = "Canada"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    is_default: bool = False


class TermPlanCreate(BaseModel):
    name: str
    section_id: int
    location_id: int
    start_date: date
    end_date: date
    total_weeks: int
    focus_badges: Optional[List[int]] = None
    focus_skills: Optional[List[int]] = None
    target_levels: Optional[List[int]] = None  # e.g., [3, 4, 5]
    theme: Optional[str] = None
    notes: Optional[str] = None


class MeetingPlanCreate(BaseModel):
    term_plan_id: Optional[int] = None
    week_number: int
    meeting_date: date
    title: Optional[str] = None
    duration_minutes: int = 90
    objectives: Optional[dict] = None
    badges_covered: Optional[List[int]] = None
    skills_covered: Optional[List[int]] = None


class MeetingPlanGenerate(BaseModel):
    term_plan_id: Optional[int] = None
    week_number: int
    include_materials: bool = True
    include_safety: bool = True
    include_weather_plan: bool = True


class GenerateRequest(BaseModel):
    use_llm: bool = False
    model_provider: str = "local"
    model: str = "gemma3:12b"
    openrouter_api_key: Optional[str] = None


class MeetingPlanResponse(BaseModel):
    id: int
    term_plan_id: Optional[int] = None
    week_number: int
    meeting_date: date
    title: Optional[str] = None
    duration_minutes: int = 90
    status: str = "planned"


class UserSettings(BaseModel):
    default_location: str = "1"
    default_duration: str = "90"
    default_section: str = ""
    api_url: str = "http://localhost:8002"
    model: str = "local"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:12b"
    use_ai_generation: bool = False
    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/auto"
    ollama_api_key: str = ""
