skills_db = [
"python","java","c++","sql","machine learning","deep learning",
"data analysis","pandas","numpy","tensorflow",
"html","css","javascript","react","nodejs",
"flask","django","docker","aws","git"
]

def extract_skills(text):

    skills = []

    for skill in skills_db:

        if skill in text:
            skills.append(skill)

    return list(set(skills))