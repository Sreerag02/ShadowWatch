"""Risk API contracts using the existing isolated SQLite fixture."""
import unittest
from unittest.mock import patch
import tests.integration.test_backend_api as contract
from app.services.risk.risk_service import build_risk_intelligence
from app.services.risk.finding_aggregator import normalize_findings
from sqlalchemy.orm import Session
from app.main import app

class RiskAPITests(unittest.TestCase):
    setUp=contract.BackendContractTests.setUp
    tearDown=contract.BackendContractTests.tearDown
    request=contract.BackendContractTests.request

    def test_all_risk_endpoints_and_parity(self):
        code,all_risk=self.request('/risk/entities')
        self.assertEqual(code,200)
        self.assertEqual(len(all_risk),1)
        code,entity=self.request('/entities/E9/risk')
        self.assertEqual(code,200)
        self.assertEqual(entity,all_risk[0])
        self.assertEqual(entity['priority_cases'],self.request('/entities/E9/priority-cases')[1])
        self.assertEqual(entity['peer_context'],self.request('/entities/E9/peer-benchmark')[1])
        self.assertEqual(entity['summary'],self.request('/entities/E9/supervisory-summary')[1])
        self.assertEqual(entity['peer_context']['status'],'NO_VALID_PEERS')
        self.assertIn('not official NCIIPC',entity['disclaimer'])

    def test_unknown_entities(self):
        for endpoint in ('risk','priority-cases','peer-benchmark','supervisory-summary'):
            self.assertEqual(self.request('/entities/MISSING/'+endpoint)[0],404)

    def test_pagination(self):
        self.assertEqual(self.request('/entities/E9/priority-cases','offset=1')[1],[])
        for query in ('limit=0','limit=1001','offset=-1'):
            self.assertEqual(self.request('/entities/E9/priority-cases',query)[0],422)

    def test_existing_feed_unchanged_and_normalization_idempotent(self):
        before=self.request('/findings')[1]
        risk=self.request('/entities/E9/risk')[1]
        self.assertEqual(before,self.request('/findings')[1])
        self.assertEqual(normalize_findings(risk['findings']),risk['findings'])

    def test_engine_errors_propagate(self):
        with Session(self.engine) as db,patch('app.services.risk.risk_service.get_findings',side_effect=RuntimeError('failed engine')):
            with self.assertRaisesRegex(RuntimeError,'failed engine'):build_risk_intelligence(db)

    def test_empty_database(self):
        from sqlalchemy import text
        with self.engine.begin() as conn:
            for table in ('telemetry','escalations','investigations','cases','alerts','assets','entities'):
                conn.execute(text('DELETE FROM '+table))
        self.assertEqual(self.request('/risk/entities'),(200,[]))

if __name__=='__main__':unittest.main()
