"""Unit tests for JD matcher and suggestion generator."""

from pathlib import Path

from src.matcher import match_resume_to_job
from src.parser import parse_resume
from src.suggestions import generate_suggestions

SAMPLE_DIR = Path(__file__).parent / "sample_data"


def test_empty_jd_match() -> None:
    resume = {
        "raw_text": "Experienced Python and Docker engineer.",
        "skills": {"Programming Languages": ["Python"], "Cloud & DevOps": ["Docker"]},
        "experience": [],
        "education": [],
        "sections": {},
    }
    result = match_resume_to_job(resume, "")
    assert result["has_jd"] is False
    assert result["overall_score"] == 0.0
    assert "No Job Description" in result["formula_explanation"]


def test_perfect_match() -> None:
    jd = "Required: Python, React, AWS, Docker, PostgreSQL."
    resume_text = """
    Software Engineer with 5 years experience.
    Skills: Python, React, AWS, Docker, PostgreSQL.
    Education: Bachelor of Science in Computer Science, 2019.
    Work Experience:
    Senior Developer | 2019 - Present
    - Built cloud microservices using Python, React, and AWS.
    """
    parsed = parse_resume(resume_text)
    match = match_resume_to_job(parsed, jd)

    assert match["has_jd"] is True
    assert match["total_missing_skills"] == 0
    assert match["section_scores"]["skills_score"] == 100.0
    assert match["overall_score"] >= 90.0


def test_zero_match() -> None:
    jd = "Required: Rust, Elixir, Haskell, Solana, Smart Contracts."
    resume_text = "I am an accountant with knowledge of Microsoft Excel and Quickbooks."
    parsed = parse_resume(resume_text)
    match = match_resume_to_job(parsed, jd)

    assert match["has_jd"] is True
    assert match["section_scores"]["skills_score"] == 0.0
    assert len(match["matched_skills"]) == 0


def test_sample_files_matching() -> None:
    resume_text = (SAMPLE_DIR / "sample_resume.txt").read_text(encoding="utf-8")
    jd_text = (SAMPLE_DIR / "sample_job_description.txt").read_text(encoding="utf-8")

    parsed = parse_resume(resume_text)
    match = match_resume_to_job(parsed, jd_text)

    assert match["has_jd"] is True
    assert match["overall_score"] > 60.0
    assert "Python" in match["matched_skills"]
    assert "React" in match["matched_skills"]
    assert "AWS" in match["matched_skills"]
    assert "PostgreSQL" in match["matched_skills"]
    # Check that transparent formula is present
    assert "Overall Score =" in match["formula_explanation"]


def test_suggestions_generation() -> None:
    resume_text = """
    Jane Doe
    jane@example.com
    Summary: Hardworking team player looking for synergy.
    Experience:
    Engineer | 2021 - Present
    - Worked on various backend features.
    - Assisted with database queries.
    """
    jd_text = "Required: Python, Docker, Kubernetes."

    parsed = parse_resume(resume_text)
    match = match_resume_to_job(parsed, jd_text)
    suggestions = generate_suggestions(parsed, match, jd_text)

    # Check keyword gap suggestion
    assert any("Docker" in tip for tip in suggestions["critical_gaps"])
    # Check buzzword detection
    assert any("team player" in b or "synergy" in b for b in suggestions["buzzwords"])
    # Check passive phrasing detection
    assert any("worked on" in p or "assisted with" in p for p in suggestions["passive_phrases"])
    # Check metric bullet warning
    assert suggestions["quantified_metrics"]["flagged"] is True
