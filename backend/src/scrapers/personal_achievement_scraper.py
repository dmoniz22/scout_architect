"""
Scraper for Personal Achievement Badges from Scouts Canada Canadian Path.
Extracts badge requirements, descriptions, and images for Beavers, Cubs, Scouts, Venturers.
"""
import re
import json
import time
import random
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
import requests
from bs4 import BeautifulSoup


@dataclass
class BadgeRequirement:
    """Single badge requirement"""
    requirement_id: str
    description: str
    is_mandatory: bool = False


@dataclass
class PersonalAchievementBadge:
    """Personal Achievement Badge data"""
    badge_name: str
    section: str  # Beavers, Cubs, Scouts, Venturers
    category: str  # Personal Achievement category
    description: Optional[str]
    requirements: List[BadgeRequirement]
    image_url: Optional[str]
    prerequisites: List[str]
    estimated_duration: Optional[str]  # e.g., "2-3 weeks"


class ScoutsCanadaScraper:
    """Scraper for Scouts Canada Canadian Path badges"""

    BASE_URL = "https://www.scouts.ca"
    CANADIAN_PATH_URL = "https://www.scouts.ca/programs/sections/canadian-path.html"

    # Section URLs for Personal Achievement Badges
    SECTION_URLS = {
        "Beavers": "https://www.scouts.ca/programs/sections/beavers/personal-achievement-badges.html",
        "Cubs": "https://www.scouts.ca/programs/sections/cubs/personal-achievement-badges.html",
        "Scouts": "https://www.scouts.ca/programs/sections/scouts/personal-achievement-badges.html",
        "Venturers": "https://www.scouts.ca/programs/sections/venturers/personal-achievement-badges.html",
    }

    def __init__(self, delay: float = 1.5):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.badges: List[PersonalAchievementBadge] = []

    def scrape_all_badges(self) -> List[PersonalAchievementBadge]:
        """Scrape all Personal Achievement Badges from all sections"""
        print("Starting Personal Achievement Badge scraping...")

        for section, url in self.SECTION_URLS.items():
            print(f"\nScraping {section} badges from: {url}")
            try:
                section_badges = self._scrape_section_badges(section, url)
                self.badges.extend(section_badges)
                print(f"  Found {len(section_badges)} badges for {section}")
            except Exception as e:
                print(f"  Error scraping {section}: {e}")
                import traceback
                traceback.print_exc()

            # Respectful delay between sections
            time.sleep(self.delay + random.uniform(0.5, 1.0))

        print(f"\nTotal badges scraped: {len(self.badges)}")
        return self.badges

    def _scrape_section_badges(self, section: str, url: str) -> List[PersonalAchievementBadge]:
        """Scrape badges for a specific section"""
        badges = []

        response = self._make_request(url)
        if not response:
            return badges

        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for badge cards/containers
        # Scouts.ca typically uses a grid layout with cards
        badge_containers = self._find_badge_containers(soup)

        for container in badge_containers:
            try:
                badge = self._parse_badge_container(section, container)
                if badge:
                    badges.append(badge)
            except Exception as e:
                print(f"  Error parsing badge: {e}")
                continue

        return badges

    def _find_badge_containers(self, soup: BeautifulSoup) -> List:
        """Find badge container elements in the page"""
        containers = []

        # Try multiple selectors that Scouts.ca might use
        selectors = [
            '.badge-card',
            '.achievement-badge',
            '.badge-grid .card',
            '.badge-item',
            '.program-card',
            '.card',
            '.badge',
            'article',
            '[class*="badge"]',
        ]

        for selector in selectors:
            containers = soup.select(selector)
            if containers:
                print(f"  Found {len(containers)} containers using: {selector}")
                break

        return containers

    def _parse_badge_container(self, section: str, container) -> Optional[PersonalAchievementBadge]:
        """Parse a single badge from its container element"""
        # Try to find badge name
        name_selectors = ['h3', 'h4', 'h5', '.badge-title', '.card-title', '.title', 'a']
        badge_name = None
        for selector in name_selectors:
            elem = container.select_one(selector)
            if elem:
                badge_name = elem.get_text(strip=True)
                if badge_name:
                    break

        if not badge_name:
            # Try the container text directly
            badge_name = container.get_text(strip=True)[:50]

        # Clean up the name
        badge_name = re.sub(r'\s+', ' ', badge_name).strip()
        if not badge_name or badge_name.lower() in ['loading', '']:
            return None

        # Extract description
        desc_selectors = ['p', '.description', '.card-text', '.badge-desc']
        description = None
        for selector in desc_selectors:
            elem = container.select_one(selector)
            if elem:
                description = elem.get_text(strip=True)
                if description:
                    break

        # Extract image URL
        image_url = None
        img_selectors = ['img', '.badge-image img', '.card-img-top']
        for selector in img_selectors:
            img = container.select_one(selector)
            if img and img.get('src'):
                image_url = self._resolve_url(img['src'])
                break

        # Look for link to detail page
        detail_url = None
        link = container.find('a', href=True)
        if link:
            detail_url = self._resolve_url(link['href'])

        # Try to get detailed requirements
        requirements = []
        if detail_url:
            try:
                requirements = self._scrape_badge_requirements(detail_url)
            except Exception as e:
                print(f"    Could not fetch requirements for {badge_name}: {e}")

        # If no requirements found, create a placeholder
        if not requirements:
            requirements = [BadgeRequirement(
                requirement_id="1",
                description="See badge requirements on Scouts Canada website",
                is_mandatory=True
            )]

        # Determine category based on badge name
        category = self._determine_category(badge_name, description)

        return PersonalAchievementBadge(
            badge_name=badge_name,
            section=section,
            category=category,
            description=description,
            requirements=requirements,
            image_url=image_url,
            prerequisites=[],
            estimated_duration=None
        )

    def _scrape_badge_requirements(self, detail_url: str) -> List[BadgeRequirement]:
        """Scrape detailed requirements from a badge detail page"""
        requirements = []

        response = self._make_request(detail_url)
        if not response:
            return requirements

        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for requirements list
        req_patterns = [
            '.requirements li',
            '.badge-requirements li',
            '[class*="requirement"] li',
            '.content li',
            'article ul li',
        ]

        req_found = False
        for pattern in req_patterns:
            req_items = soup.select(pattern)
            if req_items:
                for i, item in enumerate(req_items, 1):
                    text = item.get_text(strip=True)
                    if text and len(text) > 5:
                        # Check if it's marked as optional
                        is_mandatory = 'optional' not in text.lower() and 'choose' not in text.lower()
                        requirements.append(BadgeRequirement(
                            requirement_id=str(i),
                            description=text,
                            is_mandatory=is_mandatory
                        ))
                if requirements:
                    req_found = True
                    break

        # If still no requirements, try to find them in the main content
        if not req_found:
            content = soup.find('article') or soup.find('main') or soup
            if content:
                text = content.get_text()
                # Try to find numbered requirements
                matches = re.findall(r'(\d+[\.\)]\s*)([^\n]+)', text)
                for num, desc in matches[:20]:
                    if len(desc) > 10:
                        requirements.append(BadgeRequirement(
                            requirement_id=num.strip(),
                            description=desc.strip(),
                            is_mandatory=True
                        ))

        return requirements

    def _determine_category(self, name: str, description: Optional[str]) -> str:
        """Determine badge category from name and description"""
        text = f"{name} {description}".lower()

        categories = {
            "Outdoor": ["outdoor", "camp", "hike", "trail", "nature", "environment"],
            "Creative": ["creative", "art", "craft", "music", "perform", "creative"],
            "Service": ["service", "community", "help", "volunteer", "citizen"],
            "Physical": ["physical", "sport", "fitness", "health", "active"],
            "Leadership": ["lead", "leadership", "lead", "team", "guide"],
            "Skills": ["skill", "learn", "technology", "science", "tech"],
        }

        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category

        return "Personal Achievement"

    def _resolve_url(self, url: str) -> str:
        """Resolve relative URLs to absolute URLs"""
        if not url:
            return ""
        if url.startswith('http'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        return self.BASE_URL + url

    def _make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make HTTP request with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    # Rate limited, wait longer
                    wait_time = (attempt + 1) * 5
                    print(f"  Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"  HTTP {response.status_code} for {url}")
            except requests.RequestException as e:
                print(f"  Request error (attempt {attempt + 1}): {e}")
                time.sleep(2)

        return None

    def save_to_json(self, output_path: str = "data/personal_achievements.json"):
        """Save scraped badges to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        badges_dict = [asdict(badge) for badge in self.badges]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(badges_dict, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(self.badges)} badges to {output_file}")

    def populate_database(self):
        """Populate the database with scraped badges"""
        from sqlalchemy.orm import Session
        from src.database import engine
        from src.models import Section, Badge

        with Session(engine) as session:
            # Get section mappings
            section_map = {}
            for section_name in ["Beavers", "Cubs", "Scouts", "Venturers"]:
                section = session.query(Section).filter_by(name=section_name).first()
                if section:
                    section_map[section_name] = section.id

            # Add badges
            for badge in self.badges:
                section_id = section_map.get(badge.section)
                if not section_id:
                    continue

                # Check if badge already exists
                existing = session.query(Badge).filter_by(
                    badge_name=badge.badge_name,
                    section_id=section_id
                ).first()

                if not existing:
                    # Convert requirements to JSON
                    req_list = [
                        {"id": r.requirement_id, "desc": r.description, "mandatory": r.is_mandatory}
                        for r in badge.requirements
                    ]

                    badge_record = Badge(
                        section_id=section_id,
                        badge_name=badge.badge_name,
                        category=badge.category,
                        requirements=req_list,
                        image_url=badge.image_url,
                        prerequisites=badge.prerequisites or []
                    )
                    session.add(badge_record)

            session.commit()
            print(f"Database populated with Personal Achievement badges")


def main():
    """Run the Personal Achievement Badge scraper"""
    scraper = ScoutsCanadaScraper(delay=1.5)
    badges = scraper.scrape_all_badges()

    if badges:
        scraper.save_to_json(output_path="data/personal_achievements.json")
        scraper.populate_database()
    else:
        print("No badges were scraped")


if __name__ == "__main__":
    main()