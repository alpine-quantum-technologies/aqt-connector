from pydantic import BaseModel


class DeviceCodeData(BaseModel):
    """Data required to authenticate a device."""

    verification_uri_complete: str
    user_code: str
    device_code: str
    interval: float
