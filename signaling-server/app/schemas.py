from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DeviceCreate(BaseModel):
    display_name: str


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    display_name: str
    created_at: datetime


class DeviceTokenResponse(BaseModel):
    device_id: str
    device_token: str
    owner_id: str


class ContactCreate(BaseModel):
    user_id: str
    display_name: str
    button_index: int


class ContactUpdate(BaseModel):
    display_name: Optional[str] = None
    button_index: Optional[int] = None
    avatar_path: Optional[str] = None


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    device_id: str
    user_id: str
    display_name: str
    button_index: int
    avatar_path: Optional[str]
    created_at: datetime


class ContactListResponse(BaseModel):
    contacts: List[ContactResponse]


class DeviceStatusResponse(BaseModel):
    device_id: str
    online: bool
    last_seen_at: Optional[datetime]
