import pandas as pd
from pathlib import Path

from services.behaviour_analytics import (
    detect_duration_anomalies
)


DATA_DIR = Path("../data/metro_telecom")

INVESTIGATIONS_FILE = DATA_DIR / "investigations.csv"
CASES_FILE = DATA_DIR / "cases.csv"
ALERTS_FILE = DATA_DIR / "alerts.csv"
GROUND_TRUTH_FILE = DATA_DIR / "ground_truth.csv"


print("\n" + "=" * 70)
print("        SHADOWWATCH - R007 GROUND-TRUTH VALIDATION")
print("=" * 70)


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

investigations = pd.read_csv(
    INVESTIGATIONS_FILE
)

cases = pd.read_csv(
    CASES_FILE
)

alerts = pd.read_csv(
    ALERTS_FILE
)

ground_truth = pd.read_csv(
    GROUND_TRUTH_FILE
)


print(
    f"\nInvestigation records: {len(investigations)}"
)

print(
    f"Case records: {len(cases)}"
)

print(
    f"Alert records: {len(alerts)}"
)

print(
    f"Ground-truth records: {len(ground_truth)}"
)


# ---------------------------------------------------------
# Run R007 detector
# ---------------------------------------------------------

predicted_findings = detect_duration_anomalies(
    investigations,
    cases,
    alerts
)


# ---------------------------------------------------------
# Get predicted cases
# ---------------------------------------------------------

predicted_cases = set()

if not predicted_findings.empty:

    predicted_cases = set(
        predicted_findings["case_id"]
    )


# ---------------------------------------------------------
# Get R007 ground truth
# ---------------------------------------------------------

r007_truth = ground_truth[
    ground_truth["problem_type"]
    == "FAST_CRITICAL_CLOSURE"
].copy()


expected_cases = set(
    r007_truth[
        r007_truth["expected_detection"] == True
    ]["case_id"]
)


# ---------------------------------------------------------
# Identify ground-truth cases observable by R007
# ---------------------------------------------------------

investigation_case_ids = set(
    investigations["case_id"]
)

observable_expected_cases = (
    expected_cases
    & investigation_case_ids
)

unobservable_expected_cases = (
    expected_cases
    - investigation_case_ids
)


# ---------------------------------------------------------
# Calculate TP / FP / FN
# ---------------------------------------------------------

true_positives = (
    predicted_cases
    & observable_expected_cases
)

false_positives = (
    predicted_cases
    - observable_expected_cases
)

false_negatives = (
    observable_expected_cases
    - predicted_cases
)


TP = len(true_positives)
FP = len(false_positives)
FN = len(false_negatives)


# ---------------------------------------------------------
# Calculate metrics
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Display results
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("R007 VALIDATION RESULTS")
print("-" * 70)


print(
    f"\nTotal R007 ground-truth cases : "
    f"{len(expected_cases)}"
)

print(
    f"Observable R007 cases         : "
    f"{len(observable_expected_cases)}"
)

print(
    f"Predicted cases               : "
    f"{len(predicted_cases)}"
)

print(
    f"Unobservable ground-truth cases: "
    f"{len(unobservable_expected_cases)}"
)


print(
    f"\nTrue Positives (TP) : {TP}"
)

print(
    f"False Positives (FP): {FP}"
)

print(
    f"False Negatives (FN): {FN}"
)


print(
    f"\nPrecision           : "
    f"{precision:.4f}"
)

print(
    f"Recall              : "
    f"{recall:.4f}"
)

print(
    f"F1 Score            : "
    f"{f1:.4f}"
)


# ---------------------------------------------------------
# True positives
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("TRUE POSITIVES")
print("-" * 70)


if true_positives:

    for case_id in sorted(true_positives):
        print(case_id)

else:

    print("None")


# ---------------------------------------------------------
# False positives
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("FALSE POSITIVES")
print("-" * 70)


if false_positives:

    for case_id in sorted(false_positives):
        print(case_id)

else:

    print("None")


# ---------------------------------------------------------
# False negatives
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("FALSE NEGATIVES")
print("-" * 70)


if false_negatives:

    for case_id in sorted(false_negatives):
        print(case_id)

else:

    print("None")


# ---------------------------------------------------------
# Unobservable cases
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("UNOBSERVABLE GROUND-TRUTH CASES")
print("-" * 70)


if unobservable_expected_cases:

    for case_id in sorted(
        unobservable_expected_cases
    ):

        print(
            f"{case_id} "
            f"(no investigation record)"
        )

else:

    print("None")


print("\n" + "=" * 70)
print("R007 VALIDATION COMPLETE")
print("=" * 70)