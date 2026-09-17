import pandas as pd
from pathlib import Path

from services.behaviour_analytics import (
    detect_repeat_incidents
)

DATA_PATH = Path(
    "../data/metro_telecom"
)

print("\n" + "=" * 75)
print("        SHADOWWATCH - R008 REPEAT INCIDENT TEST")
print("=" * 75)

alerts = pd.read_csv(
    DATA_PATH / "alerts.csv"
)

cases = pd.read_csv(
    DATA_PATH / "cases.csv"
)

print(
    f"\nAlert records loaded: {len(alerts)}"
)

print(
    f"Case records loaded: {len(cases)}"
)

findings = detect_repeat_incidents(
    alerts,
    cases,
    recurrence_window_days=10,
    minimum_incidents=4
)

print("\n" + "-" * 75)
print("R008 DETECTION RESULTS")
print("-" * 75)

print(
    f"\nNumber of findings: {len(findings)}"
)

if findings.empty:
    print(
        "\nNo repeat incident patterns detected."
    )
else:
    print(
        "\nRepeat incident patterns:\n"
    )

    print(
        findings.to_string(index=False)
    )

print("\n" + "=" * 75)
print("R008 TEST COMPLETE")
print("=" * 75)