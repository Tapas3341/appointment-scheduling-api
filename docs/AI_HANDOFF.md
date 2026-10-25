# AI Handoff — Appointment Scheduling API

**Last updated:** 25 October 2026
**Current project day:** Day 2 provider profile and service endpoints verified; Day 2 review remains
**Purpose:** Portable context for a fresh AI session so implementation continues from verified progress instead of repeating setup or assuming unfinished work exists.

## 1. What I am building

I am building an API-only Appointment Scheduling API in Python/FastAPI. This is a backend-learning and portfolio project intended to demonstrate relational data modeling, HTTP/API design, authentication/authorization, PostgreSQL constraints and transactions, concurrency testing, Docker/CI, caching, background work, idempotency, and deployment.

The central engineering story is that PostgreSQL itself prevents two overlapping appointments for the same provider. An application-level “check availability, then insert” is insufficient because concurrent requests can race.

The project is intentionally small. Do not add a frontend, real payments, real email/SMS, microservices, Kubernetes, Kafka, GraphQL, or unrelated features.

## 2. Read these documents first

1. `docs/PROJECT_STATUS.md` — live progress ledger, evidence, and next actions.
2. `docs/APPOINTMENT_SCHEDULING_API_PROJECT_PLAN (2).md` — canonical specification, endpoint contract, schema, rules, and day-by-day plan.
3. `project_resume_milestones.md` — gates for what may truthfully appear on the resume.
4. `APPOINTMENT_SCHEDULING_API_CONTEXT.md` — fuller motivation, learning goals, and interview framing. Keep this private; do not put it in the public repository.
5. `DECISIONS.md` — implementation decisions and trade-offs.

If details conflict, follow the canonical project plan and the latest explicit decision record. The actual repository/code and tests establish what has been implemented. `PROJECT_STATUS.md` should reflect that evidence.

## 3. Current verified state

As of 25 October 2026, **Day 2 is complete: registration, login/JWT, protected current-user lookup, role authorization, canonical provider/service models, and all three provider/service endpoints are implemented; the project remains pre-M1**.

Public repository: https://github.com/Tapas3341/appointment-scheduling-api

Local repository path:

`C:\Users\Tapasendra Patra\appointment-scheduling-api`

Known setup and evidence:

- Python version observed: `3.14.4`.
- Dependency approach: `venv` + `pip`, with pinned dependencies in `requirements.txt`.
- Synchronous SQLAlchemy setup in `app/db.py` provides the environment-based database URL, engine, session factory, and request-scoped dependency.
- `app/models/base.py` defines the declarative base; `app/models/user.py` defines the UUID-backed user with `full_name`, unique email, password hash, constrained role, and timezone-aware timestamps.
- `alembic/env.py` loads `.env`, imports all models, and exposes `Base.metadata` to Alembic.
- The initial migration `39f41bf309ea_create_users_table.py`, initial provider/service migration `4c1e7e3415cb`, and corrective canonical-schema migration `9d7b1a6c4e20` are applied locally; `alembic current` reports `9d7b1a6c4e20 (head)` and `alembic check` reports no new operations.
- `GET /health` executes `SELECT 1` through its request-scoped session and was verified over HTTP.
- `POST /api/v1/auth/register` implements customer/provider registration, input validation, email normalization, Argon2 hashing, and `409` handling for the email unique violation.
- `POST /api/v1/auth/login` issues bearer JWTs; `get_current_user` verifies tokens and loads the active user, `GET /api/v1/users/me` returns safe profile fields, and `require_role` provides role checks.
- `ProviderProfile.user_id` is the profile primary key and FK to `users.id`; its required fields include `display_name` and IANA timezone. `Service.provider_id` references that key; services include `name`, positive `duration_minutes`, and `is_active`. Cascading deletes and the duration check are enforced in PostgreSQL. See `DECISIONS.md` for implementation choices.
- `PUT /api/v1/providers/me/profile` is provider-only, validates IANA timezones, derives identity from the authenticated user, and creates or updates only that user's profile.
- `POST /api/v1/providers/me/services` is provider-only, requires an existing profile, validates service name and positive duration, and sets `provider_id` from the authenticated user's ID. `GET /api/v1/providers/{id}/services` requires authentication and returns only active services for that provider; unknown provider IDs return an empty list.
- Manual HTTP verification returned `201` for customer/provider, `409` for duplicate email, and `422` for invalid email, short password, and admin role. Responses omit passwords/hashes; PostgreSQL confirmed Argon2 hashes. Temporary test accounts were removed.
- Twenty focused provider tests and 41 total tests pass against the dedicated local `appointments_test` PostgreSQL database. The focused and full runs were performed sequentially because both use and truncate the same test database.
- `alembic check` reports no new operations; `git diff --check` passes.
- `/docs` returned HTTP 200; Python compilation, `pip check`, and Alembic schema checks succeeded.
- `.gitignore` exists and `.venv/` was confirmed ignored.
- Automated tests use FastAPI `TestClient` and a PostgreSQL database derived by appending `_test` to the configured development database name. The database must exist first; fixtures run Alembic migrations there and truncate only that test database. The test database is `appointments_test`. Never run these fixtures against a database with data you need.
- Day 1 implementation is committed and pushed: `ae81008` (`feat: add database-backed user registration`) and `08a3e76` (`docs: record Day 1 registration checkpoint`). README and handoff documentation were refreshed for Day 2 on 25 October 2026; check Git status and latest commit before continuing.
- A tracked-file search found no context-named file in the public repository. Keep any private personal context out of the public repo.
- Availability, slot generation, appointment booking/lifecycle, broader concurrency tests, CI, Docker, Redis, RQ, and deployment are not yet implemented.

