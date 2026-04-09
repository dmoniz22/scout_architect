"""FastAPI backend for Scout Leader Lesson Architect"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import List, Optional
import json
import random
import os

from src.database import get_db, init_db, load_oas_skills
from src.models import (
    Section,
    Badge,
    OASSkill,
    Activity,
    Location,
    TermPlan,
    MeetingPlan,
    SafetyProtocol,
    UserPreference,
    LocationCreate,
    TermPlanCreate,
    MeetingPlanCreate,
    MeetingPlanGenerate,
)

app = FastAPI(title="Scout Leader Lesson Architect", version="0.1.0")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    try:
        init_db()
        print("Database initialized")
    except Exception as e:
        print(f"Database init error (may already exist): {e}")


@app.get("/sections")
def get_sections(db: Session = Depends(get_db)):
    return db.query(Section).all()


@app.post("/admin/reload-oas")
def reload_oas(db: Session = Depends(get_db)):
    """Force reload OAS skills from JSON file"""
    load_oas_skills(db)
    count = db.query(OASSkill).count()
    return {"oas_skills_loaded": count}


@app.get("/sections/{section_id}")
def get_section(section_id: int, db: Session = Depends(get_db)):
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section


@app.get("/badges")
def get_badges(section_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Badge)
    if section_id:
        query = query.filter(Badge.section_id == section_id)
    return query.all()


@app.get("/badges/{badge_id}")
def get_badge(badge_id: int, db: Session = Depends(get_db)):
    badge = db.query(Badge).filter(Badge.id == badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")
    return badge


@app.get("/oas-skills")
def get_oas_skills(
    section_id: Optional[int] = None,
    category: Optional[str] = None,
    level: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Get OAS skills, optionally filtered by section, category, or level.
    Level filter returns skills where any level matches the specified level number.
    """
    query = db.query(OASSkill)
    if section_id:
        query = query.filter(OASSkill.section_id == section_id)
    if category:
        query = query.filter(OASSkill.category == category)

    skills = query.all()

    if level:
        # Filter skills that have the specified level
        filtered_skills = []
        for skill in skills:
            levels = skill.levels if isinstance(skill.levels, list) else []
            if any(l.get("level_number") == level for l in levels):
                filtered_skills.append(skill)
        return filtered_skills

    return skills


@app.get("/locations")
def get_locations(db: Session = Depends(get_db)):
    return db.query(Location).all()


@app.get("/locations/default")
def get_default_location(db: Session = Depends(get_db)):
    location = db.query(Location).filter(Location.is_default == True).first()
    if not location:
        location = db.query(Location).first()
    return location


