"""Unit tests for parser module covering contacts, sections, education, and experience."""

from pathlib import Path

from src.parser import (
    NOT_FOUND,
    estimate_years_of_experience,
    extract_education,
    extract_email,
    extract_experience,
    extract_links,
    extract_name,
    extract_phone,
    parse_resume,
    split_sections,
)

SAMPLE_DIR = Path(__file__).parent / "sample_data"


def test_extract_contact_info() -> None:
    sample_text = """
    John Doe
    john.doe@techcorp.io | +1 (555) 234-5678
    https://linkedin.com/in/johndoe | https://github.com/johndoe
    """
    assert extract_name(sample_text) == "John Doe"
    assert extract_email(sample_text) == "john.doe@techcorp.io"
    assert "555" in extract_phone(sample_text)

    links = extract_links(sample_text)
    assert "linkedin.com/in/johndoe" in links["linkedin"]
    assert "github.com/johndoe" in links["github"]


def test_missing_fields_return_not_found() -> None:
    blank_text = "Some random text without any email or phone number or links."
    assert extract_email(blank_text) == NOT_FOUND
    assert extract_phone(blank_text) == NOT_FOUND
    links = extract_links(blank_text)
    assert links["linkedin"] == NOT_FOUND
    assert links["github"] == NOT_FOUND


def test_section_splitting() -> None:
    resume_text = """
    Alex Rivera
    alex@example.com

    Professional Summary
    Senior engineer passionate about backend architecture.

    Technical Skills
    Python, Go, PostgreSQL

    Work Experience
    Lead Architect | Acme Inc
    2020 - Present
    - Designed real-time event streaming systems.

    Education
    Master of Science in Software Engineering
    Stanford University
    2018 - 2020
    """
    sections = split_sections(resume_text)
    assert "summary" in sections
    assert "skills" in sections
    assert "experience" in sections
    assert "education" in sections


def test_education_parsing() -> None:
    text = "Bachelor of Science in Computer Science\nUniversity of California, Berkeley\n2016 - 2020"
    sections = {"education": text}
    edu = extract_education(text, sections)
    assert len(edu) >= 1
    assert "BACHELOR OF SCIENCE" in edu[0]["degree"] or "BACHELOR" in edu[0]["degree"]
    assert "2016" in edu[0]["year"] or "2020" in edu[0]["year"]


def test_experience_parsing() -> None:
    text = """
    Software Engineer | InnoTech
    Jan 2021 - Present
    - Developed GraphQL APIs in Python.
    - Reduced database query latency by 40%.
    """
    sections = {"experience": text}
    exp = extract_experience(text, sections)
    assert len(exp) == 1
    assert len(exp[0]["bullets"]) == 2
    assert "GraphQL" in exp[0]["bullets"][0]


def test_years_of_experience_estimation() -> None:
    # Explicit mention
    text1 = "Full Stack Engineer with 6 years of experience in distributed systems."
    assert estimate_years_of_experience(text1, {}) == 6.0

    # Date range deduction
    text2 = "Work History\nSoftware Engineer | Alpha Corp\n2019 - 2023"
    sections2 = {"experience": text2}
    years = estimate_years_of_experience(text2, sections2)
    assert isinstance(years, float)
    assert years >= 4.0


def test_parse_sample_resume_file() -> None:
    sample_file = SAMPLE_DIR / "sample_resume.txt"
    content = sample_file.read_text(encoding="utf-8")
    parsed = parse_resume(content)

    assert parsed["name"] == "Jane Doe"
    assert parsed["email"] == "jane.doe@example.com"
    assert "(555) 123-4567" in parsed["phone"]
    assert "linkedin.com/in/janedoe" in parsed["links"]["linkedin"]
    assert "github.com/janedoe" in parsed["links"]["github"]
    assert parsed["years_of_experience"] in (4.0, 4) or (isinstance(parsed["years_of_experience"], float) and parsed["years_of_experience"] >= 3.0)
    assert len(parsed["education"]) >= 1
    assert len(parsed["experience"]) >= 1