## 4. Frozen design

- API prefix: `/api/v1`; the endpoint contract in the plan lists resource paths without the prefix.
- Roles: `customer`, `provider`, `admin`.
- Six tables: `users`, `provider_profiles`, `services`, `availability_rules`, `appointments`, `idempotency_keys`.
- Provider timezone belongs on `provider_profiles` and uses an IANA timezone name.
- Stack: Python, FastAPI, Pydantic, PostgreSQL, SQLAlchemy 2.0 synchronous ORM with psycopg3, Alembic, JWT, password hashing, pytest, Docker Compose, GitHub Actions, Redis, RQ.
- Appointment `time_range` is PostgreSQL `tstzrange`; use `btree_gist` and a partial exclusion constraint so the same provider cannot have overlapping `held` or `confirmed` appointments.
- Ranges are half-open `[start, end)`, so adjacent appointments are allowed.
- Hold duration: five minutes, configurable for tests.
- Customer cancellation: only more than two hours before start; providers/admins can cancel at any time.
- Booking horizon: 30 days.
- Appointment instants are timezone-aware and use UTC semantics.
- Convert weekly provider-local availability rules using the provider timezone. Reject cross-midnight rules; skip local slots whose times do not exist due to a DST gap, as specified in the plan.
- Expired holds must transition to `expired` to stop blocking the database constraint. Handle expiry lazily in the booking transaction and later with background work.
- Dedicated `idempotency_keys` table is a later milestone; unique by `(user_id, key)`, storing the request hash and response status/body.
- M1 target: end of Day 3; formal concurrency proof is M2, targeted for Day 7. Targets are not evidence of completion.

Do not revert to the older four-table model, timezone-on-`users`, booking-level idempotency, ten-minute holds, or Day-4 M1 unless the developer explicitly changes the specification and records the trade-off.

## 5. Endpoint scope

The canonical plan defines 15 endpoints:

1. `GET /health`
2. `POST /auth/register`
3. `POST /auth/login`
4. `GET /users/me`
5. `PUT /providers/me/profile`
6. `POST /providers/me/services`
7. `GET /providers/{id}/services`
8. `PUT /providers/me/availability`
9. `GET /providers/{id}/slots`
10. `POST /appointments`
11. `POST /appointments/{id}/confirm`
12. `POST /appointments/{id}/cancel`
13. `GET /appointments`
14. `GET /appointments/{id}`
15. `GET /admin/appointments`

Refer to the canonical project plan for access roles, response behavior, and the complete contract. Do not implement every endpoint on Day 1.

## 6. Execution schedule

