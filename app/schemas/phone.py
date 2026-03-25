from pydantic import BaseModel, field_validator

class PhoneCreate(BaseModel):
    mac_address: str

    @field_validator("mac_address")
    @classmethod
    def validator_mac(cls, v):
        cleaned = v.replace(":", "").replace("-", "").replace("", "").upper()

        if len(cleaned) != 12:
            raise ValueError("MAC address must be exactly 12 characters long")
        return cleaned
    

class PhoneResponse(BaseModel):
    mac_address: str
    section_id: str

    model_config = {"from_attributes": True}