# Appointment Scheduling API — Project Status

**Last updated:** 22 October 2026  
**Current state:** Day 0 / pre-M1 / implementation not yet recorded as started  
**Canonical specification:** `APPOINTMENT_SCHEDULING_API_PROJECT_PLAN.md`  
**Continuity context:** `APPOINTMENT_SCHEDULING_API_CONTEXT.md`  
**Resume gates:** `project_resume_milestones.md`

> This file is the live status ledger, not another design document. Update it after each work session. Never mark an item complete just because it was planned or discussed.

## 1. Current snapshot

- [ ] Public repository created and URL recorded below.
- [ ] README created with implemented/planned scope separated.
- [ ] Local Python environment and dependency approach selected.
- [ ] Minimal FastAPI app starts locally.
- [ ] `GET /health` returns HTTP 200.
- [ ] First commit created.
- [ ] No secrets or local environment files are tracked.
- [ ] No project milestone has been claimed on the resume yet.

**Repository URL:** Not recorded yet.  
**Current branch / commit:** Not recorded yet.  
**Last known passing test command/result:** None recorded yet.  
**Last known CI result:** Not configured / not recorded yet.  
**Deployment URL:** Not applicable yet.

## 2. Canonical decisions (do not silently drift)

- API-only FastAPI service; no frontend and no microservices.
- Python, FastAPI, Pydantic, PostgreSQL, SQLAlchemy 2.0 sync + psycopg3, Alembic.
- JWT authentication and password hashing; roles are `customer`, `provider`, `admin`.
- Six canonical tables: `users`, `provider_profiles`, `services`, `availability_rules`, `appointments`, `idempotency_keys`.
- Provider IANA timezone lives on `provider_profiles`.
- Appointment times use timezone-aware instants / UTC semantics.
- PostgreSQL `tstzrange` and a partial exclusion constraint prevent overlapping `held`/`confirmed` appointments for the same provider; use half-open ranges `[start, end)` and `btree_gist`.
- Hold duration is five minutes and configurable for tests.
- Customer cancellation only if more than two hours before start; provider/admin can cancel at any time.
- Booking horizon is 30 days.
- Expired holds must have their status updated to `expired` before they stop blocking the constraint; expire lazily during booking and via background work.
- Redis availability cache starts Day 8; RQ/background jobs and dedicated-table idempotency start Day 9.
- Docker Compose and GitHub Actions are targeted for Day 7.
- M1 is targeted for the end of Day 3, but is awarded only when its evidence checklist is met.
- No real payment, email/SMS integration, frontend, Kubernetes, Kafka, GraphQL, or microservices.

If a design change becomes necessary, add it to `DECISIONS.md` with the reason and tradeoffs, then update this file and the canonical plan if appropriate.

## 3. Milestone tracker

| Milestone | Target | Status | Evidence required |
|---|---|---|---|
| M0 / foundation | Day 0 | Not started / unverified | Public repo, honest README, local `/health`, first commit, clean secrets check |
| M1 / core booking | End of Day 3 | Not started | Register/login, provider/service setup, basic hold booking, DB exclusion constraint, duplicate overlap rejected, adjacent slots allowed |
| M2 / tests + containers + CI | Day 7 | Not started | Real-Postgres concurrency test, Docker Compose from clean checkout, green GitHub Actions |
| M3 / cache + jobs + idempotency + deployment | Day 10 | Not started | Reproducible benchmark, cache invalidation/fallback, repeat-safe RQ jobs, idempotency tests, full test/CI evidence, working deployment |

## 4. Work queue — next actions

### First session: Day 0

- [ ] Create/verify public repository.
- [ ] Add README with goal, planned stack, current status, and implemented-versus-planned sections.
- [ ] Create project skeleton and minimal FastAPI application.
- [ ] Add `GET /health` returning 200.
- [ ] Select and record dependency-management approach; pin dependencies appropriately.
- [ ] Add `.gitignore` and verify secrets/local env files are not tracked.
- [ ] Make the first commit.
- [ ] Record repository URL and commit in this file.
- [ ] Take one concrete job-search action; the project must not pause applications.

### Next implementation sequence

1. Day 1: database connection, six-table model direction, Alembic, registration.
2. Day 2: login/JWT, roles, provider profile, services.
3. Day 3: PostgreSQL exclusion constraint and basic booking; assess M1 against evidence.
4. Day 4: weekly availability rules and slot generation.
5. Day 5: confirm/cancel/list endpoints and ownership/authorization.
6. Day 6: integration and concurrency tests.
7. Day 7: Docker Compose and GitHub Actions.
8. Day 8: Redis availability cache and measured benchmark.
9. Day 9: RQ jobs and dedicated idempotency table.
10. Day 10: deploy if practical, review, document, and practise interview defence.

## 5. Session log

Append one entry after every work session. Keep it short and factual.

### Template

**Date / project day:**  
**Completed:**  
**Evidence (files, tests, commit):**  
**Learned / can now explain:**  
**Blocked by / next action:**  
**Resume impact:** No change / M1 eligible / M2 eligible / M3 eligible (only after checking `project_resume_milestones.md`).

### Entries

_No implementation sessions recorded yet._

## 6. Evidence rules

- Test counts come from the actual run, not a guess.
- Concurrency claims require the test to pass against PostgreSQL.
- Performance claims require recorded, comparable before/after measurements.
- “Deployed” requires a reachable service and a known deployed revision.
- List Redis, RQ, Docker, pytest, and GitHub Actions on the resume only after actually using them.
- If implementation differs from the plan, record the difference instead of pretending it matches.
