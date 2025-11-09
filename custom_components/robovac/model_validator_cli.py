#!/usr/bin/env python3
"""Standalone CLI tool for RoboVac model validation.

This tool can be used independently to validate RoboVac model compatibility
and get suggestions for unsupported models.

Usage:
    python -m custom_components.robovac.model_validator_cli T2278
    python -m custom_components.robovac.model_validator_cli --list
"""

import argparse
import sys

from custom_components.robovac.model_validator import (
    detect_series,
    get_supported_models,
    is_supported_model,
    suggest_similar_models,
)


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Validate RoboVac model compatibility",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Example:\n  python -m custom_components.robovac.model_validator_cli T2278",
    )
    parser.add_argument(
        "model", nargs="?", help="Model code to validate (e.g., T2278)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all supported models"
    )

    args = parser.parse_args()

    if args.list:
        print("Supported Models:")
        for model in get_supported_models():
            print(f"- {model}")
        return 0

    if not args.model:
        parser.print_usage(sys.stderr)
        sys.stderr.write("error: the following arguments are required: model\n")
        return 2

    model_code = args.model
    if is_supported_model(model_code):
        series = detect_series(model_code)
        print(f"✅ {model_code} is a supported model.")
        if series:
            print(f"   Series: {series}")
        return 0
    else:
        print(f"❌ {model_code} is not a supported model.")
        suggestions = suggest_similar_models(model_code)
        if suggestions:
            print("\nSuggestions:")
            for suggestion, reason in suggestions:
                print(f"- {suggestion} ({reason})")
        return 1


if __name__ == "__main__":
    sys.exit(main())
