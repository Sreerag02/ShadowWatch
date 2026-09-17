'''
import pandas as pd
from sqlalchemy import text
from database import engine


TABLE_ORDER = [
    "entities",
    "assets",
    "alerts",
    "cases",
    "investigations",
    "escalations",
    "telemetry",
]


def import_csv(file_path, table_name):
    if table_name not in TABLE_ORDER:
        raise ValueError(f"Invalid table: {table_name}")

    df = pd.read_csv(file_path)

    if df.empty:
        print(f"SKIPPED: {table_name} is empty")
        return 0

    # Convert empty CSV values to SQL NULL
    df = df.where(pd.notnull(df), None)

    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
        method="multi"
    )

    print(f"IMPORTED: {table_name} -> {len(df)} rows")

    return len(df)
    '''

# edited by Deepa
import os
import pandas as pd
from sqlalchemy.orm import Session

TABLE_ORDER = [
    "entities",
    "assets",
    "alerts",
    "cases",
    "investigations",
    "escalations",
    "telemetry",
]

def import_organization_folder(db: Session, folder_path: str):
    """
    Imports an entire organization's CSV folder in a single transaction.
    Rolls back the entire transaction if any file fails validation.
    """
    if not os.path.exists(folder_path):
        raise ValueError(f"Directory not found: {folder_path}")

    summary = {}
    
    try:
        for table_name in TABLE_ORDER:
            file_path = os.path.join(folder_path, f"{table_name}.csv")
            
            if not os.path.exists(file_path):
                print(f"WARNING: Missing {file_path}")
                continue
                
            df = pd.read_csv(file_path)
            if df.empty:
                print(f"SKIPPED: {table_name} is empty")
                summary[table_name] = 0
                continue
                
            # Convert empty CSV values to SQL NULL
            df = df.where(pd.notnull(df), None)
            
            # Passing db.connection() instead of engine ensures this participates in the session's transaction
            df.to_sql(
                table_name,
                db.connection(),
                if_exists="append",
                index=False,
                method="multi"
            )
            
            summary[table_name] = len(df)
            print(f"IMPORTED: {table_name} -> {len(df)} rows")
            
        # Only commit if all files in the folder succeed
        db.commit() 
        return summary
        
    except Exception as e:
        db.rollback() # Transaction safety: prevents partial imports
        raise ValueError(f"Import failed for {folder_path}. Rolled back. Error: {str(e)}")