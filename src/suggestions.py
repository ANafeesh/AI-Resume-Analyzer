"""Actionable suggestions generator and weak-signal detection."""

from __future__ import annotations

import re
from typing import Any

from src.utils import get_logger

logger = get_logger(__name__)

# Common passive or weak phrases to detect
_WEAK_PHRASES = [
    r"\b(?:responsible\s+for)\b",
    r"\b(?:duties\s+included)\b",
    r"\b(?:assisted\s+with)\b",
    r"\b(?:helped\s+(?:with|in|to))\b",
    r"\b(?:worked\s+on)\b",
    r"\b(?:handled)\b",
    r"\b(?:tasked\s+with)\b",
]

# Overused cliché buzzwords
_BUZZWORDS = [
    "synergy",
    "team player",
    "go-getter",
    "hardworking",
    "hard worker",
    "think outside the box",
    "detail-oriented",
    "results-driven",
    "self-starter",
    "fast learner",
    "dynamic",
    "proven track record",
    "strategic thinker",
]

# Strong impact verbs to recommend
STRONG_ACTION_VERBS = [
    "Architected",
    "Spearheaded",
    "Engineered",
    "Orchestrated",
    "Automated",
    "Optimized",
    "Streamlined",
    "Delivered",
    "Scaled",
    "Deployed",
]


