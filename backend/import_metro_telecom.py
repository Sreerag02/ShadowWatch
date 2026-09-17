"""Compatibility command using the validated organization importer."""
from pathlib import Path
from import_data import main

if __name__ == '__main__':
    raise SystemExit(main([str(Path(__file__).resolve().parents[1] / 'data/metro_telecom')]))
