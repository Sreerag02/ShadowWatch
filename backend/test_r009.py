import pandas as pd

from services.behaviour_analytics import (
    detect_repetitive_investigations,
    detect_duration_anomalies,
    detect_repeat_incidents,
    detect_combined_suspicious_behaviour
)


DATA_DIR = "../data/metro_telecom"


investigations = pd.read_csv(
    f"{DATA_DIR}/investigations.csv"
)

cases = pd.read_csv(
    f"{DATA_DIR}/cases.csv"
)

alerts = pd.read_csv(
    f"{DATA_DIR}/alerts.csv"
)


print("\n" + "=" * 75)
print("        SHADOWWATCH - R009 OVERLAP ANALYSIS")
print("=" * 75)


# ---------------------------------------------------------
# R006
# ---------------------------------------------------------

r006_findings = detect_repetitive_investigations(
    investigations,
    similarity_threshold=0.90
)


# ---------------------------------------------------------
# R007
# ---------------------------------------------------------

r007_findings = detect_duration_anomalies(
    investigations,
    cases,
    alerts,
    minimum_deviation_ratio=0.25
)


# ---------------------------------------------------------
# R008
# ---------------------------------------------------------

r008_findings = detect_repeat_incidents(
    alerts,
    cases,
    recurrence_window_days=10,
    minimum_incidents=4
)


print("\nDetector results:")
print(f"R006 findings: {len(r006_findings)}")
print(f"R007 findings: {len(r007_findings)}")
print(f"R008 findings: {len(r008_findings)}")


# ---------------------------------------------------------
# Display R006 cases
# ---------------------------------------------------------

r006_cases = set()

if not r006_findings.empty:

    for _, finding in r006_findings.iterrows():

        ids = str(
            finding["case_ids"]
        ).split(",")

        r006_cases.update(
            case_id.strip()
            for case_id in ids
            if case_id.strip()
        )


# ---------------------------------------------------------
# Display R007 cases
# ---------------------------------------------------------

r007_cases = set()

if not r007_findings.empty:

    r007_cases = set(
        r007_findings["case_id"]
        .astype(str)
        .str.strip()
    )


# ---------------------------------------------------------
# Display R008 cases
# ---------------------------------------------------------

r008_cases = set()

if not r008_findings.empty:

    for _, finding in r008_findings.iterrows():

        ids = str(
            finding["case_ids"]
        ).split(",")

        r008_cases.update(
            case_id.strip()
            for case_id in ids
            if case_id.strip()
        )


print("\n" + "-" * 75)
print("CASES DETECTED BY EACH RULE")
print("-" * 75)


print("\nR006 cases:")
print(
    sorted(r006_cases)
    if r006_cases
    else "None"
)


print("\nR007 cases:")
print(
    sorted(r007_cases)
    if r007_cases
    else "None"
)


print("\nR008 cases:")
print(
    sorted(r008_cases)
    if r008_cases
    else "None"
)


# ---------------------------------------------------------
# Calculate overlaps
# ---------------------------------------------------------

r006_r007 = r006_cases & r007_cases
r006_r008 = r006_cases & r008_cases
r007_r008 = r007_cases & r008_cases

all_three = (
    r006_cases
    & r007_cases
    & r008_cases
)


print("\n" + "-" * 75)
print("RULE OVERLAPS")
print("-" * 75)


print("\nR006 + R007:")
print(
    sorted(r006_r007)
    if r006_r007
    else "None"
)


print("\nR006 + R008:")
print(
    sorted(r006_r008)
    if r006_r008
    else "None"
)


print("\nR007 + R008:")
print(
    sorted(r007_r008)
    if r007_r008
    else "None"
)


print("\nR006 + R007 + R008:")
print(
    sorted(all_three)
    if all_three
    else "None"
)


# ---------------------------------------------------------
# Run R009
# ---------------------------------------------------------

r009_findings = detect_combined_suspicious_behaviour(
    r006_findings,
    r007_findings,
    r008_findings,
    minimum_rules=2
)


print("\n" + "-" * 75)
print("R009 COMBINED FINDINGS")
print("-" * 75)


print(
    f"\nNumber of R009 findings: "
    f"{len(r009_findings)}"
)


if not r009_findings.empty:

    for _, finding in r009_findings.iterrows():

        print(
            f"\nCase ID        : "
            f"{finding['case_id']}"
        )

        print(
            f"Triggered rules: "
            f"{finding['triggered_rules']}"
        )

        print(
            f"Rule count     : "
            f"{finding['rule_count']}"
        )

        print(
            f"Reason         : "
            f"{finding['reason']}"
        )

        print(
            f"Evidence       : "
            f"{finding['evidence']}"
        )


print("\n" + "=" * 75)
print("R009 OVERLAP ANALYSIS COMPLETE")
print("=" * 75)