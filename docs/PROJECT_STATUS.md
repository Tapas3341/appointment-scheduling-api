# Appointment Scheduling API — Project Status

**Last updated:** 24 October 2026
**Current state:** Day 1 database/model/migration/registration slice verified / pre-M1
**Canonical specification:** `APPOINTMENT_SCHEDULING_API_PROJECT_PLAN.md`  
**Continuity context:** `APPOINTMENT_SCHEDULING_API_CONTEXT.md`  
**Resume gates:** `project_resume_milestones.md`

> This is the live execution ledger. Record evidence, not intentions. A planned feature is not a completed feature, and a manually verified endpoint is not an automated test.

## 1. Current snapshot

- [x] Public GitHub repository created.
- [x] README created to introduce the project and distinguish current implementation from planned scope.
- [x] Local Python environment and dependency approach selected.
- [x] Minimal FastAPI application created and starts locally.
- [x] `GET /health` verifies PostgreSQL through a request-scoped SQLAlchemy session.
- [x] PostgreSQL configured; SQLAlchemy engine and request-scoped session dependency implemented.
- [x] UUID-backed `User` model and initial Alembic migration applied to the local database.
- [x] Alembic reports no schema drift after applying the initial migration.
- [x] Customer/provider registration implemented with input validation and Argon2 password hashing.
- [x] Registration manually verified over HTTP for success, duplicate email, invalid email, short password, and rejected admin role.
- [x] Registration responses omit both password and password hash; PostgreSQL verification confirmed Argon2 hashes.
- [x] First commit created and pushed.
- [x] `.gitignore` added; `.venv/` confirmed ignored.
- [x] Personal context document removed from the public repository and the cleanup pushed, as reported by the developer.
- [x] At least one concrete job-search action completed alongside project work.
- [x] Latest commit and clean/synced Git state verified from terminal output on 22 October 2026.
- [ ] Confirm the private personal-context document is absent from tracked public-repository files (for example, with `git ls-files`).
- [ ] No project milestone has been claimed on the resume.

**Repository URL:** https://github.com/Tapas3341/appointment-scheduling-api  
**Local repository:** `C:\Users\Tapasendra Patra\appointment-scheduling-api`  
**Primary branch:** `main`  
**Known initial commit:** `d7c0ab3 chore: initialize appointment scheduling API`  
**Latest observed commit:** `04b2051 Update status and handoff docs at end of Day 0` (reported by the developer on 22 October 2026).
**Git state:** Day 1 implementation is not yet committed; the clean/synced state noted above was reported at the end of Day 0.
**Dependency approach:** Python virtual environment (`venv`), `pip`, pinned `requirements.txt`.  
**Python version observed:** `3.14.4`.  
**Last manually verified behavior:** PostgreSQL-backed `GET /health` returned `{"status": "ok"}`; registration returned the expected `201`, `409`, and `422` responses; `/docs` returned HTTP 200. Temporary registration test rows were removed.
**Automated test suite:** 9 registration/schema/security/API tests pass against the dedicated local `appointments_test` PostgreSQL database.
**Last known CI result:** Not configured / no result recorded.  
**Deployment URL:** Not applicable yet.

### Day 0 implementation evidence

The minimal application currently includes a FastAPI instance with project metadata and a `GET /health` route returning `{"status": "ok"}`.

The initial project structure included:

- `.gitignore`
- `README.md`
- `requirements.txt`
- `app/__init__.py`
- `app/main.py`
- `docs/`

At the end of Day 0, the dependency file contained pinned versions for the initial FastAPI application. Day 1 database dependencies and implementation are recorded below.

The `/docs` route is FastAPI-generated Swagger UI. It is not a custom frontend.

The personal-context cleanup was reported during Day 0; verify its tracked-file status before any future repository-wide publication check.

## 2. Canonical decisions — do not silently drift

