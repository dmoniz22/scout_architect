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
        # Check if data already exists
        result = db.execute(text("SELECT COUNT(*) FROM sections")).scalar()
        if result > 0:
            print(f"Database already has {result} sections, skipping seed")
            return

        # Seed Sections
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

        # Seed Locations
        db.execute(
            text("""
            INSERT INTO locations (name, city, province, country, latitude, longitude, timezone, is_default)
            VALUES ('Chilliwack, BC', 'Chilliwack', 'BC', 'Canada', 49.1579, -121.9515, 'America/Vancouver', TRUE)
        """)
        )

        # Seed User Preferences
        db.execute(
            text("""
            INSERT INTO user_preferences (key, value) VALUES
            ('default_location_id', '1'),
            ('default_section_id', '1'),
            ('default_meeting_duration', '90'),
            ('temperature_unit', 'celsius')
        """)
        )

        db.commit()
        print("Sections, locations, and preferences seeded successfully")

        # Load OAS skills from JSON
        load_oas_skills(db)

    except Exception as e:
        db.rollback()
        print(f"Seed error: {e}")
    finally:
        db.close()


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

        # Map section names to IDs (all skills apply to Scout section for now)
        section_map = {
            "Beaver": 1,
            "Cub": 2,
            "Scout": 3,
            "Venturer": 4,
            "All": 3,  # Default to Scout section
        }

        for skill in skills_data:
            skill_name = skill.get("skill_name", "")
            category = skill.get("category", "")
            levels = skill.get("levels", [])

            # Get level descriptions
            level_descs = {
                f"level{l['level_number']}_desc": json.dumps(l.get("requirements", []))
                for l in levels
                if l.get("level_number")
            }

            # Determine section - skills with "All" apply to Scout (3)
            section_id = (
                section_map.get(skill_name, 3)
                if skill_name not in ["Beaver", "Cub", "Scout", "Venturer"]
                else section_map.get(skill_name, 3)
            )

            db.execute(
                text("""
                INSERT INTO oas_skills (section_id, category, skill_name, level1_desc, level2_desc, level3_desc, level4_desc)
                VALUES (:section_id, :category, :skill_name, :level1_desc, :level2_desc, :level3_desc, :level4_desc)
            """),
                {
                    "section_id": section_id,
                    "category": category,
                    "skill_name": skill_name,
                    "level1_desc": level_descs.get("level1_desc"),
                    "level2_desc": level_descs.get("level2_desc"),
                    "level3_desc": level_descs.get("level3_desc"),
                    "level4_desc": level_descs.get("level4_desc"),
                },
            )

        db.commit()
        print(f"Loaded {len(skills_data)} OAS skills from {oas_file.name}")

    except Exception as e:
        db.rollback()
        print(f"OAS skills load error: {e}")
