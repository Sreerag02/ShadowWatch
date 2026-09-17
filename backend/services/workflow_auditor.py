"""Explain observable case handling using explicitly scoped prototype policy."""

from collections import defaultdict
from datetime import datetime

from services.rule_engine import (
    FAST_CRITICAL_CLOSURE_MINUTES,
    evaluate_critical_case,
)


RULE_STAGES = {
    'R001': 'INVESTIGATION', 'R002': 'EVIDENCE',
    'R003': 'ESCALATION', 'R004': 'CLOSURE',
}

CASE_QUERY = """
    SELECT c.case_id, c.entity_id, c.alert_id, c.opened_at, c.closed_at,
           c.status AS case_status, c.resolution, c.closure_reason,
           a.asset_id, a.timestamp AS alert_timestamp, a.severity, a.category,
           i.investigation_id, i.started_at, i.completed_at,
           i.evidence_present, i.evidence_count,
           e.escalation_id, e.escalated, e.escalated_at
    FROM cases c
    LEFT JOIN alerts a ON c.alert_id = a.alert_id AND c.entity_id = a.entity_id
    LEFT JOIN investigations i ON c.case_id = i.case_id
    LEFT JOIN escalations e ON c.case_id = e.case_id
"""


def _load_rows(predicate, parameters):
    from sqlalchemy import text
    from database import engine

    with engine.connect() as connection:
        return list(connection.execute(text(
            CASE_QUERY + predicate +
            ' ORDER BY c.case_id, i.investigation_id, e.escalation_id'
        ), parameters).mappings())


def _evidence(row):
    if row['investigation_id'] is None:
        return False
    if row['evidence_present'] is False or row['evidence_count'] == 0:
        return False
    if row['evidence_present'] is True and row['evidence_count'] is not None:
        return True if row['evidence_count'] > 0 else None
    return None


def _consensus(values):
    """Mixed or unknown records cannot establish a single true/false state."""
    values = set(values)
    return next(iter(values)) if len(values) == 1 else None


def _records(rows, id_key, fields):
    records = {}
    for row in rows:
        if row[id_key] is not None:
            record = {key: row.get(key) for key in [id_key, *fields]}
            records[row[id_key]] = {
                key: value.isoformat(sep=' ') if isinstance(value, datetime) else value
                for key, value in record.items()
            }
    return [records[key] for key in sorted(records)]


