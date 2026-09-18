"""Historical PowerGrid dataset authoring tool; explicitly running this modifies CSVs."""

def main():
    import pandas as pd
    from datetime import timedelta
    import os

    # Updated to match your new directory name
    from app.core.config import DATA_DIR
    DIR = DATA_DIR / "powergrid_utility"

    # Load baseline datasets
    alerts = pd.read_csv(f"{DIR}/alerts.csv")
    cases = pd.read_csv(f"{DIR}/cases.csv")
    investigations = pd.read_csv(f"{DIR}/investigations.csv")
    escalations = pd.read_csv(f"{DIR}/escalations.csv")
    telemetry = pd.read_csv(f"{DIR}/telemetry.csv")

    # Ensure datetimes are parsed correctly
    cases['opened_at'] = pd.to_datetime(cases['opened_at'])
    cases['closed_at'] = pd.to_datetime(cases['closed_at'])

    ground_truth = []
    def log_gt(scenario, case_id, asset_id, problem):
        ground_truth.append({"scenario_id": scenario, "entity_id": "E005", "case_id": case_id, "asset_id": asset_id, "problem_type": problem, "expected_detection": True})

    # S01: MISSING_INVESTIGATION (Drop investigation for a specific case)
    c1 = cases.iloc[5]['case_id']
    a1 = cases.iloc[5]['alert_id']
    asset1 = alerts[alerts['alert_id'] == a1]['asset_id'].values[0]
    investigations = investigations[investigations['case_id'] != c1]
    log_gt("S01", c1, asset1, "MISSING_INVESTIGATION")

    # S02: MISSING_EVIDENCE (Set evidence to false)
    c2 = cases.iloc[10]['case_id']
    a2 = cases.iloc[10]['alert_id']
    asset2 = alerts[alerts['alert_id'] == a2]['asset_id'].values[0]
    investigations.loc[investigations['case_id'] == c2, ['evidence_present', 'evidence_count']] = [False, 0]
    log_gt("S02", c2, asset2, "MISSING_EVIDENCE")

    # S03: MISSING_ESCALATION (Remove escalation for a critical case)
    c3 = cases.iloc[15]['case_id']
    a3 = cases.iloc[15]['alert_id']
    asset3 = alerts[alerts['alert_id'] == a3]['asset_id'].values[0]
    escalations = escalations[escalations['case_id'] != c3]
    log_gt("S03", c3, asset3, "MISSING_ESCALATION")

    # S04: FAST_CRITICAL_CLOSURE (Close a case in 2 minutes)
    c4 = cases.iloc[20]['case_id']
    a4 = cases.iloc[20]['alert_id']
    asset4 = alerts[alerts['alert_id'] == a4]['asset_id'].values[0]
    cases.loc[cases['case_id'] == c4, 'closed_at'] = cases.loc[cases['case_id'] == c4, 'opened_at'] + timedelta(minutes=2)
    log_gt("S04", c4, asset4, "FAST_CRITICAL_CLOSURE")

    # S05: TELEMETRY_BLIND_SPOT (Zero out telemetry for a critical asset at specific time)
    target_asset = telemetry['asset_id'].iloc[0]
    target_time = telemetry[telemetry['asset_id'] == target_asset]['timestamp'].iloc[12] # 12th hour
    telemetry.loc[(telemetry['asset_id'] == target_asset) & (telemetry['timestamp'] == target_time), 'event_count'] = 0
    log_gt("S05", "", target_asset, "TELEMETRY_BLIND_SPOT")

    # S06: REPETITIVE_INVESTIGATION (Identical notes across multiple cases)
    rep_cases = cases.iloc[30:33]['case_id'].tolist()
    investigations.loc[investigations['case_id'].isin(rep_cases), 'analyst_notes'] = "Checked logs. No issue found."
    for c in rep_cases:
        a_tmp = cases[cases['case_id'] == c]['alert_id'].values[0]
        asset_tmp = alerts[alerts['alert_id'] == a_tmp]['asset_id'].values[0]
        log_gt("S06", c, asset_tmp, "REPETITIVE_INVESTIGATION")

    # S07: REPEAT_INCIDENT (Asset with the most alerts)
    asset_counts = alerts['asset_id'].value_counts()
    repeat_asset = asset_counts.index[0]
    log_gt("S07", "", repeat_asset, "REPEAT_INCIDENT")

    # S08: KPI_GAMING_PATTERN (Fast closure + no evidence)
    c8 = cases.iloc[40]['case_id']
    a8 = cases.iloc[40]['alert_id']
    asset8 = alerts[alerts['alert_id'] == a8]['asset_id'].values[0]
    cases.loc[cases['case_id'] == c8, 'closed_at'] = cases.loc[cases['case_id'] == c8, 'opened_at'] + timedelta(minutes=1)
    investigations.loc[investigations['case_id'] == c8, ['evidence_present', 'evidence_count']] = [False, 0]
    log_gt("S08", c8, asset8, "KPI_GAMING_PATTERN")

    # Save outputs
    alerts.to_csv(f"{DIR}/alerts.csv", index=False)
    cases.to_csv(f"{DIR}/cases.csv", index=False)
    investigations.to_csv(f"{DIR}/investigations.csv", index=False)
    escalations.to_csv(f"{DIR}/escalations.csv", index=False)
    telemetry.to_csv(f"{DIR}/telemetry.csv", index=False)

    pd.DataFrame(ground_truth).to_csv(f"{DIR}/ground_truth.csv", index=False)
    print(f"Scenarios successfully injected. ground_truth.csv generated in {DIR}/")

if __name__ == "__main__":
    main()
