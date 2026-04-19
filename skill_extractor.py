import re

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

# Noise words to ignore accidental matches
noise_words = {"experience", "required", "responsibilities", "skills"}

def normalize(text):
    text = text.lower()
    text = text.replace("node.js", "nodejs")
    text = text.replace("c ++", "c++")
    text = re.sub(r"[^a-z0-9+# ]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_skills(text):
    text = normalize(text)

    extracted = set()

    # 🔥 Sort skills by length (important fix)
    # ensures "data structures" checked before "data"
    sorted_skills = sorted(skills_db, key=lambda x: len(x), reverse=True)

    for skill in sorted_skills:
        skill_norm = normalize(skill)

        # 🔥 strict word boundary match (IMPORTANT FIX)
        pattern = r'\b' + re.escape(skill_norm) + r'\b'

        if re.search(pattern, text):
            if skill_norm not in noise_words:
                extracted.add(skill)

    return sorted(extracted)