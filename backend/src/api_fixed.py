""" FastAPI backend for Scout Leader Lesson Architect """
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import List, Optional
import json
import random

from src.database import get_db, init_db
from src.models import (
    Section, Badge, OASSkill, Activity, Location, TermPlan, MeetingPlan,
    SafetyProtocol, UserPreference,
    LocationCreate, TermPlanCreate, MeetingPlanCreate, MeetingPlanGenerate
)

app = FastAPI(title="Scout Leader Lesson Architect", version="0.1.0")


@app.on_event("startup")
def startup():
    """Initialize database on startup"""
    try:
        init_db()
        print("Database initialized")
    except Exception as e:
        print(f"Database init error (may already exist): {e}")


# ============== SECTIONS ==============
@app.get("/sections")
def get_sections(db: Session = Depends(get_db)):
    return db.query(Section).all()


@app.get("/sections/{section_id}")
def get_section(section_id: int, db: Session = Depends(get_db)):
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section


# ============== BADGES ==============
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


# ============== OAS SKILLS ==============
@app.get("/oas-skills")
def get_oas_skills(section_id: Optional[int] = None, category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(OASSkill)
    if section_id:
        query = query.filter(OASSkill.section_id == section_id)
    if category:
        query = query.filter(OASSkill.category == category)
    return query.all()


# ============== LOCATIONS ==============
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


# ============== TERM PLANS ==============
@app.get("/term-plans")
def get_term_plans(status: Optional[str] = None, section_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(TermPlan)
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
def delete_term_plan(plan_id: int, db: Session = Depends(get_db)):
    db_plan = db.query(TermPlan).filter(TermPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Term plan not found")
    db.delete(db_plan)
    db.commit()
    return {"status": "deleted"}


# ============== MEETING PLANS ==============
@app.get("/term-plans/{plan_id}/meetings")
def get_meetings(plan_id: int, db: Session = Depends(get_db)):
    return db.query(MeetingPlan).filter(MeetingPlan.term_plan_id == plan_id).order_by(MeetingPlan.week_number).all()


@app.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(MeetingPlan).filter(MeetingPlan.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


@app.post("/meetings")
def create_meeting(meeting: MeetingPlanCreate, db: Session = Depends(get_db)):
    db_meeting = MeetingPlan(**meeting.dict())
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting


# ============== DETAILED ACTIVITY DATABASE ==============

ACTIVITY_DETAILS = {
    # GAMES WITH FULL INSTRUCTIONS
    "Duck Duck Goose": {
        "description": "Classic circle game where one player walks around tapping others 'duck' until saying 'goose', triggering a chase.",
        "setup": "All players sit in a tight circle facing inward. Choose one player to be 'it'.",
        "instructions": [
            "1. The 'it' player walks around the outside of the circle",
            "2. They tap each player's head saying 'Duck, duck, duck...'",
            "3. When they tap someone and say 'Goose!', that player must stand up immediately",
            "4. The Goose chases 'it' around the circle",
            "5. 'It' tries to sit in the Goose's empty spot before being tagged",
