"""Readable contradiction report: PostgreSQL by default, optional offline CSV."""

import argparse
import csv
from collections import defaultdict
from itertools import product
from pathlib import Path

from services.contradiction_engine import detect_cross_source_contradictions, SKIPPED_RULES


DATA_DIR = Path(__file__).resolve().parents[1] / 'data' / 'alpha_bank'


def _read_csv(name):
    with (DATA_DIR / name).open(newline='') as handle:
        return list(csv.DictReader(handle))


def load_csv_rows():
    """Mirror the service's LEFT JOINs using unmodified operational CSVs."""
    alerts = {(r['entity_id'], r['alert_id']): r for r in _read_csv('alerts.csv')}
    investigations, escalations = defaultdict(list), defaultdict(list)
    for row in _read_csv('investigations.csv'):
        investigations[row['case_id']].append(row)
    for row in _read_csv('escalations.csv'):
        escalations[row['case_id']].append(row)
    for case in _read_csv('cases.csv'):
        alert = alerts.get((case['entity_id'], case['alert_id']), {})
        for investigation, escalation in product(
            investigations[case['case_id']] or [{}], escalations[case['case_id']] or [{}]
        ):
            yield {
                'entity_id': case['entity_id'], 'case_id': case['case_id'],
                'alert_id': case['alert_id'], 'linked_alert_id': alert.get('alert_id'),
                'asset_id': alert.get('asset_id'), 'alert_severity': alert.get('severity'),
                'alert_timestamp': alert.get('timestamp'),
                'case_opened_at': case['opened_at'], 'case_closed_at': case['closed_at'],
                'investigation_id': investigation.get('investigation_id'),
                'investigation_started_at': investigation.get('started_at'),
                'investigation_completed_at': investigation.get('completed_at'),
                'escalation_id': escalation.get('escalation_id'),
                'escalation_escalated_at': escalation.get('escalated_at'),
            }


def check_ground_truth():
    # Evaluation metadata only; this runs after detection and never feeds it.
    rows = _read_csv('ground_truth.csv')
    labels = sorted({row['problem_type'] for row in rows})
    print('\nGround-truth problem types:', ', '.join(labels))
    contradiction_labels = [label for label in labels if
                            'CONTRADICTION' in label or label.startswith('C00') or
                            label in ('CASE_CLOSED_BEFORE_INVESTIGATION_COMPLETED',
                                      'INVESTIGATION_BEFORE_CASE_OPENED',
                                      'ESCALATION_AFTER_CASE_CLOSED', 'ALERT_AFTER_CASE_OPENED',
                                      'CLOSED_CASE_WITH_INCOMPLETE_INVESTIGATION')]
    if not contradiction_labels:
        print('Ground-truth validation for cross-source contradictions is not currently '
              'possible because the dataset contains no labelled contradiction scenarios.')
    else:
        print('Contradiction labels found:', ', '.join(contradiction_labels))
        print('A label-to-finding matching policy is needed before calculating metrics.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', action='store_true', help='Read bundled operational CSVs')
    parser.add_argument('--entity', help='Restrict findings to one entity')
    parser.add_argument('--check-ground-truth', action='store_true', help='Inspect labels after detection')
    args = parser.parse_args()
    results = detect_cross_source_contradictions(
        rows=load_csv_rows() if args.csv else None, entity_id=args.entity
    )
    print('========================================\n SHADOWWATCH CONTRADICTION ENGINE\n========================================')
    print('Source:', 'Bundled CSV' if args.csv else 'PostgreSQL')
    print('\nCross-source contradictions detected:', len(results))
    for finding in results:
        print('\n----------------------------------------')
        for name in ('rule_id', 'entity_id', 'case_id', 'severity', 'contradiction_type'):
            print(f'{name}: {finding[name]}')
        print('Source records:', finding['source_records'])
        print('\nEvidence:')
        for field, value in finding['evidence'].items():
            print(f'{field}: {value}')
        print('\nReason:\n' + finding['reason'])
    print('\nMissing timestamps/linked records are unassessable; zero findings does not prove completeness.')
    for rule, reason in SKIPPED_RULES.items():
        print(f'{rule}: {reason}')
    if args.check_ground_truth:
        check_ground_truth()
    print('\n========================================\n ANALYSIS COMPLETE\n========================================')


if __name__ == '__main__':
    main()
