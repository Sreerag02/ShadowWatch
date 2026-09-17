import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from services.rule_engine import evaluate_critical_case
from services.workflow_auditor import (
    assess_case_workflow, audit_case_workflow, audit_entity_workflows,
)


def case_row(**changes):
    opened = datetime(2026, 8, 12, 12)
    row = dict(case_id='C1', entity_id='E1', alert_id='A1', asset_id='AS1',
               severity='CRITICAL', category='RANSOMWARE', opened_at=opened,
               closed_at=opened + timedelta(minutes=60), case_status='CLOSED',
               investigation_id='I1', evidence_present=True, evidence_count=2,
               escalation_id='ESC1', escalated=True)
    row.update(changes)
    return row


class WorkflowAuditorTests(unittest.TestCase):
    def test_normal_critical_workflow(self):
        result = assess_case_workflow([case_row()])
        self.assertEqual(result['assessment'], 'NO_GAP')
        self.assertEqual(result['triggered_rules'], [])
        self.assertTrue(result['observed']['evidence'])
        self.assertEqual(result['closure_minutes'], 60)
        self.assertIsNone(evaluate_critical_case(case_row()))
        json.dumps(result)  # API-ready: timestamps are serialized.

    def test_individual_rules(self):
        scenarios = [
            ('R001', dict(investigation_id=None, evidence_present=None, evidence_count=None)),
            ('R002', dict(evidence_present=False)),
            ('R002', dict(evidence_count=0)),
            ('R003', dict(escalation_id=None, escalated=None)),
            ('R003', dict(escalated=False)),
            ('R004', dict(closed_at=datetime(2026, 8, 12, 12, 1, 18))),
        ]
        for rule, changes in scenarios:
            with self.subTest(rule=rule, changes=changes):
                result = assess_case_workflow([case_row(**changes)])
                self.assertEqual(result['triggered_rules'], [rule])
                self.assertEqual(result['assessment'], 'EXECUTION_GAP')

    def test_multiple_gaps_example(self):
        row = case_row(case_id='E001-C0081', evidence_present=False,
                       escalated=False, closed_at=datetime(2026, 8, 12, 12, 1, 18))
        result = assess_case_workflow([row])
        self.assertEqual(result['triggered_rules'], ['R002', 'R003', 'R004'])
        self.assertEqual(result['closure_minutes'], 1.3)
        self.assertEqual([gap['stage'] for gap in result['gaps']], ['EVIDENCE', 'ESCALATION', 'CLOSURE'])
        self.assertIn('1.3 minutes', result['explanation'])

    def test_null_optional_values_are_unknown(self):
        result = assess_case_workflow([case_row(category=None, opened_at=None,
                                               closed_at=None, case_status=None,
                                               evidence_present=None, escalated=None)])
        self.assertIsNone(result['closure_minutes'])
        self.assertIsNone(result['observed']['evidence'])
        self.assertIsNone(result['observed']['escalation'])
        self.assertEqual(result['triggered_rules'], [])
        self.assertTrue(any('unknown' in item for item in result['limitations']))

    def test_null_count_retains_legacy_r002(self):
        result = assess_case_workflow([case_row(evidence_count=None)])
        self.assertEqual(result['triggered_rules'], ['R002'])
        self.assertIsNone(result['observed']['evidence'])
        self.assertTrue(any('NULL evidence count' in item for item in result['limitations']))

    def test_closure_boundary_and_invalid_duration(self):
        result = assess_case_workflow([case_row(closed_at=datetime(2026, 8, 12, 12, 10))])
        self.assertEqual(result['triggered_rules'], [])
        result = assess_case_workflow([case_row(closed_at=datetime(2026, 8, 12, 11))])
        self.assertEqual(result['triggered_rules'], ['R004'])
        self.assertTrue(any('invalid' in item for item in result['limitations']))

    def test_high_policy_does_not_extend_critical_rules(self):
        result = assess_case_workflow([case_row(severity='HIGH', evidence_present=False,
                                               escalated=False,
                                               closed_at=datetime(2026, 8, 12, 12, 1))])
        self.assertEqual(result['triggered_rules'], [])
        self.assertEqual(result['assessment'], 'EXECUTION_GAP')
        self.assertEqual(result['gaps'][0]['stage'], 'EVIDENCE')
        self.assertIsNone(result['expected']['escalation'])
        self.assertIsNone(result['closure_policy'])
        result = assess_case_workflow([case_row(severity='HIGH', investigation_id=None)])
        self.assertEqual(result['gaps'][0]['stage'], 'INVESTIGATION')

    def test_out_of_scope_case_without_rules(self):
        result = assess_case_workflow([case_row(severity='LOW', investigation_id=None)])
        self.assertEqual(result['triggered_rules'], [])
        self.assertFalse(result['assessment_in_scope'])
        self.assertIsNone(result['expected']['investigation'])

    def test_multiple_records_are_preserved_and_gaps_deduplicated(self):
        good = case_row()
        bad = case_row(investigation_id='I2', evidence_present=False)
        result = assess_case_workflow([good, bad, good, bad])
        self.assertEqual(result['triggered_rules'], ['R002'])
        self.assertEqual(len(result['gaps']), 1)
        self.assertEqual(len(result['records']['investigations']), 2)
        self.assertIsNone(result['observed']['evidence'])
        self.assertEqual(result, assess_case_workflow([bad, good]))

    @patch('services.workflow_auditor._load_rows', return_value=[])
    def test_unknown_case_id(self, load):
        self.assertIsNone(audit_case_workflow("unknown' OR 1=1"))
        load.assert_called_once_with(' WHERE c.case_id = :case_id', {'case_id': "unknown' OR 1=1"})

    @patch('services.workflow_auditor._load_rows')
    def test_entity_audit_groups_cases(self, load):
        load.return_value = [case_row(case_id='C2'), case_row(), case_row()]
        results = audit_entity_workflows('E1')
        self.assertEqual([r['case_id'] for r in results], ['C1', 'C2'])
        self.assertEqual(load.call_args.args[1], {'entity_id': 'E1'})
        self.assertIn("a.severity IN ('HIGH', 'CRITICAL')", load.call_args.args[0])
        load.return_value = []
        self.assertEqual(audit_entity_workflows('unknown'), [])

    def test_mixed_case_input_is_rejected(self):
        with self.assertRaises(ValueError):
            assess_case_workflow([case_row(), case_row(case_id='C2')])


if __name__ == '__main__':
    unittest.main()
