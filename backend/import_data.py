# created by Deepa

import argparse
from database import SessionLocal
from services.data_ingestion import import_organization_folder

def main():
    parser = argparse.ArgumentParser(description="Import a ShadowWatch organization dataset.")
    parser.add_argument("folder_path", type=str, help="Path to the organization's CSV folder (e.g., ../data/beta_bank)")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        print(f"Starting import for: {args.folder_path}")
        summary = import_organization_folder(db, args.folder_path)
        
        print("\n=== Import Summary ===")
        for table, count in summary.items():
            print(f"{table.capitalize()}: {count} rows")
        print("======================\n")
            
    except Exception as e:
        print(f"\n[X] Import Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()