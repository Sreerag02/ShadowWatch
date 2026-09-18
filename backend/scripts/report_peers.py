"""Readable peer rates from existing PostgreSQL records and engine findings."""
from app.core.database import SessionLocal
from app.services.risk.risk_service import build_risk_intelligence

def main():
    with SessionLocal() as db:
        reports=build_risk_intelligence(db)
    print('SHADOWWATCH PEER BENCHMARK')
    for report in reports:
        peers=report['peer_context']
        print(f"\n{report['entity_id']} {report['entity_name']} | Peer group: {peers['peer_group']} ({peers['peer_group_source']})")
        print('Cases:',report['denominators']['cases'],'Other peers:',', '.join(peers['peer_entity_ids']) or 'none')
        for name,metric in peers['metrics'].items():
            print(f"  {name}: entity={metric['entity_value']}, peer median={metric['peer_median']}, "
                  f"difference={metric['difference_from_peer_median']} ({metric['unit']}); {metric['description']}; n={metric['valid_peer_count']}")
    print('\nANALYSIS COMPLETE')

if __name__=='__main__':main()
