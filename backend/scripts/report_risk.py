"""Read-only PostgreSQL risk report; --json emits the complete review artifact."""
import argparse
import json
from app.core.database import SessionLocal
from app.services.risk.risk_service import build_risk_intelligence

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args()
    with SessionLocal() as db:
        reports=build_risk_intelligence(db)
    if args.json:
        print(json.dumps(reports,indent=2,default=str,allow_nan=False))
        return
    print('SHADOWWATCH RISK INTELLIGENCE ENGINE')
    for report in reports:
        print(f"\nEntity: {report['entity_id']} {report['entity_name']}")
        print(f"Overall Risk: {report['overall_score']:.2f} Level: {report['overall_level']} Status: {report['score_status']}")
        for name,component in report['components'].items():
            print(f"  {name}: {component['score']} ({component['status']}); contribution {component['contribution']}")
        print('Top contributors:')
        for item in report['top_contributors'][:5]:
            print(f"  {item['rule_id']}: {item['affected_cases']} cases / {item['affected_assets']} assets. {item['example_reason']}")
        print('Priority cases:')
        for item in report['priority_cases'][:3]:
            print(f"  {item['case_id']}: {item['priority_score']} {item['priority_level']} — {item['reason']}")
        for warning in report['limitations']:
            print('  Limitation:',warning)
        print(report['disclaimer'])
    print('\nANALYSIS COMPLETE')

if __name__=='__main__':main()
