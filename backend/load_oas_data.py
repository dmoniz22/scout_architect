#!/usr/bin/env python3
"""Load OAS skills data from parsed JSON into PostgreSQL"""
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def load_data():
    # Load the parsed data
    with open('data/oas_skills_fixed.json', 'r') as f:
        skills_data = json.load(f)
    
    # Connect to database - use env vars if available (Docker), else fallback
    import os
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5435")),
        database=os.getenv("DB_NAME", "scout_architect"),
        user=os.getenv("DB_USER", "scout"),
        password=os.getenv("DB_PASSWORD", "safe_scouting_2026")
    )
    cursor = conn.cursor()
    
    # Map skill names to section IDs (we'll need to determine this from data)
    # OAS skills are mostly for Scouts (section_id=3) but some apply to Cubs (2) and Venturers (4)
    section_map = {
        'Aquatic': 3,  # Scout level
        'Camping': 3,
        'Emergency': 3,
        'Paddling': 3,
        'Sailing': 3,
        'Scoutcraft': 3,
        'Trail': 3,
        'Vertical': 3,
        'Winter': 3,
    }
    
    # Category mapping
    category_map = {
        'Aquatic': 'Water',
        'Camping': 'Camping',
        'Emergency': 'Outdoor Adventure',
        'Paddling': 'Water',
        'Sailing': 'Water',
        'Scoutcraft': 'Camping',
        'Trail': 'Wilderness',
        'Vertical': 'Wilderness',
        'Winter': 'Wilderness',
    }
    
    skills_inserted = 0
    for skill in skills_data:
        skill_name = skill['skill_name']
        category = category_map.get(skill_name, 'Outdoor Adventure')
        section_id = section_map.get(skill_name, 3)  # Default to Scout
        
        # Extract level descriptions
        level_descs = {}
        for level in skill.get('levels', []):
            level_num = level.get('level_number', 1)
            reqs = level.get('requirements', [])
            # Combine all requirements into a single description
            req_texts = [r.get('description', '') for r in reqs if r.get('description')]
            level_descs[level_num] = '\n'.join(req_texts)
        
        # Normalize to 4 levels (some may have 6, consolidate)
        l1 = level_descs.get(1, '')
        l2 = level_descs.get(2, '') or level_descs.get(3, '')
        l3 = level_descs.get(4, '') or level_descs.get(5, '')
        l4 = level_descs.get(6, '') or level_descs.get(5, '') or level_descs.get(4, '')
        
        cursor.execute("""
            INSERT INTO oas_skills 
            (section_id, category, skill_name, level1_desc, level2_desc, level3_desc, level4_desc, prerequisites)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (section_id, category, skill_name, l1, l2, l3, l4, []))
        
        result = cursor.fetchone()
        if result:
            skills_inserted += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ Loaded {skills_inserted} OAS skills into database")

if __name__ == "__main__":
    load_data()
