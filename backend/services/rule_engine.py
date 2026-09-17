def analyze_critical_cases():
    from sqlalchemy import text
    from database import engine

    query = text("""
        SELECT
            c.case_id,
            c.entity_id,
            c.opened_at,
            c.closed_at,

            a.alert_id,
            a.asset_id,
            a.severity,
            a.category,

            i.investigation_id,
            i.evidence_present,
            i.evidence_count,

            e.escalation_id,
            e.escalated

        FROM cases c

        JOIN alerts a
            ON c.alert_id = a.alert_id

        LEFT JOIN investigations i
            ON c.case_id = i.case_id

        LEFT JOIN escalations e
            ON c.case_id = e.case_id

        WHERE a.severity = 'CRITICAL'

        ORDER BY c.case_id
    """)

    findings = []

    with engine.connect() as connection:

        result = connection.execute(query)

        for row in result.mappings():

            finding = evaluate_critical_case(row)
            if finding is not None:
                findings.append(finding)

    return findings


# Configurable prototype threshold, not an industry standard.
FAST_CRITICAL_CLOSURE_MINUTES = 10


def evaluate_critical_case(row):
    """Evaluate one joined CRITICAL case row without database access."""
    case_id = row["case_id"]

    reasons = []
    triggered_rules = []

    # ------------------------------------
    # Calculate closure time
    # ------------------------------------

    opened_at = row["opened_at"]
    closed_at = row["closed_at"]

    closure_minutes = None

    if opened_at and closed_at:
        closure_minutes = (
            closed_at - opened_at
        ).total_seconds() / 60

    # ------------------------------------
    # R001 - Missing investigation
    # ------------------------------------

    if row["investigation_id"] is None:

        triggered_rules.append("R001")

        reasons.append(
            "Critical alert has no investigation record"
        )

    # ------------------------------------
    # R002 - Missing evidence
    # ------------------------------------

    elif (
        row["evidence_present"] is False
        or row["evidence_count"] is None
        or row["evidence_count"] == 0
    ):

        triggered_rules.append("R002")

        reasons.append(
            "Critical investigation contains no supporting evidence"
        )

    # ------------------------------------
    # R003 - Missing escalation
    # ------------------------------------

    if (
        row["escalation_id"] is None
        or row["escalated"] is False
    ):

        triggered_rules.append("R003")

        reasons.append(
            "Critical alert was not escalated"
        )

    # ------------------------------------
    # R004 - Fast critical closure
    # ------------------------------------

    if (
        closure_minutes is not None
        and closure_minutes < FAST_CRITICAL_CLOSURE_MINUTES
    ):

        triggered_rules.append("R004")

        reasons.append(
            f"Critical case was closed unusually quickly "
            f"({closure_minutes:.1f} minutes)"
        )

    # ------------------------------------
    # Save only suspicious cases
    # ------------------------------------

    if reasons:

        return {
            "case_id": case_id,
            "entity_id": row["entity_id"],
            "alert_id": row["alert_id"],
            "asset_id": row["asset_id"],
            "severity": row["severity"],
            "category": row["category"],
            "closure_minutes": closure_minutes,
            "rules": triggered_rules,
            "reasons": reasons
        }

    return None


if __name__ == "__main__":

    results = analyze_critical_cases()

    print("\n======================================")
    print(" SHADOWWATCH RULE ENGINE V1")
    print("======================================")

    print("\nSuspicious critical cases:", len(results))

    for finding in results:

        print("\n--------------------------------------")

        print("Case:", finding["case_id"])
        print("Entity:", finding["entity_id"])
        print("Alert:", finding["alert_id"])
        print("Asset:", finding["asset_id"])
        print("Severity:", finding["severity"])
        print("Category:", finding["category"])

        if finding["closure_minutes"] is not None:
            print(
                "Closure Time:",
                f'{finding["closure_minutes"]:.1f} minutes'
            )

        print("\nTriggered Rules:")

        for rule in finding["rules"]:
            print(" -", rule)

        print("\nReasons:")

        for reason in finding["reasons"]:
            print(" -", reason)

    print("\n======================================")
    print(" ANALYSIS COMPLETE")
    print("======================================")
