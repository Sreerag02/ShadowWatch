"""Read-only PostgreSQL HTTP verification for every current entity/case/asset.

Run explicitly: python3 test_backend_integration.py. Uses direct ASGI HTTP
requests, with no listening server or external dependencies.
"""
import asyncio
from collections import Counter
from sqlalchemy import text
from database import engine
from main import app
from test_backend_api_unit import asgi_get

async def main():
    with engine.connect() as conn:
        entities=conn.execute(text('SELECT entity_id FROM entities ORDER BY entity_id')).scalars().all()
        cases=conn.execute(text('SELECT case_id,entity_id FROM cases ORDER BY case_id')).mappings().all()
        assets=conn.execute(text('SELECT asset_id,entity_id FROM assets ORDER BY asset_id')).mappings().all()
        investigations=dict(conn.execute(text('SELECT case_id,count(*) FROM investigations GROUP BY case_id')).all())
        escalations=dict(conn.execute(text('SELECT case_id,count(*) FROM escalations GROUP BY case_id')).all())
        telemetry_counts=dict(conn.execute(text('SELECT asset_id,count(*) FROM telemetry GROUP BY asset_id')).all())
    async def get(path,query='',expected=200):
        status,data=await asyncio.wait_for(asgi_get(app,path,query),30)
        assert status==expected,(path,status,data)
        return data
    for path in ('/health','/docs','/openapi.json'):
        await get(path)
    assert len(await get('/entities'))==len(entities)
    all_findings=await get('/findings')
    summary=await get('/analytics/summary')
    assert summary['entity_count']==len(entities)
    assert summary['case_count']==len(cases)
    assert summary['finding_count']==len(all_findings)
    for entity in entities:
        detail=await get('/entities/'+entity)
        entity_cases=await get(f'/entities/{entity}/cases','limit=1000')
        entity_assets=await get(f'/entities/{entity}/assets','limit=1000')
        assert len(entity_cases)==detail['case_count']
        assert len(entity_assets)==detail['asset_count']
        assert all(r['entity_id']==entity for r in entity_cases+entity_assets)
        findings=await get(f'/entities/{entity}/findings')
        assert findings==[f for f in all_findings if f['entity_id']==entity]
        assert detail['finding_count']==len(findings)
        print(entity,'cases',len(entity_cases),'assets',len(entity_assets),'findings',len(findings))
    for case in cases:
        data=await get('/cases/'+case['case_id'])
        assert data['entity_id']==case['entity_id']
        assert len(data['investigations'])==investigations.get(case['case_id'],0)
        assert len(data['escalations'])==escalations.get(case['case_id'],0)
        assert data['findings']==[f for f in all_findings if f.get('case_id')==case['case_id']]
        if data['alert']:
            assert data['alert']['entity_id']==case['entity_id']
        if data['case_id']=='E001-C0081':
            assert {'R002','R003','R004'} <= {f['rule_id'] for f in data['findings']}
    for asset in assets:
        data=await get(f"/assets/{asset['asset_id']}/telemetry",'limit=5000')
        assert len(data)==min(5000,telemetry_counts.get(asset['asset_id'],0))
        assert all(r['entity_id']==asset['entity_id'] for r in data)
        assert [(r['timestamp'],r['telemetry_id']) for r in data]==sorted((r['timestamp'],r['telemetry_id']) for r in data)
    assert await get('/assets/E001-AS001/telemetry','start_time=2099-01-01T00:00:00')==[]
    for path in ('/entities/UNKNOWN','/cases/UNKNOWN','/assets/UNKNOWN/telemetry'):
        await get(path,expected=404)
    print(f'PASS: {len(entities)} entities, {len(cases)} case responses, {len(assets)} asset telemetry responses')
    print('Finding counts:',dict(Counter(f['rule_id'] for f in all_findings)))

if __name__=='__main__':
    asyncio.run(main())
