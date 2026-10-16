"""Export utilities for generating JSON, Markdown, and text analysis reports."""

from __future__ import annotations

import datetime
import json
from typing import Any

from src.utils import get_logger

logger = get_logger(__name__)


def generate_json_report(analysis_bundle: dict[str, Any]) -> str:
    """Serialize full analysis bundle into a formatted JSON string.

    Args:
        analysis_bundle: Combined analysis dictionary.

    Returns:
        str: Pretty-printed JSON string.
    """
    clean_bundle = dict(analysis_bundle)
    clean_bundle["generated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return json.dumps(clean_bundle, indent=2, ensure_ascii=False)


def generate_markdown_report(analysis_bundle: dict[str, Any]) -> str:
    """Generate a clean, structured Markdown report from the analysis bundle.

    Args:
        analysis_bundle: Combined analysis dictionary.

    Returns:
        str: Formatted Markdown text.
    """
    resume_parsed = analysis_bundle.get("resume", {})
    match = analysis_bundle.get("match", {})
    suggestions = analysis_bundle.get("suggestions", {})

    name = resume_parsed.get("name", "Candidate")
    email = resume_parsed.get("email", "Not found")
    phone = resume_parsed.get("phone", "Not found")
    links = resume_parsed.get("links", {})
    years = resume_parsed.get("years_of_experience", "Not found")
    timestamp = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")

    has_jd = match.get("has_jd", False)
    overall_score = match.get("overall_score", 0.0)
    sec_scores = match.get("section_scores", {})

    lines: list[str] = [
        f"# Resume Analysis Report: {name}",
        f"*Generated on: {timestamp}*",
        "",
        "---",
        "",
        "## Candidate Profile",
        f"- **Name:** {name}",
        f"- **Email:** {email}",
        f"- **Phone:** {phone}",
        f"- **LinkedIn:** {links.get('linkedin', 'Not found')}",
        f"- **GitHub:** {links.get('github', 'Not found')}",
        f"- **Portfolio:** {links.get('portfolio', 'Not found')}",
        f"- **Estimated Experience:** {years} years" if years != "Not found" else "- **Estimated Experience:** Not found",
        "",
    ]

    if has_jd:
        lines.extend([
            "## Job Description Match Summary",
            f"### **Overall Match Score: {overall_score}%**",
            "",
            "#### Section-Level Breakdown",
            f"- **Skills Coverage:** {sec_scores.get('skills_score', 0)}%",
            f"- **Experience Relevance:** {sec_scores.get('experience_score', 0)}%",
            f"- **Education Alignment:** {sec_scores.get('education_score', 0)}%",
            "",
            f"> **Scoring Formula:** {match.get('formula_explanation', '')}",
            "",
            f"- **Matched Skills:** {match.get('total_matched_skills', 0)} of {match.get('total_jd_skills', 0)} required",
            f"- **Missing Skills:** {match.get('total_missing_skills', 0)}",
            "",
            "### Matched Skills by Category",
        ])

        matched_by_cat = match.get("matched_by_category", {})
        has_any_matched = False
        for cat, skills in matched_by_cat.items():
            if skills:
                has_any_matched = True
                lines.append(f"- **{cat}:** {', '.join(skills)}")
        if not has_any_matched:
            lines.append("_No direct skill matches detected._")

        lines.extend(["", "### Missing Keywords / Gaps by Category"])
        missing_by_cat = match.get("missing_by_category", {})
        has_any_missing = False
        for cat, skills in missing_by_cat.items():
            if skills:
                has_any_missing = True
                lines.append(f"- **{cat}:** {', '.join(skills)}")
        if not has_any_missing:
            lines.append("_No missing keywords detected. Complete coverage!_")

        lines.append("")
    else:
        lines.extend([
            "## Extracted Skills Overview",
            "*(No Job Description was provided for comparative matching)*",
            "",
        ])
        cand_by_cat = match.get("candidate_skills_by_category", resume_parsed.get("skills", {}))
        for cat, skills in cand_by_cat.items():
            if skills:
                lines.append(f"- **{cat}:** {', '.join(skills)}")
        lines.append("")

    # Actionable Suggestions
    lines.extend([
        "## Actionable Suggestions & Resume Tips",
        "",
    ])

    crit = suggestions.get("critical_gaps", [])
    if crit:
        lines.append("### Critical Gaps to Address")
        for tip in crit:
            lines.append(f"- [ ] {tip}")
        lines.append("")

    weak = suggestions.get("weak_signals", [])
    if weak:
        lines.append("### Weak Signals & Content Quality")
        for tip in weak:
            lines.append(f"- [ ] {tip}")
        lines.append("")

    content = suggestions.get("content_improvements", [])
    if content:
        lines.append("### Content & Formatting Recommendations")
        for tip in content:
            lines.append(f"- [ ] {tip}")
        lines.append("")

    verbs = suggestions.get("recommended_action_verbs", [])
    if verbs:
        lines.append(f"**Recommended Impact Verbs:** {', '.join(verbs)}")
        lines.append("")

    lines.extend([
        "---",
        "*Report created by AI Resume Analyzer*",
    ])

    return "\n".join(lines)


def generate_txt_report(analysis_bundle: dict[str, Any]) -> str:
    """Generate a clean plain text report from the analysis bundle.

    Args:
        analysis_bundle: Combined analysis dictionary.

    Returns:
        str: Plain text formatted report.
    """
    md = generate_markdown_report(analysis_bundle)
    # Strip basic markdown markers for plain text readability
    clean_txt = md.replace("#", "").replace("**", "").replace("*", "").replace("---", "=" * 40)
    return clean_txt
