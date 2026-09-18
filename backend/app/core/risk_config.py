"""Configurable prototype supervisory indicators, NOT official NCIIPC thresholds."""
from copy import deepcopy
from math import isfinite

DISCLAIMER = 'Prototype ShadowWatch supervisory indicator; not official NCIIPC thresholds or a compliance certification.'
DEFAULT_CONFIG = {
    'version': 'prototype-v1',
    'component_weights': {
        'EXECUTION_GAP_RISK': .30, 'MONITORING_VISIBILITY_RISK': .20,
        'INVESTIGATION_QUALITY_RISK': .20, 'REPEAT_INCIDENT_RISK': .15,
        'RECORD_CONSISTENCY_RISK': .15,
    },
    'severity_weights': {'LOW': .25, 'MEDIUM': .50, 'HIGH': .75, 'CRITICAL': 1.0},
    'level_thresholds': {'MODERATE': 25, 'HIGH': 50, 'CRITICAL': 75},
    'priority_alert_points': {'LOW': 5, 'MEDIUM': 10, 'HIGH': 20, 'CRITICAL': 30},
    'priority_asset_points': {'LOW': 0, 'MEDIUM': 3, 'HIGH': 6, 'CRITICAL': 10},
    'priority_component_points': {
        'EXECUTION_GAP_RISK': 30, 'MONITORING_VISIBILITY_RISK': 0,
        'INVESTIGATION_QUALITY_RISK': 15, 'REPEAT_INCIDENT_RISK': 10,
        'RECORD_CONSISTENCY_RISK': 15,
    },
    'small_sample_cases': 20,
    'peer_near_tolerance': .01,
    # Stored metadata is authoritative. Sector fallbacks require explicit opt-in.
    'peer_group_fallbacks': {},
}

def risk_config(config=None):
    result = deepcopy(DEFAULT_CONFIG if config is None else config)
    if set(result) != set(DEFAULT_CONFIG):
        raise ValueError('Risk configuration must specify all documented keys')
    for key in ('component_weights', 'severity_weights', 'priority_alert_points',
                'priority_asset_points', 'priority_component_points', 'level_thresholds'):
        if set(result[key]) != set(DEFAULT_CONFIG[key]):
            raise ValueError(f'Invalid keys for {key}')
        values = result[key].values()
        if any(not isinstance(v, (int, float)) or not isfinite(v) or v < 0 for v in values):
            raise ValueError(f'Invalid numeric weights for {key}')
    if abs(sum(result['component_weights'].values()) - 1) > 1e-9:
        raise ValueError('Component weights must sum to one')
    if any(v > 1 for v in result['severity_weights'].values()):
        raise ValueError('Severity weights must be between zero and one')
    levels = result['level_thresholds']
    if not 0 < levels['MODERATE'] < levels['HIGH'] < levels['CRITICAL'] <= 100:
        raise ValueError('Level thresholds must increase within 0..100')
    for key in ('small_sample_cases', 'peer_near_tolerance'):
        if not isinstance(result[key], (int, float)) or not isfinite(result[key]) or result[key] < 0:
            raise ValueError(f'Invalid {key}')
    if not isinstance(result['peer_group_fallbacks'], dict) or any(
        not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip()
        for k, v in result['peer_group_fallbacks'].items()
    ):
        raise ValueError('Peer fallbacks require nonempty sector/group strings')
    return result

def level(score, config):
    if not isfinite(score) or not 0 <= score <= 100:
        raise ValueError('Score must be finite and within 0..100')
    for label in ('CRITICAL', 'HIGH', 'MODERATE'):
        if score >= config['level_thresholds'][label]:
            return label
    return 'LOW'
