from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db.database import get_db
from app.models.models import Location, User
from app.schemas.schemas import LocationOut, LocationCreate, LocationUpdate
from app.core.security import get_current_user

router = APIRouter()


@router.get("/locations", response_model=list[LocationOut])
async def list_locations(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Location).order_by(Location.name))
    return result.scalars().all()


@router.post("/locations", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
async def create_location(
    payload: LocationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if payload.parent_id:
        parent = await db.get(Location, payload.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Emplacement parent introuvable")

    loc = Location(name=payload.name, parent_id=payload.parent_id, color=payload.color)
    db.add(loc)
    await db.commit()
    await db.refresh(loc)
    return loc


@router.patch("/locations/{loc_id}", response_model=LocationOut)
async def update_location(
    loc_id: UUID,
    payload: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    loc = await db.get(Location, loc_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Emplacement introuvable")

    if payload.name is not None:
        loc.name = payload.name
    if payload.color is not None:
        loc.color = payload.color
    if "parent_id" in payload.model_fields_set:
        # Prevent circular reference: can't set parent to self or a descendant
        if payload.parent_id == loc_id:
            raise HTTPException(status_code=400, detail="Un emplacement ne peut pas être son propre parent")
        loc.parent_id = payload.parent_id

    await db.commit()
    await db.refresh(loc)
    return loc


@router.delete("/locations/{loc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    loc_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    loc = await db.get(Location, loc_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Emplacement introuvable")
    await db.delete(loc)
    await db.commit()
