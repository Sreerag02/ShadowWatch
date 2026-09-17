"""Explicit, backed-up repairs of Gamma/PowerGrid synthetic datasets.

Run once from any directory. Original files are retained under work/dataset_backups.
No database writes. Missing source measurements remain blank.
"""
import csv
import json
from datetime import datetime
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from services.dataset_validation import HEADERS, adapt_gamma


def read(path):
    with path.open(newline='') as handle:
        return list(csv.DictReader(handle))


def write(path, rows, headers):
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    backup = ROOT / 'work/dataset_backups/before_gamma_powergrid_repair'
    if backup.exists():
        raise SystemExit('Backup already exists; repairs are one-shot. Inspect current data before rerunning.')
    for folder in ('gamma_bank', 'powergrid_utility'):
        shutil.copytree(ROOT / 'data' / folder, backup / folder)
    changes = []
    gamma_path = ROOT / 'data/gamma_bank'
    gamma = {table: read(gamma_path / f'{table}.csv') for table in HEADERS}
    if 'Member' not in gamma['entities'][0]:
        raise SystemExit('Gamma is not in the expected original format; no files changed.')
    cases = {r['case_id']: r for r in gamma['cases']}
    alerts = {r['alert_id']: r for r in gamma['alerts']}
    for case in cases.values():
        alert = alerts[case['alert_id']]
        if case['severity'] != alert['severity']:
            changes.append(dict(file='gamma_bank/alerts.csv', id=alert['alert_id'], field='severity',
                                before=alert['severity'], after=case['severity'],
                                reason='Align with explicit source case severity; preserve fast critical closure cases.'))
            alert['severity'] = case['severity']
    for row in gamma['escalations']:
        closed = cases[row['case_id']]['closed_at']
        if datetime.fromisoformat(row['escalated_at']) > datetime.fromisoformat(closed):
            changes.append(dict(file='gamma_bank/escalations.csv', id=row['escalation_id'], field='escalated_at',
                                before=row['escalated_at'], after=closed,
                                reason='Synthetic correction: place escalation at case closure boundary.'))
            row['escalated_at'] = closed
    for table, rows in gamma.items():
        normalized = [adapt_gamma(table, row) for row in rows]
        write(gamma_path / f'{table}.csv', normalized, HEADERS[table])
    changes.append(dict(file='gamma_bank/*.csv', reason='Canonical schema conversion using documented adapter; original-only fields retained in backup; unavailable fields blank.'))

    power_path = ROOT / 'data/powergrid_utility'
    power = {table: read(power_path / f'{table}.csv') for table in HEADERS}
    cases = {r['case_id']: r for r in power['cases']}
    for table in ('investigations', 'escalations'):
        for row in power[table]:
            if row['case_id'] not in ('E005-C0021', 'E005-C0041'):
                continue
            case = cases[row['case_id']]
            opened, closed = (datetime.fromisoformat(case[key]) for key in ('opened_at', 'closed_at'))
            fields = {'started_at': 1/3, 'completed_at': 2/3} if table == 'investigations' else {'escalated_at': 5/6}
            for field, fraction in fields.items():
                replacement = (opened + (closed - opened) * fraction).isoformat(sep=' ')
                changes.append(dict(file=f'powergrid_utility/{table}.csv', id=row[HEADERS[table][0]],
                                    field=field, before=row[field], after=replacement,
                                    reason='Synthetic timing repair within existing fast-closure interval; closure duration unchanged.'))
                row[field] = replacement
        write(power_path / f'{table}.csv', power[table], HEADERS[table])
    # Preserve scenario grouping while giving every ground-truth row a unique ID.
    for index, row in enumerate(power['ground_truth']):
        if row['scenario_id'] == 'S06' and row['case_id'] in ('E005-C0032', 'E005-C0033'):
            replacement = 'S06-2' if row['case_id'] == 'E005-C0032' else 'S06-3'
            changes.append(dict(file='powergrid_utility/ground_truth.csv', id=row['case_id'],
                                field='scenario_id', before='S06', after=replacement,
                                reason='Distinct IDs for separate labelled case rows.'))
            row['scenario_id'] = replacement
    write(power_path / 'ground_truth.csv', power['ground_truth'], HEADERS['ground_truth'])
    # The explicitly labelled fast CRITICAL closure was mistakenly attached to
    # a LOW alert. Fix the synthetic label/operational severity mismatch.
    alert_id = cases['E005-C0021']['alert_id']
    for row in power['alerts']:
        if row['alert_id'] == alert_id:
            changes.append(dict(file='powergrid_utility/alerts.csv', id=alert_id, field='severity',
                                before=row['severity'], after='CRITICAL',
                                reason='Correct synthetic FAST_CRITICAL_CLOSURE scenario severity.'))
            row['severity'] = 'CRITICAL'
    write(power_path / 'alerts.csv', power['alerts'], HEADERS['alerts'])
    (ROOT / 'docs/dataset_repairs.json').write_text(json.dumps(changes, indent=2) + '\n')
    print('Repaired Gamma and PowerGrid. Original CSVs:', backup)
    print('Audit log: docs/dataset_repairs.json')


if __name__ == '__main__':
    main()
