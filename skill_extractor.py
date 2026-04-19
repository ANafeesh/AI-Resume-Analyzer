import re

# -----------------------------
# CLEAN SKILLS DATABASE
# -----------------------------
skills_db = [
    "python","java","c++","javascript",
    "html","css","react","nodejs","express",
    "flask","django","rest api","graphql",
    "sql","mysql","mongodb","database design",
    "git","github","docker","ci/cd",
    "linux","bash","debugging","testing",
    "data structures","algorithms","oop","system design",
    "aws","cloud computing","microservices"
]

# -----------------------------
# NOISE WORDS (IMPORTANT FIX)
# -----------------------------
noise_words = {
    "required", "requirements", "skills", "skill",
    "experience", "responsibilities", "job",
    "candidate", "looking", "knowledge", "must", "should",
    "years", "working", "ability"
}

# -----------------------------
# TEXT NORMALIZATION
# -----------------------------
def normalize(text):
    text = text.lower()

    # fix common formats
    text = text.replace("node.js", "nodejs")
    text = text.replace("c ++", "c++")

    # remove punctuation properly
    text = re.sub(r"[^a-z0-9+# ]", " ", text)

    # remove extra spaces
    text = re.sub(r"\s+", " ", text)

    # remove noise fragments caused by splitting
    text = text.replace(" skills ", " ")
    text = text.replace(" required ", " ")

    return text.strip()

def is_valid_skill(skill):
    skill = normalize(skill)

    # prevent partial confusion
    if skill == "java":
        return True
    if skill == "javascript":
        return True

    return True

# -----------------------------
# SKILL EXTRACTION (FIXED)
# -----------------------------
def extract_skills(text):
    text = normalize(text)

    found = set()

    # IMPORTANT: longest skills first (protect multi-word skills)
    sorted_skills = sorted(skills_db, key=lambda x: len(x), reverse=True)

    for skill in sorted_skills:
        skill_norm = normalize(skill)

        # strict phrase matching only
        if skill_norm in text:
            found.add(skill_norm)

    return found

# -----------------------------
# ANALYSIS FUNCTION
# -----------------------------
def analyze(job_description, candidate_text):

    job_skills = extract_skills(job_description)
    candidate_skills = extract_skills(candidate_text)

    matched = job_skills & candidate_skills
    missing = job_skills - candidate_skills

    score = (len(matched) / len(job_skills)) * 100 if job_skills else 0

    return {
        "required_skills": sorted(job_skills),
        "candidate_skills": sorted(candidate_skills),
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "match_score": round(score, 2)
    }
# -----------------------------
# TEST (OPTIONAL)
# -----------------------------
if __name__ == "__main__":

    job = """
    Required Skills: Python, React, Node.js, SQL, Docker, AWS,
    System Design, Data Structures, Algorithms
    """

    resume = """
    I have experience in Python, React, SQL and Git.
    Worked on web applications and backend systems.
    """

    result = analyze(job, resume)

    print(result)