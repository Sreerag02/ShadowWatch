import pandas as pd
from pathlib import Path


DATA_DIR = Path("../data/metro_telecom")

INVESTIGATIONS_FILE = DATA_DIR / "investigations.csv"
CASES_FILE = DATA_DIR / "cases.csv"
ALERTS_FILE = DATA_DIR / "alerts.csv"
GROUND_TRUTH_FILE = DATA_DIR / "ground_truth.csv"


print("\n" + "=" * 75)
print("        SHADOWWATCH - R007 INVESTIGATION DURATION ANALYSIS")
print("=" * 75)


# ---------------------------------------------------------
# 1. Load data
# ---------------------------------------------------------

investigations = pd.read_csv(INVESTIGATIONS_FILE)
cases = pd.read_csv(CASES_FILE)
alerts = pd.read_csv(ALERTS_FILE)
ground_truth = pd.read_csv(GROUND_TRUTH_FILE)

print(f"\nInvestigation records : {len(investigations)}")
print(f"Case records          : {len(cases)}")
print(f"Alert records         : {len(alerts)}")
print(f"Ground-truth records  : {len(ground_truth)}")


# ---------------------------------------------------------
# 2. Convert timestamps
# ---------------------------------------------------------

investigations["started_at"] = pd.to_datetime(
    investigations["started_at"],
    errors="coerce"
)

investigations["completed_at"] = pd.to_datetime(
    investigations["completed_at"],
    errors="coerce"
)


# ---------------------------------------------------------
# 3. Calculate investigation duration
# ---------------------------------------------------------

investigations["duration_minutes"] = (
    investigations["completed_at"]
    - investigations["started_at"]
).dt.total_seconds() / 60


# ---------------------------------------------------------
# 4. Join cases and alerts
# ---------------------------------------------------------

analysis_df = investigations.merge(
    cases[
        [
            "case_id",
            "alert_id"
        ]
    ],
    on="case_id",
    how="left"
)

analysis_df = analysis_df.merge(
    alerts[
        [
            "alert_id",
            "severity",
            "category"
        ]
    ],
    on="alert_id",
    how="left"
)


# ---------------------------------------------------------
# 5. Display duration statistics
# ---------------------------------------------------------

print("\n" + "-" * 75)
print("OVERALL DURATION STATISTICS")
print("-" * 75)

print(
    analysis_df["duration_minutes"].describe()
)


# ---------------------------------------------------------
# 6. Duration statistics by severity
# ---------------------------------------------------------

print("\n" + "-" * 75)
print("DURATION BY ALERT SEVERITY")
print("-" * 75)

severity_stats = (
    analysis_df
    .groupby("severity")["duration_minutes"]
    .agg(
        ["count", "min", "median", "mean", "max"]
    )
    .round(2)
)

print(severity_stats)


# ---------------------------------------------------------
# 7. Duration statistics by category
# ---------------------------------------------------------

print("\n" + "-" * 75)
print("DURATION BY ALERT CATEGORY")
print("-" * 75)

category_stats = (
    analysis_df
    .groupby("category")["duration_minutes"]
    .agg(
        ["count", "min", "median", "mean", "max"]
    )
    .round(2)
)

print(category_stats)


# ---------------------------------------------------------
# 8. Show shortest investigations
# ---------------------------------------------------------

print("\n" + "-" * 75)
print("10 SHORTEST INVESTIGATIONS")
print("-" * 75)

shortest = (
    analysis_df[
        [
            "investigation_id",
            "case_id",
            "severity",
            "category",
            "duration_minutes"
        ]
    ]
    .sort_values("duration_minutes")
    .head(10)
)

print(shortest.to_string(index=False))


# ---------------------------------------------------------
# 9. Ground-truth duration-related cases
# ---------------------------------------------------------

print("\n" + "-" * 75)
print("DURATION-RELATED GROUND TRUTH")
print("-" * 75)

duration_truth = ground_truth[
    ground_truth["problem_type"].str.contains(
        "DURATION|FAST|CLOSURE",
        case=False,
        na=False
    )
]

if duration_truth.empty:
    print("No duration-related ground-truth records found.")
else:
    print(
        duration_truth.to_string(index=False)
    )


# ---------------------------------------------------------
# 10. Compare ground-truth cases with durations
# ---------------------------------------------------------

if not duration_truth.empty:

    truth_cases = duration_truth["case_id"].dropna().unique()

    print("\n" + "-" * 75)
    print("DURATIONS OF GROUND-TRUTH CASES")
    print("-" * 75)

    truth_duration_data = analysis_df[
        analysis_df["case_id"].isin(truth_cases)
    ][
        [
            "investigation_id",
            "case_id",
            "severity",
            "category",
            "duration_minutes"
        ]
    ].sort_values("duration_minutes")

    print(
        truth_duration_data.to_string(index=False)
    )


print("\n" + "=" * 75)
print("R007 DATA ANALYSIS COMPLETE")
print("=" * 75)