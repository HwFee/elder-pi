from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.dependencies import get_current_user, security
from app.models import Device, User
from app.schemas import ContactCreate, ContactListResponse, ContactResponse, ContactUpdate
from app.services import contact_service, upload_service
from app.services.auth_service import decode_access_token

router = APIRouter()


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    device_id: str,
    payload: ContactCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        contact = await contact_service.create_contact(db, current_user.id, device_id, payload)
    except contact_service.ContactError as exc:
        message = str(exc)
        if message == "Device not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        if message == "Button index already used":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    return contact


@router.get("", response_model=ContactListResponse)
async def list_contacts(
    device_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    try:
        if "device_id" in payload:
            if payload["device_id"] != device_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
            contacts = await contact_service.list_contacts_for_device(db, device_id)
        elif "sub" in payload:
            device = await db.get(Device, device_id)
            if device is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
            if device.owner_id != payload["sub"]:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
            contacts = await contact_service.list_contacts_for_device(db, device_id)
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except contact_service.ContactError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return ContactListResponse(contacts=contacts)


api_router = APIRouter()


@api_router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        contact = await contact_service.update_contact(db, current_user.id, contact_id, payload)
    except contact_service.ContactError as exc:
        message = str(exc)
        if message == "Contact not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=message)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@api_router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await contact_service.delete_contact(db, current_user.id, contact_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")


@api_router.post("/{contact_id}/avatar", response_model=ContactResponse)
async def upload_avatar(
    contact_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contact = await contact_service.get_contact(db, current_user.id, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    try:
        avatar_path = await upload_service.save_avatar(file, get_settings().upload_dir)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    contact = await contact_service.update_contact(
        db, current_user.id, contact_id, ContactUpdate(avatar_path=avatar_path)
    )
    return contact