def check_quantified_achievements(experience_entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Check whether experience bullet points contain quantifiable numbers, percentages, or metrics.

    Args:
        experience_entries: List of experience dictionaries.

    Returns:
        dict[str, Any]: Quantified metrics evaluation.
    """
    all_bullets: list[str] = []
    for exp in experience_entries:
        all_bullets.extend(exp.get("bullets", []))

    if not all_bullets:
        return {
            "flagged": True,
            "metric_bullets": 0,
            "total_bullets": 0,
            "percentage": 0.0,
            "message": "No structured experience bullet points detected. Add bullet points highlighting measurable accomplishments.",
        }

    # Match numbers, percentages, currency, multipliers (e.g. 25%, $1.5M, 10x, 300+)
    metric_pattern = re.compile(r"(\d+(?:\.\d+)?%|\$\d+(?:\.\d+)?[kKmMbB]?|\b\d+x\b|\b\d+\b)")
    metric_bullets = [b for b in all_bullets if metric_pattern.search(b)]

    ratio = len(metric_bullets) / len(all_bullets)
    flagged = ratio < 0.40  # Flag if less than 40% have numbers

    if flagged:
        message = (
            f"Only {len(metric_bullets)} of {len(all_bullets)} ({ratio:.0%}) experience bullet points include measurable metrics. "
            "Strong resumes use data to validate impact (e.g., 'Reduced API latency by 35%', 'Managed a $50k budget', 'Served 100k+ MAU')."
        )
    else:
        message = f"Great work: {len(metric_bullets)} of {len(all_bullets)} ({ratio:.0%}) experience bullet points include quantifiable results."

    return {
        "flagged": flagged,
        "metric_bullets": len(metric_bullets),
        "total_bullets": len(all_bullets),
        "percentage": round(ratio * 100, 1),
        "message": message,
    }


def check_passive_phrasing(text: str) -> list[str]:
    """Detect passive or weak job responsibility phrases.

    Args:
        text: Resume text.

    Returns:
        list[str]: Found weak phrases.
    """
    detected: list[str] = []
    lower_text = text.lower()
    for pattern in _WEAK_PHRASES:
        found = re.findall(pattern, lower_text)
        if found:
            detected.extend(found)
    return sorted(set(detected))


def check_buzzwords(text: str) -> list[str]:
    """Detect overused corporate buzzwords.

    Args:
        text: Resume text.

    Returns:
        list[str]: Found buzzwords.
    """
    detected: list[str] = []
    lower_text = text.lower()
    for word in _BUZZWORDS:
        if re.search(rf"\b{re.escape(word)}\b", lower_text):
            detected.append(word)
    return sorted(set(detected))


def check_summary_length(sections: dict[str, str]) -> dict[str, Any]:
    """Evaluate length and conciseness of professional summary.

    Args:
        sections: Map of resume sections.

    Returns:
        dict[str, Any]: Summary assessment.
    """
    summary = sections.get("summary", "")
    if not summary:
        return {
            "status": "missing",
            "word_count": 0,
            "message": "No professional summary detected. A concise 3-4 sentence summary can quickly highlight your core specialization.",
        }

    words = summary.split()
    word_count = len(words)

    if word_count > 120:
        return {
            "status": "too_long",
            "word_count": word_count,
            "message": f"Professional summary is {word_count} words long. Aim for a punchy 50–90 word summary to keep recruiters engaged.",
        }
    elif word_count < 25:
        return {
            "status": "too_short",
            "word_count": word_count,
            "message": f"Professional summary is very brief ({word_count} words). Consider adding your target role, years of experience, and primary stack.",
        }

    return {
        "status": "optimal",
        "word_count": word_count,
        "message": f"Professional summary length is optimal ({word_count} words).",
    }


def check_contact_info(parsed: dict[str, Any]) -> list[str]:
    """Identify missing essential contact information.

    Args:
        parsed: Parsed resume data.

    Returns:
        list[str]: Missing contact warnings.
    """
    missing: list[str] = []
    if parsed.get("email") == "Not found":
        missing.append("Email address not found. Ensure your contact email is clearly visible at the top.")
    if parsed.get("phone") == "Not found":
        missing.append("Phone number not found. Include a phone number for recruiter outreach.")

    links = parsed.get("links", {})
    if links.get("linkedin") == "Not found":
        missing.append("LinkedIn profile URL not found. Adding your LinkedIn link increases credibility.")
    if links.get("github") == "Not found":
        missing.append("GitHub profile not found. For technical roles, a GitHub link showcases your code quality.")

    return missing


def generate_suggestions(
    resume_parsed: dict[str, Any],
    match_result: dict[str, Any] | None,
    jd_text: str | None = None,
) -> dict[str, Any]:
    """Generate comprehensive, prioritized suggestions and weak-signal feedback.

    Args:
        resume_parsed: Parsed resume details.
        match_result: Match analysis data from matcher module.
        jd_text: Job description string if provided.

    Returns:
        dict[str, Any]: Structured suggestions categorized by priority.
    """
    full_text = resume_parsed.get("raw_text", "")
    sections = resume_parsed.get("sections", {})
    experience = resume_parsed.get("experience", [])

    critical_gaps: list[str] = []
    content_improvements: list[str] = []
    weak_signals: list[str] = []

    # 1. Job Description Specific Keyword Gaps
    if match_result and match_result.get("has_jd"):
        missing_skills = match_result.get("missing_skills", [])
        jd_counts = match_result.get("jd_skill_counts", {})

        # Sort missing skills by frequency in JD
        sorted_missing = sorted(missing_skills, key=lambda s: jd_counts.get(s, 0), reverse=True)

        for skill in sorted_missing[:7]:
            count = jd_counts.get(skill, 1)
            critical_gaps.append(
                f"Add '{skill}' to your skills or experience section; it appears {count} time{'s' if count != 1 else ''} "
                "in the job description but was not detected in your resume."
            )

        # Highlight missing categories if an entire category is empty
        missing_by_cat = match_result.get("missing_by_category", {})
        for cat, skills in missing_by_cat.items():
            if skills and len(skills) >= 2:
                content_improvements.append(
                    f"Strengthen your {cat} section: consider adding required proficiencies like {', '.join(skills[:3])}."
                )

    # 2. Weak Signals Detection
    # A. Quantified Achievements
    quant_eval = check_quantified_achievements(experience)
    if quant_eval["flagged"]:
        weak_signals.append(quant_eval["message"])

    # B. Passive phrasing
    passive_phrases = check_passive_phrasing(full_text)
    if passive_phrases:
        verbs_example = ", ".join(STRONG_ACTION_VERBS[:4])
        phrases_str = ", ".join(f'"{p}"' for p in passive_phrases[:3])
        weak_signals.append(
            f"Found passive or generic phrases: {phrases_str}. "
            f"Replace them with high-impact action verbs like {verbs_example}."
        )

    # C. Buzzwords
    buzzwords_found = check_buzzwords(full_text)
    if buzzwords_found:
        buzzwords_str = ", ".join(f'"{b}"' for b in buzzwords_found[:4])
        weak_signals.append(
            f"Found overused buzzwords: {buzzwords_str}. "
            "Replace generic claims with concrete examples of projects or measurable deliverables."
        )

    # D. Professional summary
    summary_eval = check_summary_length(sections)
    if summary_eval["status"] != "optimal":
        content_improvements.append(summary_eval["message"])

    # E. Contact info completeness
    contact_warnings = check_contact_info(resume_parsed)
    content_improvements.extend(contact_warnings)

    # General structure advice
    if not sections.get("education"):
        weak_signals.append("Education section not clearly detected. Ensure degree and university headings are distinct.")
    if not sections.get("experience"):
        critical_gaps.append("Work experience section not detected. Use standard headings like 'Work Experience' or 'Employment History'.")

    return {
        "critical_gaps": critical_gaps,
        "content_improvements": content_improvements,
        "weak_signals": weak_signals,
        "quantified_metrics": quant_eval,
        "passive_phrases": passive_phrases,
        "buzzwords": buzzwords_found,
        "recommended_action_verbs": STRONG_ACTION_VERBS,
    }
