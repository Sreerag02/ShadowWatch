"""Adapt existing engines to one API contract; no rule logic is duplicated."""
import hashlib
import json
from collections import defaultdict
from sqlalchemy import Boolean, DateTime, select, text
from models import Telemetry
from services.rule_engine import evaluate_critical_case
from services.workflow_auditor import CASE_QUERY, assess_case_workflow
from services.negative_space_engine import detect_telemetry_blind_spots
from services.contradiction_engine import QUERY as CONTRADICTION_QUERY, detect_cross_source_contradictions

RULE_TYPES = {'R001': 'MISSING_INVESTIGATION', 'R002': 'MISSING_EVIDENCE',
              'R003': 'MISSING_ESCALATION', 'R004': 'FAST_CRITICAL_CLOSURE'}
# Prototype review priority, not an organization risk score.
R005_FINDING_SEVERITY = 'HIGH'

def workflow_rows(db, entity_id=None, case_id=None):
    clauses, params = [], {}
    if entity_id is not None:
        clauses.append('c.entity_id = :entity_id')
        params['entity_id'] = entity_id
    if case_id is not None:
        clauses.append('c.case_id = :case_id')
        params['case_id'] = case_id
    query = CASE_QUERY + (' WHERE ' + ' AND '.join(clauses) if clauses else '')
    statement = text(query + ' ORDER BY c.case_id, i.investigation_id, e.escalation_id').columns(
        evidence_present=Boolean(), escalated=Boolean(),
        **{key: DateTime() for key in ('opened_at', 'closed_at', 'alert_timestamp', 'started_at', 'completed_at', 'escalated_at')})
    return list(db.execute(statement, params).mappings())

def _finish(finding):
    content = json.dumps(finding, sort_keys=True, default=str)
    return {'finding_id': hashlib.sha256(content.encode()).hexdigest()[:24], **finding}

def case_rule_findings(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row['entity_id'], row['case_id'])].append(row)
    findings = {}
    for records in grouped.values():
        if records[0]['severity'] != 'CRITICAL':
            continue
        for row in records:
            raw = evaluate_critical_case(row)
            if raw is None:
                continue
            # Classify each record independently so an unknown record is not
            # labelled confirmed because another investigation has a real gap.
            record_audit = assess_case_workflow([row])
            for rule, reason in zip(raw['rules'], raw['reasons']):
                confirmed = rule in record_audit['confirmed_rules']
                if not confirmed:
                    issues = [issue['reason'] for issue in record_audit['data_issues'] if issue['rule_id'] == rule]
                    reason = '; '.join(issues) or 'Insufficient data to confirm the rule-engine trigger.'
                finding = _finish(dict(rule_id=rule, problem_type=RULE_TYPES[rule],
                    entity_id=row['entity_id'], case_id=row['case_id'], alert_id=row['alert_id'],
                    asset_id=row['asset_id'], severity=row['severity'], source='rule_engine',
                    assessment='CONFIRMED_GAP' if confirmed else 'INSUFFICIENT_DATA', reason=reason,
                    evidence={key: row.get(key) for key in {
                        'R001': ['investigation_id'],
                        'R002': ['investigation_id', 'evidence_present', 'evidence_count'],
                        'R003': ['escalation_id', 'escalated'],
                        'R004': ['opened_at', 'closed_at'],
                    }[rule]}))
                findings[finding['finding_id']] = finding
    return list(findings.values())

def get_findings(db, entity_id=None, case_id=None):
    findings = case_rule_findings(workflow_rows(db, entity_id, case_id))
    # R005 is asset-scoped, so it is not attached to unrelated individual cases.
    if case_id is None:
        query = select(Telemetry.__table__)
        if entity_id is not None:
            query = query.where(Telemetry.entity_id == entity_id)
        for raw in detect_telemetry_blind_spots(db.execute(query).mappings()):
            findings.append(_finish(dict(rule_id='R005', problem_type=raw['problem_type'],
                entity_id=raw['entity_id'], asset_id=raw['asset_id'], severity=R005_FINDING_SEVERITY,
                source='negative_space_engine', assessment='REVIEW_REQUIRED', reason=raw['reason'],
                evidence={k: v for k, v in raw.items() if k not in ('rule_id', 'problem_type', 'entity_id', 'asset_id', 'reason')})))
    clauses, params = [], {}
    for key, value in [('entity_id', entity_id), ('case_id', case_id)]:
        if value is not None:
            clauses.append(f'c.{key} = :{key}')
            params[key] = value
    query = CONTRADICTION_QUERY + (' WHERE ' + ' AND '.join(clauses) if clauses else '')
    statement = text(query).columns(**{key: DateTime() for key in (
        'case_opened_at', 'case_closed_at', 'alert_timestamp', 'investigation_started_at',
        'investigation_completed_at', 'escalation_escalated_at')})
    for raw in detect_cross_source_contradictions(db.execute(statement, params).mappings()):
        findings.append(_finish(dict(rule_id=raw['rule_id'], problem_type=raw['problem_type'],
            entity_id=raw['entity_id'], case_id=raw['case_id'], alert_id=raw['alert_id'], asset_id=raw['asset_id'],
            severity=raw['severity'], source='contradiction_engine', assessment='REVIEW_REQUIRED',
            reason=raw['reason'], evidence={**raw['evidence'], 'source_records': raw['source_records'],
                                         'contradiction_type': raw['contradiction_type']})))
    return sorted(findings, key=lambda f: (f['entity_id'], f.get('case_id') or '', f['rule_id'], f['finding_id']))
