"""Job description matching and scoring engine with transparent formula."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from src.skills import get_skill_catalog
from src.utils import clean_text, get_logger

logger = get_logger(__name__)

# Common English stop words for frequency term extraction
_STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
    "but", "by", "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does",
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had",
    "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd",
    "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off",
    "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
    "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd",
    "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
    "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves", "job", "description", "work", "candidate", "responsibilities",
    "requirements", "role", "team", "year", "years", "qualification", "qualifications",
    "ideal", "position", "ability", "strong", "experience", "required", "preferred", "plus",
}


def extract_frequent_terms(text: str, top_n: int = 15, exclude_set: set[str] | None = None) -> list[tuple[str, int]]:
    """Extract top frequency terms from job description excluding stop words and known skills.

    Args:
        text: Input job description text.
        top_n: Maximum number of terms to return.
        exclude_set: Set of lowercase terms to ignore.

    Returns:
        list[tuple[str, int]]: List of (word, count) tuples.
    """
    clean = clean_text(text).lower()
    tokens = re.findall(r"\b[a-z]{3,20}\b", clean)
    ignore = _STOP_WORDS | (exclude_set or set())

    filtered = [t for t in tokens if t not in ignore]
    counter = Counter(filtered)
    return counter.most_common(top_n)


def compute_education_score(resume_parsed: dict[str, Any], jd_text: str) -> float:
    """Compute education alignment score (0-100).

    Args:
        resume_parsed: Parsed resume data dictionary.
        jd_text: Job description string.

    Returns:
        float: Education score between 0 and 100.
    """
    edu_entries = resume_parsed.get("education", [])
    has_education = len(edu_entries) > 0 or "education" in resume_parsed.get("sections", {})

    if not has_education:
        return 0.0

    score = 60.0  # Base for having verified education section/degree

    # Look for degree levels in resume
    full_resume_text = resume_parsed.get("raw_text", "").lower()
    has_bachelors = any(term in full_resume_text for term in ["bachelor", "b.s", "b.tech", "b.e", "bs", "bsc"])
    has_masters = any(term in full_resume_text for term in ["master", "m.s", "m.tech", "mba", "ms", "msc", "phd", "doctorate"])

    jd_lower = jd_text.lower() if jd_text else ""
    wants_masters = any(term in jd_lower for term in ["master", "m.s", "advanced degree", "phd"])
    wants_bachelors = any(term in jd_lower for term in ["bachelor", "b.s", "degree in computer science"])

    if wants_masters and has_masters:
        score += 40.0
    elif wants_bachelors and (has_bachelors or has_masters):
        score += 40.0
    elif not wants_masters and not wants_bachelors and (has_bachelors or has_masters):
        score += 30.0
    else:
        score += 20.0

    return min(100.0, score)


def compute_experience_score(resume_parsed: dict[str, Any], matched_skills_count: int, total_jd_skills: int) -> float:
    """Compute experience relevance score (0-100).

    Args:
        resume_parsed: Parsed resume data dictionary.
        matched_skills_count: Number of matched skills.
        total_jd_skills: Total number of skills required by JD.

    Returns:
        float: Experience score between 0 and 100.
    """
    exp_entries = resume_parsed.get("experience", [])
    has_exp_section = len(exp_entries) > 0 or "experience" in resume_parsed.get("sections", {})

    if not has_exp_section:
        return 0.0

    # 1. Structural experience presence (up to 40 pts)
    base_score = 40.0

    # 2. Years of experience (up to 25 pts)
    years = resume_parsed.get("years_of_experience")
    if isinstance(years, (int, float)):
        if years >= 5:
            base_score += 25.0
        elif years >= 2:
            base_score += 18.0
        elif years >= 1:
            base_score += 12.0
        else:
            base_score += 5.0
    else:
        base_score += 10.0

    # 3. Ratio of matched skills integrated (up to 35 pts)
    if total_jd_skills > 0:
        match_ratio = matched_skills_count / total_jd_skills
        base_score += match_ratio * 35.0
    else:
        base_score += 35.0

    return min(100.0, base_score)


def match_resume_to_job(resume_parsed: dict[str, Any], jd_text: str | None) -> dict[str, Any]:
    """Calculate match score and keyword gap between parsed resume and job description.

    Args:
        resume_parsed: Structured resume data dictionary.
        jd_text: Raw job description text (can be empty or None).

    Returns:
        dict[str, Any]: Comprehensive matching report.
    """
    catalog = get_skill_catalog()

    # Resume skills
    resume_text = resume_parsed.get("raw_text", "")
    resume_skills_data = catalog.extract_skills_with_details(resume_text)
    resume_skills_set = set(resume_skills_data["all_skills"])
    resume_counts = resume_skills_data["counts"]

    # If no job description is provided
    if not jd_text or not jd_text.strip():
        return {
            "has_jd": False,
            "overall_score": 0.0,
            "formula_explanation": "No Job Description provided. Match scores require a target job description.",
            "section_scores": {
                "skills_score": 0.0,
                "experience_score": 0.0,
                "education_score": 0.0,
            },
            "total_jd_skills": 0,
            "total_matched_skills": 0,
            "total_missing_skills": 0,
            "matched_skills": [],
            "missing_skills": [],
            "matched_by_category": {cat: [] for cat in catalog.categories},
            "missing_by_category": {cat: [] for cat in catalog.categories},
            "frequent_terms": [],
            "candidate_skills_by_category": resume_skills_data["by_category"],
            "candidate_all_skills": resume_skills_data["all_skills"],
        }

    # Extract JD skills
    jd_skills_data = catalog.extract_skills_with_details(jd_text)
    jd_skills_set = set(jd_skills_data["all_skills"])
    jd_counts = jd_skills_data["counts"]

    # Match computation
    matched_skills_set = resume_skills_set & jd_skills_set
    missing_skills_set = jd_skills_set - resume_skills_set

    # Categorize matched and missing
    matched_by_cat: dict[str, list[str]] = {cat: [] for cat in catalog.categories}
    missing_by_cat: dict[str, list[str]] = {cat: [] for cat in catalog.categories}

    for skill in matched_skills_set:
        cat = catalog.skill_to_category.get(skill, "Other")
        if cat in matched_by_cat:
            matched_by_cat[cat].append(skill)

    for skill in missing_skills_set:
        cat = catalog.skill_to_category.get(skill, "Other")
        if cat in missing_by_cat:
            missing_by_cat[cat].append(skill)

    for cat in catalog.categories:
        matched_by_cat[cat] = sorted(matched_by_cat[cat])
        missing_by_cat[cat] = sorted(missing_by_cat[cat])

    total_jd = len(jd_skills_set)
    total_matched = len(matched_skills_set)
    total_missing = len(missing_skills_set)

    # 1. Skills score (0 - 100)
    if total_jd == 0:
        skills_score = 100.0 if len(resume_skills_set) > 0 else 50.0
    else:
        skills_score = round((total_matched / total_jd) * 100, 1)

    # 2. Experience score (0 - 100)
    experience_score = round(compute_experience_score(resume_parsed, total_matched, total_jd), 1)

    # 3. Education score (0 - 100)
    education_score = round(compute_education_score(resume_parsed, jd_text), 1)

    # Overall Match Formula:
    # 50% Skills Match + 35% Experience Relevance + 15% Education Alignment
    if total_jd == 0 and len(resume_skills_set) == 0:
        overall_score = 0.0
    else:
        overall_score = round(
            (0.50 * skills_score) + (0.35 * experience_score) + (0.15 * education_score),
            1,
        )

    # Extract frequent non-skill terms from JD
    exclude_known = {s.lower() for s in jd_skills_set}
    frequent_terms = extract_frequent_terms(jd_text, top_n=12, exclude_set=exclude_known)

    formula_text = (
        "Overall Score = (50% × Skills Score) + (35% × Experience Relevance) + (15% × Education Alignment)\n"
        f"Calculation: (0.50 × {skills_score}) + (0.35 × {experience_score}) + (0.15 × {education_score}) = {overall_score}%"
    )

    return {
        "has_jd": True,
        "overall_score": overall_score,
        "formula_explanation": formula_text,
        "section_scores": {
            "skills_score": skills_score,
            "experience_score": experience_score,
            "education_score": education_score,
        },
        "total_jd_skills": total_jd,
        "total_matched_skills": total_matched,
        "total_missing_skills": total_missing,
        "matched_skills": sorted(matched_skills_set),
        "missing_skills": sorted(missing_skills_set),
        "matched_by_category": matched_by_cat,
        "missing_by_category": missing_by_cat,
        "jd_skill_counts": jd_counts,
        "resume_skill_counts": resume_counts,
        "frequent_terms": frequent_terms,
        "candidate_skills_by_category": resume_skills_data["by_category"],
        "candidate_all_skills": resume_skills_data["all_skills"],
    }
