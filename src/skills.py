"""Curated skills catalog, alias normalization, and skill extraction."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from src.utils import get_logger, get_project_root

logger = get_logger(__name__)

# Fallback dictionary in case config file is unreadable
_DEFAULT_SKILLS: dict[str, list[dict[str, Any]]] = {
    "Programming Languages": [
        {"name": "Python", "aliases": ["python3", "py"]},
        {"name": "JavaScript", "aliases": ["js", "es6", "ecmascript"]},
        {"name": "TypeScript", "aliases": ["ts"]},
        {"name": "Java", "aliases": ["core java", "java 8", "java 11", "java 17", "java 21"]},
        {"name": "C++", "aliases": ["cpp", "c plus plus"]},
        {"name": "C#", "aliases": ["csharp", "c sharp", ".net c#"]},
        {"name": "Go", "aliases": ["golang"]},
        {"name": "Rust", "aliases": ["rust-lang"]},
        {"name": "Ruby", "aliases": ["ruby on rails", "rails"]},
        {"name": "PHP", "aliases": []},
        {"name": "Swift", "aliases": ["swiftui"]},
        {"name": "Kotlin", "aliases": []},
        {"name": "SQL", "aliases": ["structured query language", "t-sql", "pl/sql"]},
        {"name": "HTML", "aliases": ["html5"]},
        {"name": "CSS", "aliases": ["css3", "sass", "scss"]},
    ],
    "Frameworks & Libraries": [
        {"name": "React", "aliases": ["reactjs", "react.js", "react native"]},
        {"name": "Angular", "aliases": ["angularjs", "angular 2+"]},
        {"name": "Vue.js", "aliases": ["vue", "vuejs"]},
        {"name": "Next.js", "aliases": ["nextjs", "next.js", "next js"]},
        {"name": "Node.js", "aliases": ["nodejs", "node.js", "node"]},
        {"name": "Express", "aliases": ["expressjs", "express.js"]},
        {"name": "Django", "aliases": ["django rest framework", "drf"]},
        {"name": "Flask", "aliases": []},
        {"name": "FastAPI", "aliases": []},
        {"name": "Spring Boot", "aliases": ["spring", "springboot"]},
        {"name": "ASP.NET", "aliases": [".net core", "asp.net core", "dotnet"]},
        {"name": "GraphQL", "aliases": ["apollo graphql"]},
    ],
    "Databases": [
        {"name": "PostgreSQL", "aliases": ["postgres", "postgresql", "psql"]},
        {"name": "MySQL", "aliases": ["my-sql"]},
        {"name": "MongoDB", "aliases": ["mongo", "nosql"]},
        {"name": "Redis", "aliases": []},
        {"name": "SQLite", "aliases": ["sqlite3"]},
        {"name": "Elasticsearch", "aliases": ["elastic search", "elk"]},
        {"name": "DynamoDB", "aliases": ["amazon dynamodb"]},
        {"name": "Oracle", "aliases": ["oracle db", "oracle database"]},
        {"name": "Cassandra", "aliases": ["apache cassandra"]},
    ],
    "Cloud & DevOps": [
        {"name": "AWS", "aliases": ["amazon web services", "ec2", "s3", "lambda"]},
        {"name": "Azure", "aliases": ["microsoft azure"]},
        {"name": "Google Cloud", "aliases": ["gcp", "google cloud platform"]},
        {"name": "Docker", "aliases": ["containerization", "containers", "dockerfile"]},
        {"name": "Kubernetes", "aliases": ["k8s", "kubectl", "helm"]},
        {"name": "Terraform", "aliases": ["iac", "infrastructure as code"]},
        {"name": "CI/CD", "aliases": ["continuous integration", "continuous deployment", "ci-cd"]},
        {"name": "Jenkins", "aliases": []},
        {"name": "GitHub Actions", "aliases": ["gh actions"]},
        {"name": "Linux", "aliases": ["unix", "ubuntu", "debian", "centos", "bash", "shell scripting"]},
    ],
    "Data & Machine Learning": [
        {"name": "Machine Learning", "aliases": ["ml"]},
        {"name": "Deep Learning", "aliases": ["dl", "neural networks"]},
        {"name": "PyTorch", "aliases": ["torch"]},
        {"name": "TensorFlow", "aliases": ["tf", "keras"]},
        {"name": "Scikit-Learn", "aliases": ["sklearn"]},
        {"name": "Pandas", "aliases": []},
        {"name": "NumPy", "aliases": []},
        {"name": "Data Analysis", "aliases": ["data analytics", "eda"]},
        {"name": "Natural Language Processing", "aliases": ["nlp", "llm", "large language models"]},
        {"name": "Computer Vision", "aliases": ["cv", "opencv"]},
        {"name": "Tableau", "aliases": []},
        {"name": "Power BI", "aliases": ["powerbi"]},
    ],
    "Soft Skills": [
        {"name": "Communication", "aliases": ["verbal communication", "written communication"]},
        {"name": "Leadership", "aliases": ["team leadership", "mentoring", "mentorship"]},
        {"name": "Problem Solving", "aliases": ["troubleshooting", "analytical skills"]},
        {"name": "Teamwork", "aliases": ["collaboration", "cross-functional collaboration"]},
        {"name": "Critical Thinking", "aliases": []},
        {"name": "Time Management", "aliases": ["prioritization"]},
        {"name": "Agile / Scrum", "aliases": ["agile methodology", "scrum", "sprints", "kanban"]},
        {"name": "Adaptability", "aliases": ["flexibility"]},
    ],
    "Tools": [
        {"name": "Git", "aliases": ["version control"]},
        {"name": "GitHub", "aliases": []},
        {"name": "GitLab", "aliases": []},
        {"name": "Jira", "aliases": ["atlassian jira"]},
        {"name": "Confluence", "aliases": []},
        {"name": "Postman", "aliases": ["api testing"]},
        {"name": "VS Code", "aliases": ["visual studio code"]},
        {"name": "Figma", "aliases": ["ui/ux design"]},
    ],
}


class SkillCatalog:
    """Manages skill dictionaries, aliases, and regex pattern matching."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize the skill catalog with the specified or default config file.

        Args:
            config_path: Path to skills.json configuration file.
        """
        self.config_path = config_path or (get_project_root() / "config" / "skills.json")
        self.categories: dict[str, list[dict[str, Any]]] = {}
        self.alias_to_canonical: dict[str, str] = {}
        self.skill_to_category: dict[str, str] = {}
        self.patterns: list[tuple[str, re.Pattern[str], str]] = []  # (canonical, pattern, category)
        self.load_skills()

    def load_skills(self) -> None:
        """Load skills from JSON configuration and compile matching regular expressions."""
        data = None
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    data = raw_data.get("categories", {})
            except Exception as e:
                logger.error("Failed to load skills from %s: %s", self.config_path, e)

        if not data:
            logger.info("Using embedded default skills dictionary.")
            data = _DEFAULT_SKILLS

        self.categories = data
        self.alias_to_canonical.clear()
        self.skill_to_category.clear()
        self.patterns.clear()

        # Build alias maps and precompile regexes
        for category, skill_list in self.categories.items():
            for item in skill_list:
                canonical = item["name"]
                self.skill_to_category[canonical] = category
                self.alias_to_canonical[canonical.lower()] = canonical

                # Aliases
                aliases = item.get("aliases", [])
                for alias in aliases:
                    self.alias_to_canonical[alias.lower()] = canonical

                # Compile regex pattern for canonical and all aliases
                all_terms = [canonical] + aliases
                # Sort terms longest first to avoid partial matching
                sorted_terms = sorted(all_terms, key=len, reverse=True)

                pattern_parts: list[str] = []
                for term in sorted_terms:
                    term_escaped = re.escape(term)
                    # Special cases for languages/symbols
                    if term.lower() == "c++":
                        pattern_parts.append(r"(?:\bc\+\+|\bC\+\+)")
                    elif term.lower() == "c#":
                        pattern_parts.append(r"(?:\bc\#|\bC\#)")
                    elif term.lower() == "c":
                        # Match 'C' when uppercase or in programming context
                        pattern_parts.append(r"(?:\bC\b(?=[\s,/]+(?:C\+\+|C\#|assembly|embedded|programming)))")
                    elif term.lower() == "r":
                        # Match 'R' when in statistical / programming context
                        pattern_parts.append(r"(?:\bR\b(?=[\s,/]+(?:programming|statistics|python|data|analysis)))")
                    elif term.lower() == "go":
                        # Match 'Go' as programming language
                        pattern_parts.append(r"(?:\bgolang\b|\bGo\b(?=[\s,/]+(?:lang|developer|engineer|code|backend|programming)))")
                    elif term.lower() == ".net":
                        pattern_parts.append(r"(?:\.net|\bdotnet\b)")
                    elif "/" in term:
                        # e.g., CI/CD
                        parts = [re.escape(p) for p in term.split("/")]
                        pattern_parts.append(rf"\b{parts[0]}\s*/\s*{parts[1]}\b")
                    else:
                        pattern_parts.append(rf"\b{term_escaped}\b")

                if pattern_parts:
                    combined_pattern = "|".join(pattern_parts)
                    try:
                        # Case-insensitive except specific single letter patterns
                        flags = re.IGNORECASE
                        compiled = re.compile(combined_pattern, flags)
                        self.patterns.append((canonical, compiled, category))
                    except re.error as reg_err:
                        logger.warning("Invalid regex for skill %s: %s", canonical, reg_err)

    def normalize_skill(self, raw_name: str) -> str:
        """Map raw skill or alias name to its canonical name.

        Args:
            raw_name: Raw skill name or alias.

        Returns:
            str: Canonical skill name if found, else original stripped title.
        """
        cleaned = raw_name.strip().lower()
        return self.alias_to_canonical.get(cleaned, raw_name.strip())

    def extract_skills_with_details(self, text: str) -> dict[str, Any]:
        """Extract all skills, grouping by category and calculating occurrences.

        Args:
            text: Text to scan for skills.

        Returns:
            dict[str, Any]: Mapping with 'by_category', 'all_skills', 'counts', and 'total_unique'.
        """
        if not text:
            return {
                "by_category": {cat: [] for cat in self.categories},
                "all_skills": [],
                "counts": {},
                "total_unique": 0,
            }

        found_skills: set[str] = set()
        skill_counts: Counter[str] = Counter()
        by_category: dict[str, list[str]] = {cat: [] for cat in self.categories}

        for canonical, pattern, category in self.patterns:
            matches = pattern.findall(text)
            if matches:
                found_skills.add(canonical)
                skill_counts[canonical] = len(matches)
                if canonical not in by_category[category]:
                    by_category[category].append(canonical)

        # Sort within each category
        for cat in by_category:
            by_category[cat] = sorted(by_category[cat])

        return {
            "by_category": by_category,
            "all_skills": sorted(found_skills),
            "counts": dict(skill_counts),
            "total_unique": len(found_skills),
        }


# Global instance
_CATALOG_INSTANCE: SkillCatalog | None = None


def get_skill_catalog() -> SkillCatalog:
    """Retrieve the singleton SkillCatalog instance."""
    global _CATALOG_INSTANCE
    if _CATALOG_INSTANCE is None:
        _CATALOG_INSTANCE = SkillCatalog()
    return _CATALOG_INSTANCE


def extract_skills(text: str) -> dict[str, list[str]]:
    """Extract skills grouped by category from the text.

    Args:
        text: Input text string.

    Returns:
        dict[str, list[str]]: Category to list of canonical skills.
    """
    return get_skill_catalog().extract_skills_with_details(text)["by_category"]


def normalize_skill_name(name: str) -> str:
    """Normalize a skill name or alias to its canonical representation.

    Args:
        name: Skill string or alias.

    Returns:
        str: Canonical name.
    """
    return get_skill_catalog().normalize_skill(name)
