from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import EntityResponse, EntitySummaryResponse, AssetResponse, CaseSummaryResponse, FindingResponse
from services.entity_service import get_all_entities, get_entity_summary, get_entity_assets, get_entity_cases, require_entity
from services.findings_service import get_findings

router = APIRouter(prefix='/entities', tags=['entities'])

@router.get('', response_model=list[EntityResponse])
@router.get('/', response_model=list[EntityResponse], include_in_schema=False)
def list_entities(db: Session = Depends(get_db)):
    return get_all_entities(db)

@router.get('/{entity_id}', response_model=EntitySummaryResponse)
def get_entity(entity_id: str, db: Session = Depends(get_db)):
    return get_entity_summary(db, entity_id)

@router.get('/{entity_id}/assets', response_model=list[AssetResponse])
def assets(entity_id: str, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return get_entity_assets(db, entity_id, limit, offset)

@router.get('/{entity_id}/cases', response_model=list[CaseSummaryResponse])
def cases(entity_id: str, limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return get_entity_cases(db, entity_id, limit, offset)

@router.get('/{entity_id}/findings', response_model=list[FindingResponse])
def findings(entity_id: str, db: Session = Depends(get_db)):
    require_entity(db, entity_id)
    return get_findings(db, entity_id)
