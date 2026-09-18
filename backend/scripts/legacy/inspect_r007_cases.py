"""Preserved historical report; execute explicitly as a module."""

def main():
    import pandas as pd
    from pathlib import Path


    from app.core.config import DATA_DIR as DATA_ROOT
    DATA_DIR = DATA_ROOT / "metro_telecom"

    investigations = pd.read_csv(
        DATA_DIR / "investigations.csv"
    )

    cases = pd.read_csv(
        DATA_DIR / "cases.csv"
    )

    alerts = pd.read_csv(
        DATA_DIR / "alerts.csv"
    )


    # ---------------------------------------------------------
    # Convert timestamps
    # ---------------------------------------------------------

    investigations["started_at"] = pd.to_datetime(
        investigations["started_at"],
        errors="coerce"
    )

    investigations["completed_at"] = pd.to_datetime(
        investigations["completed_at"],
        errors="coerce"
    )

    investigations["duration_minutes"] = (
        investigations["completed_at"]
        - investigations["started_at"]
    ).dt.total_seconds() / 60


    # ---------------------------------------------------------
    # Join cases and alerts
    # ---------------------------------------------------------

    df = investigations.merge(
        cases[
            [
                "case_id",
                "alert_id",
                "status",
                "resolution",
                "closure_reason"
            ]
        ],
        on="case_id",
        how="left"
    )

    df = df.merge(
        alerts[
            [
                "alert_id",
                "severity",
                "category",
                "description"
            ]
        ],
        on="alert_id",
        how="left"
    )


    # ---------------------------------------------------------
    # Select the 7 one-minute critical investigations
    # ---------------------------------------------------------

    anomalies = df[
        (df["severity"] == "CRITICAL") &
        (df["duration_minutes"] == 1)
    ].copy()


    columns = [
        "investigation_id",
        "case_id",
        "severity",
        "category",
        "duration_minutes",
        "analyst_id",
        "evidence_present",
        "evidence_count",
        "root_cause_identified",
        "analyst_notes",
        "status",
        "resolution",
        "closure_reason",
        "description"
    ]


    print("\n" + "=" * 100)
    print("        R007 - INSPECTION OF ONE-MINUTE CRITICAL INVESTIGATIONS")
    print("=" * 100)

    print(f"\nNumber of cases: {len(anomalies)}")

    for _, row in anomalies.iterrows():

        print("\n" + "-" * 100)

        for column in columns:

            print(
                f"{column:25}: {row.get(column)}"
            )


    print("\n" + "=" * 100)
    print("R007 CASE INSPECTION COMPLETE")
    print("=" * 100)

if __name__ == "__main__":
    main()
