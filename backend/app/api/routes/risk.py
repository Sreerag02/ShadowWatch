"""Read-only risk intelligence endpoints; existing findings endpoints unchanged."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.entity_service import require_entity
from app.services.risk.risk_service import build_risk_intelligence
from app.schemas import RiskResponse, CasePriorityResponse, PeerBenchmarkResponse, SupervisorySummaryResponse

router = APIRouter(tags=['risk intelligence'])

def selected(db, entity_id):
    require_entity(db,entity_id)
    return next(r for r in build_risk_intelligence(db) if r['entity_id']==entity_id)

@router.get('/risk/entities',response_model=list[RiskResponse])
def all_risk(db: Session = Depends(get_db)):
    return build_risk_intelligence(db)

@router.get('/entities/{entity_id}/risk',response_model=RiskResponse)
def entity_risk(entity_id: str, db: Session = Depends(get_db)):
    return selected(db,entity_id)

@router.get('/entities/{entity_id}/priority-cases',response_model=list[CasePriorityResponse])
def priority_cases(entity_id: str, limit: int = Query(20,ge=1,le=1000), offset: int = Query(0,ge=0), db: Session = Depends(get_db)):
    return selected(db,entity_id)['priority_cases'][offset:offset+limit]

@router.get('/entities/{entity_id}/peer-benchmark',response_model=PeerBenchmarkResponse)
def peer_benchmark(entity_id: str, db: Session = Depends(get_db)):
    return selected(db,entity_id)['peer_context']

@router.get('/entities/{entity_id}/supervisory-summary',response_model=SupervisorySummaryResponse)
def summary(entity_id: str, db: Session = Depends(get_db)):
    return selected(db,entity_id)['summary']
