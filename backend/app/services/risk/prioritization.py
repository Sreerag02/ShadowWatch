"""Explainable case review order, distinct from organization risk."""
from app.core.risk_config import DISCLAIMER, risk_config, level
from app.services.risk.finding_aggregator import component_for

def prioritize_cases(cases, findings, config=None):
    config = risk_config(config)
    results = []
    for case in cases:
        rows = [f for f in findings if (f['entity_id'],f.get('case_id')) == (case['entity_id'],case['case_id'])]
        alert_points = config['priority_alert_points'].get(case.get('severity'),0)
        asset_points = config['priority_asset_points'].get(case.get('asset_criticality'),0)
        contributions = {}
        for name, cap in config['priority_component_points'].items():
            weights = [config['severity_weights'][f['severity']] for f in rows
                       if component_for(f)==name and f['assessment']!='INSUFFICIENT_DATA']
            contributions[name] = cap*max(weights,default=0)
        score = round(min(100, alert_points+asset_points+sum(contributions.values())),2)
        reasons = [f"Alert severity {case.get('severity') or 'UNKNOWN'}: {alert_points} points.",
                   f"Asset criticality {case.get('asset_criticality') or 'UNKNOWN'}: {asset_points} points."]
        reasons.extend(f'{name}: {points:g} points (maximum per component).' for name,points in contributions.items() if points)
        reasons.extend(sorted({f"{f['rule_id']} [{f['assessment']}]: {f['reason']}" for f in rows}))
        if not rows:
            reasons.append('No findings linked to this case; order reflects observed alert/asset context only.')
        results.append(dict(case_id=case['case_id'],entity_id=case['entity_id'],priority_score=score,
            priority_level=level(score,config),triggered_findings=sorted({f['finding_id'] for f in rows}),
            triggered_rules=sorted({f['rule_id'] for f in rows}),reason=' '.join(reasons),
            score_breakdown=dict(alert=alert_points,asset=asset_points,components=contributions),disclaimer=DISCLAIMER))
    return sorted(results,key=lambda r:(-r['priority_score'],r['entity_id'],r['case_id']))
