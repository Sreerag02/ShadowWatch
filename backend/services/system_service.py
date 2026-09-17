from collections import Counter
from sqlalchemy import text
from fastapi import HTTPException
from models import Entity, Asset, Alert, Case, Investigation, Escalation, Telemetry
from services.findings_service import get_findings

def health(db):
    try:
        db.execute(text('SELECT 1'))
    except Exception as exc:
        raise HTTPException(503, 'Database unavailable') from exc
    return {'status': 'ok', 'database': 'ok'}

def analytics_summary(db):
    findings = get_findings(db)
    result = {name + '_count': db.query(model).count() for name, model in [
        ('entity', Entity), ('asset', Asset), ('alert', Alert), ('case', Case),
        ('investigation', Investigation), ('escalation', Escalation), ('telemetry', Telemetry)]}
    return {**result, 'finding_count': len(findings),
            'findings_by_rule': dict(Counter(f['rule_id'] for f in findings)),
            'findings_by_assessment': dict(Counter(f['assessment'] for f in findings))}
