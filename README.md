# Appointment Scheduling API

An API-only appointment scheduling service built with Python and FastAPI. This project is both a backend engineering learning exercise and a portfolio project focused on reliable booking workflows, data integrity, authentication, and concurrency.

## Goal

Build a REST API that allows customers to book appointments with service providers while preventing overlapping bookings for the same provider.

The central design principle is that booking correctness must be enforced by the database, not just by checking availability in application code.

## Planned Stack

- **Language:** Python
- **API:** FastAPI, Pydantic
- **Database:** PostgreSQL
- **Persistence and migrations:** SQLAlchemy 2.0, Alembic, psycopg 3
- **Authentication:** Password hashing, JWT, role-based access control
- **Testing:** pytest
- **Infrastructure and delivery:** Docker Compose, GitHub Actions
- **Caching and background work:** Redis, RQ

Technologies will be added to the implemented stack only after they have actually been used.

## Current Status

**Day 2 authentication and provider/service setup complete; Day 3 booking work is next.** The project remains pre-M1 until the booking integrity criteria are verified.

The API connects to PostgreSQL, checks database connectivity through `GET /health`, supports customer/provider registration and JWT login, identifies the authenticated user, and supports provider profile and service management. Availability and appointment booking remain planned.

## Implemented

- Synchronous SQLAlchemy database engine and request-scoped sessions.
- UUID-backed user model and Alembic migration.
- `GET /health`, including a PostgreSQL connectivity check.
- `POST /api/v1/auth/register` with input validation, Argon2 password hashing, duplicate-email conflict handling, and a response that excludes password data.
- `POST /api/v1/auth/login`, bearer-token validation, `GET /api/v1/users/me`, and reusable role authorization.
- `PUT /api/v1/providers/me/profile` with IANA timezone validation and authenticated ownership.
- `POST /api/v1/providers/me/services` and authenticated `GET /api/v1/providers/{id}/services` listing active services only.
- PostgreSQL provider/service schema with migrations, positive service-duration constraint, and cascading ownership.
- 41 automated tests against a separate PostgreSQL test database.

## Planned

- Weekly availability rules and slot generation.
- Appointment booking with five-minute temporary holds.
- PostgreSQL constraints to prevent overlapping active appointments.
- Timezone-aware scheduling and booking lifecycle rules.
- Broader automated tests, containerized development, and continuous integration.
- Redis availability caching, background jobs, and idempotent booking requests.
- Deployment and technical documentation.

## Running Locally

Configure `DATABASE_URL` in `.env`, activate the project virtual environment, and apply migrations:

```powershell
python -m alembic upgrade head
python -m uvicorn app.main:app --reload
```

## API Documentation

When the application is running, open `http://127.0.0.1:8000/docs` for FastAPI's interactive API documentation.

## Tests

The automated tests use PostgreSQL. Create a separate test database named by appending `_test` to the database name in `DATABASE_URL` (for example, `appointments_test`) before running:

```powershell
python -m pytest -q
```

The test fixture applies migrations and clears rows only in that separate test database; do not point it at a database containing data you need.
