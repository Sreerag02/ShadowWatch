#added by Deepa
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from models import Case

def get_case_with_evidence(db: Session, case_id: str) -> Case:
    # Uses joinedload to fetch all evidence in a single DB hit (Join-First strategy)
    case = db.query(Case)\
        .options(
            joinedload(Case.alert),
            joinedload(Case.investigation),
            joinedload(Case.escalation)
        )\
        .filter(Case.case_id == case_id)\
        .first()
        
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        
    return case