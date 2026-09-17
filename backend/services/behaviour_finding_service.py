import pandas as pd
from sqlalchemy import text

from database import engine
from services.behaviour_analytics import (
    detect_repetitive_investigations,
    detect_duration_anomalies,
    detect_repeat_incidents,
    detect_combined_suspicious_behaviour,
)


def _load_case_entity(connection, case_id):
    """
    Find the entity associated with the requested case.
    """
    query = text("""
        SELECT entity_id
        FROM cases
        WHERE case_id = :case_id
    """)

    row = connection.execute(
        query,
        {"case_id": case_id}
    ).mappings().first()

    if row is None:
        return None

    return row["entity_id"]


def _load_entity_data(connection, entity_id):
    """
    Load operational data belonging only to one entity.

    This prevents behavioural baselines and patterns from
    being calculated across different organizations.
    """

    cases_df = pd.read_sql(
        text("""
            SELECT *
            FROM cases
            WHERE entity_id = :entity_id
        """),
        connection,
        params={"entity_id": entity_id}
    )

    alerts_df = pd.read_sql(
        text("""
            SELECT *
            FROM alerts
            WHERE entity_id = :entity_id
        """),
        connection,
        params={"entity_id": entity_id}
    )

    investigations_df = pd.read_sql(
        text("""
            SELECT i.*
            FROM investigations i
            JOIN cases c
                ON i.case_id = c.case_id
            WHERE c.entity_id = :entity_id
        """),
        connection,
        params={"entity_id": entity_id}
    )

    return investigations_df, cases_df, alerts_df


def get_behaviour_findings(case_id):
    """
    Run R006-R009 behavioural detectors for the organization
    associated with the requested case.
    """

    with engine.connect() as connection:

        # -----------------------------------------------------
        # Find the organization of the requested case
        # -----------------------------------------------------

        entity_id = _load_case_entity(
            connection,
            case_id
        )

        if entity_id is None:
            return []

        # -----------------------------------------------------
        # Load only this organization's operational data
        # -----------------------------------------------------

        (
            investigations_df,
            cases_df,
            alerts_df
        ) = _load_entity_data(
            connection,
            entity_id
        )

    # ---------------------------------------------------------
    # R006 - Repetitive / copied investigation notes
    # ---------------------------------------------------------

    r006 = detect_repetitive_investigations(
        investigations_df
    )

    # ---------------------------------------------------------
    # R007 - Investigation duration anomaly
    # ---------------------------------------------------------

    r007 = detect_duration_anomalies(
        investigations_df,
        cases_df,
        alerts_df
    )

    # ---------------------------------------------------------
    # R008 - Repeat incident pattern
    # ---------------------------------------------------------

    r008 = detect_repeat_incidents(
        alerts_df,
        cases_df,
        recurrence_window_days=10,
        minimum_incidents=4
    )

    # ---------------------------------------------------------
    # R009 - Combined suspicious investigation behaviour
    # ---------------------------------------------------------

    r009 = detect_combined_suspicious_behaviour(
        r006,
        r007,
        r008,
        minimum_rules=2
    )

    findings = []

    # ---------------------------------------------------------
    # R006
    # ---------------------------------------------------------

    if not r006.empty:

        for _, row in r006.iterrows():

            case_ids = str(
                row.get("case_ids", "")
            ).split(",")

            case_ids = [
                x.strip()
                for x in case_ids
            ]

            if case_id not in case_ids:
                continue

            findings.append({
                "rule_id": "R006",
                "problem_type": "REPETITIVE_INVESTIGATION",
                "severity": "BEHAVIOURAL",
                "reason": row.get("reason"),
                "evidence": (
                    f"Similarity score: "
                    f"{row.get('similarity_score')}; "
                    f"related investigation records: "
                    f"{row.get('repetition_count')}"
                )
            })

    # ---------------------------------------------------------
    # R007
    # ---------------------------------------------------------

    if not r007.empty:

        for _, row in r007.iterrows():

            if str(
                row.get("case_id", "")
            ).strip() != case_id:
                continue

            findings.append({
                "rule_id": "R007",
                "problem_type": "INVESTIGATION_DURATION_ANOMALY",
                "severity": str(
                    row.get("severity", "UNKNOWN")
                ),
                "reason": row.get("reason"),
                "evidence": (
                    f"Duration: "
                    f"{row.get('duration_minutes')} minutes; "
                    f"baseline: "
                    f"{row.get('baseline_duration_minutes')} minutes; "
                    f"ratio: "
                    f"{row.get('duration_ratio')}"
                )
            })

    # ---------------------------------------------------------
    # R008
    # ---------------------------------------------------------

    if not r008.empty:

        for _, row in r008.iterrows():

            case_ids = str(
                row.get("case_ids", "")
            ).split(",")

            case_ids = [
                x.strip()
                for x in case_ids
            ]

            if case_id not in case_ids:
                continue

            findings.append({
                "rule_id": "R008",
                "problem_type": "REPEAT_INCIDENT_PATTERN",
                "severity": "BEHAVIOURAL",
                "reason": row.get("reason"),
                "evidence": (
                    f"Asset: {row.get('asset_id')}; "
                    f"category: {row.get('category')}; "
                    f"incident count: "
                    f"{row.get('incident_count')}; "
                    f"time span: "
                    f"{row.get('time_span_days')} days"
                )
            })

    # ---------------------------------------------------------
    # R009
    # ---------------------------------------------------------

    if not r009.empty:

        for _, row in r009.iterrows():

            if str(
                row.get("case_id", "")
            ).strip() != case_id:
                continue

            findings.append({
                "rule_id": "R009",
                "problem_type": (
                    "COMBINED_SUSPICIOUS_INVESTIGATION_BEHAVIOUR"
                ),
                "severity": "BEHAVIOURAL",
                "reason": row.get("reason"),
                "evidence": row.get("evidence")
            })

    return findings