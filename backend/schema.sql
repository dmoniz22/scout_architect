-- Scout Leader Lesson Architect - Database Schema
-- PostgreSQL + pgvector

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- SECTIONS (Age Groups)
-- ============================================
CREATE TABLE sections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,  -- Beaver, Cub, Scout, Venturer
    min_age INTEGER NOT NULL,
    max_age INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO sections (name, min_age, max_age, description) VALUES
    ('Beaver', 5, 7, 'Beaver Scouts - Fun, friends, and the outdoors'),
    ('Cub', 8, 10, 'Cub Scouts - Adventure and discovery'),
    ('Scout', 11, 14, 'Scouts - Challenge and adventure'),
    ('Venturer', 15, 17, 'Venturer Scouts - Leadership and exploration');

-- ============================================
-- OUTDOOR ADVENTURE SKILLS (OAS)
-- ============================================
CREATE TABLE oas_skills (
    id SERIAL PRIMARY KEY,
    section_id INTEGER REFERENCES sections(id),
    category VARCHAR(50) NOT NULL,  -- Land, Water, Air, Camping, Wilderness, Outdoor Adventure
    skill_name VARCHAR(100) NOT NULL,
    level1_desc TEXT,
    level2_desc TEXT,
    level3_desc TEXT,
    level4_desc TEXT,
    prerequisites TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for semantic search on skill descriptions
CREATE INDEX oas_embeddings_idx ON oas_skills USING ivfflat (embedding vector_cosine_ops);

-- ============================================
-- BADGES (Personal Achievement)
-- ============================================
CREATE TABLE badges (
    id SERIAL PRIMARY KEY,
    section_id INTEGER REFERENCES sections(id),
    badge_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),  -- Adventure, Creative, Community, etc.
    requirements JSONB NOT NULL,  -- Array of requirement objects
    prerequisites INTEGER[],  -- Badge IDs that must be earned first
    image_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX badges_section_idx ON badges(section_id);

-- ============================================
-- ACTIVITIES (Reusable Templates)
-- ============================================
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    duration_minutes INTEGER,  -- Recommended duration
    min_age INTEGER,
    max_age INTEGER,
    sections INTEGER[],  -- Which sections it's appropriate for
    badges INTEGER[],  -- Which badges this activity supports
    oas_skills INTEGER[],  -- Which OAS skills it develops
    materials TEXT[],  -- List of materials needed
    location_type VARCHAR(20),  -- indoor, outdoor, both
    safety_notes TEXT,
    instructions TEXT,  -- Step by step
    embedding VECTOR(1536),  -- For semantic search
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX activities_embeddings_idx ON activities USING ivfflat (embedding vector_cosine_ops);

-- ============================================
-- LOCATIONS (User-saved)
-- ============================================
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(50),
    province VARCHAR(50),
    country VARCHAR(50) DEFAULT 'Canada',
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    timezone VARCHAR(50),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default location: Chilliwack, BC
INSERT INTO locations (name, city, province, country, latitude, longitude, timezone, is_default)
VALUES ('Chilliwack, BC', 'Chilliwack', 'BC', 'Canada', 49.1579, -121.9515, 'America/Vancouver', TRUE);

-- ============================================
-- TERM PLANS (8-12 week schedules)
-- ============================================
CREATE TABLE term_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    section_id INTEGER REFERENCES sections(id),
    location_id INTEGER REFERENCES locations(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_weeks INTEGER NOT NULL,
    focus_badges INTEGER[],  -- Badge IDs to focus on
    focus_skills INTEGER[],  -- OAS skill IDs to develop
    theme VARCHAR(100),  -- Optional term theme
    notes TEXT,
    status VARCHAR(20) DEFAULT 'draft',  -- draft, active, completed
    deleted_at TIMESTAMP,  -- Soft delete: null = active, timestamp = deleted
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX term_plans_section_idx ON term_plans(section_id);
CREATE INDEX term_plans_status_idx ON term_plans(status);

-- ============================================
-- MEETING PLANS (Individual meetings)
-- ============================================
CREATE TABLE meeting_plans (
    id SERIAL PRIMARY KEY,
    term_plan_id INTEGER REFERENCES term_plans(id) ON DELETE CASCADE,
    week_number INTEGER NOT NULL,
    meeting_date DATE NOT NULL,
    title VARCHAR(200),
    duration_minutes INTEGER DEFAULT 90,
    
    -- Plan content (stored as JSON for flexibility)
    objectives JSONB,  -- What Scouts will learn/do
    activities JSONB,  -- Array of activity blocks with timing
    materials_needed TEXT[],
    safety_briefing TEXT,
    weather_contingency TEXT,  -- Plan B for bad weather
    
    -- Badge/skill focus for this meeting
    badges_covered INTEGER[],
    skills_covered INTEGER[],
    
    -- Output
    generated_plan TEXT,  -- AI-generated full plan
    pdf_path VARCHAR(500),
    
    status VARCHAR(20) DEFAULT 'planned',  -- planned, delivered, completed
    
    deleted_at TIMESTAMP,  -- Soft delete: null = active, timestamp = deleted
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX meeting_plans_term_idx ON meeting_plans(term_plan_id);
CREATE INDEX meeting_plans_date_idx ON meeting_plans(meeting_date);

-- ============================================
-- SAFETY PROTOCOLS
-- ============================================
CREATE TABLE safety_protocols (
    id SERIAL PRIMARY KEY,
    activity_type VARCHAR(50),  -- hiking, camping, swimming, tools, fire, etc.
    title VARCHAR(100) NOT NULL,
    severity VARCHAR(20),  -- critical, high, medium, low
    prevention TEXT,
    response TEXT,
    required_equipment TEXT[],
    certifications_needed TEXT[],
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX safety_embeddings_idx ON safety_protocols USING ivfflat (embedding vector_cosine_ops);

-- ============================================
-- USER PREFERENCES
-- ============================================
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    key VARCHAR(50) NOT NULL UNIQUE,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Default preferences
INSERT INTO user_preferences (key, value) VALUES
    ('default_location_id', '1'),
    ('default_section_id', '1'),
    ('default_meeting_duration', '90'),
    ('temperature_unit', 'celsius');

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- View: Badges with section names
CREATE VIEW badges_with_sections AS
SELECT b.id, b.badge_name, s.name as section, b.category, b.requirements
FROM badges b
JOIN sections s ON b.section_id = s.id;

-- View: OAS skills with section names
CREATE VIEW oas_with_sections AS
SELECT o.id, o.skill_name, o.category, s.name as section
FROM oas_skills o
JOIN sections s ON o.section_id = s.id;

-- View: Meeting plans with}