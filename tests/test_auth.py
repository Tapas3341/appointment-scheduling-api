from uuid import UUID

import pytest
from sqlalchemy import select

from app.models.user import User
from app.schemas.auth import UserRegistration
from app.security import decode_access_token, hash_password, password_hash


def test_registration_schema_trims_name_and_normalizes_email() -> None:
    registration = UserRegistration(
        full_name="  Ada Example  ",
        email=" ADA@EXAMPLE.COM ",
        password="correct-horse",
        role="customer",
    )

    assert registration.full_name == "Ada Example"
    assert str(registration.email) == "ada@example.com"


@pytest.mark.parametrize(
    ("full_name", "email", "password"),
    [
        ("Ada Example", "not-an-email", "long-enough-password"),
        ("Ada Example", "ada@example.com", "short"),
        ("   ", "ada@example.com", "long-enough-password"),
    ],
)
def test_registration_schema_rejects_invalid_values(
    full_name: str,
    email: str,
    password: str,
) -> None:
    with pytest.raises(ValueError):
        UserRegistration(
            full_name=full_name,
            email=email,
            password=password,
            role="customer",
        )


def test_password_hash_can_be_verified() -> None:
    password = "correct-horse"
    password_digest = hash_password(password)

    assert password_digest != password
    assert password_hash.verify(password, password_digest)
    assert not password_hash.verify("incorrect-password", password_digest)


@pytest.mark.parametrize("role", ["customer", "provider"])
def test_registration_creates_user_and_returns_safe_response(client, db_engine, role: str) -> None:
    email = f"{role}@example.com"
    password = "registration-password"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": email,
            "password": password,
            "role": role,
        },
    )

    assert response.status_code == 201
    response_body = response.json()
    assert set(response_body) == {"id", "full_name", "email", "role", "created_at"}
    assert UUID(response_body["id"])
    assert response_body["full_name"] == "Test User"
    assert response_body["email"] == email
    assert response_body["role"] == role
    assert password not in response.text
    assert "password_hash" not in response.text

    with db_engine.connect() as connection:
        user_id, stored_password_hash = connection.execute(
            select(User.id, User.password_hash).where(User.email == email)
        ).one()

    assert user_id == UUID(response_body["id"])
    assert stored_password_hash != password
    assert stored_password_hash.startswith("$argon2id$")
    assert password_hash.verify(password, stored_password_hash)


def test_duplicate_email_returns_conflict(client) -> None:
    payload = {
        "full_name": "Test User",
        "email": "duplicate@example.com",
        "password": "registration-password",
        "role": "customer",
    }

    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    duplicate_response = client.post("/api/v1/auth/register", json=payload)

    assert duplicate_response.status_code == 409
    payload["email"] = "after-duplicate@example.com"
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201


def test_registration_rejects_admin_role(client) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Admin User",
            "email": "admin@example.com",
            "password": "registration-password",
            "role": "admin",
        },
    )

    assert response.status_code == 422


def test_login_returns_bearer_token_without_password_fields(client) -> None:
    password = "login-password"
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Login User",
            "email": "login@example.com",
            "password": password,
            "role": "customer",
        },
    )
    assert registration.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        data={"username": " LOGIN@EXAMPLE.COM ", "password": password},
    )

    assert response.status_code == 200
    response_body = response.json()
    assert set(response_body) == {"access_token", "token_type"}
    assert response_body["token_type"] == "bearer"
    assert password not in response.text
    assert "password_hash" not in response.text
    assert decode_access_token(response_body["access_token"])["sub"] == registration.json()["id"]


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("login@example.com", "incorrect-password"),
        ("unknown@example.com", "login-password"),
    ],
)
def test_login_rejects_invalid_credentials_generically(
    client,
    username: str,
    password: str,
) -> None:
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Login User",
            "email": "login@example.com",
            "password": "login-password",
            "role": "customer",
        },
    )
    assert registration.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password."
    assert response.headers["www-authenticate"] == "Bearer"
