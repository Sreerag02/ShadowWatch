"""Readable R007 report."""
import sys
from test_behaviour_analytics import main

if __name__ == "__main__":
    main(["--rule", "R007", *sys.argv[1:]])
