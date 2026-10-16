"""Unit tests for skills extraction, category grouping, and alias normalization."""

from src.skills import extract_skills, get_skill_catalog, normalize_skill_name


def test_alias_normalization() -> None:
    assert normalize_skill_name("js") == "JavaScript"
    assert normalize_skill_name("JS") == "JavaScript"
    assert normalize_skill_name("k8s") == "Kubernetes"
    assert normalize_skill_name("reactjs") == "React"
    assert normalize_skill_name("python3") == "Python"
    assert normalize_skill_name("postgres") == "PostgreSQL"
    assert normalize_skill_name("aws") == "AWS"


def test_skills_extraction_case_insensitivity() -> None:
    text = "Proficient in python, DOCKER, and kubernetes with strong sql skills."
    extracted = extract_skills(text)

    # Flatten extracted skills
    all_extracted = [s for cat_skills in extracted.values() for s in cat_skills]
    assert "Python" in all_extracted
    assert "Docker" in all_extracted
    assert "Kubernetes" in all_extracted
    assert "SQL" in all_extracted


def test_word_boundary_isolation() -> None:
    catalog = get_skill_catalog()

    # 'Java' vs 'JavaScript'
    js_text = "I build web applications using JavaScript and NodeJS."
    js_details = catalog.extract_skills_with_details(js_text)
    assert "JavaScript" in js_details["all_skills"]
    assert "Java" not in js_details["all_skills"]

    # 'C++' detection
    cpp_text = "Experience with high-performance C++ backend services."
    cpp_details = catalog.extract_skills_with_details(cpp_text)
    assert "C++" in cpp_details["all_skills"]


def test_categories_grouping() -> None:
    text = "Full stack engineer experienced in React, TypeScript, PostgreSQL, and AWS."
    extracted = extract_skills(text)

    assert "TypeScript" in extracted.get("Programming Languages", [])
    assert "React" in extracted.get("Frameworks & Libraries", [])
    assert "PostgreSQL" in extracted.get("Databases", [])
    assert "AWS" in extracted.get("Cloud & DevOps", [])


def test_empty_text_skills() -> None:
    catalog = get_skill_catalog()
    details = catalog.extract_skills_with_details("")
    assert details["total_unique"] == 0
    assert details["all_skills"] == []
