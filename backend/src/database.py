"""
Database connection and session management
"""

import os
import json
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://scout:safe_scouting_2026@localhost:5435/scout_architect",
)

engine = create_engine(DATABASE_URL, poolclass=NullPool, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database - create tables and seed data"""
    from src.models import Base

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if sections exist
        result = db.execute(text("SELECT COUNT(*) FROM sections")).scalar()

        if result == 0:
            # Fresh database - seed everything
            seed_sections(db)
            seed_locations(db)
            seed_preferences(db)
            db.commit()
            print("Seeded sections, locations, preferences")
            load_oas_skills(db)
        else:
            # Sections exist - check if OAS skills need loading
            oas_count = db.execute(text("SELECT COUNT(*) FROM oas_skills")).scalar()
            if oas_count == 0:
                print("Sections exist but OAS skills missing, loading...")
                load_oas_skills(db)
            else:
                print(
                    f"Database ready with {result} sections and {oas_count} OAS skills"
                )

    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
    finally:
        db.close()


def seed_sections(db):
    """Seed sections table"""
    sections_data = [
        {
            "name": "Beaver",
            "min_age": 5,
            "max_age": 7,
            "description": "Beaver Scouts - Fun, friends, and the outdoors",
        },
        {
            "name": "Cub",
            "min_age": 8,
            "max_age": 10,
            "description": "Cub Scouts - Adventure and discovery",
        },
        {
            "name": "Scout",
            "min_age": 11,
            "max_age": 14,
            "description": "Scouts - Challenge and adventure",
        },
        {
            "name": "Venturer",
            "min_age": 15,
            "max_age": 17,
            "description": "Venturer Scouts - Leadership and exploration",
        },
    ]
    for s in sections_data:
        db.execute(
            text("""
            INSERT INTO sections (name, min_age, max_age, description) 
            VALUES (:name, :min_age, :max_age, :description)
        """),
            s,
        )


def seed_locations(db):
    """Seed locations table"""
    db.execute(
        text("""
        INSERT INTO locations (name, city, province, country, latitude, longitude, timezone, is_default)
        VALUES ('Chilliwack, BC', 'Chilliwack', 'BC', 'Canada', 49.1579, -121.9515, 'America/Vancouver', TRUE)
    """)
    )


def seed_preferences(db):
    """Seed user preferences"""
    db.execute(
        text("""
        INSERT INTO user_preferences (key, value) VALUES
        ('default_location_id', '1'),
        ('default_section_id', '1'),
        ('default_meeting_duration', '90'),
        ('temperature_unit', 'celsius')
    """)
    )


def load_oas_skills(db: Session):
    """Load OAS skills from JSON data file"""
    # Try to find the data file
    possible_paths = [
        Path(__file__).parent.parent / "data" / "oas_skills_fixed.json",
        Path("/app/data/oas_skills_fixed.json"),
    ]

    oas_file = None
    for path in possible_paths:
        if path.exists():
            oas_file = path
            break

    if not oas_file:
        print("OAS skills data file not found, skipping")
        return

    try:
        with open(oas_file, "r") as f:
            skills_data = json.load(f)

        for skill in skills_data:
            skill_name = skill.get("skill_name", "")
            category = skill.get("category", "")
            levels_list = skill.get("levels", [])

            # Format levels as JSON array
            formatted_levels = []
            for level in levels_list:
                formatted_levels.append(
                    {
                        "level_number": level.get("level_number"),
                        "requirements": level.get("requirements", []),
                    }
                )

            # All skills apply to Scout section (3) for now
            section_id = 3

            db.execute(
                text("""
                INSERT INTO oas_skills (section_id, category, skill_name, levels)
                VALUES (:section_id, :category, :skill_name, CAST(:levels AS jsonb))
            """),
                {
                    "section_id": section_id,
                    "category": category,
                    "skill_name": skill_name,
                    "levels": json.dumps(formatted_levels),
                },
            )

        db.commit()
        print(
            f"Loaded {len(skills_data)} OAS skills with all 9 levels from {oas_file.name}"
        )

    except Exception as e:
        db.rollback()
        print(f"OAS skills load error: {e}")
