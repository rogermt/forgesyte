# Phase 12 — Validation Subsystem Code Bundle

Below are all coding files for the Phase 12 validation subsystem.

---

## server/app/phase12/validation.py

```python
from typing import Any, Dict


class InputValidationError(Exception):
    """
    Raised when incoming request payload is invalid.
    """
    pass


class OutputValidationError(Exception):
    """
    Raised when plugin output is invalid or malformed.
    """
    pass


def validate_input_payload(payload: Dict[str, Any]) -> None:
    """
    Phase 12: input MUST be validated before execution.
    """
    image = payload.get("image")
    if not image:
        raise InputValidationError("Empty image payload")

    mime = payload.get("mime_type")
    if not mime or not isinstance(mime, str):
        raise InputValidationError("Missing or invalid mime_type")


def validate_plugin_output(raw_output: Any) -> Dict[str, Any]:
    """
    Phase 12: plugin output MUST be a dict-like structure.
    """
    if raw_output is None:
        raise OutputValidationError("Plugin returned None")

    if not isinstance(raw_output, dict):
        raise OutputValidationError("Plugin output must be a dict")

    return raw_output
```

---

## server/tests/phase_12/test_input_validation.py

```python
import pytest
from app.phase12.validation import (
    validate_input_payload,
    InputValidationError,
)


def test_input_validation_rejects_empty_image():
    with pytest.raises(InputValidationError):
        validate_input_payload({"image": b"", "mime_type": "image/png"})


def test_input_validation_rejects_missing_mime():
    with pytest.raises(InputValidationError):
        validate_input_payload({"image": b"123"})


def test_input_validation_accepts_valid_payload():
    validate_input_payload({"image": b"123", "mime_type": "image/png"})
```

---

## server/tests/phase_12/test_output_validation.py

```python
import pytest
from app.phase12.validation import (
    validate_plugin_output,
    OutputValidationError,
)


def test_output_validation_rejects_none():
    with pytest.raises(OutputValidationError):
        validate_plugin_output(None)


def test_output_validation_rejects_non_dict():
    with pytest.raises(OutputValidationError):
        validate_plugin_output("not a dict")


def test_output_validation_accepts_valid_dict():
    assert validate_plugin_output({"ok": True}) == {"ok": True}
```

---

# End of Validation subsystem bundle
