"""Resume parser for contact details, section headings, education, experience, and years of experience."""

from __future__ import annotations

import datetime
import re
from typing import Any

from src.skills import extract_skills
from src.utils import get_logger

logger = get_logger(__name__)

NOT_FOUND = "Not found"

# Standard section header regex patterns
_SECTION_PATTERNS = {
    "summary": re.compile(
        r"^(?:professional\s+summary|executive\s+summary|summary|profile|about\s+me|about|objective)$",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"^(?:work\s+experience|professional\s+experience|experience|employment\s+history|career\s+history|work\s+history)$",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:education|academic\s+background|academic\s+qualifications|academics|qualifications|degrees)$",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^(?:skills|technical\s+skills|core\s+skills|core\s+competencies|technologies|expertise|skills\s*&\s*competencies)$",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^(?:projects|personal\s+projects|academic\s+projects|key\s+projects)$",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^(?:certifications|certificates|licenses|certifications\s*&\s*licenses)$",
        re.IGNORECASE,
    ),
}

_DEGREE_PATTERNS = [
    r"\b(?:ph\.?d|doctorate|doctor\s+of\s+philosophy)\b",
    r"\b(?:m\.?s\.?|m\.?sc\.?|master\s+of\s+science|m\.?a\.?|master\s+of\s+arts|m\.?tech|m\.?e\.?|mba|master)\b",
    r"\b(?:b\.?s\.?|b\.?sc\.?|bachelor\s+of\s+science|b\.?a\.?|bachelor\s+of\s+arts|b\.?tech|b\.?e\.?|bachelor)\b",
    r"\b(?:associate\s+degree|associate\s+of\s+science|associate\s+of\s+arts|diploma)\b",
]

_MONTHS = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
_YEAR = r"(?:19|20)\d{2}"
_DATE_RANGE_REGEX = re.compile(
    rf"(?:{_MONTHS}\s+)?({_YEAR})\s*(?:-|–|—|to)\s*(?:({_MONTHS}\s+)?({_YEAR})|present|current|now)",
    re.IGNORECASE,
)


def extract_email(text: str) -> str:
    """Extract candidate email address.

    Args:
        text: Resume text.

    Returns:
        str: Email address or 'Not found'.
    """
    pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    matches = re.findall(pattern, text)
    for email in matches:
        # Strip trailing dot or punctuation if attached
        clean_email = email.rstrip(".,;:)")
        if "." in clean_email.split("@")[-1] and len(clean_email.split("@")[-1]) >= 2:
            return clean_email
    return NOT_FOUND


def extract_phone(text: str) -> str:
    """Extract candidate phone number.

    Args:
        text: Resume text.

    Returns:
        str: Phone number or 'Not found'.
    """
    patterns = [
        # +1 (123) 456-7890, +91 9876543210, (123) 456-7890, 123-456-7890
        r"(?:\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}",
        r"\+?\d{1,4}[\s.-]?\d{3,4}[\s.-]?\d{3,5}",
    ]
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            candidate = match.group(0).strip()
            # Verify candidate has between 10 and 15 digits
            digits = re.sub(r"\D", "", candidate)
            if 10 <= len(digits) <= 15:
                return candidate
    return NOT_FOUND


