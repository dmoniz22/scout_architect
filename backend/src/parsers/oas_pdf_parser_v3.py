"""
OAS PDF Parser v3 - Clean level extraction
Parse Outdoor Adventure Skills badge PDFs with proper structure.
"""
import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
import PyPDF2


@dataclass
class OASRequirement:
    """Single competency requirement"""
    requirement_number: str  # "1.1", "2.5", etc.
    description: str


@dataclass
class OASLevel:
    """A level of an OAS skill"""
    level_number: int
    requirements: List[OASRequirement]


@dataclass
class OASSkill:
    """Complete OAS skill"""
    skill_name: str
    category: str
    levels: List[OASLevel]


class OASPDFParserV3:
    """Improved parser with proper level grouping"""

    def __init__(self, pdf_dir: str = "badge_data/OAS"):
        self.pdf_dir = Path(pdf_dir)
        self.skills: List[OASSkill] = []

    def parse_all_pdfs(self) -> List[OASSkill]:
        """Parse all OAS PDF files"""
        if not self.pdf_dir.exists():
            raise FileNotFoundError(f"PDF directory not found: {self.pdf_dir}")

        # Get PDFs, preferring " (2)" versions (likely newer)
        pdf_files = sorted(self.pdf_dir.glob("*.pdf"))
        unique_files = []
        seen = set()

        for pdf in reversed(pdf_files):
            base = pdf.stem.replace(" (2)", "").replace(" Skills", "").replace(" Skill", "")
            if base not in seen:
                unique_files.insert(0, pdf)
                seen.add(base)

        print(f"Found {len(unique_files)} unique PDF files")

        for pdf_file in unique_files:
            print(f"\nParsing: {pdf_file.name}")
            try:
                skill = self.parse_single_pdf(pdf_file)
                if skill and skill.levels:
                    self.skills.append(skill)
                    print(f"  ✓ Extracted {len(skill.levels)} levels")
                    for lvl in skill.levels:
                        print(f"    Level {lvl.level_number}: {len(lvl.requirements)} requirements")
            except Exception as e:
                print(f"  ✗ Error: {e}")

        return self.skills

    def parse_single_pdf(self, pdf_path: Path) -> Optional[OASSkill]:
        """Parse a single OAS PDF file"""
        skill_name = pdf_path.stem.replace(" (2)", "").replace(" Skills", "").replace(" Skill", "").strip()
        category = f"{skill_name} Skills"

        # Extract all text from PDF
        all_text = self._extract_text(pdf_path)
        if not all_text:
            return None

        # Clean the text
        cleaned_text = self._clean_text(all_text)

        # Parse competencies
        competencies = self._parse_competencies(cleaned_text)

        # Group by level
        level_groups = self._group_by_level(competencies)

        # Create level objects
        levels = []
        for level_num in sorted(level_groups.keys()):
            if 1 <= level_num <= 9:  # Valid level numbers
                levels.append(OASLevel(
                    level_number=level_num,
                    requirements=level_groups[level_num]
                ))

        if not levels:
            return None

        return OASSkill(
            skill_name=skill_name,
            category=category,
            levels=levels
        )

    def _extract_text(self, pdf_path: Path) -> str:
        """Extract text from PDF pages"""
        text_parts = []
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return "\n".join(text_parts)

    def _clean_text(self, text: str) -> str:
        """Remove headers, footers, and noise"""
        lines = text.split('\n')
        cleaned = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip header/footer patterns
            skip_patterns = [
                "OUTDOOR ADVENTURE SKILLS",
                "Canadianpath.ca",
                r"^\d+$",  # Standalone page numbers
                r"^CAMPING SKILLS$",
                r"^AQUATIC SKILLS$",
                r"^PADDLING SKILLS$",
                r"^TRAIL SKILLS$",
                r"^VERTICAL SKILLS$",
                r"^WINTER SKILLS$",
                r"^SAILING SKILLS$",
                r"^SCOUTCRAFT SKILLS$",
                r"^EMERGENCY SKILLS$",
                r"Competencies$",
                r"Requirements \(cont'd\)",
            ]

            should_skip = any(re.search(pattern, line, re.IGNORECASE) for pattern in skip_patterns)
            if should_skip:
                continue

            cleaned.append(line)

        return "\n".join(cleaned)

    def _parse_competencies(self, text: str) -> List[OASRequirement]:
        """Extract all X.Y competency patterns from text"""
        competencies = []

        # Pattern: number.number followed by description
        # Allow multi-line descriptions that end with next competency or specific markers
        pattern = r'(\d+)\.(\d+)\s+([^\n]*(?:\n(?!(?:\d+\.\d+|[A-Z][a-z]+ Skills|Competencies|Canadianpath))[^\n]*)*)'

        matches = re.finditer(pattern, text, re.MULTILINE)

        for match in matches:
            level_num = match.group(1)
            item_num = match.group(2)
            desc = match.group(3)

            # Clean description
            desc = self._clean_description(desc)

            if len(desc) > 10:  # Meaningful description
                competencies.append(OASRequirement(
                    requirement_number=f"{level_num}.{item_num}",
                    description=desc
                ))

        return competencies

    def _clean_description(self, desc: str) -> str:
        """Clean requirement description"""
        # Remove trailing page numbers
        desc = re.sub(r'\s+\d+$', '', desc.strip())
        # Remove "Requirements (cont'd)" and similar
        desc = re.sub(r'Requirements?\s*\(cont.*?\)', '', desc, flags=re.IGNORECASE)
        # Replace multiple spaces/newlines with single space
        desc = ' '.join(desc.split())
        return desc.strip()

    def _group_by_level(self, competencies: List[OASRequirement]) -> Dict[int, List[OASRequirement]]:
        """Group competencies by their level number (first digit)"""
        levels: Dict[int, List[OASRequirement]] = {}

        for comp in competencies:
            # Parse level from requirement_number like "1.5", "2.3", etc.
            match = re.match(r'^(\d+)\.', comp.requirement_number)
            if match:
                level_num = int(match.group(1))
                if level_num not in levels:
                    levels[level_num] = []
                levels[level_num].append(comp)

        return levels

    def save_to_json(self, output_path: str = "data/oas_skills_v3.json"):
        """Save parsed skills to JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        skills_dict = [asdict(skill) for skill in self.skills]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(skills_dict, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved {len(self.skills)} skills to {output_file}")

    def print_summary(self):
        """Print summary of parsed data"""
        print(f"\n{'='*60}")
