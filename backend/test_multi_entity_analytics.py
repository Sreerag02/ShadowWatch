"""Read-only analytics smoke/regression checks for all database organizations."""
from collections import Counter

from sqlalchemy import text
from database import engine
from services.rule_engine import analyze_critical_cases
from services.negative_space_engine import detect_telemetry_blind_spots
from services.workflow_auditor import audit_entity_workflows
from services.contradiction_engine import detect_cross_source_contradictions


def main():
    with engine.connect() as connection:
        entities = connection.execute(text('SELECT entity_id FROM entities ORDER BY entity_id')).scalars().all()
        expected_workflows = dict(connection.execute(text(
            "SELECT c.entity_id, count(*) FROM cases c JOIN alerts a ON c.alert_id=a.alert_id "
            "AND c.entity_id=a.entity_id WHERE a.severity IN ('HIGH','CRITICAL') GROUP BY c.entity_id"
        )).all())
    rules = analyze_critical_cases()
    telemetry = detect_telemetry_blind_spots()
    contradictions = detect_cross_source_contradictions()
    expected_alpha = {'E001-C0003': ['R003'], 'E001-C0025': ['R002'],
                      'E001-C0069': ['R003'], 'E001-C0074': ['R003'],
                      'E001-C0081': ['R002', 'R003', 'R004']}
    assert {r['case_id']: r['rules'] for r in rules if r['entity_id'] == 'E001'} == expected_alpha
    assert {r['asset_id'] for r in telemetry if r['entity_id'] == 'E001'} == {'E001-AS001', 'E001-AS017'}
    counts = [Counter(row['entity_id'] for row in rows) for rows in (rules, telemetry, contradictions)]
    for entity_id in entities:
        workflows = audit_entity_workflows(entity_id)
        assert len(workflows) == expected_workflows.get(entity_id, 0)
        assert all(r['entity_id'] == entity_id for r in workflows)
        filtered = detect_cross_source_contradictions(entity_id=entity_id)
        assert filtered == [r for r in contradictions if r['entity_id'] == entity_id]
        print(entity_id, 'critical findings:', counts[0][entity_id], 'R005:', counts[1][entity_id],
              'workflows:', len(workflows), 'contradictions:', counts[2][entity_id])
    print('Multi-entity analytics and Alpha regressions: PASS')


if __name__ == '__main__':
    main()
