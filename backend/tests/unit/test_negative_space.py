import unittest
from datetime import datetime, timedelta

from app.services.analytics.negative_space_engine import detect_telemetry_blind_spots
from scripts.validate_negative_space import evaluate_findings


def telemetry(values, asset='A', entity='E'):
    return [dict(entity_id=entity, asset_id=asset,
                 timestamp=datetime(2026, 1, 1) + timedelta(hours=i),
                 event_count=value) for i, value in enumerate(values)]


class NegativeSpaceTests(unittest.TestCase):
    def test_sustained_drop_and_recovery(self):
        rows = telemetry([100] * 24 + [0, 1, 2] + [100] * 6 + [0] * 30)
        findings = detect_telemetry_blind_spots(reversed(rows))
        self.assertEqual(len(findings), 2)
        self.assertEqual(findings[0]['baseline_activity'], 100)
        self.assertEqual(findings[0]['observed_activity'], 1)
        self.assertEqual(findings[0]['drop_percentage'], 99)
        self.assertEqual(findings[1]['consecutive_low_points'], 30)

    def test_quiet_short_history_transient_and_ratio_boundary(self):
        for values in ([0] * 30, [2] * 24 + [0] * 3,
                       [100] * 5 + [0] * 3, [100] * 24 + [0] * 2,
                       [100] * 24 + [10] * 3):
            with self.subTest(values=values):
                self.assertEqual(detect_telemetry_blind_spots(telemetry(values)), [])

    def test_invalid_values_break_persistence(self):
        for invalid in (None, '', float('nan'), float('inf'), -1, 'bad'):
            rows = telemetry([100] * 24 + [0, invalid, 0, 0])
            self.assertEqual(detect_telemetry_blind_spots(rows), [])

    def test_duplicates_and_gaps(self):
        rows = telemetry([100] * 24 + [0] * 3)
        self.assertEqual(len(detect_telemetry_blind_spots(rows + rows)), 1)
        self.assertEqual(detect_telemetry_blind_spots(rows[:-1] + [rows[-2]]), [])
        conflict = dict(rows[-2], event_count=100)
        self.assertEqual(detect_telemetry_blind_spots(rows + [conflict]), [])
        self.assertEqual(detect_telemetry_blind_spots(rows[:25] + rows[26:]), [])

    def test_entity_asset_isolation(self):
        rows = telemetry([100] * 24 + [0] * 3)
        rows += telemetry([100] * 27, entity='OTHER')
        rows += telemetry([0] * 27, asset='B')
        findings = detect_telemetry_blind_spots(rows)
        self.assertEqual([(f['entity_id'], f['asset_id']) for f in findings], [('E', 'A')])

    def test_evaluation_counts_and_empty_inputs(self):
        findings = [dict(rule_id='R005', entity_id='E', asset_id=a) for a in ['A', 'A', 'B']]
        truth = [dict(problem_type='TELEMETRY_BLIND_SPOT', expected_detection='true',
                      entity_id='E', asset_id=a) for a in ['A', 'C']]
        metrics = evaluate_findings(findings, truth)
        self.assertEqual([metrics[k] for k in ['TP', 'FP', 'FN']], [1, 1, 1])
        self.assertEqual(metrics['F1'], 0.5)
        self.assertEqual(evaluate_findings([], [])['F1'], 0)


if __name__ == '__main__':
    unittest.main()
