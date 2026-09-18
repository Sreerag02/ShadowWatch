"""Read-only live risk/API verification; assertions fail the process on errors."""
import asyncio
import math
from app.core.database import SessionLocal
from app.services.risk.risk_service import build_risk_intelligence
from app.services.analytics.findings_service import get_findings
from app.services.risk.finding_aggregator import normalize_findings
from tests.integration.test_backend_api import asgi_get
from app.main import app
from app.schemas import RiskResponse

async def main():
    with SessionLocal() as db:
        before=get_findings(db)
        reports=build_risk_intelligence(db)
        assert before==get_findings(db),'Risk analysis changed the source feed'
    async def get(path,query=''):
        status,data=await asyncio.wait_for(asgi_get(app,path,query),60)
        assert status==200,(path,status)
        return data
    api=await get('/risk/entities')
    expected=[RiskResponse.model_validate(r).model_dump(mode='json') for r in reports]
    assert api==expected
    for report in api:
        eid=report['entity_id']
        assert report==await get(f'/entities/{eid}/risk')
        assert report['priority_cases']==await get(f'/entities/{eid}/priority-cases','limit=1000')
        assert report['peer_context']==await get(f'/entities/{eid}/peer-benchmark')
        assert report['summary']==await get(f'/entities/{eid}/supervisory-summary')
        assert math.isfinite(report['overall_score']) and 0<=report['overall_score']<=100
        assert all(f['entity_id']==eid for f in report['findings'])
        assert len(report['priority_cases'])==report['denominators']['cases']
        assert all(p['reason'] and 0<=p['priority_score']<=100 for p in report['priority_cases'])
        assert report['aggregation']['total_findings']==len(normalize_findings(report['findings']))
        raw_ids={f['finding_id'] for f in before if f['entity_id']==eid}
        risk_source_ids={i for f in report['findings'] for i in f['source_finding_ids']}
        assert raw_ids<=risk_source_ids,'Lost original findings'
        print(eid,report['overall_score'],report['overall_level'],report['aggregation']['total_findings'],
              'peers',report['peer_context']['peer_entity_ids'],flush=True)
    print(f'PASS: risk, priorities, peer benchmarks and summaries for {len(reports)} entities; source findings unchanged.')

import os
import unittest

@unittest.skipUnless(os.getenv('SHADOWWATCH_RUN_POSTGRES_TESTS') == '1',
                     'Set SHADOWWATCH_RUN_POSTGRES_TESTS=1 for read-only PostgreSQL checks')
class RiskLiveTests(unittest.TestCase):
    def test_live_regression(self):
        asyncio.run(main())


if __name__=='__main__':asyncio.run(main())
