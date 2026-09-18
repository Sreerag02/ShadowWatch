"""Pure risk calculations over supplied findings and exposure sets, not detectors."""
from collections import defaultdict
from app.core.risk_config import DISCLAIMER, risk_config, level
from app.services.risk.finding_aggregator import (
    COMPONENT_ENGINES, ENGINES, aggregate_findings, component_for, normalize_findings,
)

EXPOSURES = {
    'EXECUTION_GAP_RISK': 'serious_cases',
    'MONITORING_VISIBILITY_RISK': 'monitored_assets',
    'INVESTIGATION_QUALITY_RISK': 'investigated_cases',
    'REPEAT_INCIDENT_RISK': 'cases',
    'RECORD_CONSISTENCY_RISK': 'cases',
}

def rate(numerator, denominator, unit='percent'):
    return dict(numerator=numerator, denominator=denominator,
                value=round(100*numerator/denominator, 4) if denominator else None,
                unit=unit, status='AVAILABLE' if denominator else 'NO_DENOMINATOR')

def calculate_risk(entity, findings, exposures, engine_status=None, config=None):
    config = risk_config(config)
    findings = normalize_findings(findings)
    if any(f['entity_id'] != entity['entity_id'] for f in findings):
        raise ValueError('Risk findings must belong to the selected entity')
    statuses = dict(engine_status) if engine_status is not None else {name:'AVAILABLE' for name in ENGINES}
    if any(v not in ('AVAILABLE', 'UNAVAILABLE') for v in statuses.values()):
        raise ValueError('Engine status must be AVAILABLE or UNAVAILABLE')
    populations = {key:set(exposures.get(key, [])) for key in set(EXPOSURES.values()) | {'critical_cases','investigated_serious_cases'}}
    if not populations['serious_cases'] <= populations['cases'] or not populations['investigated_cases'] <= populations['cases']:
        raise ValueError('Case exposure sets must be subsets of all cases')
    if not populations['critical_cases'] <= populations['serious_cases'] or not populations['investigated_serious_cases'] <= populations['serious_cases'] & populations['investigated_cases']:
        raise ValueError('Invalid serious/critical investigation exposure sets')
    warnings = list(exposures.get('limitations', []))
    if len(populations['cases']) < config['small_sample_cases']:
        warnings.append('Small case population: rates can change sharply with one case.')
    components = {}
    scored = [f for f in findings if f['assessment'] != 'INSUFFICIENT_DATA']
    for name, population_key in EXPOSURES.items():
        population = populations[population_key]
        rows = [f for f in scored if component_for(f) == name]
        key = 'asset_id' if population_key == 'monitored_assets' else 'case_id'
        weights = defaultdict(float)
        excluded = []
        for f in rows:
            if f.get(key) not in population:
                excluded.append(f['finding_id'])
                continue
            weights[f[key]] = max(weights[f[key]], config['severity_weights'][f['severity']])
        missing = sorted(e for e in COMPONENT_ENGINES[name] if statuses.get(e) != 'AVAILABLE')
        status = 'ENGINE_UNAVAILABLE' if missing else 'NO_DENOMINATOR' if not population else 'AVAILABLE'
        score = 100*sum(weights.values())/len(population) if status == 'AVAILABLE' else None
        components[name] = dict(score=round(score,4) if score is not None else None,
            weight=config['component_weights'][name],
            contribution=round((score or 0)*config['component_weights'][name],4),
            exposure=population_key, denominator=len(population), affected_count=len(weights),
            weighted_affected_count=sum(weights.values()), status=status, missing_engines=missing,
            excluded_finding_ids=sorted(excluded), finding_ids=sorted(f['finding_id'] for f in rows),
            formula='100 * sum(max severity weight per eligible case/asset) / eligible population')
        if status != 'AVAILABLE':
            warnings.append(f'{name}: {status}; contributes no observed points, not evidence of safety.')
        if excluded:
            warnings.append(f'{name}: {len(excluded)} findings lack an eligible scoring exposure; retained for review.')
    unmapped = sorted({f['rule_id'] for f in findings if component_for(f) is None})
    if unmapped:
        warnings.append('Unmapped rules retained but not scored: ' + ', '.join(unmapped))
    unknown = sum(f['assessment']=='INSUFFICIENT_DATA' for f in findings)
    if unknown:
        warnings.append(f'{unknown} insufficient-data findings retained but not scored as confirmed gaps.')
    overall = round(min(100, sum(c['contribution'] for c in components.values())),2)
    coverage = sum(c['weight'] for c in components.values() if c['status']=='AVAILABLE')
    aggregation = aggregate_findings(findings)
    def affected(rules, population, field='case_id'):
        return {f.get(field) for f in scored if f['rule_id'] in rules} & populations[population]
    metrics = {
        'findings_per_100_cases': rate(len(findings),len(populations['cases']),'findings per 100 cases'),
        'execution_gap_rate': rate(len({f['case_id'] for f in scored if component_for(f)=='EXECUTION_GAP_RISK'} & populations['serious_cases']),len(populations['serious_cases'])),
        'missing_escalation_rate': rate(len(affected({'R003'},'critical_cases')),len(populations['critical_cases'])),
        'missing_evidence_rate': rate(len(affected({'R002','WF_EVIDENCE'},'investigated_serious_cases')),len(populations['investigated_serious_cases'])),
        'telemetry_blind_spot_rate': rate(len(affected({'R005'},'monitored_assets','asset_id')),len(populations['monitored_assets'])),
        'repetitive_investigation_rate': rate(len(affected({'R006'},'investigated_cases')),len(populations['investigated_cases'])),
        'repeat_incident_rate': rate(len(affected({'R008'},'cases')),len(populations['cases'])),
        'contradiction_rate': rate(len(affected({'C001','C002','C003','C004'},'cases')),len(populations['cases'])),
        'behaviour_findings_per_100_investigated_cases': rate(aggregation['behaviour_analytics_count'],len(populations['investigated_cases']),'findings per 100 investigated cases'),
    }
    metric_engines = {
        'missing_escalation_rate': {'rule_engine'}, 'missing_evidence_rate': {'rule_engine','workflow_auditor'},
        'execution_gap_rate': COMPONENT_ENGINES['EXECUTION_GAP_RISK'],
        'telemetry_blind_spot_rate': {'negative_space_engine'},
        'repetitive_investigation_rate': {'behaviour_analytics'}, 'repeat_incident_rate': {'behaviour_analytics'},
        'contradiction_rate': {'contradiction_engine'},
        'behaviour_findings_per_100_investigated_cases': {'behaviour_analytics'},
        'findings_per_100_cases': ENGINES,
    }
    for name, required in metric_engines.items():
        if any(statuses.get(e) != 'AVAILABLE' for e in required):
            metrics[name].update(value=None,status='ENGINE_UNAVAILABLE')
    metrics['median_investigation_minutes'] = dict(value=exposures.get('median_investigation_minutes'),
        unit='minutes', sample_count=exposures.get('valid_duration_count',0),
        status='AVAILABLE' if exposures.get('median_investigation_minutes') is not None else 'NO_OBSERVATIONS')
    contributors = []
    for rule in sorted({f['rule_id'] for f in scored}):
        rows = [f for f in scored if f['rule_id']==rule]
        component = component_for(rows[0])
        contributors.append(dict(rule_id=rule, component=component,
            affected_cases=len({f['case_id'] for f in rows if f.get('case_id')}),
            affected_assets=len({f['asset_id'] for f in rows if f.get('asset_id')}),
            finding_count=len(rows), example_reason=rows[0]['reason'],
            finding_ids=sorted(f['finding_id'] for f in rows)))
    contributors.sort(key=lambda r:(-components.get(r['component'],{}).get('contribution',0),-r['affected_cases'],r['rule_id']))
    active = [name for name, c in sorted(components.items(),key=lambda item:(-item[1]['contribution'],item[0])) if c['contribution']>0]
    explanation = (f"{entity['entity_id']} has an observed prototype score of {overall:.2f} ({level(overall,config)}). " +
        ('Largest component contributions: ' + ', '.join(active[:2]) + '.' if active else 'No scored findings in available components.') +
        ' Missing evidence or unavailable components must not be interpreted as low underlying risk.')
    return dict(entity_id=entity['entity_id'],entity_name=entity['entity_name'],sector=entity.get('sector'),
        peer_group=entity.get('peer_group'), overall_score=overall, overall_level=level(overall,config),
        score_status='AVAILABLE' if coverage >= 1-1e-9 else 'PARTIAL',
        available_component_weight=round(coverage,4),
        unavailable_component_upper_bound=round(min(100,overall+100*(1-coverage)),2),
        components=components, aggregation=aggregation, metrics=metrics,
        denominators={key:len(value) for key,value in populations.items()},
        data_coverage=exposures.get('data_coverage',{}), engine_status=statuses,
        top_contributors=contributors, explanation=explanation, limitations=sorted(set(warnings)),
        disclaimer=DISCLAIMER, config=config, findings=findings)
