"""Preserved historical report; execute explicitly as a module."""

def main():
    import pandas as pd
    from pathlib import Path

    from app.core.config import DATA_DIR as DATA_ROOT
    DATA_DIR = DATA_ROOT / "alpha_bank"

    entities = pd.read_csv(DATA_DIR / "entities.csv")
    assets = pd.read_csv(DATA_DIR / "assets.csv")
    alerts = pd.read_csv(DATA_DIR / "alerts.csv")
    cases = pd.read_csv(DATA_DIR / "cases.csv")
    investigations = pd.read_csv(DATA_DIR / "investigations.csv")
    escalations = pd.read_csv(DATA_DIR / "escalations.csv")
    telemetry = pd.read_csv(DATA_DIR / "telemetry.csv")
    ground_truth = pd.read_csv(DATA_DIR / "ground_truth.csv")

    print("=== SHADOWWATCH ALPHA BANK DATA VALIDATION ===")

    # 1. Basic counts
    print("\nRecord counts:")
    print("Entities:", len(entities))
    print("Assets:", len(assets))
    print("Alerts:", len(alerts))
    print("Cases:", len(cases))
    print("Investigations:", len(investigations))
    print("Escalations:", len(escalations))
    print("Telemetry:", len(telemetry))
    print("Ground truth:", len(ground_truth))


    # 2. Duplicate IDs
    checks = {
        "entities": (entities, "entity_id"),
        "assets": (assets, "asset_id"),
        "alerts": (alerts, "alert_id"),
        "cases": (cases, "case_id"),
        "investigations": (investigations, "investigation_id"),
        "escalations": (escalations, "escalation_id"),
        "telemetry": (telemetry, "telemetry_id"),
    }

    print("\nDuplicate ID checks:")

    for name, (df, column) in checks.items():
        duplicates = df[column].duplicated().sum()

        if duplicates == 0:
            print(f"PASS - {name}")
        else:
            print(f"FAIL - {name}: {duplicates} duplicate IDs")


    # 3. Relationship validation
    print("\nRelationship checks:")

    invalid_assets = assets[
        ~assets["entity_id"].isin(entities["entity_id"])
    ]

    print(
        "assets -> entities:",
        "PASS" if invalid_assets.empty else f"FAIL ({len(invalid_assets)})"
    )

    invalid_alert_entities = alerts[
        ~alerts["entity_id"].isin(entities["entity_id"])
    ]

    print(
        "alerts -> entities:",
        "PASS" if invalid_alert_entities.empty else f"FAIL ({len(invalid_alert_entities)})"
    )

    invalid_alert_assets = alerts[
        ~alerts["asset_id"].isin(assets["asset_id"])
    ]

    print(
        "alerts -> assets:",
        "PASS" if invalid_alert_assets.empty else f"FAIL ({len(invalid_alert_assets)})"
    )

    invalid_cases = cases[
        ~cases["alert_id"].isin(alerts["alert_id"])
    ]

    print(
        "cases -> alerts:",
        "PASS" if invalid_cases.empty else f"FAIL ({len(invalid_cases)})"
    )

    invalid_investigations = investigations[
        ~investigations["case_id"].isin(cases["case_id"])
    ]

    print(
        "investigations -> cases:",
        "PASS" if invalid_investigations.empty else f"FAIL ({len(invalid_investigations)})"
    )

    invalid_escalations = escalations[
        ~escalations["case_id"].isin(cases["case_id"])
    ]

    print(
        "escalations -> cases:",
        "PASS" if invalid_escalations.empty else f"FAIL ({len(invalid_escalations)})"
    )

    invalid_telemetry_assets = telemetry[
        ~telemetry["asset_id"].isin(assets["asset_id"])
    ]

    print(
        "telemetry -> assets:",
        "PASS" if invalid_telemetry_assets.empty else f"FAIL ({len(invalid_telemetry_assets)})"
    )


    # 4. Timestamp conversion
    alerts["timestamp"] = pd.to_datetime(alerts["timestamp"])

    cases["opened_at"] = pd.to_datetime(cases["opened_at"])
    cases["closed_at"] = pd.to_datetime(cases["closed_at"])

    investigations["started_at"] = pd.to_datetime(
        investigations["started_at"]
    )

    investigations["completed_at"] = pd.to_datetime(
        investigations["completed_at"]
    )

    telemetry["timestamp"] = pd.to_datetime(
        telemetry["timestamp"]
    )

    if "escalated_at" in escalations.columns:
        escalations["escalated_at"] = pd.to_datetime(
            escalations["escalated_at"],
            errors="coerce"
        )


    # 5. Alert -> Case timestamp check
    case_alert = cases.merge(
        alerts[["alert_id", "timestamp"]],
        on="alert_id",
        how="left"
    )

    bad_case_opening = case_alert[
        case_alert["opened_at"] < case_alert["timestamp"]
    ]

    print("\nTimestamp checks:")

    print(
        "Alert before case:",
        "PASS" if bad_case_opening.empty
        else f"FAIL ({len(bad_case_opening)})"
    )


    # 6. Case open -> close check
    bad_case_closure = cases[
        cases["closed_at"] < cases["opened_at"]
    ]

    print(
        "Case opening before closure:",
        "PASS" if bad_case_closure.empty
        else f"FAIL ({len(bad_case_closure)})"
    )


    # 7. Investigation timestamps
    investigation_cases = investigations.merge(
        cases[["case_id", "opened_at", "closed_at"]],
        on="case_id",
        how="left"
    )

    bad_investigations = investigation_cases[
        (investigation_cases["started_at"] <
         investigation_cases["opened_at"])
        |
        (investigation_cases["completed_at"] <
         investigation_cases["started_at"])
        |
        (investigation_cases["completed_at"] >
         investigation_cases["closed_at"])
    ]

    print(
        "Investigation timing:",
        "PASS" if bad_investigations.empty
        else f"FAIL ({len(bad_investigations)})"
    )


    # 8. Standard severity values
    allowed_severities = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    }

    bad_severities = alerts[
        ~alerts["severity"].isin(allowed_severities)
    ]

    print(
        "\nSeverity values:",
        "PASS" if bad_severities.empty
        else f"FAIL ({len(bad_severities)})"
    )


    # 9. Confidence check
    bad_confidence = alerts[
        (alerts["confidence"] < 0)
        | (alerts["confidence"] > 1)
    ]

    print(
        "Confidence range:",
        "PASS" if bad_confidence.empty
        else f"FAIL ({len(bad_confidence)})"
    )


    # 10. Ground truth references
    gt_case_ids = ground_truth["case_id"].dropna()

    invalid_gt_cases = gt_case_ids[
        ~gt_case_ids.isin(cases["case_id"])
    ]

    print(
        "Ground truth case references:",
        "PASS" if invalid_gt_cases.empty
        else f"FAIL ({len(invalid_gt_cases)})"
    )

    print("\n=== VALIDATION COMPLETE ===")

if __name__ == "__main__":
    main()
