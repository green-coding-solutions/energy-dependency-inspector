#!/usr/bin/env python3
"""
Validate JSON files against the Syft schema.

Usage:
    python3 validate_syft_json.py <json_file> [schema_file]

Examples:
    python3 validate_syft_json.py output.json
    python3 validate_syft_json.py output.json custom_schema.json
"""

import json
import sys
import argparse
from pathlib import Path


def validate_json_against_schema(json_file: str, schema_file: str = None) -> bool:
    """
    Validate a JSON file against the Syft schema.

    Args:
        json_file: Path to the JSON file to validate
        schema_file: Path to the schema file (optional, uses default Syft schema)

    Returns:
        True if valid, False otherwise
    """
    try:
        import jsonschema
    except ImportError:
        print("Error: jsonschema package not found. Install with: pip install jsonschema")
        return False

    # Default schema path
    if schema_file is None:
        schema_file = "schema-16.0.39.json"

    # Check if files exist
    json_path = Path(json_file)
    schema_path = Path(schema_file)

    if not json_path.exists():
        print(f"Error: JSON file not found: {json_file}")
        return False

    if not schema_path.exists():
        print(f"Error: Schema file not found: {schema_file}")
        return False

    try:
        # Load the schema
        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Load the JSON file
        with open(json_path, "r") as f:
            data = json.load(f)

        # Validate
        jsonschema.validate(data, schema)
        print(f"✓ {json_file} is valid according to the Syft schema")
        return True

    except json.JSONDecodeError as e:
        print(f"✗ JSON parse error in {json_file}: {e}")
        return False

    except jsonschema.ValidationError as e:
        print(f"✗ Validation error in {json_file}:")
        print(f"  Message: {e.message}")
        if e.path:
            print(f"  Path: {' -> '.join(map(str, e.path))}")
        if e.schema_path:
            print(f"  Schema path: {' -> '.join(map(str, e.schema_path))}")
        return False

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Validate JSON files against the Syft schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 validate_syft_json.py output.json
  python3 validate_syft_json.py output.json custom_schema.json
  python3 validate_syft_json.py minimal_syft_sample.json
        """,
    )

    parser.add_argument("json_file", help="Path to the JSON file to validate")

    parser.add_argument(
        "schema_file", nargs="?", help="Path to the schema file (optional, defaults to bundled Syft schema)"
    )

    args = parser.parse_args()

    success = validate_json_against_schema(args.json_file, args.schema_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
