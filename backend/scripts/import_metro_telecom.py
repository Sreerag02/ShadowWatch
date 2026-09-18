from app.core.config import DATA_DIR
"""Compatibility command using the validated organization importer."""
from pathlib import Path
from scripts.import_data import main

if __name__ == '__main__':
    raise SystemExit(main([str(DATA_DIR / 'metro_telecom')]))
