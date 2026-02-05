#!/usr/bin/env python3
"""API Contract Drift Scanner.

Detects schema drift in API responses by comparing real responses against
expected field contracts.

Usage:
    python scripts/scan_api_contracts.py
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


# Expected field contracts for each API response
EXPECTED_CONTRACTS = {
    "AnalyzeResponse": {
        "job_id": str,
        "device_requested": str,
        "device_used": str,
        "fallback": bool,
        "frames": list,
        "result": (type(None), dict),
    },
    "JobResponse": {
        "job_id": str,
        "status": str,
        "result": (type(None), dict),
        "error": (type(None), str),
        "created_at": str,  # ISO format
        "completed_at": (type(None), str),
        "plugin": str,
        "progress": (type(None), int, float),
    },
    "JobStatusResponse": {
        "job_id": str,
        "status": str,
        "device_requested": str,
        "device_used": str,
    },
    "JobResultResponse": {
        "job_id": str,
        "result": (type(None), dict),
        "error": (type(None), str),
    },
}


def check_field(
    field_name: str, field_value: Any, expected_type: Tuple[type, ...] | type
) -> Tuple[bool, str]:
    """Check if field matches expected type.

    Args:
        field_name: Name of field
        field_value: Actual field value
        expected_type: Expected type(s)

    Returns:
        (is_valid, error_message)
    """
    if not isinstance(expected_type, tuple):
        expected_type = (expected_type,)

    if not isinstance(field_value, expected_type):
        expected_names = ", ".join(t.__name__ for t in expected_type)
        actual_name = type(field_value).__name__
        return False, f"Type mismatch: {field_name} (expected {expected_names}, got {actual_name})"

    return True, ""


def scan_contract(response_name: str, data: Dict[str, Any]) -> List[str]:
    """Scan a response against its contract.

    Args:
        response_name: Name of the response type (e.g., "AnalyzeResponse")
        data: Actual response data

    Returns:
        List of error messages (empty if valid)
    """
    if response_name not in EXPECTED_CONTRACTS:
        return [f"Unknown response type: {response_name}"]

    contract = EXPECTED_CONTRACTS[response_name]
    errors = []

    # Check required fields are present
    for field_name, expected_type in contract.items():
        if field_name not in data:
            errors.append(f"Missing required field: {field_name}")
            continue

        # Check type matches
        is_valid, error_msg = check_field(field_name, data[field_name], expected_type)
        if not is_valid:
            errors.append(error_msg)

    # Check for unexpected fields (extra fields)
    for field_name in data:
        if field_name not in contract:
            # Extra fields are OK (forward compatibility)
            pass

    return errors


def scan_sample_files() -> int:
    """Scan sample contract files in tests/contracts/.

    Returns:
        0 if all valid, 1 if any drift detected
    """
    contract_dir = Path("server/tests/contracts")
    if not contract_dir.exists():
        print("ℹ️  No sample contracts found at server/tests/contracts/")
        return 0

    contract_files = list(contract_dir.glob("*.json"))
    if not contract_files:
        print("ℹ️  No JSON contract files found at server/tests/contracts/")
        return 0

    all_valid = True

    for contract_file in contract_files:
        try:
            data = json.loads(contract_file.read_text())
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {contract_file}: {e}")
            all_valid = False
            continue

        # Infer response type from filename
        # e.g., "analyze_response.json" → "AnalyzeResponse"
        type_name = "".join(
            word.capitalize() for word in contract_file.stem.split("_")
        )

        errors = scan_contract(type_name, data)

        if errors:
            print(f"❌ API Contract Drift in {contract_file.name}:")
            for error in errors:
                print(f"   - {error}")
            all_valid = False
        else:
            print(f"✓ {type_name} contract valid")

    return 0 if all_valid else 1


def check_models_py() -> int:
    """Verify models.py defines all expected response classes.

    Returns:
        0 if all models defined, 1 if any missing
    """
    models_file = Path("server/app/models.py")
    if not models_file.exists():
        print("❌ server/app/models.py not found")
        return 1

    content = models_file.read_text()
    all_defined = True

    for response_name in EXPECTED_CONTRACTS:
        if f"class {response_name}" not in content:
            print(f"❌ Missing model class: {response_name}")
            all_defined = False
        else:
            print(f"✓ {response_name} defined in models.py")

    return 0 if all_defined else 1


def main() -> int:
    """Run all contract scanners.

    Returns:
        Exit code (0 = all valid, 1 = drift detected)
    """
    print("🔍 API Contract Drift Scanner\n")

    print("Checking model definitions...")
    models_valid = check_models_py() == 0
    print()

    print("Scanning sample contract files...")
    samples_valid = scan_sample_files() == 0
    print()

    if models_valid and samples_valid:
        print("✅ API Contracts Stable\n")
        return 0
    else:
        print("❌ API Contract Drift Detected\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
