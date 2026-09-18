"""Read-only system verification. Run from backend: python -m scripts.verify_system."""
from collections import Counter
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from app.core.database import engine
from app.schemas import RiskResponse
from app.services.ingestion.dataset_validation import validate_all
from app.services.analytics.rule_engine import analyze_critical_cases
from app.services.analytics.negative_space_engine import detect_telemetry_blind_spots
from app.services.analytics.workflow_auditor import audit_entity_workflows
from app.services.analytics.contradiction_engine import detect_cross_source_contradictions
from app.services.analytics.behaviour_finding_service import get_behaviour_findings
from app.services.analytics.findings_service import get_findings
from app.services.risk.finding_aggregator import normalize_findings
from app.services.risk.risk_service import build_risk_intelligence
from app.services.risk.benchmark_engine import peer_identity
from scripts.verify_database import verify_database


def run_check(label, action):
    try:
        action()
    except Exception as exc:
        print(f'{label:.<38} FAIL: {type(exc).__name__}: {exc}')
        return False
    print(f'{label:.<38} PASS')
    return True


def main():
    print('=' * 60 + '\n SHADOWWATCH SYSTEM VERIFICATION\n' + '=' * 60)
    state = {}
    results = []
    def check(label, action):
        results.append(run_check(label, action))

    def connection():
        with engine.connect() as conn:
            assert conn.execute(text('SELECT 1')).scalar() == 1
    check('Database Connection', connection)

    def organizations():
        with engine.connect() as conn:
            rows = list(conn.execute(text(
                'SELECT entity_id,entity_name,sector,peer_group FROM entities ORDER BY entity_id'
            )).mappings())
        assert rows, 'No organizations are imported'
        state['entities'] = [dict(r) for r in rows]
        print('Organizations:', len(rows))
        for row in rows:
            print(dict(row))
    check('Organizations', organizations)

    def integrity():
        summary, errors = verify_database(engine, validate_all())
        for row in summary:
            print(row)
        assert not errors, '\n'.join(errors)
        assert 'ground_truth' not in inspect(engine).get_table_names(), 'Ground truth must remain evaluation-only'
    check('Entity Relationships / Source Values', integrity)

    def core():
        rows = analyze_critical_cases()
        for r in rows:
            assert r['rules'] and len(r['rules']) == len(r['reasons'])
        print('Core cases by entity:', dict(Counter(r['entity_id'] for r in rows)))
    check('R001-R004 Rule Engine', core)

    def telemetry():
        rows = detect_telemetry_blind_spots()
        assert all(r['rule_id']=='R005' and r['reason'] for r in rows)
        print('R005 episodes:',len(rows))
    check('R005 Negative Space', telemetry)

    def workflows():
        for entity in state['entities']:
            for result in audit_entity_workflows(entity['entity_id']):
                assert result['entity_id']==entity['entity_id'] and result['explanation'] and result['records']
    check('Workflow Auditor', workflows)

    def contradictions():
        rows = detect_cross_source_contradictions()
        assert all(r['reason'] and r['evidence'] for r in rows)
        print('Supported contradiction findings:',len(rows),'(zero is valid)')
    check('Contradiction Engine', contradictions)

    with Session(engine) as db:
        def behaviour():
            rows = get_behaviour_findings(db=db)
            assert all(r['reason'] and r['evidence'] and r['rule_id'] in {'R006','R007','R008','R009'} for r in rows)
            print('Behaviour counts:',dict(Counter(r['rule_id'] for r in rows)))
        check('Behaviour Analytics R006-R009', behaviour)

        def aggregation():
            source = get_findings(db)
            normalized = normalize_findings(source)
            assert normalize_findings(normalized)==normalized
            assert {r['finding_id'] for r in source} <= {k for r in normalized for k in r['source_finding_ids']}
            assert all(r['reason'] and isinstance(r['evidence'],dict) for r in normalized)
            state['source_ids'] = {r['finding_id'] for r in source}
        check('Finding Aggregation', aggregation)

        def risk():
            reports = build_risk_intelligence(db)
            assert {r['entity_id'] for r in reports}=={r['entity_id'] for r in state['entities']}
            for report in reports:
                RiskResponse.model_validate(report)
                assert len(report['priority_cases'])==report['denominators']['cases']
                assert all(p['reason'] and 0<=p['priority_score']<=100 for p in report['priority_cases'])
                print(report['entity_id'],report['overall_score'],report['overall_level'],report['score_status'])
            assert state['source_ids'] <= {k for r in reports for f in r['findings'] for k in f['source_finding_ids']}
            state['reports'] = reports
        check('Risk Intelligence / Case Priority', risk)

        def peers():
            reports = {r['entity_id']:r for r in state['reports']}
            for eid,r in reports.items():
                identity = peer_identity(r,r['config'])
                for other in r['peer_context']['peer_entity_ids']:
                    other_identity = peer_identity(reports[other],r['config'])
                    assert other!=eid
                    assert all(identity[key] and identity[key].casefold()==other_identity[key].casefold()
                               for key in ('group','sector'))
                assert r['summary']['overall_score']==r['overall_score']
                assert r['summary']['peer_context']==r['peer_context']
        check('Peer Benchmarking / Explainability', peers)
    success = all(results)
    print('-' * 60 + '\nFINAL STATUS: ' + ('PASS' if success else 'FAIL') + '\n' + '=' * 60)
    return 0 if success else 1


if __name__ == '__main__':
    raise SystemExit(main())
