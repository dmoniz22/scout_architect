# Detailed activity database - to be imported by api.py
# Contains full instructions for games, skills, and activities

ACTIVITY_DETAILS = {
    "Duck Duck Goose": {
        "description": "Classic circle tap-and-chase game",
        "setup": "Sit in circle, one player is 'it'",
        "instructions": [
            "1. 'It' walks around circle tapping heads 'Duck'",
            "2. Eventually taps someone and says 'Goose!'",
            "3. Goose chases 'it' around circle",
            "4. 'It' tries to sit in Goose's spot"
        ],
        "materials": ["Open space"],
        "safety": "Run clockwise only. No pushing.",
        "tips": "Use gentle taps for younger kids"
    },
    "Musical Statues": {
        "description": "Dance and freeze when music stops",
        "instructions": [
            "1. Play music, everyone dances",
            "2. Stop music suddenly",
            "3. Everyone freeze like statues",
            "4. Anyone moving is out"
        ],
        "materials": ["Music player"],
        "safety": "Clear area of hazards"
    },
    "Capture the Flag": {
        "description": "Teams try to steal opponent's flag",
        "instructions": [
            "1. Split into two teams with territories",
            "2. Each team has a flag at their base",
            "3. Players cross into enemy territory to capture flag",
            "4. If tagged in enemy territory, go to jail",
            "5. Teammates can free jail by touching",
            "6. First team to capture opponent's flag wins"
        ],
        "materials": ["Two flags", "Boundary markers"],
        "safety": "Two-hand touch only, no tackling"
    },
    "Nature Scavenger Hunt": {
        "description": "Find natural items on a list",
        "instructions": [
            "1. Give each team a list of items to find",
            "2. Items: pinecone, leaf, rock, feather, etc.",
            "3. Set boundaries and time limit",
            "4. Teams explore to find items",
            "5. Return when time expires",
            "6. Most items found wins"
        ],
        "materials": ["Scavenger hunt lists", "Bags", "Pencils"],
        "safety": "Stay in boundaries. Look don't touch unknown plants."
    },
    "Knot Tying": {
        "description": "Learn essential Scout knots",
        "instructions": [
            "1. Square Knot: Right over left, left over right",
            "2. Bowline: Make loop, rabbit up hole, around tree, back down",
            "3. Clove Hitch: Two half-hitches around post",
            "4. Practice each knot 5 times",
            "5. Test by having partner check your knot",
            "6. Teach a partner your best knot"
        ],
        "materials": ["Rope (5ft per Scout)", "Knot tying boards/trees"],
        "safety": "Check all ropes for fraying. No rope around necks."
    },
    "Shelter Building": {
        "description": "Build emergency shelters using natural materials",
        "instructions": [
            "1. Find a natural hollow or clearing",
            "2. Collect branches and sticks",
            "3. Create A-frame ribs leaning against ridge pole",
            "4. Add horizontal branches between ribs",
            "5. Layer leaves and debris for waterproofing",
            "6. Test: Can it keep you dry? Is it off ground?",
            "7. Disassemble and return materials to forest"
        ],
        "materials": ["Optional: Tarp/groundsheet", "No tools needed"],
        "safety": "Check for widowmakers above. Watch for insects/ant nests."
    }
}

GAME_TEMPLATES = [
    "Duck Duck Goose", "Musical Statues", "Capture the Flag",
    "Predator vs Prey", "Hospital Tag", "Relay Races"
]

SKILL_TEMPLATES = [
    "Nature Scavenger Hunt", "Knot Tying", "Flag Ceremony",
    "Shelter Building", "First Aid Basics", "Map Reading"
]

FOCUS_TEMPLATES = [
    "Team Building Challenge", "Nature Hike", "Service Project",
    "Cooking Demonstration", "Compass Activity", "Safety Drill"
]

SECTION_ACTIVITIES = {
    "Beaver": {
        "games": GAME_TEMPLATES[:3],
        "skills": SKILL_TEMPLATES[:3],
        "focus": FOCUS_TEMPLATES[:3]
    },
    "Cub": {
        "games": GAME_TEMPLATES[:4],
        "skills": SKILL_TEMPLATES[:4],
        "focus": FOCUS_TEMPLATES[:4]
    },
    "Scout": {
        "games": GAME_TEMPLATES,
        "skills": SKILL_TEMPLATES,
        "focus": FOCUS_TEMPLATES
    },
    "Venturer": {
        "games": GAME_TEMPLATES[2:],
        "skills": SKILL_TEMPLATES[2:],
        "focus": FOCUS_TEMPLATES[2:]
    }
}
