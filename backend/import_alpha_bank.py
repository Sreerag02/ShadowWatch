from pathlib import Path

from services.data_ingestion import import_csv


DATA_DIR = Path("../data/alpha_bank")

files = [
    ("entities.csv", "entities"),
    ("assets.csv", "assets"),
    ("alerts.csv", "alerts"),
    ("cases.csv", "cases"),
    ("investigations.csv", "investigations"),
    ("escalations.csv", "escalations"),
    ("telemetry.csv", "telemetry"),
]


print("\n=== SHADOWWATCH DATA INGESTION ===\n")

total = 0

for filename, table in files:
    path = DATA_DIR / filename

    if not path.exists():
        print(f"ERROR: File not found -> {path}")
        break

    count = import_csv(path, table)
    total += count

print(f"\nTotal rows imported: {total}")
print("\n=== INGESTION COMPLETE ===")