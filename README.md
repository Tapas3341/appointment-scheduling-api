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

**Day 0 — Foundation in progress.**

The initial repository and application setup are being established. The API's booking, authentication, and persistence features are planned but are not yet implemented.

## Implemented

- Initial public GitHub repository.
- Local development setup and API foundation — in progress; verified capabilities will be recorded as they are completed.

## Planned

- User registration, login, and role-based access for customers, providers, and administrators.
- Provider profiles, services, and weekly availability rules.
- Appointment booking with five-minute temporary holds.
- PostgreSQL constraints to prevent overlapping active appointments.
- Timezone-aware scheduling and booking lifecycle rules.
- Automated tests, containerized development, and continuous integration.
- Redis availability caching, background jobs, and idempotent booking requests.
- Deployment and technical documentation.

## Project Structure

The initial structure will be documented as the application develops.

## Running Locally

Local setup instructions will be added after the development environment and health endpoint have been verified.

## API Documentation

Once the application is running, FastAPI will provide interactive API documentation through its Swagger UI and OpenAPI endpoints.
