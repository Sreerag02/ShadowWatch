# created by Deepa

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from schemas import TelemetryResponse
from services.telemetry_service import get_asset_telemetry

router = APIRouter(
    prefix="/assets",
    tags=["telemetry"]
)

@router.get("/{asset_id}/telemetry", response_model=List[TelemetryResponse])
def get_telemetry(asset_id: str, db: Session = Depends(get_db)):
    """
    Returns chronological telemetry for a specific asset.
    """
    return get_asset_telemetry(db, asset_id=asset_id)