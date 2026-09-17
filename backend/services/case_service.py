from sqlalchemy.orm import joinedload, selectinload
from fastapi import HTTPException
from models import Case
from services.findings_service import get_findings, workflow_rows
from services.workflow_auditor import assess_case_workflow

def get_case_with_evidence(db, case_id):
    case = db.query(Case).options(joinedload(Case.alert), selectinload(Case.investigations),
                                 selectinload(Case.escalations)).filter_by(case_id=case_id).first()
    if case is None:
        raise HTTPException(404, f'Case {case_id} not found')
    return {**{column.name: getattr(case, column.name) for column in Case.__table__.columns},
            'alert': case.alert, 'investigations': case.investigations, 'escalations': case.escalations,
            'investigation': case.investigations[0] if len(case.investigations) == 1 else None,
            'escalation': case.escalations[0] if len(case.escalations) == 1 else None,
            'findings': get_findings(db, case.entity_id, case_id),
            'workflow': assess_case_workflow(workflow_rows(db, case.entity_id, case_id))}
