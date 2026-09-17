"""Verify entity counts, source values, and entity ownership without DB writes."""

import argparse
from sqlalchemy import MetaData, select

from services.dataset_validation import TABLES, validate_all, add_validation_arguments, validation_options


def verify_database(engine, reports):
    metadata = MetaData()
    errors, summary = [], []
    with engine.connect() as connection:
        metadata.reflect(bind=connection, only=list(TABLES))
        stored = {}
        for name in TABLES:
            table = metadata.tables[name]
            key = next(iter(table.primary_key.columns)).name
            stored[name] = {r[key]: dict(r) for r in connection.execute(select(table)).mappings()}
        owners = {key: row['entity_id'] for key, row in stored['cases'].items()}
        for entity_id, entity in sorted(stored['entities'].items()):
            counts = {'entity_id': entity_id, 'entity_name': entity['entity_name']}
            for name in TABLES[1:]:
                counts[name] = sum((owners.get(r['case_id']) if name in ('investigations', 'escalations')
                                    else r['entity_id']) == entity_id for r in stored[name].values())
            summary.append(counts)
        for name in ('assets', 'alerts', 'cases', 'telemetry'):
            for key, row in stored[name].items():
                if row['entity_id'] not in stored['entities']:
                    errors.append(f'{name} {key}: missing entity')
                if name in ('alerts', 'telemetry') and row['asset_id'] is not None:
                    parent = stored['assets'].get(row['asset_id'])
                    if not parent or parent['entity_id'] != row['entity_id']:
                        errors.append(f'{name} {key}: invalid/cross-entity asset')
                if name == 'cases':
                    parent = stored['alerts'].get(row['alert_id'])
                    if not parent or parent['entity_id'] != row['entity_id']:
                        errors.append(f'cases {key}: invalid/cross-entity alert')
        for name in ('investigations', 'escalations'):
            for key, row in stored[name].items():
                if row['case_id'] not in owners:
                    errors.append(f'{name} {key}: missing case')
        for report in reports:
            if report['errors']:
                errors.append(f"{report['folder']}: source validation failed")
                continue
            entity_id = report['entity_id']
            for name in TABLES:
                table = metadata.tables[name]
                key = next(iter(table.primary_key.columns)).name
                expected = report['tables'][name]
                actual_ids = {pk for pk, r in stored[name].items()
                              if (owners.get(r['case_id']) if name in ('investigations', 'escalations')
                                  else r['entity_id']) == entity_id}
                if actual_ids != {row[key] for row in expected}:
                    errors.append(f'{entity_id} {name}: source/database ID or count mismatch')
                for row in expected:
                    actual = stored[name].get(row[key])
                    if actual is None or any(actual.get(k) != v for k, v in row.items()):
                        errors.append(f'{entity_id} {name} {row[key]}: source/database value mismatch')
        # No ground truth table is created or touched by this integration.
    return summary, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_validation_arguments(parser)
    args = parser.parse_args()
    from database import engine
    summary, errors = verify_database(engine, validate_all(**validation_options(args)))
    print('SHADOWWATCH MULTI-ENTITY DATABASE VERIFICATION')
    print('Organizations:', len(summary))
    for row in summary:
        print(row)
    for error in errors:
        print('FAIL:', error)
    print('Source values, counts and entity ownership:', 'FAIL' if errors else 'PASS')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
