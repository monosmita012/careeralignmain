"""Train and evaluate CareerAlign's seven-class TF-IDF + Naive Bayes baseline.

Run from the repository root with::

    python backend/train_careeralign_classifier.py

The saved train/test split is used as-is. TF-IDF is fitted only on training
text, then used to transform the held-out test text.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.naive_bayes import MultinomialNB


BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = BACKEND_DIR / "data" / "processed"
MODEL_DIR = BACKEND_DIR / "models"
TRAIN_PATH = DATA_DIR / "careeralign_train.parquet"
TEST_PATH = DATA_DIR / "careeralign_test.parquet"

VECTOR_PATH = MODEL_DIR / "tfidf_vectorizer.joblib"
CLASSIFIER_PATH = MODEL_DIR / "role_classifier.joblib"
METADATA_PATH = MODEL_DIR / "role_classifier_metadata.json"

TEXT_COLUMN = "text"
TARGET_COLUMN = "career_role"
CLASS_ORDER = [
    "Data Analyst",
    "Data Engineer",
    "Business Analyst",
    "Project Manager",
    "Product Manager",
    "QA Automation Engineer",
    "System Administrator",
]
EXPECTED_TRAIN_ROWS = 16_956
EXPECTED_TEST_ROWS = 4_239
VECTOR_CONFIG: dict[str, Any] = {
    "lowercase": True,
    "strip_accents": "unicode",
    "ngram_range": (1, 2),
    "min_df": 2,
    "max_df": 0.95,
    "sublinear_tf": True,
}


def load_and_validate_splits() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the prepared splits and fail early if their contract has changed."""
    for path in (TRAIN_PATH, TEST_PATH):
        if not path.is_file():
            raise FileNotFoundError(f"Required prepared split is missing: {path}")

    train = pd.read_parquet(TRAIN_PATH)
    test = pd.read_parquet(TEST_PATH)
    required = {TEXT_COLUMN, TARGET_COLUMN}
    for name, frame in (("train", train), ("test", test)):
        missing_columns = required - set(frame.columns)
        if missing_columns:
            raise ValueError(f"{name} split is missing columns: {sorted(missing_columns)}")
        if frame[[TEXT_COLUMN, TARGET_COLUMN]].isna().any().any():
            raise ValueError(f"{name} split has missing text or target values")
        if not frame[TEXT_COLUMN].map(lambda value: isinstance(value, str)).all():
            raise TypeError(f"{name} split contains non-string text values")

    if len(train) != EXPECTED_TRAIN_ROWS or len(test) != EXPECTED_TEST_ROWS:
        raise ValueError(
            "Prepared split sizes changed: "
            f"train={len(train)} (expected {EXPECTED_TRAIN_ROWS}), "
            f"test={len(test)} (expected {EXPECTED_TEST_ROWS})"
        )

    for name, frame in (("train", train), ("test", test)):
        found_classes = set(frame[TARGET_COLUMN].unique())
        if found_classes != set(CLASS_ORDER):
            raise ValueError(
                f"{name} split classes differ from the approved seven classes: "
                f"{sorted(found_classes)}"
            )

    if len(train) + len(test) != 21_195:
        raise ValueError("Train/test total does not equal the approved 21,195 rows")

    return train, test


