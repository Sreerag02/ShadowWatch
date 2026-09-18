"""Non-destructive import: validate first, skip existing entities, transact per organization."""

import argparse


from app.services.ingestion.dataset_validation import (
    TABLES, validate_all, print_reports, add_validation_arguments, validation_options,
)


from app.services.ingestion.importer import import_organization, import_validated_connection


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
    from app.core.database import engine

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
