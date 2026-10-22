# Appointment Scheduling API — Project Status

**Last updated:** 22 October 2026  
**Current state:** Day 0 complete / pre-M1  
**Canonical specification:** `APPOINTMENT_SCHEDULING_API_PROJECT_PLAN.md`  
**Continuity context:** `APPOINTMENT_SCHEDULING_API_CONTEXT.md`  
**Resume gates:** `project_resume_milestones.md`

> This is the live execution ledger. Record evidence, not intentions. A planned feature is not a completed feature, and a manually verified endpoint is not an automated test.

## 1. Current snapshot

- [x] Public GitHub repository created.
- [x] README created to introduce the project and distinguish current implementation from planned scope.
- [x] Local Python environment and dependency approach selected.
- [x] Minimal FastAPI application created and starts locally.
- [x] `GET /health` manually verified successfully.
- [x] First commit created and pushed.
- [x] `.gitignore` added; `.venv/` confirmed ignored.
- [x] Personal context document removed from the public repository and the cleanup pushed, as reported by the developer.
- [x] At least one concrete job-search action completed alongside project work.
- [ ] Final post-cleanup Git status and latest commit hash reverified in the next session.
- [ ] No project milestone has been claimed on the resume.

**Repository URL:** https://github.com/Tapas3341/appointment-scheduling-api  
**Local repository:** `C:\Users\Tapasendra Patra\appointment-scheduling-api`  
**Primary branch:** `main`  
**Known initial commit:** `d7c0ab3 chore: initialize appointment scheduling API`  
**Latest cleanup commit:** Pushed, but its hash has not been recorded here; verify with `git log -1 --oneline`.  
**Dependency approach:** Python virtual environment (`venv`), `pip`, pinned `requirements.txt`.  
**Python version observed:** `3.14.4`.  
**Last manually verified behavior:** `GET /health` returned the expected healthy response; FastAPI's generated `/docs` Swagger UI opened.  
**Automated test suite:** Not implemented or recorded yet.  
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

The dependency file contains pinned versions for the initial FastAPI application. Database packages and the database layer have not yet been implemented.

The `/docs` route is FastAPI-generated Swagger UI. It is not a custom frontend.

**Before Day 1 implementation:** verify the latest repository commit, clean working tree, and that the removed personal context file is no longer tracked in the public repository.

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

### First actions: Day 1

1. Verify `git status --short`, `git log -1 --oneline`, and that personal context material is not tracked in the public repository.
2. Review the installed Python version and current pinned dependencies. Check compatibility before adding database packages; do not assume Python 3.14 compatibility for every dependency.
3. Set up PostgreSQL for local development and verify the connection.
4. Add the SQLAlchemy 2.0 synchronous database configuration using psycopg3.
5. Learn and implement the initial user model and database session lifecycle.
6. Set up Alembic and generate/apply the first migration.
7. Implement registration with appropriate request validation and password hashing.
8. Verify the behavior with focused manual/API checks; introduce automated tests only as actually implemented.
9. Commit the working Day 1 changes and update this status ledger.

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

**Evidence:** Repository: https://github.com/Tapas3341/appointment-scheduling-api. Known initial commit: `d7c0ab3`. `/health` was manually verified. The latest cleanup commit hash must be checked in the next session. No automated test suite, CI, database layer, or deployment is recorded yet.

**Learned / can now explain:** Basic FastAPI application setup, the health endpoint, generated Swagger UI, local Python environment/dependency setup, Git commits, and keeping personal context out of a public repository.

**Blocked by / next action:** Verify final Git state, then begin Day 1 with PostgreSQL, SQLAlchemy, Alembic, and registration.

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
