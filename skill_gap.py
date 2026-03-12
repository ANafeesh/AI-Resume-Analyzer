def find_skill_gap(skills, job_desc):

    job_words = job_desc.lower().split()

    missing = []

    for word in job_words:

        if word not in skills:
            missing.append(word)

    return list(set(missing))