from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import TelemetryResponse
from services.telemetry_service import get_asset_telemetry

router = APIRouter(prefix='/assets', tags=['telemetry'])

@router.get('/{asset_id}/telemetry', response_model=list[TelemetryResponse])
def get_telemetry(asset_id: str, start_time: datetime | None = None, end_time: datetime | None = None,
                  entity_id: str | None = None, limit: int = Query(500, ge=1, le=5000),
                  offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return get_asset_telemetry(db, asset_id, limit, offset, start_time, end_time, entity_id)
