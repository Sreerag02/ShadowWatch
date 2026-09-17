"""Validated organization import; never inserts ground-truth records."""
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError
from services.dataset_validation import TABLES, validate_folder
from import_all_entities import import_validated_connection

TABLE_ORDER = list(TABLES)

def import_organization_folder(db, folder_path):
    """Own this session's transaction; validate all files before the first insert."""
    folder = Path(folder_path).resolve()
    if not folder.is_dir():
        raise ValueError(f'Directory not found: {folder}')
    report = validate_folder(folder)
    if report['errors']:
        raise ValueError('Dataset validation failed:\n' + '\n'.join(report['errors']))
    try:
        status = import_validated_connection(db.connection(), report)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise ValueError('Import rolled back: database constraint/connection failure. '
                         'Check duplicate IDs and schema compatibility.') from exc
    except Exception:
        db.rollback()
        raise
    print(status)
    skipped = status.startswith('SKIPPED')
    return {table: 0 if skipped else len(report['tables'][table]) for table in TABLES}
