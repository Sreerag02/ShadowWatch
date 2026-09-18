"""Asset-level evaluation: ground truth has no episode timestamps.

Unlabelled detections count as FP under the synthetic dataset's closed-world
assumption. Multiple episodes on one asset count once, not as separate TP.
"""

import argparse
import csv

from scripts.report_negative_space import DATA_DIR, load_findings


def evaluate_findings(findings, ground_truth):
    expected = {
        (row['entity_id'], row['asset_id']) for row in ground_truth
        if row['problem_type'] == 'TELEMETRY_BLIND_SPOT'
        and str(row['expected_detection']).lower() == 'true'
    }
    detected = {
        (row['entity_id'], row['asset_id']) for row in findings
        if row['rule_id'] == 'R005'
    }
    tp, fp, fn = len(expected & detected), len(detected - expected), len(expected - detected)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        'TP': tp, 'FP': fp, 'FN': fn,
        'Precision': precision, 'Recall': recall,
        'F1': 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        'False positive assets': sorted(detected - expected),
        'False negative assets': sorted(expected - detected),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', action='store_true')
    args = parser.parse_args()
    findings = load_findings(args.csv)
    # Read labels only after detection has completed.
    with (DATA_DIR / 'ground_truth.csv').open(newline='') as handle:
        metrics = evaluate_findings(findings, csv.DictReader(handle))
    print('R005 VALIDATION (entity + asset; no episode timing labels)')
    for name, value in metrics.items():
        print(f'{name}: {value:.2%}' if isinstance(value, float) else f'{name}: {value}')


if __name__ == '__main__':
    main()
