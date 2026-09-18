"""Executable R005 report: DB by default, or --csv for bundled offline data."""

import argparse
import csv
from pathlib import Path

from app.services.analytics.negative_space_engine import detect_telemetry_blind_spots


from app.core.config import DATA_DIR as DATA_ROOT
DATA_DIR = DATA_ROOT / 'alpha_bank'


def load_findings(use_csv=False):
    if use_csv:
        with (DATA_DIR / 'telemetry.csv').open(newline='') as handle:
            return detect_telemetry_blind_spots(csv.DictReader(handle))
    return detect_telemetry_blind_spots()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', action='store_true', help='Use bundled telemetry instead of PostgreSQL')
    args = parser.parse_args()
    findings = load_findings(args.csv)
    print('\n======================================')
    print(' SHADOWWATCH NEGATIVE-SPACE ENGINE')
    print('======================================')
    print('\nTelemetry blind spots detected:', len(findings))
    for finding in findings:
        print('\n--------------------------------------')
        for label, key in [('Rule', 'rule_id'), ('Entity', 'entity_id'),
                           ('Asset', 'asset_id'), ('Start', 'start_time'),
                           ('End', 'end_time')]:
            print(f'{label}: {finding[key]}')
        print(f"Baseline: {finding['baseline_activity']:.2f}")
        print(f"Observed: {finding['observed_activity']:.2f}")
        print(f"Drop: {finding['drop_percentage']:.2f}%")
        print('\nReason:\n' + finding['reason'])
    print('\n======================================\n ANALYSIS COMPLETE\n======================================')


if __name__ == '__main__':
    main()
