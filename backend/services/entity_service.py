from fastapi import HTTPException
from models import Entity, Asset, Alert, Case

def require_entity(db, entity_id):
    entity = db.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(404, f'Entity {entity_id} not found')
    return entity

def get_all_entities(db):
    return db.query(Entity).order_by(Entity.entity_id).all()

def get_entity_summary(db, entity_id):
    from services.findings_service import get_findings
    entity = require_entity(db, entity_id)
    return {**{key: getattr(entity, key) for key in ('entity_id','entity_name','sector','peer_group','country')},
            'asset_count': db.query(Asset).filter_by(entity_id=entity_id).count(),
            'alert_count': db.query(Alert).filter_by(entity_id=entity_id).count(),
            'case_count': db.query(Case).filter_by(entity_id=entity_id).count(),
            'finding_count': len(get_findings(db, entity_id))}

def get_entity_assets(db, entity_id, limit=100, offset=0):
    require_entity(db, entity_id)
    return db.query(Asset).filter_by(entity_id=entity_id).order_by(Asset.asset_id).offset(offset).limit(limit).all()

def get_entity_cases(db, entity_id, limit=100, offset=0):
    require_entity(db, entity_id)
    return db.query(Case).filter_by(entity_id=entity_id).order_by(Case.case_id).offset(offset).limit(limit).all()
