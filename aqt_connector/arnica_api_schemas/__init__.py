"""Schemas for the ARNICA API."""

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with serialization config."""

    model_config = ConfigDict(from_attributes=True)