def extract_links(text: str) -> dict[str, str]:
    """Extract professional links such as LinkedIn, GitHub, and portfolios.

    Args:
        text: Resume text.

    Returns:
        dict[str, str]: Dictionary containing 'linkedin', 'github', and 'portfolio'.
    """
    links = {
        "linkedin": NOT_FOUND,
        "github": NOT_FOUND,
        "portfolio": NOT_FOUND,
    }

    # LinkedIn
    linkedin_match = re.search(r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[a-zA-Z0-9_\-\/]+", text, re.IGNORECASE)
    if linkedin_match:
        url = linkedin_match.group(0).rstrip(".,)")
        links["linkedin"] = url if url.startswith("http") else f"https://{url}"

    # GitHub
    github_match = re.search(r"(?:https?:\/\/)?(?:www\.)?github\.com\/[a-zA-Z0-9_\-\/]+", text, re.IGNORECASE)
    if github_match:
        url = github_match.group(0).rstrip(".,)")
        links["github"] = url if url.startswith("http") else f"https://{url}"

    # Portfolio / personal website
    url_matches = re.findall(r"https?:\/\/[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(?:\/[^\s]*)?", text)
    for u in url_matches:
        u_clean = u.rstrip(".,;)")
        if "linkedin.com" not in u_clean.lower() and "github.com" not in u_clean.lower():
            links["portfolio"] = u_clean
            break

    return links


def extract_name(text: str) -> str:
    """Best-effort extraction of the candidate's name from header lines.

    Args:
        text: Resume text.

    Returns:
        str: Candidate name or 'Not found'.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return NOT_FOUND

    # Look at the first 6 non-empty lines
    for line in lines[:6]:
        # Filter out lines that look like emails, URLs, phones, or section titles
        lower_line = line.lower()
        if (
            "@" in line
            or "http" in lower_line
            or "www." in lower_line
            or "github" in lower_line
            or "linkedin" in lower_line
            or "resume" in lower_line
            or "curriculum vitae" in lower_line
            or "phone" in lower_line
            or "email" in lower_line
            or "page " in lower_line
        ):
            continue

        # Exclude lines with numbers
        if re.search(r"\d", line):
            continue

        # Check for 2 to 4 words
        words = line.split()
        if 2 <= len(words) <= 4:
            # Check characters are alphabetic with allowed punctuation (. or -)
            if all(re.match(r"^[A-Za-z.\-]+$", w) for w in words):
                return " ".join(words).title()

    return NOT_FOUND


def split_sections(text: str) -> dict[str, str]:
    """Split resume text into recognized standard sections.

    Args:
        text: Resume text.

    Returns:
        dict[str, str]: Map of section name to section text.
    """
    sections: dict[str, list[str]] = {
        "header": [],
        "summary": [],
        "experience": [],
        "education": [],
        "skills": [],
        "projects": [],
        "certifications": [],
        "other": [],
    }

    current_section = "header"
    lines = text.splitlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if line matches a known section header
        header_candidate = re.sub(r"[:\-_#=*]+$", "", stripped).strip()
        found_header = None

        if len(header_candidate.split()) <= 4:
            for sec_key, pattern in _SECTION_PATTERNS.items():
                if pattern.match(header_candidate):
                    found_header = sec_key
                    break

        if found_header:
            current_section = found_header
        else:
            sections[current_section].append(stripped)

    return {k: "\n".join(v).strip() for k, v in sections.items() if v}


def extract_education(text: str, sections: dict[str, str]) -> list[dict[str, str]]:
    """Extract education entries including degree, institution, and year.

    Args:
        text: Full resume text.
        sections: Dictionary of extracted sections.

    Returns:
        list[dict[str, str]]: List of education records.
    """
    edu_text = sections.get("education", "")
    target_text = edu_text if edu_text else text
    if not target_text.strip():
        return []

    # Split into logical blocks by blank lines or paragraphs
    raw_blocks = [b.strip() for b in re.split(r"\n\s*\n", target_text) if b.strip()]
    if len(raw_blocks) <= 1:
        # Fallback to lines if no empty line separators
        lines = [l.strip() for l in target_text.splitlines() if l.strip()]
        # If short list of lines, treat as a single entry or group into pairs/triplets
        raw_blocks = ["\n".join(lines)]

    entries: list[dict[str, str]] = []

    for block in raw_blocks:
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue

        detected_degree = None
        detected_inst = None
        detected_year = NOT_FOUND

        for line in lines:
            if not detected_degree:
                for deg_pat in _DEGREE_PATTERNS:
                    match = re.search(deg_pat, line, re.IGNORECASE)
                    if match:
                        detected_degree = match.group(0).upper()
                        break

            if not detected_inst:
                for inst_kw in ["university", "college", "institute", "school", "academy", "polytechnic"]:
                    if inst_kw in line.lower():
                        detected_inst = line
                        break

            if detected_year == NOT_FOUND:
                year_match = re.search(r"\b(19\d{2}|20\d{2})\b", line)
                if year_match:
                    detected_year = year_match.group(0)

        if detected_degree or detected_inst or (edu_text and lines):
            entries.append({
                "entry": " | ".join(lines),
                "degree": detected_degree or "Degree / Certificate",
                "institution": detected_inst or NOT_FOUND,
                "year": detected_year,
            })

    return entries


def extract_experience(text: str, sections: dict[str, str]) -> list[dict[str, Any]]:
    """Extract work experience entries with title, date range, and bullet points.

    Args:
        text: Full resume text.
        sections: Dictionary of extracted sections.

    Returns:
        list[dict[str, Any]]: Extracted experience entries.
    """
    exp_text = sections.get("experience", "")
    if not exp_text:
        return []

    lines = exp_text.splitlines()
    entries: list[dict[str, Any]] = []
    current_entry: dict[str, Any] | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check for date range
        date_match = _DATE_RANGE_REGEX.search(stripped)
        is_bullet = stripped.startswith(("-", "•", "*", "–", "—")) or re.match(r"^\d+\.", stripped)

        if date_match and not is_bullet:
            if current_entry and current_entry["dates"] == NOT_FOUND and not current_entry["bullets"]:
                # Current line is the date line for the preceding job title/company headline
                current_entry["dates"] = date_match.group(0)
                current_entry["headline"] += f" | {stripped}"
            else:
                if current_entry:
                    entries.append(current_entry)
                current_entry = {
                    "headline": stripped,
                    "dates": date_match.group(0),
                    "bullets": [],
                }
        elif is_bullet:
            clean_bullet = re.sub(r"^[-•*–—\d.]+\s*", "", stripped)
            if current_entry:
                current_entry["bullets"].append(clean_bullet)
            else:
                current_entry = {
                    "headline": "Experience Item",
                    "dates": NOT_FOUND,
                    "bullets": [clean_bullet],
                }
        else:
            if current_entry and len(current_entry["bullets"]) == 0:
                # Supplementary company / position info
                current_entry["headline"] += f" | {stripped}"
            elif current_entry:
                current_entry["bullets"].append(stripped)
            else:
                current_entry = {
                    "headline": stripped,
                    "dates": NOT_FOUND,
                    "bullets": [],
                }

    if current_entry:
        entries.append(current_entry)

    return entries


def estimate_years_of_experience(text: str, sections: dict[str, str]) -> float | str:
    """Estimate total years of experience from explicit mentions and date spans.

    Args:
        text: Full resume text.
        sections: Dictionary of extracted sections.

    Returns:
        float | str: Estimated years as float, or 'Not found'.
    """
    # 1. Look for explicit mentions like "5+ years of experience" or "7 years experience"
    explicit_match = re.search(
        r"(\d+(?:\.\d+)?)\+?\s*(?:-\s*\d+)?\s*years(?:\s+of)?\s+experience",
        text,
        re.IGNORECASE,
    )
    if explicit_match:
        try:
            return round(float(explicit_match.group(1)), 1)
        except ValueError:
            pass

    # 2. Extract date intervals from experience section or entire text
    target_text = sections.get("experience", text)
    matches = _DATE_RANGE_REGEX.findall(target_text)

    current_year = datetime.datetime.now().year
    intervals: list[tuple[int, int]] = []

    for match in matches:
        start_year = int(match[0])
        # match[2] is end year if present, otherwise it matched "present"
        end_year_str = match[2]
        end_year = int(end_year_str) if end_year_str else current_year

        if 1970 <= start_year <= current_year and start_year <= end_year <= current_year + 1:
            intervals.append((start_year, end_year))

    if not intervals:
        return NOT_FOUND

    # Merge overlapping or contiguous intervals to avoid double-counting
    intervals.sort(key=lambda x: x[0])
    merged: list[tuple[int, int]] = []
    for start, end in intervals:
        if not merged:
            merged.append((start, end))
        else:
            prev_start, prev_end = merged[-1]
            if start <= prev_end:
                merged[-1] = (prev_start, max(prev_end, end))
            else:
                merged.append((start, end))

    total_years = sum(end - start for start, end in merged)
    # Give at least 0.5 year if start == end
    if total_years == 0 and merged:
        total_years = 1.0

    return round(float(min(total_years, 45.0)), 1)


def parse_resume(text: str) -> dict[str, Any]:
    """Parse complete resume text into structured fields.

    Args:
        text: Raw extracted resume text.

    Returns:
        dict[str, Any]: Structured resume profile.
    """
    if not text or not text.strip():
        return {
            "name": NOT_FOUND,
            "email": NOT_FOUND,
            "phone": NOT_FOUND,
            "links": {"linkedin": NOT_FOUND, "github": NOT_FOUND, "portfolio": NOT_FOUND},
            "sections": {},
            "education": [],
            "experience": [],
            "years_of_experience": NOT_FOUND,
            "skills": {},
            "raw_text": "",
        }

    sections = split_sections(text)
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    links = extract_links(text)
    education = extract_education(text, sections)
    experience = extract_experience(text, sections)
    years = estimate_years_of_experience(text, sections)
    skills = extract_skills(text)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "links": links,
        "sections": sections,
        "education": education,
        "experience": experience,
        "years_of_experience": years,
        "skills": skills,
        "raw_text": text,
    }
