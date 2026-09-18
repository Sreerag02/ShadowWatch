"""Compatibility entry point for truthful R008 evaluation."""
import sys
from scripts.validate_behaviour_ground_truth import main

if __name__ == "__main__":
    main(["--rule", "R008", *sys.argv[1:]])
