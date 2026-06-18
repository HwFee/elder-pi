from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.dependencies import get_current_user
from app.models import User
from app.routers.contacts import router as contacts_router
from app.schemas import DeviceCreate, DeviceResponse, DeviceTokenResponse, DeviceStatusResponse
from app.services import device_service
from app.socket.manager import manager

router = APIRouter()


@router.post("", response_model=DeviceTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    payload: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    device, token = await device_service.create_device(db, current_user, payload.display_name)
    return DeviceTokenResponse(device_id=device.id, device_token=token)


@router.get("", response_model=list[DeviceResponse])
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await device_service.list_devices(db, current_user.id)


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    device = await device_service.get_owned_device(db, current_user.id, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


@router.get("/{device_id}/status", response_model=DeviceStatusResponse)
async def get_device_status(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    device = await device_service.get_owned_device(db, current_user.id, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    manager.sweep_stale()
    return DeviceStatusResponse(
        device_id=device_id,
        online=manager.is_online(device_id),
        last_seen_at=manager.get_last_seen(device_id),
    )


router.include_router(contacts_router, prefix="/{device_id}/contacts")
