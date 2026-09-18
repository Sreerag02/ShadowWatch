"""Request-session adapter for offline behavioural findings."""
import pandas as pd
from sqlalchemy import select
from app.models import Case, Alert, Investigation
from app.services.analytics.behaviour_analytics import analyze_behaviour

# Prototype supervisory review priorities, not entity risk scores.
SEVERITIES = {'R006':'MEDIUM','R007':'MEDIUM','R008':'MEDIUM','R009':'HIGH'}

def get_behaviour_findings(case_id=None, db=None, entity_id=None):
    if db is None:
        from app.core.database import SessionLocal
        with SessionLocal() as session:
            return get_behaviour_findings(case_id,session,entity_id)
    if case_id is not None:
        case=db.get(Case,case_id)
        if case is None or (entity_id is not None and case.entity_id != entity_id):
            return []
        entity_id=case.entity_id
    cases_query=select(Case.__table__)
    alerts_query=select(Alert.__table__)
    inv_query=select(Investigation.__table__).join(Case,Case.case_id==Investigation.case_id)
    if entity_id is not None:
        cases_query=cases_query.where(Case.entity_id==entity_id)
        alerts_query=alerts_query.where(Alert.entity_id==entity_id)
        inv_query=inv_query.where(Case.entity_id==entity_id)
    def frame(query):
        result=db.execute(query)
        return pd.DataFrame(result.mappings().all(),columns=list(result.keys()))
    cases,alerts,investigations=frame(cases_query),frame(alerts_query),frame(inv_query)
    tables=analyze_behaviour(investigations,cases,alerts)
    case_index={r['case_id']:r for r in cases.to_dict('records')}
    alert_index={r['alert_id']:r for r in alerts.to_dict('records')}
    findings=[]
    for rule, table in tables.items():
        for row in table.to_dict('records'):
            affected=[row['case_id']] if row.get('case_id') else row['case_ids'].split(', ')
            for affected_case in affected:
                if case_id is not None and affected_case != case_id:
                    continue
                case=case_index[affected_case]
                alert=alert_index.get(case['alert_id'],{})
                findings.append(dict(rule_id=rule,problem_type=row['finding_type'],entity_id=row['entity_id'],
                    case_id=affected_case,alert_id=case['alert_id'],asset_id=alert.get('asset_id'),
                    severity=SEVERITIES[rule],source='behaviour_analytics',assessment='REVIEW_REQUIRED',
                    reason=row['reason'],evidence={k:v for k,v in row.items() if k not in ('rule_id','finding_type','reason')}))
    return findings