- API-only FastAPI service; no frontend and no microservices.
- Python, FastAPI, Pydantic, PostgreSQL, SQLAlchemy 2.0 synchronous ORM with psycopg3, and Alembic.
- JWT authentication and password hashing; roles are `customer`, `provider`, and `admin`.
- Six canonical tables: `users`, `provider_profiles`, `services`, `availability_rules`, `appointments`, and `idempotency_keys`.
- Provider IANA timezone belongs on `provider_profiles`.
- Appointment times use timezone-aware instants with UTC semantics.
- PostgreSQL `tstzrange` and a partial exclusion constraint prevent overlapping `held`/`confirmed` appointments for the same provider. Use half-open ranges `[start, end)` and `btree_gist`.
- Hold duration is five minutes and configurable for tests.
- Customers may cancel only more than two hours before the appointment starts; providers/admins can cancel at any time.
- Booking horizon is 30 days.
- Expired holds must transition to `expired` before they stop blocking the database constraint. Handle expiry lazily during booking and later with background work.
- Redis availability caching starts on Day 8.
- RQ/background jobs and the dedicated idempotency table start on Day 9.
- Docker Compose and GitHub Actions are targeted for Day 7.
- M1 is targeted for the end of Day 3 and is awarded only when its evidence checklist is met.
- No real payments, email/SMS integration, frontend, Kubernetes, Kafka, GraphQL, or microservices.

If a consequential design change becomes necessary, record the reason and trade-offs in `DECISIONS.md`, then update the canonical plan and this file where appropriate.

## 3. Milestone tracker

| Milestone                                    | Target       | Status       | Evidence required                                                                                                                                        |
| -------------------------------------------- | ------------ | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| M0 / foundation                              | Day 0        | **Complete** | Public repo, honest README, minimal FastAPI app, manually verified `/health`, first commit, dependency setup, `.gitignore` and public-repository cleanup |
| M1 / core booking                            | End of Day 3 | Not started  | Registration/login, provider/service setup, basic hold booking, database exclusion constraint, overlapping booking rejected and adjacent slots allowed   |
| M2 / tests + containers + CI                 | Day 7        | Not started  | Real-PostgreSQL concurrency test, Docker Compose from clean checkout, passing pytest suite, green GitHub Actions                                         |
| M3 / cache + jobs + idempotency + deployment | Day 10       | Not started  | Reproducible benchmark, cache invalidation/fallback, repeat-safe background jobs, idempotency tests, full test/CI evidence, working deployment           |

M0 completion does not imply that M1 or any later milestone is complete.

## 4. Work queue

### Completed: Day 0

- [x] Create/verify the public repository.
- [x] Add the initial README and project skeleton.
- [x] Create the minimal FastAPI application.
- [x] Add and manually verify `GET /health`.
- [x] Select `venv` + `pip` and pinned dependencies.
- [x] Add `.gitignore` and confirm `.venv/` is ignored.
- [x] Create and push the initial commit.
- [x] Remove the personal context document from the public repository and push the cleanup, as reported.
- [x] Complete at least one job-search action alongside project work.

### Day 1 implementation checklist

1. [x] Review Python version and pinned dependencies; install and verify the database/authentication dependencies.
2. [x] Set up PostgreSQL for local development and verify the connection.
3. [x] Add synchronous SQLAlchemy engine, session factory, and request-scoped session dependency.
4. [x] Define the UUID-backed user model and configure Alembic metadata.
5. [x] Generate and apply the initial migration; verify the PostgreSQL schema.
6. [x] Implement and manually verify registration validation, persistence, hashing, and response safety.
7. [x] Verify `alembic check`, Python compilation, and the database-backed health endpoint.
8. [x] Add automated tests against a separate PostgreSQL test database; all 9 pass.
9. [ ] Review and commit the Day 1 work.

### Day 1 — 24 October 2026

**Completed:** Configured synchronous SQLAlchemy and a request-scoped session dependency; added a UUID-based `User` model with required `full_name`; configured Alembic to load `DATABASE_URL` and model metadata; replaced the local, unapplied integer-ID migration and applied the corrected initial migration; made `/health` query PostgreSQL; implemented customer/provider registration with normalized email, validation, Argon2 hashing, and duplicate-email conflict handling.

