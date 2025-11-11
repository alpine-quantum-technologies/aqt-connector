"""AQT-connector models."""

from pydantic import BaseModel, ConfigDict


class BaseModelSerialisable(BaseModel):
    """BaseModel with serialization config."""

    model_config = ConfigDict(from_attributes=True)
