from pathlib import Path
from services.data_ingestion import import_csv


# ============================================================
# METRO TELECOM DATA IMPORTER
# ============================================================

DATA_DIR = Path("../data/metro_telecom")

FILES = [
    ("entities.csv", "entities"),
    ("assets.csv", "assets"),
    ("alerts.csv", "alerts"),
    ("cases.csv", "cases"),
    ("investigations.csv", "investigations"),
    ("escalations.csv", "escalations"),
    ("telemetry.csv", "telemetry"),
]


print("\n" + "=" * 60)
print("        METRO TELECOM DATA INGESTION")
print("=" * 60)

total = 0

for filename, table in FILES:

    path = DATA_DIR / filename

    if not path.exists():
        print(f"\nERROR: File not found -> {path}")
        continue

    try:
        count = import_csv(path, table)
        total += count

    except Exception as e:
        print(f"\nERROR importing {filename}")
        print(f"Reason: {e}")


print("\n" + "=" * 60)
print(f"TOTAL METRO TELECOM ROWS IMPORTED: {total}")
print("=" * 60)
print("\nMetro Telecom ingestion complete.")