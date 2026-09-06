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