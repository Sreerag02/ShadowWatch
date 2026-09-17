# created by Deepa

from sqlalchemy.orm import Session
from models import Telemetry

def get_asset_telemetry(db: Session, asset_id: str, limit: int = 500):
    """
    Retrieves telemetry for an asset, ordered chronologically.
    """
    return db.query(Telemetry)\
        .filter(Telemetry.asset_id == asset_id)\
        .order_by(Telemetry.timestamp.asc())\
        .limit(limit)\
        .all()