"""One read-only request batch, using existing analytics and database records."""
from collections import defaultdict
from statistics import median
from sqlalchemy import select
from app.models import Entity, Case, Alert, Asset, Investigation, Telemetry
from app.services.analytics.findings_service import get_findings, workflow_rows
from app.services.analytics.workflow_auditor import assess_case_workflow
from app.services.risk.finding_aggregator import ENGINES, workflow_findings
from app.services.risk.risk_engine import calculate_risk
from app.services.risk.prioritization import prioritize_cases
from app.services.risk.benchmark_engine import benchmark_entity
from app.services.risk.explainability import supervisory_summary
from app.core.risk_config import risk_config

def build_risk_intelligence(db, config=None):
    config = risk_config(config)
    def records(model):
        return [dict(r) for r in db.execute(select(model.__table__)).mappings()]
    entities, cases, alerts, assets, investigations = [records(m) for m in (Entity,Case,Alert,Asset,Investigation)]
    alert_index = {r['alert_id']:r for r in alerts}
    asset_index = {r['asset_id']:r for r in assets}
    case_index = {r['case_id']:r for r in cases}
    for case in cases:
        alert = alert_index.get(case['alert_id'])
        if not alert or alert['entity_id'] != case['entity_id']:
            raise ValueError('Case/alert ownership mismatch in risk inputs')
        asset = asset_index.get(alert['asset_id'])
        if asset and asset['entity_id'] != case['entity_id']:
            raise ValueError('Case/asset ownership mismatch in risk inputs')
        case.update(severity=alert['severity'],asset_id=alert['asset_id'],
                    asset_criticality=asset['criticality'] if asset else None)
    grouped = defaultdict(list)
    for row in workflow_rows(db):
        grouped[(row['entity_id'],row['case_id'])].append(row)
    audits = [assess_case_workflow(rows) for _,rows in sorted(grouped.items())]
    # Exceptions propagate: a failed engine must never be represented as zero findings.
    raw_findings = get_findings(db)
    raw_findings += workflow_findings(audits,raw_findings)
    telemetry_assets = defaultdict(set)
    for entity_id,asset_id in db.execute(select(Telemetry.entity_id,Telemetry.asset_id).distinct()):
        telemetry_assets[entity_id].add(asset_id)
    reports, priorities = [], {}
    for entity in sorted(entities,key=lambda r:r['entity_id']):
        eid = entity['entity_id']
        own_cases = [c for c in cases if c['entity_id']==eid]
        own_assets = [a for a in assets if a['entity_id']==eid]
        inv = [i for i in investigations if case_index[i['case_id']]['entity_id']==eid]
        durations = []
        for i in inv:
            if i['started_at'] is not None and i['completed_at'] is not None:
                duration = (i['completed_at']-i['started_at']).total_seconds()/60
                if duration >= 0:
                    durations.append(duration)
        serious = {c['case_id'] for c in own_cases if c['severity'] in ('HIGH','CRITICAL')}
        investigated = {i['case_id'] for i in inv}
        monitored = {a['asset_id'] for a in own_assets if a['monitoring_expected'] is True}
        coverage = dict(investigation_count=len(inv), notes_present=sum(bool((i['analyst_notes'] or '').strip()) for i in inv),
            valid_duration_count=len(durations), unknown_monitoring_assets=sum(a['monitoring_expected'] is None for a in own_assets),
            monitored_assets_with_telemetry=len(monitored & telemetry_assets[eid]),
            cases_with_unknown_severity=sum(c['severity'] is None for c in own_cases),
            workflow_data_issue_cases=sum(bool(a['data_issues']) for a in audits if a['entity_id']==eid))
        limitations = ['Behaviour rules are prototype review signals; repetitive templates may create false positives.',
            'No finding does not prove normal behaviour: detectors can skip missing inputs or sparse baselines.',
            'Metrics describe all currently loaded records; organizations may cover different observation periods.']
        if coverage['unknown_monitoring_assets']:
            limitations.append('Unknown monitoring expectations excluded from monitored-asset denominator.')
        if len(durations)<len(inv):
            limitations.append('Some investigation durations are missing or invalid; R007 and duration benchmarks have limited coverage.')
        if coverage['notes_present']<len(inv):
            limitations.append('Some investigation notes are absent; text-similarity coverage is incomplete.')
        if coverage['monitored_assets_with_telemetry']<len(monitored):
            limitations.append('Some monitored assets have no telemetry records; zero blind-spot findings does not establish visibility.')
        if coverage['workflow_data_issue_cases']:
            limitations.append('Workflow Auditor reports incomplete or inconsistent evidence for some cases.')
        exposure = dict(cases={c['case_id'] for c in own_cases},serious_cases=serious,
            critical_cases={c['case_id'] for c in own_cases if c['severity']=='CRITICAL'},
            investigated_cases=investigated,investigated_serious_cases=serious & investigated,
            monitored_assets=monitored,median_investigation_minutes=median(durations) if durations else None,
            valid_duration_count=len(durations),data_coverage=coverage,limitations=limitations)
        report = calculate_risk(entity,[f for f in raw_findings if f['entity_id']==eid],exposure,
            engine_status={e:'AVAILABLE' for e in ENGINES},config=config)
        reports.append(report)
        priorities[eid] = prioritize_cases(own_cases,report['findings'],config)
    output = []
    for report in reports:
        peers = benchmark_entity(report,reports,config)
        ranked = priorities[report['entity_id']]
        output.append(dict(**report,peer_context=peers,priority_cases=ranked,
                           summary=supervisory_summary(report,peers,ranked)))
    return output
