import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
try:
    from .data_loader import load_candidates
    from .text_utils import split_skills
except ImportError:  # Support ``python train_model.py`` from backend/.
    from data_loader import load_candidates
    from text_utils import split_skills

df = load_candidates()

MIN_SAMPLES = 5
counts = df["job_role"].value_counts()
print(counts, "\n")

rare = counts[counts < MIN_SAMPLES].index.tolist()
print("Dropped rare roles:", rare)
df = df[~df["job_role"].isin(rare)]
X_train, X_test, y_train, y_test = train_test_split(
    df["skills_text"], df["job_role"],
    test_size=0.2, random_state=42, stratify=df["job_role"])

def build():
    return Pipeline([
        ("tfidf", TfidfVectorizer(tokenizer=split_skills, token_pattern=None, lowercase=False)),
        ("nb", MultinomialNB()),
    ])

model = build().fit(X_train, y_train)
pred = model.predict(X_test)
print("Accuracy:", round(accuracy_score(y_test, pred), 3))
print(classification_report(y_test, pred))

final = build().fit(df["skills_text"], df["job_role"])      # retrain on all data
out = Path(__file__).parent / "models"
out.mkdir(exist_ok=True)
joblib.dump(final, out / "role_model.pkl")
print("Saved models/role_model.pkl")
