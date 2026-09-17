"""Readable R008 report."""
import sys
from test_behaviour_analytics import main

if __name__ == "__main__":
    main(["--rule", "R008", *sys.argv[1:]])
