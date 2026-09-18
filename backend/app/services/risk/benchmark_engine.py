"""Compare observed rates only within the same explicit group AND sector."""
from statistics import median, mean
from app.core.risk_config import risk_config

def peer_identity(entity, config):
    sector = (entity.get('sector') or '').strip()
    group = (entity.get('peer_group') or '').strip()
    source = 'stored' if group else 'unavailable'
    if not group and sector:
        mapping = {k.casefold():v for k,v in config['peer_group_fallbacks'].items()}
        group = mapping.get(sector.casefold(),'')
        source = 'configured_sector_fallback' if group else 'unavailable'
    return dict(group=group or None,sector=sector or None,source=source)

def benchmark_entity(selected, reports, config=None):
    config = risk_config(config)
    identity = peer_identity(selected,config)
    def key(item):
        p = peer_identity(item,config)
        return ((p['group'] or '').casefold(),(p['sector'] or '').casefold())
    peers = [r for r in reports if r['entity_id'] != selected['entity_id'] and
             identity['group'] and identity['sector'] and key(r)==key(selected)]
    metrics = {}
    for name, metric in selected['metrics'].items():
        values = [r['metrics'][name]['value'] for r in peers if r['metrics'][name]['value'] is not None]
        value = metric['value']
        midpoint = median(values) if values else None
        delta = value-midpoint if value is not None and midpoint is not None else None
        description = ('unavailable' if delta is None else 'near peer median' if abs(delta)<=config['peer_near_tolerance']
                       else 'above peer median' if delta>0 else 'below peer median')
        metrics[name] = dict(entity_value=value,peer_median=round(midpoint,4) if midpoint is not None else None,
            peer_mean=round(mean(values),4) if values else None,
            difference_from_peer_median=round(delta,4) if delta is not None else None,
            description=description,valid_peer_count=len(values),unit=metric['unit'],
            status='AVAILABLE' if delta is not None else 'ENTITY_METRIC_UNAVAILABLE' if value is None else 'NO_VALID_PEERS')
    return dict(entity_id=selected['entity_id'],peer_group=identity['group'],sector=identity['sector'],
        peer_group_source=identity['source'],stored_peer_group=selected.get('peer_group'),
        peer_entity_ids=sorted(r['entity_id'] for r in peers),
        peer_members=[dict(entity_id=r['entity_id'],**peer_identity(r,config)) for r in sorted(peers,key=lambda r:r['entity_id'])],
        status='AVAILABLE' if peers else 'NO_VALID_PEERS',metrics=metrics,
        explanation='Peer statistics exclude the selected entity and unavailable metric values. Same group and sector required; no best/worst ranking. No time-window alignment is assumed.')