- **Day 0 — Complete:** Repository, README, skeleton, health endpoint, dependency setup, initial commit, and public-repository cleanup.
- **Day 1 — Database/model/migration/registration slice verified:** PostgreSQL connection, SQLAlchemy session lifecycle, UUID user model, applied Alembic migration, database-backed health check, and manually verified registration.
- **Day 2 — Complete:** Authentication, canonical provider/service schema, profile and service endpoints, and 41 automated tests are verified.
- **Day 3 — Next:** Experiment with PostgreSQL ranges/exclusion constraints, add appointment schema and migration, implement basic holds, and verify overlap rejection plus adjacent-slot success.
- **Day 4:** Availability rules and slot generation.
- **Day 5:** Confirm/cancel/list/admin endpoints and ownership rules.
- **Day 6:** Integration and concurrency tests.
- **Day 7:** Docker Compose and GitHub Actions; M2 evidence review.
- **Day 8:** Redis availability cache, invalidation, fallback, benchmark.
- **Day 9:** RQ background jobs and idempotency.
- **Day 10:** Deployment/polish/interview defence, with a local demo fallback if deployment is blocked.

Continue from the recorded state. Do not restart planning or redesign the system just because a new chat has begun.

## 7. How to teach and collaborate

Act as a **backend engineering tutor and reviewer, not a code vending machine**.

- I want to learn backend engineering and defend the project in interviews. Finishing quickly by pasting generated code is not the only goal.
- Explain concepts and reasoning first. Prefer a hint, small example, or focused pseudocode before a complete implementation.
- Let me write the core logic. Review my code, identify the first conceptual/implementation error, and explain how to reason toward a fix.
- When I explicitly ask for a full implementation, it is acceptable to provide one, but explain the important decisions and failure modes.
- Prefer straightforward Python and clear control flow over unnecessary abstractions.
- Do not redesign a frozen decision without a concrete reason. If a change is justified, explain the trade-off and update the decision/status documents.
- Do not silently assume something has been implemented. Ask for the relevant code, test output, or repository state when needed.
- Never ask me to upload code or log files. Ask me to paste relevant snippets and output directly into chat inside Markdown code blocks.
- Keep the session scoped to the current day's deliverable. Batch trivial steps where sensible, but do not skip verification.
- At the end of a work session, provide a short technical recap, a Git commit suggestion, and the status-log entry.
- Applications/job search continue alongside project work. Do not make the project a reason to postpone applications.

## 8. Day 2 completion and Day 3 starting point

Day 2 acceptance criteria are met for login/token validation, current-user lookup, role authorization, provider profiles, and services. The full suite has 41 passing tests against `appointments_test`; the provider-specific suite has 20. The current migration head is `9d7b1a6c4e20`.

Start Day 3 from the canonical plan's “Day 3 — Core scheduling and Milestone 1” section. First experiment with PostgreSQL range overlap and adjacent half-open ranges; then add `appointments` with the partial exclusion constraint for active statuses and implement the basic five-minute hold. Keep `appointments_test` separate from development. Do not claim M1 until the overlap/adjacency behavior and cancellation/expiry evidence in the plan are verified.

The Day 2 ownership pattern to reuse is: validate the bearer token, load `current_user`, authorize by role, and derive owner IDs from that user rather than client-supplied identity.

## 9. Truthfulness and resume constraints

- Resume bullets are gated by `project_resume_milestones.md`.
- Do not fabricate request counts, test counts, latency, throughput, cache improvements, or deployment status.
- Benchmark Redis against the same dataset and comparable request conditions; record the methodology and actual results.
- The concurrency test must use real PostgreSQL. It should prove exactly one success for parallel attempts at the same slot and should fail if the exclusion constraint is removed. Shared setup must be committed so concurrent workers can see it.
- “CI green” means the actual GitHub Actions workflow passed on the current commit.
- “Deployed” means a reachable deployment with a known revision.
- If deployment is blocked after a reasonable effort, retain a local Docker Compose demo and state the limitation honestly.
- M0 completion does not authorize claims about database-backed registration, authentication, automated tests, CI, caching, background jobs, or deployment.

## 10. Session continuity rule

At the beginning of each new session:

1. Read `PROJECT_STATUS.md` and this handoff.
2. Confirm the current day and the most recent evidence.
3. Ask for only the smallest missing piece of evidence that materially affects the next step.
4. Start from the next incomplete task.
5. Update the status and handoff after the work session.

**Current next task: Begin Day 3 with PostgreSQL range/exclusion-constraint exploration and appointment schema design. M1 remains incomplete.**
