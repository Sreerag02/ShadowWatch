"""Validate all datasets without connecting to PostgreSQL."""
import argparse
from pathlib import Path
import sys

from app.services.ingestion.dataset_validation import validate_all, print_reports, add_validation_arguments, validation_options


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    add_validation_arguments(parser)
    args = parser.parse_args()
    raise SystemExit(0 if print_reports(validate_all(**validation_options(args))) else 1)
