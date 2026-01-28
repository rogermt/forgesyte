from typing import Any, Dict

from pydantic import BaseModel, ConfigDict


class ToolSchema(BaseModel):
    """
    Canonical schema for plugin tools.

    Enforces:
    - description: str
    - input_schema: dict
    - output_schema: dict
    """

    model_config = ConfigDict(
        extra="forbid",  # no unknown fields allowed
        arbitrary_types_allowed=False,
        validate_assignment=True,
    )

    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    handler: Any = None  # handler is optional for schema validation
