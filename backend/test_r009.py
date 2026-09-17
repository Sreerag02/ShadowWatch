"""Readable R009 report."""
import sys
from test_behaviour_analytics import main

if __name__ == "__main__":
    main(["--rule", "R009", *sys.argv[1:]])
