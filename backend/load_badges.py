#!/usr/bin/env python3
"""Load sample badge data into PostgreSQL"""
import psycopg2
from psycopg2.extras import RealDictCursor

def load_badges():
    sample_badges = [
        # Beaver (5-7) - Section 1
        {"section_id": 1, "name": "Fire Safety", "category": "Adventure", "requirements": [{"requirement": "I know how to stop, drop, and roll"}, {"requirement": "I can identify fire hazards in my home"}]},
        {"section_id": 1, "name": "Home Safety", "category": "Community", "requirements": [{"requirement": "I know my address and phone number"}, {"requirement": "I can identify emergency exits"}]},
        {"section_id": 1, "name": "Nature", "category": "Creative", "requirements": [{"requirement": "I can identify 5 trees in my area"}, {"requirement": "I know to respect wildlife"}]},
        {"section_id": 1, "name": "Camping", "category": "Adventure", "requirements": [{"requirement": "I can help set up a tent"}, {"requirement": "I know how to pack for a camp"}]},
        {"section_id": 1, "name": "Explorer", "category": "Adventure", "requirements": [{"requirement": "I went on a nature hike"}, {"requirement": "I can use a map"}]},
        
        # Cub (8-10) - Section 2
        {"section_id": 2, "name": "First Aid", "category": "Community", "requirements": [{"requirement": "I can treat minor cuts"}, {"requirement": "I know when to call 911"}]},
        {"section_id": 2, "name": "Campcraft", "category": "Adventure", "requirements": [{"requirement": "I can pitch a tent"}, {"requirement": "I can cook over a fire"}]},
        {"section_id": 2, "name": "Leader", "category": "Leadership", "requirements": [{"requirement": "I can lead a game"}, {"requirement": "I helped at a Beaver meeting"}]},
        {"section_id": 2, "name": "Swimmer", "category": "Sports", "requirements": [{"requirement": "I can swim 25 meters"}, {"requirement": "I know water safety rules"}]},
        {"section_id": 2, "name": "Map Skills", "category": "Skills", "requirements": [{"requirement": "I can read a map"}, {"requirement": "I can use a compass"}]},
        
        # Scout (11-14) - Section 3
        {"section_id": 3, "name": "First Aid", "category": "Community", "requirements": [{"requirement": "I can perform CPR"}, {"requirement": "I know the recovery position"}]},
        {"section_id": 3, "name": "Camping", "category": "Adventure", "requirements": [{"requirement": "I can set up camp in various conditions"}, {"requirement": "I can cook meals for my patrol"}]},
        {"section_id": 3, "name": "Hiking", "category": "Adventure", "requirements": [{"requirement": "I completed a 10km hike"}, {"requirement": "I can plan a hiking route"}]},
        {"section_id": 3, "name": "Leadership", "category": "Leadership", "requirements": [{"requirement": "I led a patrol activity"}, {"requirement": "I mentored younger scouts"}]},
        {"section_id": 3, "name": "Cooking", "category": "Skills", "requirements": [{"requirement": "I can plan a menu"}, {"requirement": "I can cook for a group"}]},
        {"section_id": 3, "name": "Emergency Preparedness", "category": "Community", "requirements": [{"requirement": "I created a home emergency plan"}, {"requirement": "I know emergency procedures"}]},
        {"section_id": 3, "name": "Winter Camping", "category": "Adventure", "requirements": [{"requirement": "I camped in winter conditions"}, {"requirement": "I know cold weather safety"}]},
        {"section_id": 3, "name": "Knots", "category": "Skills", "requirements": [{"requirement": "I know 8 knots"}, {"requirement": "I can teach knot tying"}]},
        
        # Venturer (15-17) - Section 4
        {"section_id": 4, "name": "Advanced First Aid", "category": "Community", "requirements": [{"requirement": "I am certified in first aid"}, {"requirement": "I can respond to emergencies"}]},
        {"section_id": 4, "name": "Expedition", "category": "Adventure", "requirements": [{"requirement": "I planned a multi-day trip"}, {"requirement": "I led navigation"}]},
        {"section_id": 4, "name": "Mentorship", "category": "Leadership", "requirements": [{"requirement": "I mentored younger scouts"}, {"requirement": "I helped train leaders"}]},
        {"section_id": 4, "name": "Citizenship", "category": "Community", "requirements": [{"requirement": "I volunteered in my community"}, {"requirement": "I understand civic responsibilities"}]},
        {"section_id": 4, "name": "Environment", "category": "Scoutcraft", "requirements": [{"requirement": "I led a conservation project"}, {"requirement": "I understand Leave No Trace"}]},
    ]
    
    conn = psycopg2.connect(
        host="localhost",
        port=5435,
        database="scout_architect",
        user="scout",
        password="safe_scouting_2026"
    )
    cursor = conn.cursor()
    
    inserted = 0
    for badge in sample_badges:
        cursor.execute("""
            INSERT INTO badges (section_id, badge_name, category, requirements, prerequisites)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (
            badge["section_id"],
            badge["name"],
            badge["category"],
            json.dumps(badge["requirements"]),
            []
        ))
        result = cursor.fetchone()
        if result:
            inserted += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Loaded {inserted} badges into database")

if __name__ == "__main__":
    import json
    load_badges()
