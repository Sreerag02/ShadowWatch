import json
import unittest
from datetime import datetime, timedelta, timezone

from app.services.analytics.contradiction_engine import detect_cross_source_contradictions


START = datetime(2026, 8, 12, 10)


def record(**changes):
    row = dict(entity_id='E1', case_id='C1', alert_id='A1', linked_alert_id='A1',
               asset_id='AS1', alert_severity='LOW', alert_timestamp=START,
               case_opened_at=START + timedelta(minutes=5),
               case_closed_at=START + timedelta(minutes=60), investigation_id='I1',
               investigation_started_at=START + timedelta(minutes=10),
               investigation_completed_at=START + timedelta(minutes=40),
               escalation_id='ESC1', escalation_escalated_at=START + timedelta(minutes=50))
    row.update(changes)
    return row


class ContradictionTests(unittest.TestCase):
    def rules(self, row):
        return [f['rule_id'] for f in detect_cross_source_contradictions([row])]

    def test_valid_chronology(self):
        self.assertEqual(self.rules(record()), [])

    def test_each_supported_rule(self):
        changes = {
            'C001': {'investigation_completed_at': START + timedelta(minutes=61)},
            'C002': {'investigation_started_at': START},
            'C003': {'escalation_escalated_at': START + timedelta(minutes=61)},
            'C004': {'alert_timestamp': START + timedelta(minutes=6)},
        }
        for rule, fields in changes.items():
            with self.subTest(rule=rule):
                self.assertEqual(self.rules(record(**fields)), [rule])

    def test_multiple_contradictions(self):
        self.assertEqual(self.rules(record(
            investigation_completed_at=START + timedelta(hours=2),
            investigation_started_at=START,
            escalation_escalated_at=START + timedelta(hours=2),
            alert_timestamp=START + timedelta(minutes=6),
        )), ['C001', 'C002', 'C003', 'C004'])

    def test_null_closure_only_skips_dependent_checks(self):
        self.assertEqual(self.rules(record(case_closed_at=None,
                                          investigation_started_at=START)), ['C002'])

    def test_null_investigation_timestamps(self):
        self.assertEqual(self.rules(record(investigation_started_at=None,
                                          investigation_completed_at=None)), [])

    def test_missing_escalation(self):
        self.assertEqual(self.rules(record(escalation_id=None,
                                          escalation_escalated_at=START + timedelta(hours=2))), [])

    def test_missing_optional_records(self):
        self.assertEqual(self.rules({'entity_id': 'E1', 'case_id': 'C1'}), [])
        self.assertEqual(self.rules({}), [])
        self.assertEqual(self.rules(record(linked_alert_id=None,
                                          alert_timestamp=START + timedelta(hours=2))), [])
        self.assertEqual(self.rules(record(investigation_id=None,
                                          investigation_completed_at=START + timedelta(hours=2))), [])

    def test_equal_timestamps(self):
        row = record()
        for key in ('alert_timestamp', 'case_opened_at', 'case_closed_at',
                    'investigation_started_at', 'investigation_completed_at',
                    'escalation_escalated_at'):
            row[key] = START
        self.assertEqual(self.rules(row), [])

    def test_explanation_and_json_evidence(self):
        result = detect_cross_source_contradictions([
            record(investigation_completed_at=START + timedelta(hours=2))
        ])[0]
        self.assertEqual(result['severity'], 'HIGH')
        self.assertEqual(result['alert_severity'], 'LOW')
        self.assertEqual(result['source_records'], {'case_id': 'C1', 'investigation_id': 'I1'})
        self.assertEqual(result['evidence'], {
            'investigations.completed_at': '2026-08-12 12:00:00',
            'cases.closed_at': '2026-08-12 11:00:00',
        })
        for value in ('C1', 'I1', 'investigations.completed_at', '2026-08-12 12:00:00', 'Review'):
            self.assertIn(value, result['reason'])
        json.dumps(result)

    def test_join_duplicates_preserve_distinct_investigations(self):
        first = record(investigation_completed_at=START + timedelta(hours=2))
        duplicate = dict(first, escalation_id='ESC2')
        second = dict(first, investigation_id='I2')
        results = detect_cross_source_contradictions([first, duplicate, second])
        self.assertEqual(len(results), 2)
        self.assertEqual(results, detect_cross_source_contradictions([second, duplicate, first]))

    def test_entity_filter_and_empty_rows(self):
        row = record(investigation_started_at=START)
        other = dict(row, entity_id='E2')
        self.assertEqual(len(detect_cross_source_contradictions([row, other])), 2)
        self.assertEqual(len(detect_cross_source_contradictions([row, other], entity_id='E1')), 1)
        self.assertEqual(detect_cross_source_contradictions([row], entity_id='unknown'), [])
        self.assertEqual(detect_cross_source_contradictions([]), [])

    def test_iso_strings_and_invalid_timestamps(self):
        self.assertEqual(self.rules(record(investigation_started_at='2026-08-12 10:00:00')), ['C002'])
        for value in ('', 'invalid', None, 123):
            self.assertEqual(self.rules(record(investigation_started_at=value)), [])

    def test_mixed_timezone_is_unassessable(self):
        self.assertEqual(self.rules(record(investigation_started_at=START.replace(tzinfo=timezone.utc))), [])
        row = record(case_opened_at=START.replace(tzinfo=timezone.utc),
                     investigation_started_at=(START - timedelta(minutes=1)).replace(tzinfo=timezone.utc))
        self.assertEqual(self.rules(row), ['C002'])


if __name__ == '__main__':
    unittest.main()
