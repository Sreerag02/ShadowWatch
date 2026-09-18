from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import HealthResponse, AnalyticsSummaryResponse
from app.services.system_service import health, analytics_summary

router = APIRouter(tags=['system'])

@router.get('/health', response_model=HealthResponse)
def check_health(db: Session = Depends(get_db)):
    return health(db)

@router.get('/analytics/summary', response_model=AnalyticsSummaryResponse)
def summary(db: Session = Depends(get_db)):
    return analytics_summary(db)
