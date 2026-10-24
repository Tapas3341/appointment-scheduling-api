from fastapi import APIRouter, Depends, HTTPException, status
from psycopg.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.schemas.auth import UserRegistration, UserRegistrationResponse
from app.security import hash_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    registration: UserRegistration,
    db: Session = Depends(get_db),
) -> UserRegistrationResponse:
    user = User(
        full_name=registration.full_name,
        email=str(registration.email),
        password_hash=hash_password(registration.password),
        role=registration.role,
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if (
            isinstance(exc.orig, UniqueViolation)
            and exc.orig.diag.constraint_name == "ix_users_email"
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            ) from exc
        raise

    db.refresh(user)
    return user
