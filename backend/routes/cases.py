# created by Deepa

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import CaseResponse
from services.case_service import get_case_with_evidence

router = APIRouter(
    prefix="/cases",
    tags=["cases"]
)

@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, db: Session = Depends(get_db)):
    """
    Retrieves a case and its nested alert, investigation, and escalation evidence.
    """
    return get_case_with_evidence(db, case_id=case_id)