from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from models import Case

from services.rule_engine import analyze_critical_cases
from services.behaviour_finding_service import get_behaviour_findings


# Mapping from existing rule IDs to API problem types.
RULE_PROBLEM_TYPES = {
    "R001": "MISSING_INVESTIGATION",
    "R002": "MISSING_EVIDENCE",
    "R003": "MISSING_ESCALATION",
    "R004": "FAST_CRITICAL_CLOSURE",
}


def get_rule_engine_findings(case_id):
    """
    Get existing R001-R004 findings for one case.

    The original rule_engine.py is not modified.
    This function only adapts its output to the API schema.
    """

    results = analyze_critical_cases()

    findings = []

    for result in results:

        if result["case_id"] != case_id:
            continue

        rules = result.get("rules", [])
        reasons = result.get("reasons", [])

        for index, rule_id in enumerate(rules):

            reason = (
                reasons[index]
                if index < len(reasons)
                else None
            )

            findings.append({
                "rule_id": rule_id,
                "problem_type": RULE_PROBLEM_TYPES.get(
                    rule_id,
                    "UNKNOWN"
                ),
                "severity": result["severity"],
                "reason": reason,
                "evidence": (
                    f"Alert: {result['alert_id']}; "
                    f"Asset: {result['asset_id']}"
                )
            })

    return findings


def get_case_with_evidence(db: Session, case_id: str) -> Case:

    case = db.query(Case)\
        .options(
            joinedload(Case.alert),
            joinedload(Case.investigation),
            joinedload(Case.escalation)
        )\
        .filter(Case.case_id == case_id)\
        .first()

    if not case:
        raise HTTPException(
            status_code=404,
            detail=f"Case {case_id} not found"
        )

    # ---------------------------------------------------------
    # Existing R001-R004 rule engine
    # ---------------------------------------------------------

    rule_findings = get_rule_engine_findings(case_id)

    # ---------------------------------------------------------
    # Team Member 3 behavioural analytics R006-R009
    # ---------------------------------------------------------

    behavioural_findings = get_behaviour_findings(case_id)

    # ---------------------------------------------------------
    # Combine both finding sources
    # ---------------------------------------------------------

    case.findings = (
        rule_findings +
        behavioural_findings
    )

    return case