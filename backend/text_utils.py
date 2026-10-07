def split_skills(text):
    return [s.strip().lower() for s in str(text).split(",") if s.strip()]
