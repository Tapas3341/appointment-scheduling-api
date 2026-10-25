from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user, require_role
from app.models.provider_profile import ProviderProfile
from app.models.service import Service
from app.models.user import User
from app.schemas.providers import (
    ProviderProfileResponse,
    ProviderProfileUpdate,
    ServiceCreate,
    ServiceResponse,
)

router = APIRouter(prefix="/providers", tags=["providers"])


@router.put("/me/profile", response_model=ProviderProfileResponse)
def update_provider_profile(
    profile_data: ProviderProfileUpdate,
    current_user: User = Depends(require_role("provider")),
    db: Session = Depends(get_db),
) -> ProviderProfileResponse:
    profile = db.get(ProviderProfile, current_user.id)
    if profile is None:
        profile = ProviderProfile(
            user_id=current_user.id,
            display_name=profile_data.display_name,
            timezone=profile_data.timezone,
        )
        db.add(profile)
    else:
        profile.display_name = profile_data.display_name
        profile.timezone = profile_data.timezone

    db.commit()
    db.refresh(profile)
    return profile


@router.post(
    "/me/services",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_provider_service(
    service_data: ServiceCreate,
    current_user: User = Depends(require_role("provider")),
    db: Session = Depends(get_db),
) -> ServiceResponse:
    profile = db.get(ProviderProfile, current_user.id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider profile not found.",
        )

    service = Service(
        provider_id=current_user.id,
        name=service_data.name,
        duration_minutes=service_data.duration_minutes,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.get(
    "/{id}/services",
    response_model=list[ServiceResponse],
    dependencies=[Depends(get_current_user)],
)
def list_provider_services(
    provider_id: UUID = Path(alias="id"),
    db: Session = Depends(get_db),
) -> list[ServiceResponse]:
    return list(
        db.scalars(
            select(Service)
            .where(Service.provider_id == provider_id, Service.is_active.is_(True))
            .order_by(Service.created_at, Service.id)
        )
    )
