import pandas as pd
from pathlib import Path

from services.behaviour_analytics import (
    detect_repetitive_investigations
)


# Path to Metro Telecom investigation data
DATA_PATH = Path("../data/metro_telecom/investigations.csv")


print("\n" + "=" * 70)
print("        SHADOWWATCH - R006 BEHAVIOUR ANALYTICS TEST")
print("=" * 70)


# Load investigation data
investigations = pd.read_csv(DATA_PATH)

print(f"\nInvestigation records loaded: {len(investigations)}")


# Run R006 detector
findings = detect_repetitive_investigations(
    investigations,
    similarity_threshold=0.90
)


print("\nR006 DETECTION RESULTS")
print("-" * 70)

print(f"Number of findings: {len(findings)}")


if findings.empty:

    print("\nNo repetitive investigation patterns detected.")

else:

    print("\nRepetitive investigation findings:\n")

    print(
        findings.to_string(index=False)
    )


print("\n" + "=" * 70)
print("R006 TEST COMPLETE")
print("=" * 70)