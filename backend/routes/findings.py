from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import FindingResponse
from services.findings_service import get_findings
from services.entity_service import require_entity

router = APIRouter(tags=['findings'])

@router.get('/findings', response_model=list[FindingResponse])
def findings(entity_id: str | None = None, db: Session = Depends(get_db)):
    if entity_id is not None:
        require_entity(db, entity_id)
    return get_findings(db, entity_id)
