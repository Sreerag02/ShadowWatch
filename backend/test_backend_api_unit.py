"""HTTP and import contracts against isolated SQLite, never production writes."""
import asyncio
import contextlib
from datetime import datetime, timedelta
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from main import app
from database import get_db
from import_all_entities import import_organization
from services.data_ingestion import import_organization_folder
from services.dataset_validation import ROOT
from test_multi_entity_unit import fixture, write_fixture

async def asgi_get(application, path, query=''):
    messages=[]
    received=False
    async def receive():
        nonlocal received
        if not received:
            received=True
            return {'type':'http.request','body':b'','more_body':False}
        await asyncio.Event().wait()
    async def send(message): messages.append(message)
    scope={'type':'http','asgi':{'version':'3.0'},'http_version':'1.1','method':'GET',
           'scheme':'http','path':path,'raw_path':path.encode(),'query_string':query.encode(),
           'root_path':'','headers':[], 'client':('127.0.0.1',1234),'server':('localhost',80)}
    await application(scope,receive,send)
    status=next(m['status'] for m in messages if m['type']=='http.response.start')
    body=b''.join(m.get('body',b'') for m in messages if m['type']=='http.response.body')
    try: body=json.loads(body)
    except ValueError: body=body.decode()
    return status,body

class BackendContractTests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
        @event.listens_for(self.engine,'connect')
        def enable(conn,_): conn.execute('PRAGMA foreign_keys=ON')
        with self.engine.begin() as conn:
            for statement in (ROOT/'database/schema.sql').read_text().split(';'):
                if statement.strip(): conn.exec_driver_sql(statement)
        self.report=fixture()
        self.report['tables']['alerts'][0]['severity']='CRITICAL'
        self.report['tables']['investigations'][0]['evidence_present']=True
        import_organization(self.engine,self.report)
        def override():
            with Session(self.engine) as session: yield session
        app.dependency_overrides[get_db]=override
    def tearDown(self):
        app.dependency_overrides.clear(); self.engine.dispose()
    def request(self,path,query=''):
        return asyncio.run(asyncio.wait_for(asgi_get(app,path,query),10))

    def test_health_docs_and_all_endpoints(self):
        self.assertEqual(self.request('/health'),(200,{'status':'ok','database':'ok'}))
        self.assertEqual(self.request('/docs')[0],200)
        paths=self.request('/openapi.json')[1]['paths']
        self.assertTrue({'/health','/entities','/entities/{entity_id}','/entities/{entity_id}/assets',
            '/entities/{entity_id}/cases','/cases/{case_id}','/assets/{asset_id}/telemetry',
            '/findings','/entities/{entity_id}/findings','/analytics/summary'} <= set(paths))

    def test_entities_lists_and_404s(self):
        self.assertEqual(self.request('/entities')[1][0]['entity_id'],'E9')
        self.assertEqual(self.request('/entities/')[0],200)
        entity=self.request('/entities/E9')[1]
        self.assertEqual((entity['asset_count'],entity['case_count']),(1,1))
        self.assertIsNone(self.request('/entities/E9/assets')[1][0]['monitoring_expected'])
        self.assertEqual(self.request('/entities/E9/cases')[1][0]['case_id'],'C9')
        for path in ['/entities/unknown','/entities/unknown/assets','/entities/unknown/cases',
                     '/entities/unknown/findings','/cases/unknown','/assets/unknown/telemetry']:
            self.assertEqual(self.request(path)[0],404,path)
        self.assertEqual(self.request('/findings','entity_id=unknown')[0],404)

    def test_null_case_evidence(self):
        code,case=self.request('/cases/C9')
        self.assertEqual(code,200)
        self.assertIsNone(case['investigation']['evidence_count'])
        self.assertIsNone(case['escalation']['escalated'])
        self.assertEqual(case['workflow']['assessment'],'INSUFFICIENT_DATA')
        self.assertEqual(case['findings'][0]['rule_id'],'R002')
        self.assertEqual(case['findings'][0]['assessment'],'INSUFFICIENT_DATA')
        self.assertNotIn('no supporting evidence',case['findings'][0]['reason'])

    def test_multiple_records_not_discarded(self):
        with self.engine.begin() as conn:
            conn.execute(text("INSERT INTO investigations (investigation_id,case_id,evidence_present,evidence_count) VALUES ('I10','C9',0,0)"))
            conn.execute(text("INSERT INTO escalations (escalation_id,case_id,escalated) VALUES ('S10','C9',0)"))
        code,case=self.request('/cases/C9')
        self.assertEqual(code,200)
        self.assertEqual(len(case['investigations']),2)
        self.assertEqual(len(case['escalations']),2)
        self.assertIsNone(case['investigation'])
        self.assertIsNone(case['escalation'])
        findings=[f for f in case['findings'] if f['rule_id']=='R002']
        self.assertEqual(len(findings),2)
        self.assertEqual({f['assessment'] for f in findings},{'CONFIRMED_GAP','INSUFFICIENT_DATA'})

    def test_telemetry_filters(self):
        self.assertEqual(self.request('/assets/AS9/telemetry','start_time=2099-01-01T00:00:00'),(200,[]))
        self.assertEqual(len(self.request('/assets/AS9/telemetry','start_time=2026-01-01&end_time=2026-01-01')[1]),1)
        self.assertEqual(self.request('/assets/AS9/telemetry','offset=1')[1],[])
        for query in ['limit=0','limit=5001','offset=-1','start_time=bad',
                      'start_time=2027-01-01&end_time=2026-01-01','start_time=2026-01-01T00:00:00Z']:
            self.assertEqual(self.request('/assets/AS9/telemetry',query)[0],422,query)
        self.assertEqual(self.request('/assets/AS9/telemetry','entity_id=another')[0],404)

    def test_consistent_findings_and_summary(self):
        findings=self.request('/findings')[1]
        self.assertEqual(findings,self.request('/entities/E9/findings')[1])
        self.assertEqual(findings,self.request('/findings','entity_id=E9')[1])
        self.assertEqual(self.request('/analytics/summary')[1]['finding_count'],len(findings))
        self.assertEqual(self.request('/entities/E9')[1]['finding_count'],len(findings))
        self.assertEqual(len({f['finding_id'] for f in findings}),len(findings))
        self.assertEqual(findings,self.request('/findings')[1])

    def test_r005_and_contradictions_integrate(self):
        from models import Telemetry
        with self.engine.begin() as conn:
            conn.execute(text("UPDATE investigations SET completed_at='2026-01-03 00:00:00'"))
            conn.execute(text('DELETE FROM telemetry'))
            conn.execute(Telemetry.__table__.insert(),[dict(telemetry_id=f'T{i}',entity_id='E9',asset_id='AS9',
                timestamp=datetime(2026,1,1)+timedelta(hours=i),event_count=100 if i<24 else 0) for i in range(27)])
        code,findings=self.request('/findings')
        self.assertEqual(code,200)
        self.assertTrue({'R002','R005','C001'} <= {f['rule_id'] for f in findings})
        self.assertEqual(len([f for f in findings if f['rule_id']=='R005']),1)
        self.assertNotIn('R005',{f['rule_id'] for f in self.request('/cases/C9')[1]['findings']})
        rows=self.request('/assets/AS9/telemetry')[1]
        self.assertEqual([r['timestamp'] for r in rows],sorted(r['timestamp'] for r in rows))

    def test_health_failure_sanitized(self):
        def broken():
            session=MagicMock()
            session.execute.side_effect=OperationalError('sensitive',{},Exception('secret'))
            yield session
        app.dependency_overrides[get_db]=broken
        code,body=self.request('/health')
        self.assertEqual(code,503)
        self.assertNotIn('secret',str(body))

    def test_behaviour_rules_in_shared_and_case_feeds(self):
        from models import Alert, Case, Investigation
        start = datetime(2026, 2, 1)
        note = 'Reviewed authentication records and confirmed unusual access from external networks'
        with self.engine.begin() as conn:
            for i in range(7):
                when = start + timedelta(days=i)
                conn.execute(Alert.__table__.insert().values(alert_id=f'BA{i}', entity_id='E9',
                    asset_id='AS9', timestamp=when, severity='HIGH', category='ACCESS'))
                conn.execute(Case.__table__.insert().values(case_id=f'BC{i}', alert_id=f'BA{i}',
                    entity_id='E9', opened_at=when, status='OPEN'))
                conn.execute(Investigation.__table__.insert().values(investigation_id=f'BI{i}',
                    case_id=f'BC{i}', started_at=when,
                    completed_at=when + timedelta(minutes=1 if i == 0 else 60), analyst_notes=note))
        code, findings = self.request('/findings')
        self.assertEqual(code, 200)
        self.assertEqual(findings, self.request('/entities/E9/findings')[1])
        affected = [f for f in findings if f['case_id'] == 'BC0']
        self.assertEqual(affected, self.request('/cases/BC0')[1]['findings'])
        behaviour = [f for f in affected if f['source'] == 'behaviour_analytics']
        self.assertEqual({f['rule_id'] for f in behaviour}, {'R006','R007','R008','R009'})
        self.assertTrue(all(f['assessment'] == 'REVIEW_REQUIRED' and f['evidence'] for f in behaviour))
        self.assertEqual(len({f['finding_id'] for f in findings}), len(findings))
        self.assertEqual(findings, self.request('/findings')[1])

    def test_bad_imports_rejected_before_writes(self):
        for mode in ('missing','severity','confidence','cross_entity','empty','duplicate'):
            report=fixture()
            if mode=='severity':report['tables']['alerts'][0]['severity']='INVALID'
            if mode=='confidence':report['tables']['alerts'][0]['confidence']='2'
            if mode=='cross_entity':report['tables']['assets'][0]['entity_id']='other'
            if mode=='duplicate':report['tables']['assets'].append(report['tables']['assets'][0].copy())
            with tempfile.TemporaryDirectory() as temp,Session(self.engine) as session:
                folder=Path(temp);write_fixture(folder,report)
                if mode=='missing':(folder/'telemetry.csv').unlink()
                if mode=='empty':(folder/'telemetry.csv').write_text('')
                with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'validation failed'):
                    import_organization_folder(session,folder)
            with self.engine.connect() as conn:
                self.assertEqual(conn.execute(text('SELECT count(*) FROM entities')).scalar(),1)

    def test_repeat_import_skip_and_cli_failure(self):
        from import_data import main
        with tempfile.TemporaryDirectory() as temp,Session(self.engine) as session,contextlib.redirect_stdout(io.StringIO()):
            write_fixture(Path(temp),self.report)
            summary=import_organization_folder(session,temp)
            self.assertTrue(all(v==0 for v in summary.values()))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(['/tmp/nonexistent-shadowwatch-contract-test']),1)

    def test_session_import_rolls_back_on_existing_child_id(self):
        report=fixture()
        for rows in report['tables'].values():
            for row in rows:
                if row.get('entity_id')=='E9': row['entity_id']='E10'
        with tempfile.TemporaryDirectory() as temp,Session(self.engine) as session:
            write_fixture(Path(temp),report)
            with self.assertRaisesRegex(ValueError,'rolled back'):
                import_organization_folder(session,temp)
        with self.engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT count(*) FROM entities WHERE entity_id='E10'")).scalar(),0)

    def test_new_folder_import_and_entity_isolation(self):
        report=fixture()
        mapping={'E9':'E10','AS9':'AS10','A9':'A10','C9':'C10','I9':'I10','S9':'S10','T9':'T10','GT9':'GT10'}
        for rows in report['tables'].values():
            for row in rows:
                for key,value in row.items():
                    if isinstance(value,str):row[key]=mapping.get(value,value)
        with tempfile.TemporaryDirectory() as temp,Session(self.engine) as session,contextlib.redirect_stdout(io.StringIO()):
            write_fixture(Path(temp),report)
            summary=import_organization_folder(session,temp)
            self.assertTrue(all(value==1 for value in summary.values()))
        self.assertEqual([r['case_id'] for r in self.request('/entities/E10/cases')[1]],['C10'])
        self.assertEqual([r['asset_id'] for r in self.request('/entities/E10/assets')[1]],['AS10'])
        self.assertTrue(all(f['entity_id']=='E9' for f in self.request('/entities/E9/findings')[1]))

    def test_session_closes_on_exception(self):
        mock=MagicMock()
        with patch('database.SessionLocal',return_value=mock):
            dependency=get_db();next(dependency)
            with self.assertRaises(RuntimeError):dependency.throw(RuntimeError('test'))
        mock.close.assert_called_once()

if __name__=='__main__':unittest.main()
