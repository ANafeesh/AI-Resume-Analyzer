from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def calculate_match(skills, job_desc):

    resume_text = " ".join(skills)

    docs = [resume_text, job_desc]

    tfidf = TfidfVectorizer()

    matrix = tfidf.fit_transform(docs)

    similarity = cosine_similarity(matrix)

    score = similarity[0][1] * 100

    return round(score,2)