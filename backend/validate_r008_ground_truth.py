import pandas as pd
from pathlib import Path

from services.behaviour_analytics import (
    detect_repeat_incidents
)


DATA_DIR = Path("../data/metro_telecom")

ALERTS_PATH = DATA_DIR / "alerts.csv"
CASES_PATH = DATA_DIR / "cases.csv"
GROUND_TRUTH_PATH = DATA_DIR / "ground_truth.csv"


print("\n" + "=" * 75)
print("        SHADOWWATCH - R008 GROUND TRUTH VALIDATION")
print("=" * 75)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

alerts = pd.read_csv(ALERTS_PATH)
cases = pd.read_csv(CASES_PATH)
ground_truth = pd.read_csv(GROUND_TRUTH_PATH)

print(f"\nAlerts loaded: {len(alerts)}")
print(f"Cases loaded: {len(cases)}")
print(f"Ground truth records loaded: {len(ground_truth)}")


# ---------------------------------------------------------
# R008 GROUND TRUTH
# ---------------------------------------------------------

r008_truth = ground_truth[
    ground_truth["problem_type"] == "REPEAT_INCIDENT"
].copy()

expected_cases = set(
    r008_truth[
        r008_truth["expected_detection"] == True
    ]["case_id"]
)

print(
    f"\nR008 expected cases: {len(expected_cases)}"
)

print(
    "Expected case IDs:",
    sorted(expected_cases)
)


# ---------------------------------------------------------
# RUN R008 DETECTOR
# ---------------------------------------------------------

findings = detect_repeat_incidents(
    alerts,
    cases,
    recurrence_window_days=10,
    minimum_incidents=4
)


print(
    f"\nR008 predicted findings: {len(findings)}"
)


# ---------------------------------------------------------
# EXTRACT PREDICTED CASE IDs
# ---------------------------------------------------------

predicted_cases = set()

if not findings.empty:

    for _, finding in findings.iterrows():

        case_ids = [
            case_id.strip()
            for case_id in str(
                finding["case_ids"]
            ).split(",")
            if case_id.strip()
        ]

        predicted_cases.update(case_ids)


# ---------------------------------------------------------
# CALCULATE METRICS
# ---------------------------------------------------------

true_positives = (
    expected_cases & predicted_cases
)

false_positives = (
    predicted_cases - expected_cases
)

false_negatives = (
    expected_cases - predicted_cases
)


tp = len(true_positives)
fp = len(false_positives)
fn = len(false_negatives)


precision = (
    tp / (tp + fp)
    if (tp + fp) > 0
    else 0
)

recall = (
    tp / (tp + fn)
    if (tp + fn) > 0
    else 0
)

f1 = (
    2 * precision * recall / (precision + recall)
    if (precision + recall) > 0
    else 0
)


# ---------------------------------------------------------
# DISPLAY RESULTS
# ---------------------------------------------------------

print("\n" + "-" * 75)
print("R008 VALIDATION RESULTS")
print("-" * 75)

print(
    f"\nExpected cases : {len(expected_cases)}"
)

print(
    f"Predicted cases: {len(predicted_cases)}"
)

print(f"\nTP: {tp}")
print(f"FP: {fp}")
print(f"FN: {fn}")

print(f"\nPrecision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1 Score : {f1:.4f}")


print("\nTrue Positives:")
print(
    sorted(true_positives)
    if true_positives
    else "None"
)

print("\nFalse Positives:")
print(
    sorted(false_positives)
    if false_positives
    else "None"
)

print("\nFalse Negatives:")
print(
    sorted(false_negatives)
    if false_negatives
    else "None"
)


print("\n" + "=" * 75)
print("R008 GROUND TRUTH VALIDATION COMPLETE")
print("=" * 75)