def assess_case_workflow(rows):
    """Pure assessment of joined rows for exactly one case; empty -> None.

    R001-R004 retain their existing per-record semantics. Multiple child rows
    are retained as evidence, but duplicate join findings are collapsed.
    None in expected means no policy; None in observed means unknown/mixed.
    """
    rows = list(rows)
    if not rows:
        return None
    row = rows[0]
    if any((r['case_id'], r['entity_id']) != (row['case_id'], row['entity_id']) for r in rows):
        raise ValueError('Assessment requires rows for one entity/case')
    severity = row['severity']
    in_scope = severity in ('HIGH', 'CRITICAL')
    critical = severity == 'CRITICAL'
    opened, closed = row['opened_at'], row['closed_at']
    duration = (closed - opened).total_seconds() / 60 if opened and closed else None
    expected = {
        'case': True,
        'investigation': True if in_scope else None,
        'evidence': True if in_scope else None,
        'escalation': True if critical else None,
        'closure': None,  # No completion deadline or closure mandate is defined.
    }
    observed = {
        'case': True,
        'investigation': any(r['investigation_id'] is not None for r in rows),
        'evidence': _consensus(_evidence(r) for r in rows),
        'escalation': _consensus(
            False if r['escalation_id'] is None else r['escalated'] for r in rows
        ),
        'closure': True if closed else (False if row.get('case_status') == 'OPEN' else None),
    }
    gaps = {}
    for record in rows:
        if critical:
            finding = evaluate_critical_case(record)
            if finding:
                for rule, reason in zip(finding['rules'], finding['reasons']):
                    gaps[(rule, reason)] = dict(stage=RULE_STAGES[rule], rule_id=rule, reason=reason)
        elif severity == 'HIGH':
            # HIGH expectations are auditor prototype policy, not new R rules.
            stage = ('INVESTIGATION' if record['investigation_id'] is None else
                     'EVIDENCE' if _evidence(record) is False else None)
            if stage:
                reason = (f'HIGH prototype expectation: {stage.lower()} is missing '
                          'from the recorded workflow.')
                gaps[(stage, reason)] = dict(stage=stage, rule_id=None, reason=reason)
    gaps = list(gaps.values())
    gaps.sort(key=lambda gap: (gap['rule_id'] or '', gap['stage']))
    limitations = [
        'Prototype expectations only; NO_GAP is not a certification of compliance.',
        'Evidence flags/counts do not prove evidence quality or investigation effectiveness.',
        'No mandatory closure deadline, full stage-order policy, or HIGH escalation policy is defined.',
        'Case-based auditing cannot find alerts that have no case.',
    ]
    if not in_scope:
        limitations.append('This severity is outside the HIGH/CRITICAL prototype assessment scope.')
    for stage in ('evidence', 'escalation', 'closure'):
        if observed[stage] is None:
            limitations.append(f'{stage.capitalize()} observation is unknown or mixed; inspect source records.')
    if duration is None:
        limitations.append('Closure duration is unknown because a required timestamp is missing.')
    elif duration < 0:
        limitations.append('Closure precedes opening: duration is invalid; the legacy R004 result is retained.')
    if any(r['investigation_id'] is not None and r['evidence_count'] is None for r in rows) and critical:
        limitations.append('R002 treats a NULL evidence count as missing supporting evidence; actual evidence presence may be unknown.')
    assessment = 'EXECUTION_GAP' if gaps else 'NO_GAP'
    labels = {True: 'Present', False: 'Absent', None: 'Unknown/mixed'}
    explanation = [
        f"Case {row['case_id']} is associated with a {severity or 'unknown-severity'} "
        f"{row['category'] or 'uncategorized'} alert.",
        'Expected workflow (prototype): ' + ' → '.join(
            stage.capitalize() for stage, required in expected.items() if required
        ),
        'Observed workflow: ' + ' → '.join(
            f'{stage.capitalize()}: {labels[value]}' for stage, value in observed.items()
        ),
        f'Closure time: {duration:.1f} minutes.' if duration is not None else 'Closure time: unknown.',
        'Execution gaps: ' + ('; '.join(g['reason'] for g in gaps) or 'None detected within evaluated expectations.'),
        'Prioritize for supervisory review.' if gaps else 'Review limitations before interpreting this result.',
    ]
    if critical:
        explanation.insert(2, f'Prototype closure timing check: durations below '
                           f'{FAST_CRITICAL_CLOSURE_MINUTES} minutes trigger R004; '
                           'this does not establish a required completion deadline.')
    return {
        'case_id': row['case_id'], 'entity_id': row['entity_id'],
        'alert_id': row['alert_id'], 'asset_id': row['asset_id'],
        'severity': severity, 'category': row['category'],
        'expected': expected, 'observed': observed, 'gaps': gaps,
        'closure_minutes': duration,
        'closure_policy': {'minimum_minutes': FAST_CRITICAL_CLOSURE_MINUTES,
                           'scope': 'CRITICAL only; prototype'} if critical else None,
        'triggered_rules': sorted({g['rule_id'] for g in gaps if g['rule_id']}),
        'assessment': assessment, 'assessment_in_scope': in_scope,
        'limitations': limitations, 'explanation': '\n'.join(explanation),
        'records': {
            'case': _records(rows, 'case_id', ['alert_timestamp', 'opened_at', 'closed_at',
                                             'case_status', 'resolution', 'closure_reason'])[0],
            'investigations': _records(rows, 'investigation_id',
                                      ['started_at', 'completed_at', 'evidence_present', 'evidence_count']),
            'escalations': _records(rows, 'escalation_id', ['escalated', 'escalated_at']),
        },
    }


def audit_case_workflow(case_id):
    """Return an assessment, or None when the case ID does not exist."""
    return assess_case_workflow(_load_rows(' WHERE c.case_id = :case_id', {'case_id': case_id}))


def audit_entity_workflows(entity_id):
    """Audit HIGH/CRITICAL cases for one entity using one read-only query."""
    rows = _load_rows(" WHERE c.entity_id = :entity_id AND a.severity IN ('HIGH', 'CRITICAL')",
                      {'entity_id': entity_id})
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['case_id']].append(row)
    return [assess_case_workflow(grouped[key]) for key in sorted(grouped)]