def main() -> None:
    # Refuse to overwrite prior model artifacts; review/remove them explicitly
    # before intentionally training a replacement.
    existing = [path for path in (VECTOR_PATH, CLASSIFIER_PATH, METADATA_PATH) if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing model artifacts: "
            + ", ".join(str(path) for path in existing)
        )

    train, test = load_and_validate_splits()
    y_train = train[TARGET_COLUMN]
    y_test = test[TARGET_COLUMN]

    print(f"Input verification: train={len(train)}, test={len(test)}, total={len(train) + len(test)}")
    print(f"Classes: {CLASS_ORDER}")

    # Fit the vocabulary and IDF weights on training text only to prevent
    # information from the held-out test set leaking into vectorization.
    vectorizer = TfidfVectorizer(**VECTOR_CONFIG)
    X_train = vectorizer.fit_transform(train[TEXT_COLUMN])
    X_test = vectorizer.transform(test[TEXT_COLUMN])

    print(f"Vocabulary size: {len(vectorizer.vocabulary_)}")
    print(f"Training matrix shape: {X_train.shape}; non-zero values: {X_train.nnz}")
    print(f"Test matrix shape: {X_test.shape}; non-zero values: {X_test.nnz}")

    classifier = MultinomialNB()
    classifier.fit(X_train, y_train)
    predictions = classifier.predict(X_test)

    accuracy = float(accuracy_score(y_test, predictions))
    per_class_p, per_class_r, per_class_f, support = precision_recall_fscore_support(
        y_test,
        predictions,
        labels=CLASS_ORDER,
        zero_division=0,
    )
    macro = precision_recall_fscore_support(
        y_test, predictions, labels=CLASS_ORDER, average="macro", zero_division=0
    )
    weighted = precision_recall_fscore_support(
        y_test, predictions, labels=CLASS_ORDER, average="weighted", zero_division=0
    )

    print(f"Accuracy: {accuracy:.6f}")
    print(
        "Macro precision/recall/F1: "
        f"{macro[0]:.6f} / {macro[1]:.6f} / {macro[2]:.6f}"
    )
    print(
        "Weighted precision/recall/F1: "
        f"{weighted[0]:.6f} / {weighted[1]:.6f} / {weighted[2]:.6f}"
    )

    print("\nPer-class classification report:")
    print("Class | Precision | Recall | F1 | Support")
    for index, label in enumerate(CLASS_ORDER):
        print(
            f"{label} | {per_class_p[index]:.6f} | {per_class_r[index]:.6f} | "
            f"{per_class_f[index]:.6f} | {int(support[index])}"
        )

    matrix = confusion_matrix(y_test, predictions, labels=CLASS_ORDER)
    print("\nConfusion matrix (rows=actual, columns=predicted; fixed class order):")
    print("Actual \\ Predicted | " + " | ".join(CLASS_ORDER))
    for label, row in zip(CLASS_ORDER, matrix):
        print(label + " | " + " | ".join(str(int(value)) for value in row))

    confusion_pairs = [
        (int(matrix[i, j]), CLASS_ORDER[i], CLASS_ORDER[j])
        for i in range(len(CLASS_ORDER))
        for j in range(len(CLASS_ORDER))
        if i != j and matrix[i, j] > 0
    ]
    confusion_pairs.sort(key=lambda item: (-item[0], item[1], item[2]))
    print("\nMost common confusion pairs (actual -> predicted):")
    for count, actual, predicted in confusion_pairs[:10]:
        print(f"{actual} -> {predicted}: {count}")

    report = classification_report(
        y_test,
        predictions,
        labels=CLASS_ORDER,
        output_dict=True,
        zero_division=0,
    )
    f1_by_class = {label: float(report[label]["f1-score"]) for label in CLASS_ORDER}
    precision_by_class = {label: float(report[label]["precision"]) for label in CLASS_ORDER}
    recall_by_class = {label: float(report[label]["recall"]) for label in CLASS_ORDER}
    print(
        "\nBest F1 class: "
        f"{max(CLASS_ORDER, key=lambda label: f1_by_class[label])} "
        f"({max(f1_by_class.values()):.6f})"
    )
    print(
        "Worst F1 class: "
        f"{min(CLASS_ORDER, key=lambda label: f1_by_class[label])} "
        f"({min(f1_by_class.values()):.6f})"
    )
    print(
        "Lowest recall: "
        f"{min(CLASS_ORDER, key=lambda label: recall_by_class[label])} "
        f"({min(recall_by_class.values()):.6f})"
    )
    print(
        "Lowest precision: "
        f"{min(CLASS_ORDER, key=lambda label: precision_by_class[label])} "
        f"({min(precision_by_class.values()):.6f})"
    )

    # The majority class is selected using training labels only; its accuracy
    # is then measured on the same held-out test targets.
    majority_class = y_train.value_counts().idxmax()
    majority_predictions = np.full(len(y_test), majority_class, dtype=object)
    majority_accuracy = float(accuracy_score(y_test, majority_predictions))
    absolute_improvement = accuracy - majority_accuracy
    relative_improvement = (
        absolute_improvement / majority_accuracy * 100 if majority_accuracy else float("nan")
    )
    print(f"\nTraining majority class: {majority_class}")
    print(f"Majority baseline accuracy: {majority_accuracy:.6f}")
    print(f"Naive Bayes accuracy: {accuracy:.6f}")
    print(f"Absolute improvement: {absolute_improvement:.6f} ({absolute_improvement * 100:.3f} percentage points)")
    print(f"Relative improvement: {relative_improvement:.3f}%")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, VECTOR_PATH)
    joblib.dump(classifier, CLASSIFIER_PATH)
    metadata = {
        "text_column": TEXT_COLUMN,
        "target_column": TARGET_COLUMN,
        "class_order": CLASS_ORDER,
        "vectorizer": {
            **VECTOR_CONFIG,
            "ngram_range": list(VECTOR_CONFIG["ngram_range"]),
        },
        "classifier": "sklearn.naive_bayes.MultinomialNB",
        "train_rows": len(train),
        "test_rows": len(test),
        "accuracy": accuracy,
        "macro": {"precision": float(macro[0]), "recall": float(macro[1]), "f1": float(macro[2])},
        "weighted": {"precision": float(weighted[0]), "recall": float(weighted[1]), "f1": float(weighted[2])},
        "majority_class": majority_class,
        "majority_baseline_accuracy": majority_accuracy,
        "scikit_learn_version": sklearn.__version__,
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print("\nSaved artifacts:")
    print(VECTOR_PATH)
    print(CLASSIFIER_PATH)
    print(METADATA_PATH)
    print("TF-IDF fitted on training text only: yes")


if __name__ == "__main__":
    main()
