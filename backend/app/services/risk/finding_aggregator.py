"""Normalize the shared feed plus auditor gaps; never re-detect anomalies."""
from collections import Counter
from hashlib import sha256
import json

COMPONENT_RULES = {
    'EXECUTION_GAP_RISK': {'R001','R002','R003','R004','WF_INVESTIGATION','WF_EVIDENCE'},
    'MONITORING_VISIBILITY_RISK': {'R005'},
    'INVESTIGATION_QUALITY_RISK': {'R006','R007','R009'},
    'REPEAT_INCIDENT_RISK': {'R008'},
    'RECORD_CONSISTENCY_RISK': {'C001','C002','C003','C004'},
}
COMPONENT_ENGINES = {
    'EXECUTION_GAP_RISK': {'rule_engine', 'workflow_auditor'},
    'MONITORING_VISIBILITY_RISK': {'negative_space_engine'},
    'INVESTIGATION_QUALITY_RISK': {'behaviour_analytics'},
    'REPEAT_INCIDENT_RISK': {'behaviour_analytics'},
    'RECORD_CONSISTENCY_RISK': {'contradiction_engine'},
}
ENGINES = set().union(*COMPONENT_ENGINES.values())

def component_for(finding):
    return next((name for name, rules in COMPONENT_RULES.items() if finding['rule_id'] in rules), None)

def normalize_findings(findings):
    unique = {}
    for raw in findings:
        row = dict(raw)
        row['source_engine'] = row.pop('source', None) or row.get('source_engine')
        row.setdefault('case_id', None)
        row.setdefault('asset_id', None)
        row.setdefault('alert_id', None)
        row.setdefault('evidence', {})
        for key in ('entity_id', 'rule_id', 'problem_type', 'reason', 'source_engine'):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f'Finding requires {key}')
        if row.get('severity') not in ('LOW','MEDIUM','HIGH','CRITICAL'):
            raise ValueError('Finding requires a recognized severity')
        if row.get('assessment') not in ('CONFIRMED_GAP','REVIEW_REQUIRED','INSUFFICIENT_DATA'):
            raise ValueError('Finding requires an explicit assessment')
        if not isinstance(row['evidence'], dict):
            raise ValueError('Finding evidence must be structured')
        source_ids = row.pop('source_finding_ids', None)
        original_id = row.pop('finding_id', None)
        # Exact content duplicates collapse even if external IDs differ.
        key = json.dumps(row, sort_keys=True, default=str, allow_nan=False)
        if key not in unique:
            unique[key] = {**row, 'finding_id': sha256(key.encode()).hexdigest()[:24], 'source_finding_ids': []}
        if source_ids is not None:
            unique[key]['source_finding_ids'].extend(source_ids)
        elif original_id:
            unique[key]['source_finding_ids'].append(original_id)
    for row in unique.values():
        row['source_finding_ids'] = sorted(set(row['source_finding_ids']))
    return [unique[k] for k in sorted(unique)]

def workflow_findings(audits, existing):
    covered = {(f['entity_id'], f.get('case_id'), f['rule_id']) for f in existing
               if f['assessment'] == 'CONFIRMED_GAP'}
    output = []
    for audit in audits:
        for gap in audit['gaps']:
            rule = gap['rule_id'] or 'WF_' + gap['stage']
            if (audit['entity_id'], audit['case_id'], rule) in covered:
                continue
            output.append(dict(entity_id=audit['entity_id'], case_id=audit['case_id'],
                asset_id=audit['asset_id'], alert_id=audit['alert_id'], rule_id=rule,
                problem_type='WORKFLOW_' + gap['stage'] + '_GAP', severity=audit['severity'],
                source='workflow_auditor', assessment='CONFIRMED_GAP', reason=gap['reason'],
                evidence={'stage':gap['stage'], 'records':audit['records']}))
    return output

def aggregate_findings(findings):
    def counts(key):
        return dict(sorted(Counter(f[key] for f in findings).items()))
    return dict(total_findings=len(findings), findings_by_rule=counts('rule_id'),
        findings_by_problem_type=counts('problem_type'), findings_by_severity=counts('severity'),
        findings_by_assessment=counts('assessment'),
        affected_cases=len({f['case_id'] for f in findings if f.get('case_id')}),
        affected_assets=len({f['asset_id'] for f in findings if f.get('asset_id')}),
        execution_gap_count=sum(component_for(f) == 'EXECUTION_GAP_RISK' and f['assessment'] == 'CONFIRMED_GAP' for f in findings),
        negative_space_count=sum(f['rule_id']=='R005' for f in findings),
        contradiction_count=sum(f['source_engine']=='contradiction_engine' for f in findings),
        behaviour_analytics_count=sum(f['source_engine']=='behaviour_analytics' for f in findings))
