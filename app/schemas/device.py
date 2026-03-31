from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime



class DeviceBase(BaseModel):
    identifier: str
    section_id: uuid.UUID

class DeviceCreate(DeviceBase):
    pass


class DevicePositionSchema(BaseModel):
    x_pos: float
    y_pos: float

    model_config = ConfigDict(from_attributes=True)


class DeviceResponse(DeviceBase):
    id: uuid.UUID
    created_at: datetime

    #adding the position of the device to the response model, it can be None if the position is not set for the device
    position: DevicePositionSchema | None = None

    model_config = ConfigDict(from_attributes=True)


class DeviceUpdate(BaseModel):
    identifier: str | None = None
    classification: str | None = None
    x_pos: float | None = None
    y_pos: float | None = None