"""Import one validated organization folder; failures exit nonzero."""
import argparse
from database import SessionLocal
from services.data_ingestion import import_organization_folder

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder_path')
    args = parser.parse_args(argv)
    with SessionLocal() as db:
        try:
            summary = import_organization_folder(db, args.folder_path)
        except ValueError as exc:
            print(f'Import failed: {exc}')
            return 1
    for table, count in summary.items():
        print(f'{table}: {count} inserted')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