**Evidence:** `alembic current` reports `39f41bf309ea (head)`; `alembic check` reports no new upgrade operations; PostgreSQL `\d users` confirmed the UUID ID, required fields, unique email index, role check constraint, and timezone-aware timestamps. Manual HTTP checks returned `201` for customer/provider registration, `409` for duplicate email, and `422` for invalid email, short password, and admin role. Responses contained no password/hash; PostgreSQL confirmed Argon2 hashes and temporary manual-check users were removed. `/health` returned `{"status": "ok"}`; `/docs` returned HTTP 200. Nine automated tests pass against the separate `appointments_test` database, covering schema validation/normalization, password hashing, customer/provider registration, safe responses, persistence, duplicate rollback, and admin rejection. `python -m compileall -q app`, `pip check`, and Alembic schema checks passed. `.env` is ignored and not tracked.

**Learned / can now explain:** SQLAlchemy models register table descriptions in metadata; Alembic compares metadata with PostgreSQL and applies versioned migrations; FastAPI yield dependencies scope database sessions to requests; Pydantic validates public input/output; Argon2 stores one-way password hashes; PostgreSQL uniqueness is the final protection against concurrent duplicate registrations.

**Blocked by / next action:** Review and commit the verified Day 1 changes. Then continue with Day 2 login/JWT and role-based authorization; do not claim M1 until its complete booking evidence exists.

**Resume impact:** No change; Day 1 registration and database foundation are implemented, but M1 is not complete.

### Planned implementation sequence

1. **Day 1:** Database connection, initial models/migrations, registration.
2. **Day 2:** Login/JWT, roles, provider profile, services.
3. **Day 3:** PostgreSQL exclusion constraint and basic booking; assess M1 against evidence.
4. **Day 4:** Weekly availability rules and slot generation.
5. **Day 5:** Confirm/cancel/list endpoints and ownership/authorization.
6. **Day 6:** Integration and concurrency tests.
7. **Day 7:** Docker Compose and GitHub Actions.
8. **Day 8:** Redis availability cache and measured benchmark.
9. **Day 9:** RQ jobs and dedicated idempotency table.
10. **Day 10:** Deployment if practical, polish, documentation, and interview defence.

## 5. Session log

Append one entry after every work session. Keep it short and factual.

**Template**

**Date / project day:**  
**Completed:**  
**Evidence (files, tests, commit):**  
**Learned / can now explain:**  
**Blocked by / next action:**  
**Resume impact:** No change / M1 eligible / M2 eligible / M3 eligible (only after checking `project_resume_milestones.md`).

### Day 0 — 22 October 2026

**Completed:** Created the public repository and initial project skeleton; implemented a minimal FastAPI app and `/health`; opened generated Swagger UI; selected `venv` + `pip` with pinned dependencies; added `.gitignore`; created and pushed the initial commit; removed the personal context document from the public repository and pushed the cleanup; completed job-search activity and DSA practice.

**Evidence:** Repository: https://github.com/Tapas3341/appointment-scheduling-api. Initial commit: `d7c0ab3`. Latest observed commit: `04b2051 Update status and handoff docs at end of Day 0`. Terminal output confirmed branch `main` is up to date with `origin/main` and the working tree is clean. `/health` was manually verified. The developer reported removing the personal context document and pushing the cleanup; absence from tracked files still needs explicit confirmation. No automated test suite, CI, database layer, or deployment is recorded yet.

**Learned / can now explain:** Basic FastAPI application setup, the health endpoint, generated Swagger UI, local Python environment/dependency setup, Git commits, and keeping personal context out of a public repository.

**Blocked by / next action:** Confirm the private personal-context document is not tracked in the public repository, then begin Day 1 with PostgreSQL, SQLAlchemy, Alembic, and registration.

**Resume impact:** No change; M0 foundation only. Do not claim backend database, authentication, automated testing, CI, caching, background jobs, or deployment features yet.

## 6. Evidence rules

- Test counts come from actual test runs, never estimates.
- A manually exercised endpoint is not an automated test.
- Concurrency claims require a passing test against PostgreSQL.
- Performance claims require recorded, comparable before/after measurements.
- “CI green” means the actual GitHub Actions workflow passed on the current commit.
- “Deployed” means a reachable service with a known deployed revision.
- List Redis, RQ, Docker, pytest, and GitHub Actions on the resume only after actually using them.
- If implementation differs from the plan, record the difference instead of pretending it matches.
- Keep personal job-search context out of the public repository.
