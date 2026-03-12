def generate_feedback(score, missing):

    if score > 80:
        return "Excellent candidate for this job."

    elif score > 60:
        return "Good candidate but should improve: " + ", ".join(missing[:3])

    else:
        return "Low match. Candidate should learn: " + ", ".join(missing[:5])