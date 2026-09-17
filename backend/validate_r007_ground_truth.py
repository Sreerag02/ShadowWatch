"""Compatibility entry point for truthful R007 evaluation."""
import sys
from validate_behaviour_ground_truth import main

if __name__ == "__main__":
    main(["--rule", "R007", *sys.argv[1:]])
