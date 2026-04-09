""" Scout Leader Lesson Architect - Streamlit Dashboard """
import streamlit as st
import requests
from datetime import datetime, timedelta

# Configure page
st.set_page_config(page_title="Scout Leader Lesson Architect", page_icon="🏕️", layout="wide")

# API Configuration
import os
API_URL = os.getenv("API_URL", "http://localhost:8002")
# External URL for browser-accessible links (PDF downloads)
EXTERNAL_API_URL = os.getenv("EXTERNAL_API_URL", "http://localhost:8002")

if 'current_term_plan' not in st.session_state:
    st.session_state.current_term_plan = None
if 'generated_meeting' not in st.session_state:
    st.session_state.generated_meeting = None

def api_get(endpoint: str):
    try:
        response = requests.get(f"{API_URL}{endpoint}", timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        return None

def api_post(endpoint: str, data: dict):
    try:
        response = requests.post(f"{API_URL}{endpoint}", json=data, timeout=30)
        return response.json() if response.status_code in [200, 201] else None
    except Exception as e:
        return None

def main():
    st.title("Scout Leader Lesson Architect")
    st.markdown("*Plan meetings, build terms, create memories*")
    
    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Select Mode:", ["Single Meeting", "Term Planner", "My Term Plans", "Settings"])
    
    if "Single Meeting" in page:
        single_meeting_page()
    elif "Term Planner" in page:
        term_planner_page()
    elif "My Term Plans" in page:
        my_terms_page()
    else:
        settings_page()

def single_meeting_page():
    st.header("Single Meeting Planner")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Meeting Details")
        section_choice = st.selectbox("Age Group:", 
            [("Beaver (5-7)", 1), ("Cub (8-10)", 2), ("Scout (11-14)", 3), ("Venturer (15-17)", 4)],
            format_func=lambda x: x[0])
        meeting_date = st.date_input("Meeting Date:", value=datetime.now())
        duration = st.slider("Duration (minutes):", 60, 180, 90, 15)
    with col2:
        st.subheader("Quick Info")
        st.info("Weather for Chilliwack, BC\n\nHigh: 12C")
        if st.button("Generate Meeting Plan", type="primary", use_container_width=True):
            st.success("Meeting plan generated!")

def term_planner_page():
    st.header("Term Planner")
    sections = api_get("/sections") or []
    badges = api_get("/badges") or []
    oas_skills = api_get("/oas-skills") or []
    locations = api_get("/locations") or []
    
    tab1, tab2 = st.tabs(["Create New Term Plan", "Quick Add Meeting"])
    
    with tab1:
        with st.form("term_plan_form"):
            term_name = st.text_input("Term Plan Name", placeholder="e.g., Fall 2026")
            section_options = [(s['id'], s['name']) for s in sections]
            section_choice = st.selectbox("Scout Section", options=section_options, 
                format_func=lambda x: x[1])
            location_options = [(loc['id'], loc['name']) for loc in locations]
            if not location_options:
                location_options = [(1, "Chilliwack")]
            location_choice = st.selectbox("Location", options=location_options,
                format_func=lambda x: x[1])
            start_date = st.date_input("Term Start Date", value=datetime.now())
            end_date = st.date_input("Term End Date", value=datetime.now() + timedelta(weeks=10))
            term_theme = st.text_input("Term Theme (optional)")
            duration = st.slider("Meeting Duration (minutes)", 60, 180, 90, 15)
            badge_options = {b['id']: b['badge_name'] for b in badges}
            focus_badges = st.multiselect("Focus Badges", options=list(badge_options.keys()),
                format_func=lambda x: badge_options.get(x, f"Badge {x}"))
            skill_options = {s['id']: f"{s['category']} - {s['skill_name']}" for s in oas_skills}
            focus_skills = st.multiselect("Focus OAS Skills", options=list(skill_options.keys()),
                format_func=lambda x: skill_options.get(x, f"Skill {x}"))
            
            if start_date and end_date:
                total_weeks = (end_date - start_date).days // 7
                st.markdown(f"**Total weeks: {total_weeks}**")
            
            submitted = st.form_submit_button("Create Term Plan", type="primary")
            if submitted and term_name:
                plan_data = {
                    "name": term_name,
                    "section_id": section_choice[0] if isinstance(section_choice, tuple) else section_choice,
                    "location_id": location_choice[0] if isinstance(location_choice, tuple) else location_choice,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_weeks": total_weeks,
                    "focus_badges": focus_badges,
                    "focus_skills": focus_skills,
                    "theme": term_theme,
                    "notes": ""
                }
                result = api_post("/term-plans", plan_data)
                if result:
                    st.success(f"Term plan '{term_name}' created!")
                    st.session_state.created_term_plan = result
                    
    if hasattr(st.session_state, 'created_term_plan') and st.session_state.created_term_plan:
        plan = st.session_state.created_term_plan
        st.markdown("---")
        st.subheader(f"{plan.get('name', 'Term Plan')}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Section", str(plan.get('section_id')))
        col2.metric("Weeks", plan.get('total_weeks'))
        col3.metric("Status", plan.get('status', 'draft'))
        
        if st.button("Generate All Meeting Plans"):
            with st.spinner("Generating..."):
                result = api_post(f"/term-plans/{plan['id']}/generate-meetings", {})
                if result:
                    st.success(f"Generated {result.get('meetings_generated', 0)} meetings!")
                else:
                    st.error("Failed to generate")

def my_terms_page():
    st.header("My Term Plans")
    term_plans = api_get("/term-plans") or []
    if not term_plans:
        st.warning("No term plans yet. Create one first!")
        return
    
    st.markdown(f"**{len(term_plans)} term plan(s) found**")
    
    for plan in term_plans:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{plan.get('name', 'Untitled')}")
                st.markdown(f"{plan.get('start_date', '')} to {plan.get('end_date', '')} ({plan.get('total_weeks', 0)} weeks)")
            with col2:
                if st.button(f"View", key=f"view_{plan['id']}"):
                    st.session_state.view_plan_id = plan['id']
        
        if hasattr(st.session_state, 'view_plan_id') and st.session_state.view_plan_id == plan['id']:
            meetings = api_get(f"/term-plans/{plan['id']}/meetings") or []
            st.markdown("---")
            
            # Full term plan download at top level
            term_pdf_url = f"{EXTERNAL_API_URL}/term-plans/{plan['id']}/pdf"
            term_md_url = f"{EXTERNAL_API_URL}/term-plans/{plan['id']}/md"
            st.markdown("### 📋 Download Full Term Plan")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"[📄 PDF]({term_pdf_url})", unsafe_allow_html=True)
            with col2:
                st.markdown(f"[📝 Markdown (editable)]({term_md_url})", unsafe_allow_html=True)
            
            st.subheader(f"Meeting Schedule")
            
            for meeting in sorted(meetings, key=lambda x: x.get('week_number', 0)):
                with st.expander(f"Week {meeting.get('week_number')}: {meeting.get('title', 'Meeting')}"):
                    st.markdown(f"**Date:** {meeting.get('meeting_date')}")
                    st.markdown(f"**Duration:** {meeting.get('duration_minutes', 90)} minutes")
                    
                    if meeting.get('generated_plan'):
                        st.markdown("**Status:** Generated")
                        # Download links
                        pdf_url = f"{EXTERNAL_API_URL}/meetings/{meeting['id']}/pdf"
                        md_url = f"{EXTERNAL_API_URL}/meetings/{meeting['id']}/md"
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"[📄 PDF]({pdf_url})", unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"[📝 Markdown]({md_url})", unsafe_allow_html=True)
                    else:
                        st.markdown("**Status:** Not Generated")
                        if st.button(f"Generate Now", key=f"gen_{meeting['id']}"):
                            with st.spinner("Generating..."):
                                result = api_post(f"/meetings/{meeting['id']}/generate", {})
                                if result:
                                    st.success("Generated!")
                                    st.rerun()
            
            if st.button("Close View"):
                st.session_state.pop('view_plan_id', None)

def settings_page():
    st.header("Settings")
    st.info("Application settings coming soon!")

if __name__ == "__main__":
    main()
