"""Readable R008 report."""
import sys
from scripts.report_behaviour import main

if __name__ == "__main__":
    main(["--rule", "R008", *sys.argv[1:]])
