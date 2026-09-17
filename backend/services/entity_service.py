# created by Deepa

from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import Entity, Asset, Alert, Case

def get_all_entities(db: Session):
    return db.query(Entity).all()

def get_entity_summary(db: Session, entity_id: str):
    entity = db.query(Entity).filter(Entity.entity_id == entity_id).first()
    
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
        
    # Calculate summary counts for the dashboard
    asset_count = db.query(Asset).filter(Asset.entity_id == entity_id).count()
    alert_count = db.query(Alert).filter(Alert.entity_id == entity_id).count()
    case_count = db.query(Case).filter(Case.entity_id == entity_id).count()
    
    return {
        "entity_id": entity.entity_id,
        "entity_name": entity.entity_name,
        "sector": entity.sector,
        "peer_group": entity.peer_group,
        "country": entity.country,
        "asset_count": asset_count,
        "alert_count": alert_count,
        "case_count": case_count
    }