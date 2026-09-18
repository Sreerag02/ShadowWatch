from fastapi import HTTPException
from app.models import Asset, Telemetry

def get_asset_telemetry(db, asset_id, limit=500, offset=0, start_time=None, end_time=None, entity_id=None):
    asset = db.get(Asset, asset_id)
    if asset is None or (entity_id is not None and asset.entity_id != entity_id):
        raise HTTPException(404, f'Asset {asset_id} not found')
    if any(t is not None and t.tzinfo is not None for t in (start_time, end_time)):
        raise HTTPException(422, 'Use timestamps without time zones, matching the database schema')
    if start_time is not None and end_time is not None and start_time > end_time:
        raise HTTPException(422, 'start_time must be no later than end_time')
    query = db.query(Telemetry).filter_by(asset_id=asset_id, entity_id=asset.entity_id)
    if start_time is not None:
        query = query.filter(Telemetry.timestamp >= start_time)
    if end_time is not None:
        query = query.filter(Telemetry.timestamp <= end_time)
    return query.order_by(Telemetry.timestamp, Telemetry.telemetry_id).offset(offset).limit(limit).all()
