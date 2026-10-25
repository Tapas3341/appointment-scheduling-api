from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException

from app.dependencies import require_role
from app.models.user import User
from app.security import ALGORITHM, JWT_SECRET_KEY


def create_test_token(subject: str, *, expires_at: datetime | None = None) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": subject,
            "exp": expires_at or now + timedelta(minutes=5),
            "iat": now,
        },
        JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )


def register_user(client) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Current User",
            "email": "current-user@example.com",
            "password": "current-user-password",
            "role": "customer",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_current_user_returns_authenticated_user_without_password_hash(client) -> None:
    registered_user = register_user(client)
    token = create_test_token(registered_user["id"])

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    response_body = response.json()
    assert set(response_body) == {"id", "full_name", "email", "role", "created_at"}
    assert response_body["id"] == registered_user["id"]
    assert response_body["full_name"] == registered_user["full_name"]
    assert response_body["email"] == registered_user["email"]
    assert response_body["role"] == registered_user["role"]
    assert "password_hash" not in response.text


def test_current_user_requires_token(client) -> None:
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("token", ["not.a.jwt", create_test_token("not-a-uuid")])
def test_current_user_rejects_malformed_or_invalid_token(client, token: str) -> None:
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_current_user_rejects_token_with_invalid_signature(client) -> None:
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            "iat": datetime.now(timezone.utc),
        },
        "x" * 32,
        algorithm=ALGORITHM,
    )

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_current_user_rejects_expired_token(client) -> None:
    token = create_test_token(
        str(uuid4()),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_current_user_rejects_token_for_deleted_user(client) -> None:
    token = create_test_token(str(uuid4()))

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_role_dependency_allows_matching_role() -> None:
    user = User(
        full_name="Provider User",
        email="provider@example.com",
        password_hash="not-used",
        role="provider",
    )

    assert require_role("provider")(user) is user


def test_role_dependency_rejects_nonmatching_role() -> None:
    user = User(
        full_name="Customer User",
        email="customer@example.com",
        password_hash="not-used",
        role="customer",
    )

    with pytest.raises(HTTPException) as exc_info:
        require_role("provider")(user)

    assert exc_info.value.status_code == 403
