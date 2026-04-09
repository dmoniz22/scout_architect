"""
Improved OAS PDF Parser v2
Parses Outdoor Adventure Skills badge PDFs with proper level extraction.
"""
import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
import PyPDF2


@dataclass
class OASRequirement:
    """Single requirement/competency"""
    requirement_number: str  # e.g., "1.1", "2.5"
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
    prerequisites: List[str]


class OASPDFParserV2:
    def __init__(self, pdf_dir: str = "badge_data/OAS"):
        self.pdf_dir = Path(pdf_dir)
        self.skills: List[OASSkill] = []
    
    def parse_all_pdfs(self) -> List[OASSkill]:
        """Parse all OAS PDF files"""
        if not self.pdf_dir.exists():
            raise FileNotFoundError(f"PDF directory not found: {self.pdf_dir}")
        
        pdf_files = sorted(self.pdf_dir.glob("*.pdf"))
        # Filter out duplicates (Trail Skills (2).pdf is preferred over Trail Skills.pdf)
        unique_files = []
        seen_names = set()
        for pdf in reversed(pdf_files):  # Process newer files first
            base = pdf.stem.replace(" (2)", "").replace(" Skills", "").replace(" Skill", "")
            if base not in seen_names:
                unique_files.insert(0, pdf)
                seen_names.add(base)
        
        print(f"Found {len(unique_files)} unique PDF files")
        
        for pdf_file in unique_files:
            print(f"Parsing: {pdf_file.name}")
            try:
                skill = self.parse_single_pdf(pdf_file)
                if skill and skill.levels:
                    self.skills.append(skill)
                    print(f"  -> Extracted {len(skill.levels)} levels")
            except Exception as e:
                print(f"  ERROR: {e}")
        
        return self.skills
    
    def parse_single_pdf(self, pdf_path: Path) -> Optional[OASSkill]:
        """Parse a single OAS PDF"""
        # Extract skill name from filename
        skill_name = pdf_path.stem.replace(" (2)", "").replace(" Skills", "").replace(" Skill", "").strip()
        category = f"{skill_name} Skills"
        
        # Extract text from all pages
        pages_text = self._extract_text_from_pdf(pdf_path)
        if not pages_text:
            return None
        
        # Group competencies by level
        levels_data = self._group_by_level(pages_text)
        
        if not levels_data:
            return None
        
        # Create level objects
        levels = []
        for level_num in sorted(levels_data.keys()):
            reqs = levels_data[level_num]
            levels.append(OASLevel(
                level_number=level_num,
                requirements=reqs
            ))
        
        return OASSkill(
            skill_name=skill_name,
            category=category,
            levels=levels,
            prerequisites=[]  # Will be inferred from "d." patterns if present
        )
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> List[str]:
        """Extract text from each page of PDF"""
        pages = []
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        pages.append(text)
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return pages
    
    def _group_by_level(self, pages_text: List[str]) -> Dict[int, List[OASRequirement]]:
        """Group competencies by their level number"""
        levels: Dict[int, List[OASRequirement]] = {}
        
        for page_text in pages_text:
            # Clean up the text
            text = self._clean_text(page_text)
            
            # Find all competencies: number like "1.1", "2.3", "3.15"
            # Pattern: digit.digit+ followed by description
            pattern = r'(?:(\d+)\.(\d+))\s+([^.]+?)(?=\d+\.\d+|$)'
            matches = re.findall(pattern, text, re.DOTALL)
            
            for level_str, item_str, desc in matches:
                level_num = int(level_str)
                item_num = f"{level_str}.{item_str}"
                
                # Clean up description
                desc_clean = self._clean_description(desc)
                if len(desc_clean) < 5:  # Too short, probably noise
                    continue
                
                if level_num not in levels:
                    levels[level_num] = []
                
                levels[level_num].append(OASRequirement(
                    requirement_number=item_num,
                    description=desc_clean
                ))
        
        return levels
    
    def _clean_text(self, text: str) -> str:
        """Remove headers, footers, and other noise"""
        # Remove common headers/footers
        lines = text.split('\n')
        cleaned = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines
            if not line:
                continue
            # Skip header/footer patterns
            if any(skip in line for skip in [
                "OUTDOOR ADVENTURE SKILLS",
                "Canadianpath.ca",
                "Competencies",
                "Aquatic Skills",
                "Camping Skills",
                "Emergency Skill",
                "Paddling Skills",
                "Sailing skills",
                "Scoutcraft Skill", 
                "Trail Skills",
                "Vertical Skills",
                "Winter Skills"
            ]):
                continue
            # Skip page numbers at end of line
            if re.match(r'^\d+$', line):
                continue
            cleaned.append(line)
        
        return '\n'.join(cleaned)
    
    def _clean_description(self, desc: str) -> str:
        """Clean up requirement description"""
        # Remove newlines and extra spaces
        desc = ' '.join(desc.split())
        # Remove trailing page numbers
        desc = re.sub(r'\s+\d+$', '', desc)
        # Remove trailing punctuation that shouldn't be there
        desc = desc.strip()
        return desc
    
    def save_to_json(self, output_path: str = "data/oas_skills_v2.json"):
        """Save parsed skills to JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        skills_dict = [asdict(skill) for skill in self.skills]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(skills_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved {len(self.skills)} skills to {output_file}")
    
    def print_summary(self):
        """Print summary of parsed data"""
        print(f"\n{'='*50}")
        print(f"PARSED {len(self.skills)} OAS SKILLS")
        print(f"{'='*50}")
        
        for skill in self.skills:
            print(f"\n{skill.skill_name}")
            for level in skill.levels:
                print(f"  Level {level.level_number}: {len(level.requirements)} requirements")
                # Show first 2 requirements as sample
                for req in level.requirements[:2]:
                    short_desc = req.description[:60] + "..." if len(req.description) > 60 else req.description
                    print(f"    {req.requirement_number}: {short_desc}")


def main():
    """Run the parser"""
    parser = OASPDFParserV2(pdf_dir="badge_data/OAS")
    parser.parse_all_pdfs()
    parser.print_summary()
    parser.save_to_json("data/oas_skills_v2.json")


if __name__ == "__main__":
    main()