@app.post("/locations")
def create_location(location: LocationCreate, db: Session = Depends(get_db)):
    db_location = Location(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


# ============== Ollama Integration ==============
@app.get("/ollama/status")
def get_ollama_status():
    """Check if Ollama is available and return available models"""
    import requests

    # Extract base URL - remove /api/generate if present
    ollama_base = os.getenv("OLLAMA_API_URL", "http://host.docker.internal:11434")
    ollama_base = ollama_base.replace("/api/generate", "").replace("/api/chat", "")

    try:
        response = requests.get(f"{ollama_base}/api/tags", timeout=5)
        if response.ok:
            models = response.json().get("models", [])
            return {
                "status": "connected",
                "models": [m.get("name") for m in models],
                "url": ollama_base,
            }
        else:
            return {"status": "error", "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/term-plans")
def get_term_plans(
    status: Optional[str] = None,
    section_id: Optional[int] = None,
    include_deleted: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(TermPlan)
    # Filter out soft-deleted items by default
    if not include_deleted:
        query = query.filter(TermPlan.deleted_at.is_(None))
    if status:
        query = query.filter(TermPlan.status == status)
    if section_id:
        query = query.filter(TermPlan.section_id == section_id)
    return query.order_by(TermPlan.created_at.desc()).all()


@app.get("/term-plans/{plan_id}")
def get_term_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(TermPlan).filter(TermPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Term plan not found")
    return plan


@app.post("/term-plans")
def create_term_plan(plan: TermPlanCreate, db: Session = Depends(get_db)):
    db_plan = TermPlan(**plan.dict())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)

    # Create meeting records for each week
    from datetime import datetime

    if isinstance(plan.start_date, str):
        start = datetime.fromisoformat(plan.start_date).date()
    else:
        start = plan.start_date

    for week in range(1, plan.total_weeks + 1):
        meeting_date = start + timedelta(weeks=week - 1)
        meeting = MeetingPlan(
            term_plan_id=db_plan.id,
            week_number=week,
            meeting_date=meeting_date,
            title=f"Week {week}: Planning",
            duration_minutes=90,
            status="planned",
        )
        db.add(meeting)

    db.commit()

    return db_plan


@app.put("/term-plans/{plan_id}")
def update_term_plan(plan_id: int, plan: TermPlanCreate, db: Session = Depends(get_db)):
    db_plan = db.query(TermPlan).filter(TermPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Term plan not found")
    for key, value in plan.dict().items():
        setattr(db_plan, key, value)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@app.delete("/term-plans/{plan_id}")
def delete_term_plan(
    plan_id: int, permanent: bool = False, db: Session = Depends(get_db)
):
    """Soft delete a term plan (can be restored within 30 days). Use permanent=true to delete forever."""
    from datetime import datetime

    db_plan = db.query(TermPlan).filter(TermPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Term plan not found")

    if permanent:
        # Hard delete - actually remove from database
        # Also delete all meetings
        db.query(MeetingPlan).filter(MeetingPlan.term_plan_id == plan_id).delete()
        db.delete(db_plan)
        db.commit()
        return {"status": "permanently deleted"}
    else:
        # Soft delete - mark as deleted
        db_plan.deleted_at = datetime.utcnow()
        # Also soft delete all meetings
        db.query(MeetingPlan).filter(MeetingPlan.term_plan_id == plan_id).update(
            {"deleted_at": datetime.utcnow()}
        )
        db.commit()
        return {
            "status": "deleted",
            "restoreable_until": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }


@app.post("/term-plans/{plan_id}/restore")
def restore_term_plan(plan_id: int, db: Session = Depends(get_db)):
    """Restore a soft-deleted term plan"""
    from datetime import datetime

    db_plan = db.query(TermPlan).filter(TermPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Term plan not found")

    if db_plan.deleted_at is None:
        raise HTTPException(status_code=400, detail="Term plan is not deleted")

    # Check if within 30-day recovery window
    days_since_delete = (datetime.utcnow() - db_plan.deleted_at).days
    if days_since_delete > 30:
        raise HTTPException(status_code=410, detail="Recovery window expired (30 days)")

    db_plan.deleted_at = None
    db.query(MeetingPlan).filter(MeetingPlan.term_plan_id == plan_id).update(
        {"deleted_at": None}
    )
    db.commit()
    return {"status": "restored"}


@app.get("/deleted-term-plans")
def get_deleted_term_plans(db: Session = Depends(get_db)):
    """Get all soft-deleted term plans (within 30-day recovery window)"""
    from datetime import datetime

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    return (
        db.query(TermPlan)
        .filter(TermPlan.deleted_at.isnot(None), TermPlan.deleted_at > thirty_days_ago)
        .order_by(TermPlan.deleted_at.desc())
        .all()
    )


@app.get("/term-plans/{plan_id}/meetings")
def get_meetings(
    plan_id: int, include_deleted: bool = False, db: Session = Depends(get_db)
):
    query = db.query(MeetingPlan).filter(MeetingPlan.term_plan_id == plan_id)
    # Filter out soft-deleted items by default
    if not include_deleted:
        query = query.filter(MeetingPlan.deleted_at.is_(None))
    return query.order_by(MeetingPlan.week_number).all()


@app.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(MeetingPlan).filter(MeetingPlan.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@app.delete("/meetings/{meeting_id}")
def delete_meeting(
    meeting_id: int, permanent: bool = False, db: Session = Depends(get_db)
):
    """Soft delete a meeting (can be restored within 30 days). Use permanent=true to delete forever."""
    from datetime import datetime

    meeting = db.query(MeetingPlan).filter(MeetingPlan.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if permanent:
        db.delete(meeting)
        db.commit()
        return {"status": "permanently deleted"}
    else:
        meeting.deleted_at = datetime.utcnow()
        db.commit()
        return {
            "status": "deleted",
            "restoreable_until": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }


@app.post("/meetings/{meeting_id}/restore")
def restore_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """Restore a soft-deleted meeting"""
    from datetime import datetime

    meeting = db.query(MeetingPlan).filter(MeetingPlan.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if meeting.deleted_at is None:
        raise HTTPException(status_code=400, detail="Meeting is not deleted")

    days_since_delete = (datetime.utcnow() - meeting.deleted_at).days
    if days_since_delete > 30:
        raise HTTPException(status_code=410, detail="Recovery window expired (30 days)")

    meeting.deleted_at = None
    db.commit()
    return {"status": "restored"}


@app.get("/deleted-meetings")
def get_deleted_meetings(db: Session = Depends(get_db)):
    """Get all soft-deleted meetings (within 30-day recovery window)"""
    from datetime import datetime

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    return (
        db.query(MeetingPlan)
        .filter(
            MeetingPlan.deleted_at.isnot(None), MeetingPlan.deleted_at > thirty_days_ago
        )
        .order_by(MeetingPlan.deleted_at.desc())
        .all()
    )


@app.put("/meetings/{meeting_id}")
def update_meeting(meeting_id: int, title: str = None, db: Session = Depends(get_db)):
    """Update meeting details - primarily the title before generation"""
    meeting = db.query(MeetingPlan).filter(MeetingPlan.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if title is not None:
        meeting.title = title

    db.commit()
    db.refresh(meeting)
    return meeting


@app.post("/meetings")
def create_meeting(meeting: MeetingPlanCreate, db: Session = Depends(get_db)):
    db_meeting = MeetingPlan(**meeting.dict())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting


# ============== MEETING GENERATION WITH DETAILED ACTIVITIES ==============

ACTIVITY_DETAILS = {
    "Duck Duck Goose": {
        "description": "Classic circle game where one player walks around tapping others 'duck' until saying 'goose'.",
        "instructions": [
            "1. All players sit in a circle facing inward",
            "2. 'It' walks around outside tapping heads saying 'Duck'",
            "3. Eventually says 'Goose!' - that player stands and chases",
            "4. 'It' tries to sit in the empty spot before being tagged",
            "5. If caught, remain 'it'; if safe, Goose becomes 'it'",
        ],
        "materials": ["Open space"],
        "safety": "Run clockwise only. No pushing.",
    },
    "Musical Statues": {
        "description": "Dance and freeze when music stops",
        "instructions": [
            "1. Play music while everyone dances",
            "2. Stop music suddenly - everyone freezes",
            "3. Anyone moving is out",
            "4. Continue until 2-3 players remain (winners)",
        ],
        "materials": ["Music player"],
        "safety": "Clear area of hazards before starting",
    },
    "Capture the Flag": {
        "description": "Teams try to capture opponent's flag",
        "instructions": [
            "1. Split into two teams with territories",
            "2. Each team has a flag at their base",
            "3. Cross into enemy territory to capture their flag",
            "4. If tagged in enemy territory, go to jail",
            "5. Teammates can free you by touching jail",
            "6. First team to capture opponent's flag wins",
        ],
        "materials": ["Two flags", "Boundary markers"],
        "safety": "Two-hand touch only, no tackling",
    },
    "Predator vs Prey": {
        "description": "Tag game teaching food chain dynamics",
        "instructions": [
            "1. Designate 'habitats' (safe zones) around area",
            "2. Most players are prey (rabbits, deer, mice)",
            "3. 2-3 players are predators (wolves, hawks)",
            "4. Prey must leave habitats to 'forage'",
            "5. Predators tag prey outside habitats",
            "6. Tagged prey become predators next round",
        ],
        "materials": ["Cones for habitats"],
        "safety": "Safe zones are strictly safe - no tagging inside",
    },
    "Hospital Tag": {
        "description": "Tagged players need 'treatment' to rejoin",
        "instructions": [
            "1. 1-2 players are 'it'",
            "2. When tagged, sit down and yell 'Hospital!'",
            "3. Two teammates must link arms and circle patient",
            "4. Say 'Treatment!' three times to heal",
            "5. Patient is healed and can rejoin",
            "6. Switch taggers every few minutes",
        ],
        "materials": ["Open space"],
        "safety": "Sit immediately when tagged",
    },
    "Relay Races": {
        "description": "Team relay competitions",
        "instructions": [
            "1. Teams line up behind start line",
            "2. First person runs to cone, does task, returns",
            "3. Tasks: touch cone, jumping jacks, answer riddle",
            "4. Tap next teammate who runs",
            "5. Continue until all team members have gone",
            "6. First team finished wins",
        ],
        "materials": ["Cones", "Task cards (optional)"],
        "safety": "Stay in lanes, no cutting across",
    },
    "Wide Games": {
        "description": "Large-scale outdoor games over expanded area",
        "instructions": [
            "1. Define large boundaries (forest, fields)",
            "2. Examples: Manhunt, Search/Rescue, Capture zones",
            "3. Set clear objectives: find items, collect clues",
            "4. Use whistles for pause/stop",
            "5. Debrief about strategy and teamwork",
        ],
        "materials": ["Whistle", "Boundary markers"],
        "safety": "Buddy system required. Boundaries enforced.",
    },
    "Nature Scavenger Hunt": {
        "description": "Find natural items on a list",
        "instructions": [
            "1. Give teams list of items: pinecone, leaf, rock, feather",
            "2. Set boundaries and time limit",
            "3. Teams explore to find items",
            "4. Return when time expires",
            "5. Most items found wins",
        ],
        "materials": ["Scavenger hunt lists", "Bags", "Pencils"],
        "safety": "Stay in boundaries. Look don't touch unknown plants.",
    },
    "Knot Tying": {
        "description": "Learn essential Scout knots",
        "instructions": [
            "1. Square Knot: Right over left, left over right",
            "2. Bowline: Make loop, rabbit up hole, around tree, back",
            "3. Clove Hitch: Two half-hitches around post",
            "4. Practice each knot 5 times",
            "5. Test: Partner checks your knot",
            "6. Teach your best knot to partner",
        ],
        "materials": ["Rope (5ft per Scout)", "Knot boards"],
        "safety": "Check ropes for fraying. No rope around necks.",
    },
    "First Aid Basics": {
        "description": "Learn basic first aid skills",
        "instructions": [
            "1. Review contents of first aid kit",
            "2. Practice cleaning and bandaging a scrape",
            "3. Learn how to apply pressure to stop bleeding",
            "4. Practice RICE method for sprains (Rest, Ice, Compress, Elevate)",
            "5. When to call for adult help",
            "6. Role play scenarios",
        ],
        "materials": ["First aid kit", "Bandages", "Gauze"],
        "safety": "Use fake wounds for practice. Sharps only with supervision.",
    },
    "Shelter Building": {
        "description": "Build emergency shelters using natural materials",
        "instructions": [
            "1. Find natural hollow or flat area",
            "2. Collect fallen branches and debris",
            "3. Create A-frame ribs from ridge pole",
            "4. Add horizontal branches between ribs",
            "5. Layer leaves/debris for waterproofing",
            "6. Test: Is it off ground? Can it keep you dry?",
            "7. Disassemble properly",
        ],
        "materials": ["Optional: Tarp", "No tools needed"],
        "safety": "Check for widowmakers above. Avoid poison ivy.",
    },
    "Map Reading": {
        "description": "Learn to read and use maps",
        "instructions": [
            "1. Identify map symbols and legend",
            "2. Orient the map to north",
            "3. Find your current location on map",
            "4. Identify landmarks and terrain features",
            "5. Practice pacing distances",
            "6. Navigate to points on map",
        ],
        "materials": ["Maps of area", "Compasses"],
        "safety": "Stay in designated area. Buddy system.",
    },
    "Flag Ceremony": {
        "description": "Conduct proper opening/closing ceremony",
        "instructions": [
            "1. Form horseshoe around flag pole",
            "2. Color party marches to flag",
            "3. Raise/lower flag with proper respect",
            "4. Salute during national anthem",
            "5. Recite Scout Promise/Law",
            "6. Color party marches back",
        ],
        "materials": ["Canadian flag", "Rope"],
        "safety": "Handle flag with respect. No horseplay.",
    },
    "Cooking": {
        "description": "Outdoor cooking basics",
        "instructions": [
            "1. Build and light a fire using proper technique",
            "2. Create fire lays: teepee, log cabin",
            "3. Cook simple meal over fire",
            "4. Practice fire safety",
            "5. Properly extinguish and clean up",
            "6. Leave no trace principles",
        ],
        "materials": ["Fire pit/trench", "Matches/flint", "Firewood", "Food to cook"],
        "safety": "Fire permit required. Bucket of water nearby. Never leave fire unattended.",
    },
    "Compass Orienteering": {
        "description": "Navigate using compass bearings",
        "instructions": [
            "1. Explain compass parts and how to take a bearing",
            "2. Practice aligning compass with map",
            "3. Set up course with checkpoints",
            "4. Scouts navigate from point to point using bearings",
            "5. Record times and accuracy",
            "6. Discuss what affects navigation",
        ],
        "materials": ["Compasses", "Maps", "Control markers"],
        "safety": "Stay on trails. Report back if lost.",
    },
}


# ============== LLM Integration ==============
def call_ollama(prompt: str, model: str = "gemma3:12b") -> str:
    """Call Ollama API to generate content"""
    import requests

    # Get base URL from environment, strip any /api/* suffix
    base_url = os.getenv("OLLAMA_API_URL", "http://host.docker.internal:11434")
    base_url = base_url.replace("/api/generate", "").replace("/api/chat", "")

    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        if response.ok:
            return response.json().get("response", "")
        else:
            print(f"Ollama error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Ollama connection error: {e}")
        return None


def generate_with_llm(
    section_name, week_number, duration, theme, location_name, skills=None
) -> dict:
    """Generate meeting content using LLM"""
    # Age ranges for different sections
    age_ranges = {
        "Beaver": "ages 5-7 (young children)",
        "Cub": "ages 8-10 (older children)",
        "Scout": "ages 11-14 (early teens)",
        "Venturer": "ages 14-18 (teens/young adults)",
    }
    age_context = age_ranges.get(section_name, f"{section_name} Scouts")

    # Build skills context - MUST be emphasized as core requirements
    skills_context = ""
    required_activities = ""
    if skills and len(skills) > 0:
        skills_list = ", ".join(skills)
        skills_context = f"\n\n**CRITICAL REQUIREMENT: You MUST incorporate these specific OAS (Outdoors Adventure Skills) skills as the MAIN FOCUS of the meeting: {skills_list}**"
        # Map skills to suggested activities
        skill_activities = {
            "Camping": [
                "shelter building",
                "camping basics",
                "tent setup",
                "fire starting",
                "outdoor cooking",
            ],
            "Scoutcraft": ["knots", "lashings", "tools", "pioneering", "rope work"],
            "Trail": [
                "hiking",
                "orienteering",
                "compass",
                "map reading",
                "trail skills",
            ],
            "Nature": ["nature identification", "wildlife", "plants", "environmental"],
            "First Aid": ["first aid", "injury treatment", "safety"],
            "Aquatics": ["swimming", "water safety", "kayaking", "canoeing"],
            "Climbing": ["climbing", "bouldering", "ropes courses"],
        }
        activities_for_skills = []
        for skill in skills:
            if skill in skill_activities:
                activities_for_skills.extend(skill_activities[skill][:2])
        if activities_for_skills:
            required_activities = f"\n- Each main activity should teach/practice these specific skills: {', '.join(activities_for_skills)}"

    prompt = f"""Create a detailed {section_name} Scouts meeting plan for week {week_number}.{skills_context}

Requirements:
- Duration: {duration} minutes
- Theme: {theme if theme else "general scouting activities"}
- Location context: {location_name}
- Age group: {age_context}{required_activities}
- The meeting MUST have 2-3 main activities that directly teach the OAS skills listed above
- Include: opening, main activities, closing
- Include timing for each activity
- Include materials needed
- Include safety notes
- Make it age-appropriate and engaging for {age_context}

Format the output as a detailed meeting plan with:
1. Title (descriptive, like "Week X: [Activity Focus]") - Include the skills being taught
2. Timeline (with times)
3. Objectives - Must include the OAS skills
4. Materials Needed
5. Safety Notes
6. Location-specific considerations for {location_name}"""

    result = call_ollama(prompt)

    if result:
        # Extract title from the generated content - look for "Title:" or "##" heading
        lines = result.split("\n")
        title = None
        for line in lines:
            line = line.strip()
            if line.lower().startswith("title:") or line.lower().startswith("**title:"):
                title = line.split(":", 1)[1].strip().replace("**", "")
                break
            elif line.startswith("## ") or line.startswith("**"):
                # Use the first heading as title
                title = line.replace("##", "").replace("**", "").strip()
                break

        # If no title found, generate one from skills
        if not title:
            if skills and len(skills) > 0:
                title = f"Week {week_number}: {', '.join(skills)}"
            else:
                title = f"Week {week_number}: {theme or 'Scouting Activities'}"

        return {
            "title": title,
            "plan": result,
            "objectives": ["Develop Scout skills", "Practice teamwork", "Have fun"],
            "activities": [],
            "materials": [],
        }
    return None


SECTION_ACTIVITIES = {
    "Beaver": {
        "games": ["Duck Duck Goose", "Musical Statues", "Relay Races"],
        "skills": ["Nature Scavenger Hunt", "Simple Knots", "Flag Ceremony"],
        "focus": ["Team Building", "Nature Walk", "Crafts"],
    },
    "Cub": {
        "games": [
            "Capture the Flag",
            "Predator vs Prey",
            "Hospital Tag",
            "Relay Races",
        ],
        "skills": ["Knot Tying", "First Aid Basics", "Map Reading", "Flag Ceremony"],
        "focus": ["Shelter Building", "Orienteering", "Cooking", "Service Project"],
    },
    "Scout": {
        "games": [
            "Capture the Flag",
            "Wide Games",
            "Predator vs Prey",
            "Hospital Tag",
            "Compass Orienteering",
        ],
        "skills": [
            "Shelter Building",
            "Knot Tying",
            "First Aid Basics",
            "Map Reading",
            "Compass Orienteering",
        ],
        "focus": [
            "Expedition Planning",
            "Cooking",
            "Advanced First Aid",
            "Service Project",
            "Leadership",
        ],
    },
    "Venturer": {
        "games": ["Wide Games", "Capture the Flag", "Strategic Games"],
        "skills": ["First Aid", "Trip Planning", "Compass Orienteering", "Cooking"],
        "focus": [
            "Expedition Leadership",
            "Service Projects",
            "Peer Mentorship",
            "Risk Assessment",
        ],
    },
}


def get_activity_details(activity_name, activity_type, section_name):
    """Get detailed instructions for an activity"""
    details = ACTIVITY_DETAILS.get(
        activity_name,
        {
            "description": f"{activity_name} activity",
            "instructions": [
                "1. Gather group",
                "2. Explain activity",
                "3. Demonstrate",
                "4. Practice",
                "5. Debrief",
            ],
            "materials": ["TBD"],
            "safety": "Follow standard safety guidelines",
        },
    )
    return details


def generate_meeting_content(
    section_name,
    week_number,
    duration,
    theme,
    badges,
    skills,
    location_name="Chilliwack, BC",
):
    """Generate detailed meeting content"""
    random.seed(week_number * 1000 + hash(location_name) % 1000)

    # Add location context to the generation
    location_note = f"\n\n**Note:** This meeting plan is designed for {location_name}. Consider local weather, facilities, and resources."
    activities = SECTION_ACTIVITIES.get(section_name, SECTION_ACTIVITIES["Scout"])

    game1 = random.choice(activities["games"])
    game2 = random.choice([g for g in activities["games"] if g != game1])
    skill = random.choice(activities["skills"])
    focus = theme if theme else random.choice(activities["focus"])

    # Get detailed instructions
    game1_details = get_activity_details(game1, "game", section_name)
    skill_details = get_activity_details(skill, "skill", section_name)
    activity_details = get_activity_details(focus, "activity", section_name)

    # Build timeline with detailed descriptions
    if duration <= 75:
        timeline = [
            {"time": "0:00-0:10", "name": "Opening Ceremony", "type": "ceremony"},
            {
                "time": "0:10-0:25",
                "name": f"Game: {game1}",
                "type": "game",
                "details": game1_details,
            },
            {
                "time": "0:25-0:45",
                "name": f"Skill: {skill}",
                "type": "skill",
                "details": skill_details,
            },
            {"time": "0:45-0:55", "name": "Snack Break", "type": "break"},
            {
                "time": "0:55-1:10",
                "name": f"Activity: {focus}",
                "type": "activity",
                "details": activity_details,
            },
            {"time": "1:10-1:20", "name": f"Game: {game2}", "type": "game"},
            {"time": "1:20-1:25", "name": "Closing", "type": "ceremony"},
        ]
    else:
        timeline = [
            {"time": "0:00-0:10", "name": "Opening Ceremony", "type": "ceremony"},
            {
                "time": "0:10-0:25",
                "name": f"Game: {game1}",
                "type": "game",
                "details": game1_details,
            },
            {
                "time": "0:25-0:45",
                "name": f"Skill: {skill}",
                "type": "skill",
                "details": skill_details,
            },
            {"time": "0:45-0:50", "name": "Snack", "type": "break"},
            {
                "time": "0:50-1:15",
                "name": f"Activity: {focus}",
                "type": "activity",
                "details": activity_details,
            },
            {"time": "1:15-1:25", "name": f"Game: {game2}", "type": "game"},
            {"time": "1:25-1:30", "name": "Closing Circle", "type": "ceremony"},
        ]

    # Build objectives
    objectives = [f"Develop {section_name} Scout skills", "Practice teamwork"]
    if badges:
        objectives.append(f"Progress on: {', '.join(badges[:2])}")
    if skills:
        objectives.append(f"Build skills: {', '.join(skills[:2])}")

    # Collect materials from all activities
    materials = set()
    for item in timeline:
        if "details" in item and "materials" in item["details"]:
            materials.update(item["details"]["materials"])
    materials.add("First aid kit")
    materials.add("Water")
    materials = list(materials)

    # Build activities JSON
    activities_json = []
    for item in timeline:
        activity_data = {
            "time": item["time"],
            "activity": item["name"],
            "type": item["type"],
        }
        if "details" in item:
            activity_data["description"] = item["details"]["description"]
            activity_data["instructions"] = item["details"]["instructions"]
            activity_data["safety"] = item["details"]["safety"]
        activities_json.append(activity_data)

    # Generate detailed markdown plan
    title = f"Week {week_number}: {focus}"
    lines = [f"# {title}", ""]
    lines.append(f"**Section:** {section_name} Scouts")
    lines.append(f"**Duration:** {duration} minutes")
    lines.append("")

    lines.append("## Timeline\n")
    for item in timeline:
        emoji = {
            "ceremony": "🚩",
            "game": "🎮",
            "skill": "🎯",
            "break": "🍎",
            "activity": "🏕️",
        }.get(item["type"], "•")
        lines.append(f"### {emoji} {item['time']} - {item['name']}\n")
        if "details" in item:
            lines.append(f"**{item['details']['description']}**\n")
            lines.append("\n**Instructions:**")
            for instr in item["details"]["instructions"]:
                lines.append(f"- {instr}")
            lines.append(f"\n**Materials:** {', '.join(item['details']['materials'])}")
            lines.append(f"\n**Safety:** {item['details']['safety']}")
        lines.append("")

    lines.append("## Objectives\n")
    for obj in objectives:
        lines.append(f"- {obj}")
    lines.append("")

    lines.append("## Materials Needed\n")
    for mat in materials:
        lines.append(f"- [ ] {mat}")
    lines.append("")

    lines.append("## Safety Notes\n")
    lines.append("- Stay with your buddy at all times")
    lines.append("- Report injuries or concerns immediately")
    lines.append("- Follow leader instructions")
    lines.append("- Use equipment only with supervision")
    lines.append("")

    # Add location-specific note
    if location_name and location_name != "Chilliwack, BC":
        lines.append(f"## Location Notes\n")
        lines.append(f"- This plan is tailored for {location_name}")
        lines.append("- Consider local weather conditions and facilities")
        lines.append("")

    return {
        "title": title,
        "plan": "\n".join(lines),
        "objectives": objectives,
        "activities": activities_json,
        "materials": materials,
        "timeline": timeline,
    }


@app.post("/meetings/{meeting_id}/generate")
def generate_single_meeting(
    meeting_id: int,
    use_llm: bool = False,
    model: str = "gemma3:12b",
    ollama_url: str = "http://host.docker.internal:11434",
    db: Session = Depends(get_db),
):
    """Generate meeting plan - template or LLM based"""
    meeting = db.query(MeetingPlan).filter(MeetingPlan.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    term_plan = db.query(TermPlan).filter(TermPlan.id == meeting.term_plan_id).first()
    section = db.query(Section).filter(Section.id == term_plan.section_id).first()
    location = db.query(Location).filter(Location.id == term_plan.location_id).first()
    location_name = location.name if location else "Chilliwack, BC"

    badge_names = []
    if meeting.badges_covered:
        badges = db.query(Badge).filter(Badge.id.in_(meeting.badges_covered)).all()
        badge_names = [b.badge_name for b in badges]

    skill_names = []
    if meeting.skills_covered:
        skills = (
            db.query(OASSkill).filter(OASSkill.id.in_(meeting.skills_covered)).all()
        )
        skill_names = [s.skill_name for s in skills]

    # Also get skills from term plan if not specified on meeting
    if not skill_names and term_plan.focus_skills:
        term_skills = (
            db.query(OASSkill).filter(OASSkill.id.in_(term_plan.focus_skills)).all()
        )
        skill_names = [s.skill_name for s in term_skills]

    # Use LLM if requested, otherwise fall back to template
    if use_llm:
        content = generate_with_llm(
            section.name,
            meeting.week_number,
            meeting.duration_minutes or 90,
            term_plan.theme,
            location_name,
            skill_names,
        )
        if not content:
            # Fall back to template if LLM fails
            content = generate_meeting_content(
                section.name,
                meeting.week_number,
                meeting.duration_minutes or 90,
                term_plan.theme,
                badge_names,
                skill_names,
                location_name,
            )
    else:
        content = generate_meeting_content(
            section.name,
            meeting.week_number,
            meeting.duration_minutes or 90,
            term_plan.theme,
            badge_names,
            skill_names,
            location_name,
        )

    meeting.title = content["title"]
    meeting.generated_plan = content["plan"]
    meeting.objectives = content["objectives"]
    meeting.activities = content["activities"]
    meeting.materials_needed = content["materials"]
    meeting.status = "generated"
    db.commit()

    return {"meeting_id": meeting_id, "title": content["title"], "status": "generated"}


@app.post("/term-plans/{plan_id}/generate-meetings")
def generate_all_meetings(
    plan_id: int,
    use_llm: bool = False,
    model: str = "gemma3:12b",
    db: Session = Depends(get_db),
):
    """Generate all meetings for a term plan. Set use_llm=true to use LLM for generation."""
    term_plan = db.query(TermPlan).filter(TermPlan.id == plan_id).first()
    if not term_plan:
        raise HTTPException(status_code=404, detail="Term plan not found")

    section = db.query(Section).filter(Section.id == term_plan.section_id).first()
    location = db.query(Location).filter(Location.id == term_plan.location_id).first()
    location_name = location.name if location else "Chilliwack, BC"

    existing = db.query(MeetingPlan).filter(MeetingPlan.term_plan_id == plan_id).all()
    existing_weeks = {m.week_number: m for m in existing}

    badge_names = []
    if term_plan.focus_badges:
        badges = db.query(Badge).filter(Badge.id.in_(term_plan.focus_badges)).all()
        badge_names = [b.badge_name for b in badges]

    skill_names = []
    if term_plan.focus_skills:
        skills = (
            db.query(OASSkill).filter(OASSkill.id.in_(term_plan.focus_skills)).all()
        )
        skill_names = [s.skill_name for s in skills]

    generated_count = 0
    from datetime import datetime

    if isinstance(term_plan.start_date, str):
        start = datetime.fromisoformat(term_plan.start_date).date()
    else:
        start = term_plan.start_date

    for week in range(1, term_plan.total_weeks + 1):
        meeting_date = start + timedelta(weeks=week - 1)

        if week in existing_weeks:
            meeting = existing_weeks[week]
        else:
            meeting = MeetingPlan(
                term_plan_id=plan_id,
                week_number=week,
                meeting_date=meeting_date,
                duration_minutes=90,
                status="planned",
            )
            db.add(meeting)

        # Use LLM if requested
        if use_llm:
            content = generate_with_llm(
                section.name, week, 90, term_plan.theme, location_name
            )
            if not content:
                # Fall back to template if LLM fails
                content = generate_meeting_content(
                    section.name,
                    week,
                    90,
                    term_plan.theme,
                    badge_names[:2],
                    skill_names[:2],
                    location_name,
                )
        else:
            content = generate_meeting_content(
                section.name,
                week,
                90,
                term_plan.theme,
                badge_names[:2],
                skill_names[:2],
                location_name,
            )

        meeting.title = content["title"]
        meeting.generated_plan = content["plan"]
        meeting.objectives = content["objectives"]
        meeting.activities = content["activities"]
        meeting.materials_needed = content["materials"]
        meeting.status = "generated"
        generated_count += 1

    term_plan.status = "planned"
    db.commit()

    return {
        "term_plan_id": plan_id,
        "meetings_generated": generated_count,
        "total_weeks": term_plan.total_weeks,
        "status": "success",
    }


# ============== PDF EXPORT ==============
@app.get("/meetings/{meeting_id}/pdf")
def download_meeting_pdf(meeting_id: int, db: Session = Depends(get_db)):
    """Generate and download meeting plan as PDF"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
        ListFlowable,
        ListItem,
    )
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER

    meeting = db.query(MeetingPlan).filter(MeetingPlan.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    term_plan = db.query(TermPlan).filter(TermPlan.id == meeting.term_plan_id).first()
    section = db.query(Section).filter(Section.id == term_plan.section_id).first()

    # Create PDF in memory
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DocTitle",
            fontSize=24,
            textColor=colors.HexColor("#1f4e79"),
            spaceAfter=20,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocHeading",
            fontSize=14,
            textColor=colors.HexColor("#2e75b5"),
            spaceAfter=10,
            spaceBefore=15,
        )
    )
    styles.add(ParagraphStyle(name="DocNormal", fontSize=11, spaceAfter=6))
    styles.add(
        ParagraphStyle(name="DocBullet", fontSize=11, leftIndent=20, spaceAfter=3)
    )

    story = []

    # Title
    story.append(Paragraph(f"{meeting.title}", styles["DocTitle"]))
    story.append(Spacer(1, 0.1 * inch))

    # Meeting info
    story.append(
        Paragraph(f"<b>Section:</b> {section.name} Scouts", styles["DocNormal"])
    )
    story.append(Paragraph(f"<b>Date:</b> {meeting.meeting_date}", styles["DocNormal"]))
    story.append(
        Paragraph(
            f"<b>Duration:</b> {meeting.duration_minutes} minutes", styles["DocNormal"]
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    # Objectives
    if meeting.objectives:
        story.append(Paragraph("Objectives", styles["DocHeading"]))
        for obj in meeting.objectives:
            story.append(Paragraph(f"• {obj}", styles["DocBullet"]))
        story.append(Spacer(1, 0.1 * inch))

    # Activities/Timeline
    story.append(Paragraph("Meeting Timeline", styles["DocHeading"]))
    if meeting.activities:
        for activity in meeting.activities:
            emoji = {
                "ceremony": "🚩",
                "game": "🎮",
                "skill": "🎯",
                "break": "🍎",
                "activity": "🏕️",
            }.get(activity.get("type"), "•")
            story.append(
                Paragraph(
                    f"<b>{emoji} {activity.get('time', '')}</b> - {activity.get('activity', '')}",
                    styles["DocNormal"],
                )
            )
            if activity.get("instructions"):
                for instr in activity["instructions"]:
                    story.append(Paragraph(f"   {instr}", styles["DocBullet"]))
            if activity.get("safety"):
                story.append(
                    Paragraph(
                        f"   <i>Safety: {activity['safety']}</i>", styles["DocBullet"]
                    )
                )
            story.append(Spacer(1, 0.05 * inch))

    story.append(Spacer(1, 0.1 * inch))

    # Materials
    if meeting.materials_needed:
        story.append(Paragraph("Materials Needed", styles["DocHeading"]))
        materials_text = "• " + "<br/>• ".join(
            [m for m in meeting.materials_needed if m]
        )
        story.append(Paragraph(materials_text, styles["DocNormal"]))
        story.append(Spacer(1, 0.1 * inch))

    # Full plan text
    if meeting.generated_plan:
        story.append(Paragraph("Full Meeting Plan", styles["DocHeading"]))
        # Clean up HTML-like tags that might be malformed
        import re

        plan_text = re.sub(r"<[^>]+>", "", meeting.generated_plan)  # Strip all HTML
        plan_text = plan_text.replace("\n", "<br/>")
        story.append(Paragraph(plan_text[:2000] + "...", styles["DocNormal"]))

    # Build PDF
    doc.build(story)

    # Return PDF
    buffer.seek(0)
    from starlette.responses import StreamingResponse

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=meeting_{meeting_id}.pdf"
        },
    )


@app.get("/term-plans/{plan_id}/pdf")
def download_term_plan_pdf(plan_id: int, db: Session = Depends(get_db)):
    """Generate and download entire term plan as PDF"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib import colors

    term_plan = db.query(TermPlan).filter(TermPlan.id == plan_id).first()
    if not term_plan:
        raise HTTPException(status_code=404, detail="Term plan not found")

    section = db.query(Section).filter(Section.id == term_plan.section_id).first()
    meetings = (
        db.query(MeetingPlan)
        .filter(MeetingPlan.term_plan_id == plan_id)
        .order_by(MeetingPlan.week_number)
        .all()
    )

    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DocTitle",
            fontSize=24,
            textColor=colors.HexColor("#1f4e79"),
            spaceAfter=20,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DocHeading",
            fontSize=16,
            textColor=colors.HexColor("#2e75b5"),
            spaceAfter=10,
        )
    )
    styles.add(ParagraphStyle(name="DocNormal", fontSize=11, spaceAfter=6))
    styles.add(ParagraphStyle(name="Small", fontSize=9, textColor=colors.grey))

    story = []

    # Title page
    story.append(Paragraph(f"{term_plan.name}", styles["DocTitle"]))
    story.append(
        Paragraph(f"<b>Section:</b> {section.name} Scouts", styles["DocNormal"])
    )
    story.append(
        Paragraph(
            f"<b>Dates:</b> {term_plan.start_date} to {term_plan.end_date}",
            styles["DocNormal"],
        )
    )
    story.append(
        Paragraph(f"<b>Weeks:</b> {term_plan.total_weeks}", styles["DocNormal"])
    )
    if term_plan.theme:
        story.append(Paragraph(f"<b>Theme:</b> {term_plan.theme}", styles["DocNormal"]))
    story.append(Spacer(1, 0.5 * inch))

    # Meeting summaries
    story.append(Paragraph("Meeting Schedule", styles["DocHeading"]))
    for meeting in meetings:
        story.append(
            Paragraph(
                f"<b>Week {meeting.week_number}:</b> {meeting.title}",
                styles["DocNormal"],
            )
        )
        story.append(Paragraph(f"   {meeting.meeting_date}", styles["Small"]))

    story.append(PageBreak())

    # Full meeting details
    for i, meeting in enumerate(meetings):
        story.append(
            Paragraph(
                f"Week {meeting.week_number}: {meeting.title}", styles["DocHeading"]
            )
        )

        if meeting.generated_plan:
            import re

            plan_text = re.sub(r"<[^>]+>", "", meeting.generated_plan)  # Strip all HTML
            plan_text = plan_text.replace("\n", "<br/>")[:1500]
            story.append(Paragraph(plan_text + "...", styles["DocNormal"]))

        if i < len(meetings) - 1:
            story.append(PageBreak())

    doc.build(story)

    buffer.seek(0)
    from starlette.responses import StreamingResponse

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=term_plan_{plan_id}.pdf"
        },
    )


# ============== MARKDOWN EXPORT ==============
@app.get("/meetings/{meeting_id}/md")
def download_meeting_md(meeting_id: int, db: Session = Depends(get_db)):
    """Generate and download meeting plan as Markdown"""
    from starlette.responses import Response

    meeting = db.query(MeetingPlan).filter(MeetingPlan.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    term_plan = db.query(TermPlan).filter(TermPlan.id == meeting.term_plan_id).first()
    section = db.query(Section).filter(Section.id == term_plan.section_id).first()

    md = f"""# {meeting.title}

## Meeting Details
- **Section:** {section.name} Scouts
- **Date:** {meeting.meeting_date}
- **Duration:** {meeting.duration_minutes} minutes
- **Week:** {meeting.week_number}

"""

    if meeting.objectives:
        md += "## Objectives\n"
        for obj in meeting.objectives:
            md += f"- {obj}\n"
        md += "\n"

    if meeting.materials_needed:
        md += "## Setup\n"
        for item in meeting.materials_needed:
            md += f"- {item}\n"
        md += "\n"

    if meeting.materials_needed:
        md += "## Supplies Needed\n"
        for item in meeting.materials_needed:
            md += f"- {item}\n"
        md += "\n"

    if meeting.generated_plan:
        md += "## Meeting Plan\n"
        md += meeting.generated_plan
        md += "\n"

    if meeting.safety_briefing:
        md += "## Safety Notes\n"
        md += meeting.safety_notes + "\n"

    return Response(
        md,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=meeting_{meeting_id}.md"
        },
    )


@app.get("/term-plans/{plan_id}/md")
def download_term_plan_md(plan_id: int, db: Session = Depends(get_db)):
    """Generate and download entire term plan as Markdown"""
    from starlette.responses import Response

    term_plan = db.query(TermPlan).filter(TermPlan.id == plan_id).first()
    if not term_plan:
        raise HTTPException(status_code=404, detail="Term plan not found")

    section = db.query(Section).filter(Section.id == term_plan.section_id).first()
    location = db.query(Location).filter(Location.id == term_plan.location_id).first()
    meetings = (
        db.query(MeetingPlan)
        .filter(MeetingPlan.term_plan_id == plan_id)
        .order_by(MeetingPlan.week_number)
        .all()
    )

    md = f"""# {term_plan.name}

## Term Plan Details
- **Section:** {section.name} Scouts
- **Location:** {location.name if location else "TBD"}
- **Start Date:** {term_plan.start_date}
- **End Date:** {term_plan.end_date}
- **Total Weeks:** {term_plan.total_weeks}

"""

    if term_plan.theme:
        md += f"## Theme\n{term_plan.theme}\n\n"

    if term_plan.notes:
        md += f"## Notes\n{term_plan.notes}\n\n"

    md += "---\n\n# Meeting Schedule\n\n"

    for meeting in meetings:
        md += f"## Week {meeting.week_number}: {meeting.title}\n\n"
        md += f"**Date:** {meeting.meeting_date} | **Duration:** {meeting.duration_minutes} minutes\n\n"

        if meeting.objectives:
            md += "### Objectives\n"
            for obj in meeting.objectives:
                md += f"- {obj}\n"
            md += "\n"

        if meeting.materials_needed:
            md += "### Supplies Needed\n"
            for item in meeting.materials_needed:
                md += f"- {item}\n"
            md += "\n"

        if meeting.generated_plan:
            md += "### Meeting Plan\n"
            md += meeting.generated_plan
            md += "\n\n"

        if meeting.safety_briefing:
            md += "### Safety Notes\n"
            md += meeting.safety_notes + "\n\n"

        md += "---\n\n"

    return Response(
        md,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=term_plan_{plan_id}.md"},
    )


# ============== SOFT DELETE CLEANUP (for cron job) ==============


@app.post("/admin/cleanup-deleted")
def cleanup_deleted_items(db: Session = Depends(get_db)):
    """Permanently delete items that have been soft-deleted for more than 30 days. Call via cron."""
    from datetime import datetime

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    # Find and permanently delete old deleted term plans
    old_term_plans = (
        db.query(TermPlan)
        .filter(TermPlan.deleted_at.isnot(None), TermPlan.deleted_at < thirty_days_ago)
        .all()
    )

    term_plan_count = 0
    for plan in old_term_plans:
        # Delete associated meetings first
        db.query(MeetingPlan).filter(MeetingPlan.term_plan_id == plan.id).delete()
        db.delete(plan)
        term_plan_count += 1

    # Find and permanently delete old deleted meetings
    old_meetings = (
        db.query(MeetingPlan)
        .filter(
            MeetingPlan.deleted_at.isnot(None), MeetingPlan.deleted_at < thirty_days_ago
        )
        .all()
    )

    meeting_count = len(old_meetings)
    for meeting in old_meetings:
        db.delete(meeting)

    db.commit()

    return {
        "status": "cleanup complete",
        "term_plans_permanently_deleted": term_plan_count,
        "meetings_permanently_deleted": meeting_count,
    }
