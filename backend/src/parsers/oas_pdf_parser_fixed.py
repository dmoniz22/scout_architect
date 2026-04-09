"""OAS PDF Parser - Fixed Version Parses Outdoor Adventure Skills badge PDFs with proper cleaning and deduplication."""
import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Set
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


class OASPDFParserFixed:
    """Fixed parser with proper cleaning and deduplication"""
    
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
                    total_reqs = sum(len(l.requirements) for l in skill.levels)
                    print(f" ✓ Extracted {len(skill.levels)} levels, {total_reqs} total requirements")
            except Exception as e:
                print(f" ✗ Error: {e}")
        
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
        
        # Group by level and deduplicate
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
                r"^OUTDOOR ADVENTURE SKILLS",
                r"^Canadianpath\.ca",
                r"^\d+$",  # Standalone page numbers
                r"^(CAMPING|AQUATIC|PADDLING|TRAIL|VERTICAL|WINTER|SAILING|SCOUTCRAFT|EMERGENCY)\s+SKILLS$",
                r"^Competencies$",
                r"^Requirements?\s*\(cont'd?\)",
                r"^Requirements?\s*\(cont'd?\)\d*$",
            ]
            
            should_skip = any(re.search(pattern, line, re.IGNORECASE) for pattern in skip_patterns)
            if should_skip:
                continue
            
            cleaned.append(line)
        
        return "\n".join(cleaned)
    
    def _parse_competencies(self, text: str) -> List[OASRequirement]:
        """Extract all X.Y competency patterns from text"""
        competencies = []
        seen: Set[tuple] = set()
        
        # Pattern: number.number followed by description
        # Format: "1.1 I can..." or "1.2 I have..." etc.
        # The description continues until the next X.Y pattern
        pattern = r'(\d+)\.(\d+)\s+([^.].*?)(?=(?:\d+\.\d+\s+[A-Z])|$)'
        
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            level_num = match.group(1)
            item_num = match.group(2)
            desc = match.group(3)
            
            # Clean description
            desc = self._clean_description(desc)
            
            # Skip if too short or looks like garbage
            if len(desc) < 10 or len(desc) > 500:
                continue
            
            req_key = (level_num, item_num)
            
            # Skip exact duplicates
            if req_key in seen:
                # Keep the shorter, cleaner version
                continue
            
            seen.add(req_key)
            
            competencies.append(OASRequirement(
                requirement_number=f"{level_num}.{item_num}",
                description=desc
            ))
        
        return competencies
    
    def _clean_description(self, desc: str) -> str:
        """Clean requirement description"""
        # Remove trailing page numbers
        desc = re.sub(r'\s+\d+$', '', desc.strip())
        
        # Remove "Requirements (cont'd)" and similar artifacts
        desc = re.sub(r'Requirements?\s*\(cont[^)]*\)', '', desc, flags=re.IGNORECASE)
        
        # Remove "AQUATIC SKILLS", "CAMPING SKILLS", etc. that appear in descriptions
        desc = re.sub(r'\s*(?:AQUATIC|CAMPING|PADDLING|TRAIL|VERTICAL|WINTER|SAILING|SCOUTCRAFT|EMERGENCY)\s+SKILLS', '', desc, flags=re.IGNORECASE)
        
        # Remove trailing "Scouts can..." explanations at the end
        desc = re.sub(r'\.\s*Scouts?\s+(?:can|demonstrate).*$', '.', desc, flags=re.IGNORECASE)
        
        # Remove standalone "Scouts can..." lines
        desc = re.sub(r'\s+Scouts?\s+(?:can|demonstrate)\s+.*$', '', desc, flags=re.IGNORECASE)
        
        # Clean up multiple spaces
        desc = ' '.join(desc.split())
        
        # Ensure it ends with proper punctuation
        if desc and desc[-1] not in '.!?':
            desc += '.'
        
        return desc.strip()
    
    def _group_by_level(self, competencies: List[OASRequirement]) -> Dict[int, List[OASRequirement]]:
        """Group competencies by their level number and deduplicate descriptions"""
        levels: Dict[int, List[OASRequirement]] = {}
        seen_desc: Dict[int, Set[str]] = {}
        
        for comp in competencies:
            # Parse level from requirement_number like "1.5", "21.3", etc.
            match = re.match(r'^(\d+)\.', comp.requirement_number)
            if match:
                level_num = int(match.group(1))
                
                # Normalize level number (handle cases like 21 -> 1, 22 -> 2, etc.)
                if level_num > 9:
                    level_num = level_num % 10
                    if level_num == 0:
                        level_num = 10  # Handle 10, 20, 30...
                
                # Initialize seen_desc for this level if needed
                if level_num not in seen_desc:
                    seen_desc[level_num] = set()
                
                # Check for duplicate/similar descriptions
                desc_key = comp.description.lower()[:50]  # First 50 chars for comparison
                
                if desc_key in seen_desc[level_num]:
                    continue
                
                seen_desc[level_num].add(desc_key)
                
                # Update the requirement number to use normalized level
                parts = comp.requirement_number.split('.')
                if len(parts) == 2:
                    comp.requirement_number = f"{level_num}.{parts[1]}"
                
                if level_num not in levels:
                    levels[level_num] = []
                
                levels[level_num].append(comp)
        
        # Sort requirements within each level by requirement number
        for level_num in levels:
            levels[level_num].sort(key=lambda x: x.requirement_number)
        
        return levels
    
    def save_to_json(self, output_path: str = "data/oas_skills_fixed.json"):
        """Save parsed skills to JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        skills_dict = [asdict(skill) for skill in self.skills]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(skills_dict, f, indent=2, ensure_ascii=False)
        
        total_reqs = sum(sum(len(l.requirements) for l in s.levels) for s in self.skills)
        print(f"\n{'='*60}")
        print(f"✓ Saved {len(self.skills)} skills to {output_file}")
        print(f"✓ Total requirements: {total_reqs}")
        print(f"{'='*60}")
    
    def print_summary(self):
        """Print summary of parsed data"""
        print(f"\n{'='*60}")
        print(f"PARSED {len(self.skills)} OAS SKILLS")
        print(f"{'='*60}")
        
        for skill in self.skills:
            total_reqs = sum(len(l.requirements) for l in skill.levels)
            print(f"\n{skill.skill_name}: {len(skill.levels)} levels, {total_reqs} requirements")


def main():
    """Run the parser"""
    parser = OASPDFParserFixed(pdf_dir="badge_data/OAS")
    parser.parse_all_pdfs()
    parser.print_summary()
    parser.save_to_json("data/oas_skills_fixed.json")


if __name__ == "__main__":
    main()