import pandas as pd
from pathlib import Path

from services.behaviour_analytics import (
    detect_repetitive_investigations
)


# ============================================================
# FILE PATHS
# ============================================================

DATA_DIR = Path("../data/metro_telecom")

INVESTIGATIONS_FILE = DATA_DIR / "investigations.csv"
GROUND_TRUTH_FILE = DATA_DIR / "ground_truth.csv"


print("\n" + "=" * 70)
print("        SHADOWWATCH - R006 GROUND-TRUTH VALIDATION")
print("=" * 70)


# ============================================================
# 1. LOAD DATA
# ============================================================

investigations = pd.read_csv(
    INVESTIGATIONS_FILE
)

ground_truth = pd.read_csv(
    GROUND_TRUTH_FILE
)

print(
    f"\nInvestigation records: {len(investigations)}"
)

print(
    f"Ground-truth records: {len(ground_truth)}"
)


# ============================================================
# 2. RUN R006 DETECTOR
# ============================================================

predicted_findings = detect_repetitive_investigations(
    investigations,
    similarity_threshold=0.90
)


# ============================================================
# 3. EXTRACT PREDICTED CASE IDs
# ============================================================

predicted_cases = set()

if not predicted_findings.empty:

    for case_list in predicted_findings["case_ids"]:

        cases = [
            case.strip()
            for case in case_list.split(",")
        ]

        predicted_cases.update(cases)


# ============================================================
# 4. EXTRACT R006 GROUND TRUTH
# ============================================================

r006_truth = ground_truth[
    ground_truth["problem_type"]
    == "REPETITIVE_INVESTIGATION"
].copy()


# Only records expected to be detected
expected_cases = set(
    r006_truth[
        r006_truth["expected_detection"] == True
    ]["case_id"]
)


# ============================================================
# 5. CALCULATE TP / FP / FN
# ============================================================

true_positives = predicted_cases & expected_cases

false_positives = predicted_cases - expected_cases

false_negatives = expected_cases - predicted_cases


TP = len(true_positives)
FP = len(false_positives)
FN = len(false_negatives)


# ============================================================
# 6. CALCULATE METRICS
# ============================================================

if TP + FP > 0:
    precision = TP / (TP + FP)
else:
    precision = 0.0


if TP + FN > 0:
    recall = TP / (TP + FN)
else:
    recall = 0.0


if precision + recall > 0:
    f1 = (
        2 * precision * recall
        / (precision + recall)
    )
else:
    f1 = 0.0


# ============================================================
# 7. DISPLAY RESULTS
# ============================================================

print("\n" + "-" * 70)
print("R006 VALIDATION RESULTS")
print("-" * 70)

print(f"\nExpected R006 cases : {len(expected_cases)}")
print(f"Predicted cases     : {len(predicted_cases)}")

print(f"\nTrue Positives (TP) : {TP}")
print(f"False Positives (FP): {FP}")
print(f"False Negatives (FN): {FN}")

print(
    f"\nPrecision           : {precision:.4f}"
)

print(
    f"Recall              : {recall:.4f}"
)

print(
    f"F1 Score            : {f1:.4f}"
)


# ============================================================
# 8. SHOW CASE DETAILS
# ============================================================

print("\n" + "-" * 70)
print("TRUE POSITIVES")
print("-" * 70)

for case_id in sorted(true_positives):
    print(case_id)


print("\n" + "-" * 70)
print("FALSE POSITIVES")
print("-" * 70)

if false_positives:
    for case_id in sorted(false_positives):
        print(case_id)
else:
    print("None")


print("\n" + "-" * 70)
print("FALSE NEGATIVES")
print("-" * 70)

if false_negatives:
    for case_id in sorted(false_negatives):
        print(case_id)
else:
    print("None")


print("\n" + "=" * 70)
print("R006 VALIDATION COMPLETE")
print("=" * 70)