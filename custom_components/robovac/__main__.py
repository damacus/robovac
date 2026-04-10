"""Entry point for running the model validator CLI as a module."""

import sys

from custom_components.robovac.model_validator_cli import main

if __name__ == "__main__":
    sys.exit(main())
