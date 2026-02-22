"""Pydantic models for plugin manifest validation (Phase 12).

Validates manifest.json files loaded from plugins, enforcing
allowed plugin types and tool schema structure.
"""

from typing import Any, List

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_PLUGIN_TYPES = {"yolo", "ocr", "custom"}


class ManifestTool(BaseModel):
    """Schema for a single tool entry in a plugin manifest."""

    model_config = ConfigDict(extra="allow")  # Preserve legacy fields like input_types

    id: str = Field(..., description="Unique tool identifier")
    title: str = Field("", description="Human-readable tool name")
    description: str = Field("", description="Tool description")
    inputs: Any = Field(default_factory=list)
    outputs: Any = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Tool id must be a non-empty string")
        return v


class PluginManifest(BaseModel):
    """Schema for plugin manifest.json validation."""

    name: str = Field(..., description="Plugin identifier")
    version: str = Field("1.0.0")
    description: str = Field("")
    type: str = Field(default="custom", description="Plugin type")
    tools: List[ManifestTool] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ALLOWED_PLUGIN_TYPES:
            raise ValueError(
                f"Invalid plugin type '{v}'. "
                f"Allowed types: {sorted(ALLOWED_PLUGIN_TYPES)}"
            )
        return v
