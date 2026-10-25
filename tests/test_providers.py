from uuid import uuid4

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.provider_profile import ProviderProfile
from app.models.service import Service
from app.models.user import User

PASSWORD = "provider-password"
PROFILE_PATH = "/api/v1/providers/me/profile"


def create_account(client, *, email: str, role: str) -> tuple[dict, str]:
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"User {role}",
            "email": email,
            "password": PASSWORD,
            "role": role,
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": PASSWORD},
    )
    assert login.status_code == 200
    return registration.json(), login.json()["access_token"]


def profile_payload(
    display_name: str = "Example Provider",
    timezone: str = "Asia/Kolkata",
) -> dict[str, str]:
    return {"display_name": display_name, "timezone": timezone}


def service_payload(
    name: str = "Consultation",
    duration_minutes: int = 30,
) -> dict[str, str | int]:
    return {"name": name, "duration_minutes": duration_minutes}


def create_provider_profile(client, token: str) -> None:
    response = client.put(
        PROFILE_PATH,
        json=profile_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_provider_can_create_and_update_own_profile(client, db_engine) -> None:
    registered_user, token = create_account(
        client,
        email="provider@example.com",
        role="provider",
    )
    headers = {"Authorization": f"Bearer {token}"}

    created = client.put(PROFILE_PATH, json=profile_payload(), headers=headers)

    assert created.status_code == 200
    created_body = created.json()
    assert set(created_body) == {
        "user_id",
        "display_name",
        "timezone",
        "created_at",
        "updated_at",
    }
    assert created_body["user_id"] == registered_user["id"]
    assert created_body["display_name"] == "Example Provider"
    assert created_body["timezone"] == "Asia/Kolkata"
    assert "password_hash" not in created.text

    updated = client.put(
        PROFILE_PATH,
        json=profile_payload("Updated Provider", "Europe/London"),
        headers=headers,
    )

    assert updated.status_code == 200
    assert updated.json()["display_name"] == "Updated Provider"
    assert updated.json()["timezone"] == "Europe/London"

    with Session(db_engine) as db:
        profile_count = db.scalar(
            select(func.count()).select_from(ProviderProfile).where(
                ProviderProfile.user_id == registered_user["id"]
            )
        )
    assert profile_count == 1


def test_customer_cannot_create_provider_profile(client) -> None:
    _, token = create_account(
        client,
        email="customer@example.com",
        role="customer",
    )

    response = client.put(
        PROFILE_PATH,
        json=profile_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_admin_cannot_create_provider_profile(client, db_engine) -> None:
    registered_user, token = create_account(
        client,
        email="admin@example.com",
        role="customer",
    )
    with db_engine.begin() as connection:
        connection.execute(
            update(User)
            .where(User.id == registered_user["id"])
            .values(role="admin")
        )

    response = client.put(
        PROFILE_PATH,
        json=profile_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_provider_profile_rejects_invalid_timezone(client) -> None:
    _, token = create_account(
        client,
        email="timezone@example.com",
        role="provider",
    )

    response = client.put(
        PROFILE_PATH,
        json=profile_payload(timezone="banana/timezone"),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_provider_profile_rejects_blank_display_name(client) -> None:
    _, token = create_account(
        client,
        email="blank-name@example.com",
        role="provider",
    )

    response = client.put(
        PROFILE_PATH,
        json=profile_payload(display_name="   "),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_provider_can_only_modify_own_profile(client, db_engine) -> None:
    provider_a, token_a = create_account(
        client,
        email="provider-a@example.com",
        role="provider",
    )
    provider_b, token_b = create_account(
        client,
        email="provider-b@example.com",
        role="provider",
    )
    response_b = client.put(
        PROFILE_PATH,
        json=profile_payload("Provider B", "Europe/London"),
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response_b.status_code == 200

    response_a = client.put(
        PROFILE_PATH,
        json=profile_payload("Provider A", "Asia/Tokyo"),
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert response_a.status_code == 200
    assert response_a.json()["user_id"] == provider_a["id"]
    with Session(db_engine) as db:
        profile_b = db.get(ProviderProfile, provider_b["id"])
        assert profile_b is not None
        assert profile_b.display_name == "Provider B"
        assert profile_b.timezone == "Europe/London"


def test_provider_can_create_service(client) -> None:
    registered_user, token = create_account(
        client,
        email="service-provider@example.com",
        role="provider",
    )
    create_provider_profile(client, token)

    response = client.post(
        "/api/v1/providers/me/services",
        json=service_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["provider_id"] == registered_user["id"]
    assert response.json()["name"] == "Consultation"
    assert response.json()["duration_minutes"] == 30
    assert response.json()["is_active"] is True
    assert set(response.json()) == {
        "id",
        "provider_id",
        "name",
        "duration_minutes",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert "password_hash" not in response.text


def test_provider_cannot_create_service_without_profile(client) -> None:
    _, token = create_account(
        client,
        email="no-profile@example.com",
        role="provider",
    )

    response = client.post(
        "/api/v1/providers/me/services",
        json=service_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Provider profile not found."


@pytest.mark.parametrize("role", ["customer", "admin"])
def test_non_provider_cannot_create_service(client, db_engine, role: str) -> None:
    registered_user, token = create_account(
        client,
        email=f"{role}-service@example.com",
        role="customer",
    )
    if role == "admin":
        with db_engine.begin() as connection:
            connection.execute(
                update(User)
                .where(User.id == registered_user["id"])
                .values(role="admin")
            )

    response = client.post(
        "/api/v1/providers/me/services",
        json=service_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "payload",
    [
        service_payload(duration_minutes=0),
        service_payload(duration_minutes=-1),
        service_payload(name="   "),
        service_payload(name="x" * 256),
    ],
    ids=["zero-duration", "negative-duration", "blank-name", "long-name"],
)
def test_service_creation_rejects_invalid_data(client, payload) -> None:
    _, token = create_account(
        client,
        email="invalid-service@example.com",
        role="provider",
    )
    create_provider_profile(client, token)

    response = client.post(
        "/api/v1/providers/me/services",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


@pytest.mark.parametrize("role", ["customer", "provider", "admin"])
def test_authenticated_roles_can_list_provider_services(client, db_engine, role: str) -> None:
    provider, provider_token = create_account(
        client,
        email="catalog-provider@example.com",
        role="provider",
    )
    create_provider_profile(client, provider_token)
    created = client.post(
        "/api/v1/providers/me/services",
        json=service_payload(),
        headers={"Authorization": f"Bearer {provider_token}"},
    )
    assert created.status_code == 201

    requester, token = create_account(
        client,
        email=f"{role}-catalog@example.com",
        role="customer" if role == "admin" else role,
    )
    if role == "admin":
        with db_engine.begin() as connection:
            connection.execute(
                update(User).where(User.id == requester["id"]).values(role="admin")
            )

    response = client.get(
        f"/api/v1/providers/{provider['id']}/services",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [created.json()["id"]]


def test_service_listing_requires_authentication(client) -> None:
    response = client.get(f"/api/v1/providers/{uuid4()}/services")

    assert response.status_code == 401


def test_service_listing_is_scoped_to_provider_and_active_services(
    client,
    db_engine,
) -> None:
    provider_a, token_a = create_account(
        client,
        email="catalog-a@example.com",
        role="provider",
    )
    _, token_b = create_account(
        client,
        email="catalog-b@example.com",
        role="provider",
    )
    create_provider_profile(client, token_a)
    create_provider_profile(client, token_b)
    service_a = client.post(
        "/api/v1/providers/me/services",
        json=service_payload("Provider A service"),
        headers={"Authorization": f"Bearer {token_a}"},
    )
    service_b = client.post(
        "/api/v1/providers/me/services",
        json=service_payload("Provider B service"),
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert service_a.status_code == service_b.status_code == 201

    response = client.get(
        f"/api/v1/providers/{provider_a['id']}/services",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert [item["id"] for item in response.json()] == [service_a.json()["id"]]
    assert service_b.json()["id"] not in {
        item["id"] for item in response.json()
    }

    with db_engine.begin() as connection:
        connection.execute(
            update(Service)
            .where(Service.id == service_a.json()["id"])
            .values(is_active=False)
        )
    active_services = client.get(
        f"/api/v1/providers/{provider_a['id']}/services",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert active_services.status_code == 200
    assert active_services.json() == []


def test_nonexistent_provider_service_listing_returns_empty_list(client) -> None:
    _, token = create_account(
        client,
        email="catalog-requester@example.com",
        role="customer",
    )

    response = client.get(
        f"/api/v1/providers/{uuid4()}/services",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []
