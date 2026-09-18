"""Readable R007 report."""
import sys
from scripts.report_behaviour import main

if __name__ == "__main__":
    main(["--rule", "R007", *sys.argv[1:]])
