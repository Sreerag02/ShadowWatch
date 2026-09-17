"""Non-destructive import: validate first, skip existing entities, transact per organization."""

import argparse

from sqlalchemy import MetaData, select

from services.dataset_validation import (
    TABLES, validate_all, print_reports, add_validation_arguments, validation_options,
)


def import_organization(engine, report):
    with engine.begin() as connection:
        return import_validated_connection(connection, report)


def import_validated_connection(connection, report):
    if report['errors']:
        return 'BLOCKED - validation failed'
    entity = report['tables']['entities'][0]
    entity_id = entity['entity_id']
    metadata = MetaData()
    metadata.reflect(bind=connection, only=list(TABLES))
    entities = metadata.tables['entities']
    if connection.execute(select(entities.c.entity_id).where(entities.c.entity_id == entity_id)).first():
        return f'SKIPPED {entity_id} - entity already exists'
    for name in TABLES:
        table = metadata.tables[name]
        rows = report['tables'][name]
        for offset in range(0, len(rows), 500):
            connection.execute(table.insert(), rows[offset:offset + 500])
    # Verify every supplied value before committing, not merely total counts.
    for name in TABLES:
        table = metadata.tables[name]
        key = next(iter(table.primary_key.columns)).name
        expected = {row[key]: row for row in report['tables'][name]}
        for offset in range(0, len(expected), 500):
            ids = list(expected)[offset:offset + 500]
            actual = list(connection.execute(select(table).where(table.c[key].in_(ids))).mappings())
            if len(actual) != len(ids):
                raise ValueError(f'{name}: post-import count mismatch')
            for row in actual:
                if any(row[column] != value for column, value in expected[row[key]].items()):
                    raise ValueError(f'{name} {row[key]}: post-import value mismatch')
    return f'IMPORT SUCCESS {entity_id}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    add_validation_arguments(parser)
    parser.add_argument('--only', nargs='+', metavar='FOLDER', help='Import selected folders after validating all datasets')
    parser.add_argument('--dry-run', action='store_true', help='Validate without database writes')
    args = parser.parse_args()
    reports = validate_all(**validation_options(args))
    if args.only and set(args.only) - {r['folder'] for r in reports}:
        parser.error('Unknown organization folder')
    selected = [r for r in reports if not args.only or r['folder'] in args.only]
    print_reports(selected)
    if args.dry_run:
        return int(any(r['errors'] for r in selected))
    from database import engine

    failed = False
    print('\nSHADOWWATCH MULTI-ENTITY IMPORT')
    for report in selected:
        try:
            message = import_organization(engine, report)
            failed |= message.startswith('BLOCKED')
        except Exception as exc:
            # Avoid printing DB connection strings/SQL-bound operational data.
            message = f'ROLLED BACK - {type(exc).__name__}; inspect source constraints before retrying'
            failed = True
        print(report['folder'], message)
    print('IMPORT COMPLETE' if not failed else 'IMPORT INCOMPLETE - blocked/failed organizations were not imported')
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
