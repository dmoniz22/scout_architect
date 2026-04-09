"""
Parser for Outdoor Adventure Skills (OAS) badge PDFs from Scouts Canada.
Extracts skill requirements for each level (1-4 or 1-5) from PDF documents.
"""
import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional
import PyPDF2


@dataclass
class OASRequirement:
    """Single requirement for an OAS skill level"""
    requirement_number: str
    description: str


@dataclass
class OASLevel:
    """A single level of an OAS skill (e.g., Level 1, Level 2, etc.)"""
    level_number: int
    requirements: List[OASRequirement]
    notes: Optional[str] = None


@dataclass
class OASSkill:
    """Complete OAS skill with all levels"""
    skill_name: str
    category: str
    description: Optional[str]
    levels: List[OASLevel]
    prerequisites: List[str]


class OASPDFParser:
    """Parser for OAS badge PDF documents"""

    def __init__(self, pdf_dir: str = "badge_data/OAS"):
        self.pdf_dir = Path(pdf_dir)
        self.skills: List[OASSkill] = []

    def parse_all_pdfs(self) -> List[OASSkill]:
        """Parse all OAS PDF files in the directory"""
        if not self.pdf_dir.exists():
            raise FileNotFoundError(f"PDF directory not found: {self.pdf_dir}")

        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files to parse")

        for pdf_file in sorted(pdf_files):
            # Skip duplicate Trail Skills files
            if pdf_file.name == "Trail Skills.pdf" and "(2)" in str(pdf_file):
                continue
            print(f"Parsing: {pdf_file.name}")
            try:
                skill = self.parse_single_pdf(pdf_file)
                if skill:
                    self.skills.append(skill)
            except Exception as e:
                print(f"Error parsing {pdf_file.name}: {e}")

        return self.skills

    def parse_single_pdf(self, pdf_path: Path) -> Optional[OASSkill]:
        """Parse a single OAS PDF file"""
        # Extract skill name from filename
        skill_name = pdf_path.stem.replace(" Skills", "").replace(" Skill", "").strip()

        # Map skill categories
        category_mapping = {
            "Aquatic": "Aquatic Skills",
            "Camping": "Camping Skills",
            "Emergency": "Emergency Skills",
            "Paddling": "Paddling Skills",
            "Sailing": "Sailing Skills",
            "Scoutcraft": "Scoutcraft Skills",
            "Trail": "Trail Skills",
            "Vertical": "Vertical Skills",
            "Winter": "Winter Skills",
        }

        category = category_mapping.get(skill_name, skill_name + " Skills")

        # Extract text from PDF
        text = self._extract_text_from_pdf(pdf_path)

        if not text:
            return None

        # Parse levels from the text
        levels = self._parse_levels(text)

        # Extract prerequisites if mentioned
        prerequisites = self._extract_prerequisites(text)

        return OASSkill(
            skill_name=skill_name,
            category=category,
            description=None,
            levels=levels,
            prerequisites=prerequisites
        )

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract all text from a PDF file"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
        return text

    def _parse_levels(self, text: str) -> List[OASLevel]:
        """Parse OAS levels from PDF text"""
        levels = []

        # Try to find Level headers (e.g., "Level 1", "Level 2", etc.)
        level_pattern = r'Level\s+(\d+)\s*[:\-]?\s*(.*?)(?=Level\s+\d+|$)'
        level_matches = list(re.finditer(level_pattern, text, re.DOTALL | re.IGNORECASE))

        if level_matches:
            for match in level_matches:
                level_num = int(match.group(1))
                level_content = match.group(2).strip()

                # Parse requirements from this level's content
                requirements = self._parse_requirements(level_content)

                levels.append(OASLevel(
                    level_number=level_num,
                    requirements=requirements,
                    notes=None
                ))

        # If no levels found, try alternative patterns
        if not levels:
            # Try to find numbered sections
            alt_pattern = r'(?:^|\n)\s*\(?\s*(\d+)\s*\)?[\.\)]?\s+(.+?)(?=(?:\n\s*(?:^|\n)\s*\(?\s*\d+\s*\)?[\.\)]?\s+|$))'
            matches = re.findall(alt_pattern, text, re.MULTILINE | re.DOTALL)

            if matches:
                requirements = []
                for num, desc in matches[:10]:  # Limit to first 10 items
                    requirements.append(OASRequirement(
                        requirement_number=str(num),
                        description=desc.strip().replace('\n', ' ')
                    ))

                if requirements:
                    levels.append(OASLevel(
                        level_number=1,
                        requirements=requirements,
                        notes="General requirements"
                    ))

        return levels

    def _parse_requirements(self, level_text: str) -> List[OASRequirement]:
        """Parse individual requirements from level text"""
        requirements = []

        # Look for numbered requirements (e.g., "1.", "2." or "I.", "II.")
        req_patterns = [
            r'(?:^|\n)\s*(\d+[\.\)]\s*[^\n]+)',  # 1. or 1)
            r'(?:^|\n)\s*([IVX]+[\.\)\:]?\s*[^\n]+)',  # I. or II.
            r'(?:^|\n)\s*([a-z]\)[^\n]+)',  # a) or b)
        ]

        for pattern in req_patterns:
            matches = re.findall(pattern, level_text, re.MULTILINE)
            if matches:
                for match in matches:
                    # Extract requirement number and description
                    clean_match = match.strip()
                    # Try to separate number from text
                    parts = re.split(r'\s+', clean_match, 1)
                    if len(parts) == 2:
                        req_num, desc = parts
                    else:
                        req_num = "?"
                        desc = clean_match

                    requirements.append(OASRequirement(
                        requirement_number=req_num.rstrip('.'),
                        description=desc.strip()
                    ))

        # Remove duplicates while preserving order
        seen = set()
        unique_reqs = []
        for req in requirements:
            key = (req.requirement_number, req.description)
            if key not in seen:
                seen.add(key)
                unique_reqs.append(req)

        return unique_reqs

    def _extract_prerequisites(self, text: str) -> List[str]:
        """Extract prerequisite mentions from text"""
        prerequisites = []

        # Look for prerequisite mentions
        prereq_patterns = [
            r'[Pp]rerequisite[s]?:?\s*([^\n]+)',
            r'[Rr]equire[s]?\s*:?\s*([^\n]+(?:Level\s*\d+[^\n]+)?)',
        ]

        for pattern in prereq_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) < 200:  # Avoid capturing too much
                    prerequisites.append(match.strip())

        return prerequisites

    def save_to_json(self, output_path: str = "data/oas_skills.json"):
        """Save parsed skills to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        skills_dict = [asdict(skill) for skill in self.skills]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(skills_dict, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(self.skills)} skills to {output_file}")

    def populate_database(self):
        """Populate the database with parsed skills"""
        from sqlalchemy.orm import Session
        from src.database import engine
        from src.models import Section, OASSkill

        with Session(engine) as session:
            # Get or create sections
            sections = {}
            section_data = {
                "Beavers": (5, 7),
                "Cubs": (8, 10),
                "Scouts": (11, 14),
                "Venturers": (15, 17),
            }

            for name, (min_age, max_age) in section_data.items():
                section = session.query(Section).filter_by(name=name).first()
                if not section:
                    section = Section(
                        name=name,
                        min_age=min_age,
                        max_age=max_age,
                        description=f"{name} section"
                    )
                    session.add(section)
                    session.flush()
                sections[name] = section

            # Add OAS skills
            for skill in self.skills:
                # Determine target section based on skill difficulty
                target_sections = []
                if skill.category in ["Scoutcraft Skills", "Trail Skills"]:
                    target_sections = ["Cubs", "Scouts", "Venturers"]
                elif skill.category in ["Camping Skills", "Emergency Skills"]:
                    target_sections = ["Scouts", "Venturers"]
                elif skill.category in ["Vertical Skills", "Winter Skills", "Sailing Skills"]:
                    target_sections = ["Scouts", "Venturers"]
                else:
                    target_sections = ["Scouts", "Venturers"]

                for section_name in target_sections:
                    section = sections[section_name]

                    # Create separate records for each level
                    for level in skill.levels:
                        level_key = f"{skill.skill_name}_L{level.level_number}"

                        # Check if this skill already exists
                        existing = session.query(OASSkill).filter_by(
                            skill_name=level_key,
                            section_id=section.id
                        ).first()

                        if not existing:
                            # Combine requirements into description
                            req_text = "\n".join([
                                f"{r.requirement_number}. {r.description}"
                                for r in level.requirements
                            ])

                            oas_skill = OASSkill(
                                section_id=section.id,
                                category=skill.category,
                                skill_name=level_key,
                                level1_desc=req_text,
                                prerequisites=skill.prerequisites if skill.prerequisites else []
                            )
                            session.add(oas_skill)

            session.commit()
            print(f"Database populated with OAS skills")


def main():
    """Run the OAS PDF parser"""
    parser = OASPDFParser(pdf_dir="badge_data/OAS")
    skills = parser.parse_all_pdfs()

    if skills:
        parser.save_to_json(output_path="data/oas_skills.json")
        parser.populate_database()
    else:
        print("No skills were parsed")


if __name__ == "__main__":
    main()