import pandas as pd
from pathlib import Path

from services.behaviour_analytics import (
    detect_duration_anomalies
)


DATA_DIR = Path("../data/metro_telecom")

INVESTIGATIONS_FILE = DATA_DIR / "investigations.csv"
CASES_FILE = DATA_DIR / "cases.csv"
ALERTS_FILE = DATA_DIR / "alerts.csv"


print("\n" + "=" * 75)
print("        SHADOWWATCH - R007 DURATION ANOMALY TEST")
print("=" * 75)


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


print(f"\nInvestigation records loaded : {len(investigations)}")
print(f"Case records loaded          : {len(cases)}")
print(f"Alert records loaded         : {len(alerts)}")


# ---------------------------------------------------------
# Run R007 detector
# ---------------------------------------------------------

findings = detect_duration_anomalies(
    investigations,
    cases,
    alerts
)


# ---------------------------------------------------------
# Display results
# ---------------------------------------------------------

print("\n" + "-" * 75)
print("R007 DETECTION RESULTS")
print("-" * 75)

print(f"\nNumber of findings: {len(findings)}")


if findings.empty:

    print("\nNo investigation duration anomalies detected.")

else:

    print("\nInvestigation duration anomalies:\n")

    print(
        findings.to_string(index=False)
    )


print("\n" + "=" * 75)
print("R007 TEST COMPLETE")
print("=" * 75)