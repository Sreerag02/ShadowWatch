"""Deterministic cross-source timestamp checks; operational records only."""

from datetime import datetime


# Configurable prototype review priorities, not organizational risk scores.
RULE_SEVERITIES = {rule: 'HIGH' for rule in ('C001', 'C002', 'C003', 'C004')}
SKIPPED_RULES = {
    'C005': 'SKIPPED - insufficient source evidence: nullable completed_at '
            'does not prove incompletion, and investigations has no status field.'
}

# Each check names left/right timestamps: left > right triggers a finding.
# Strict comparisons allow equal timestamps.
CHECKS = (
    ('C001', 'CASE_CLOSED_BEFORE_INVESTIGATION_COMPLETED',
     'investigation_id', 'investigation_completed_at', 'case_closed_at',
     'investigations.completed_at', 'cases.closed_at',
     'Review whether closure preceded investigation completion or timestamps need correction.'),
    ('C002', 'INVESTIGATION_BEFORE_CASE_OPENED',
     'investigation_id', 'case_opened_at', 'investigation_started_at',
     'cases.opened_at', 'investigations.started_at',
     'Review whether investigation activity predates case creation or was linked/backfilled incorrectly.'),
    ('C003', 'ESCALATION_AFTER_CASE_CLOSED',
     'escalation_id', 'escalation_escalated_at', 'case_closed_at',
     'escalations.escalated_at', 'cases.closed_at',
     'Review whether escalation occurred after closure or reflects delayed recording.'),
    ('C004', 'ALERT_AFTER_CASE_OPENED',
     'linked_alert_id', 'alert_timestamp', 'case_opened_at',
     'alerts.timestamp', 'cases.opened_at',
     'Review whether the case predates its linked alert or the linkage/timestamps need correction.'),
)

QUERY = """
    SELECT c.entity_id, c.case_id, c.alert_id,
           c.opened_at AS case_opened_at, c.closed_at AS case_closed_at,
           a.alert_id AS linked_alert_id, a.asset_id,
           a.severity AS alert_severity, a.timestamp AS alert_timestamp,
           i.investigation_id, i.started_at AS investigation_started_at,
           i.completed_at AS investigation_completed_at,
           e.escalation_id, e.escalated_at AS escalation_escalated_at
    FROM cases c
    LEFT JOIN alerts a ON c.alert_id = a.alert_id AND c.entity_id = a.entity_id
    LEFT JOIN investigations i ON c.case_id = i.case_id
    LEFT JOIN escalations e ON c.case_id = e.case_id
"""


def _timestamp(value):
    """Accept PostgreSQL datetimes or ISO CSV strings; absent/invalid -> unknown."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return None


def _evaluate_row(row):
    if not row.get('entity_id') or not row.get('case_id'):
        return
    for rule, kind, linked_id, left_key, right_key, left_field, right_field, review in CHECKS:
        if not row.get(linked_id):
            continue
        left, right = _timestamp(row.get(left_key)), _timestamp(row.get(right_key))
        if left is None or right is None:
            continue
        # The schema uses TIMESTAMP without time zone. Do not invent a zone
        # when externally supplied rows mix aware and naive timestamps.
        if (left.utcoffset() is None) != (right.utcoffset() is None):
            continue
        if left <= right:
            continue
        source_id = row[linked_id]
        left_value, right_value = left.isoformat(sep=' '), right.isoformat(sep=' ')
        finding = {
            'rule_id': rule,
            'problem_type': 'CROSS_SOURCE_CONTRADICTION',
            'contradiction_type': kind,
            'entity_id': row['entity_id'], 'case_id': row['case_id'],
            'alert_id': row.get('alert_id'), 'asset_id': row.get('asset_id'),
            'severity': RULE_SEVERITIES[rule], 'alert_severity': row.get('alert_severity'),
            'source_records': {'case_id': row['case_id'], linked_id: source_id},
            'evidence': {left_field: left_value, right_field: right_value},
            'reason': (
                f"Case {row['case_id']} and linked record {source_id} have inconsistent "
                f'chronology: {left_field} = {left_value} is later than '
                f'{right_field} = {right_value}. {review}'
            ),
        }
        yield finding


def detect_cross_source_contradictions(rows=None, entity_id=None):
    """Return JSON-ready findings, sorted by entity, case, rule, source, values.

    No arguments reads PostgreSQL through the existing database engine. Rows
    supplied explicitly must use QUERY's aliases and can be used without DB
    dependencies. Every severity is checked. Missing values are unassessable,
    not contradictions. A finding is a review prompt, not proof of misconduct.
    C003 compares recorded timestamps even if the escalation flag is false or
    unknown; it does not assert that an escalation actually took place.
    """
    if rows is None:
        from sqlalchemy import text
        from app.core.database import engine

        query = QUERY
        parameters = {}
        if entity_id is not None:
            query += ' WHERE c.entity_id = :entity_id'
            parameters['entity_id'] = entity_id
        with engine.connect() as connection:
            rows = list(connection.execute(text(query), parameters).mappings())
    findings = {}
    for row in rows:
        if entity_id is not None and row.get('entity_id') != entity_id:
            continue
        for finding in _evaluate_row(row):
            # A multi-investigation/multi-escalation join repeats unrelated
            # records. Keep one finding per compared pair and actual values.
            key = (finding['entity_id'], finding['case_id'], finding['rule_id'],
                   tuple(sorted(finding['source_records'].items())),
                   tuple(sorted(finding['evidence'].items())))
            findings[key] = finding
    return [findings[key] for key in sorted(findings)]
