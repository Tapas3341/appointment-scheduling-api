# AI Handoff — Appointment Scheduling API

**Last updated:** 22 October 2026  
**Purpose:** Portable context for a new AI session so work can continue without reopening a long prior conversation.

## 1. What I am building

I am building an API-only Appointment Scheduling API in Python/FastAPI. It is a backend-learning and portfolio project designed to demonstrate relational data modeling, HTTP/API design, authentication/authorization, PostgreSQL constraints and transactions, concurrency testing, Docker/CI, caching, background work, idempotency, and deployment.

The central engineering story is that PostgreSQL itself prevents two overlapping appointments for the same provider. An application-level “check availability, then insert” is not enough because concurrent requests can race.

The project is intentionally small. Do not add a frontend, real payments, real email/SMS, microservices, Kubernetes, Kafka, GraphQL, or unrelated features.

## 2. Read these documents first

1. `APPOINTMENT_SCHEDULING_API_PROJECT_PLAN.md` — canonical specification, endpoint contract, schema, rules, and day-by-day plan.
2. `PROJECT_STATUS.md` — live progress ledger and next actions. Trust its recorded evidence, not assumptions.
3. `project_resume_milestones.md` — gates for what may truthfully appear on the resume.
4. `APPOINTMENT_SCHEDULING_API_CONTEXT.md` — fuller motivation, learning goals, and interview framing.
5. `DECISIONS.md` — create only when the first consequential implementation decision needs to be recorded; do not invent prior decisions.

If details conflict, follow the canonical project plan and the latest explicit decision record. Update companion docs when a design change is deliberately accepted.

## 3. Current state

As of 22 October 2026, the project is recorded as **Day 0 / pre-M1 / implementation not yet started or not yet evidenced**. Do not claim that code, tests, CI, benchmarks, or deployment exist unless `PROJECT_STATUS.md` and the repository prove it.

Immediate next task: complete Day 0 foundation—public repository, honest README, minimal FastAPI app, `GET /health`, dependency setup, `.gitignore`/secrets check, and first commit. Then update `PROJECT_STATUS.md` with the repo URL, commit, and actual results.

## 4. Frozen design

- API prefix: `/api/v1`; the endpoint contract in the plan lists resource paths without the prefix.
- Roles: `customer`, `provider`, `admin`.
- Six tables: `users`, `provider_profiles`, `services`, `availability_rules`, `appointments`, `idempotency_keys`.
- Provider timezone belongs on `provider_profiles` and uses an IANA timezone name.
- Stack: Python, FastAPI, Pydantic, PostgreSQL, SQLAlchemy 2.0 synchronous ORM with psycopg3, Alembic, JWT, password hashing, pytest, Docker Compose, GitHub Actions, Redis, RQ.
- Appointment `time_range` is PostgreSQL `tstzrange`; use `btree_gist` and a partial exclusion constraint so the same provider cannot have overlapping `held` or `confirmed` appointments.
- Ranges are half-open `[start, end)`, so adjacent appointments are allowed.
- Hold duration: five minutes, configurable for tests.
- Customer cancellation: only more than two hours before start; providers/admins can cancel any time.
- Booking horizon: 30 days.
- Appointment instants are timezone-aware and use UTC semantics. Convert weekly provider-local availability rules using the provider timezone. Reject cross-midnight rules; skip local slots whose times do not exist due to a DST gap, as specified in the plan.
- Expired holds must be transitioned to `expired` to stop blocking the database constraint. Handle expiry lazily in the booking transaction and later with background work.
- Dedicated `idempotency_keys` table is a later milestone; unique by `(user_id, key)`, stores request hash and response status/body.
- M1 target: end of Day 3; formal concurrency proof is M2, target Day 7. Targets are not evidence of completion.

Do not revert to the older four-table model, timezone-on-`users`, booking-level idempotency, ten-minute holds, or Day-4 M1 unless the user explicitly changes the spec and records the tradeoff.

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

Refer to §5 of `APPOINTMENT_SCHEDULING_API_PROJECT_PLAN.md` for access roles, response behavior, and the complete contract. Do not implement every endpoint on Day 0; follow the daily plan.

## 6. Execution schedule

- Day 0: repository, README, skeleton, health endpoint, first commit.
- Day 1: database, models/migrations, registration.
- Day 2: login/JWT, roles, provider profile/services.
- Day 3: exclusion constraint, basic booking, M1 evidence review.
- Day 4: availability rules and slot generation.
- Day 5: confirm/cancel/list/admin and ownership rules.
- Day 6: integration/concurrency tests.
- Day 7: Docker Compose and GitHub Actions; M2 evidence review.
- Day 8: Redis availability cache, invalidation, fallback, benchmark.
- Day 9: RQ background jobs and idempotency.
- Day 10: deployment/polish/interview defence, with a local demo fallback if deployment is blocked.

Continue from the current recorded state; do not restart planning or redesign the system just because a new chat has begun.

## 7. How to help me

Act as a **tutor and reviewer, not a code vending machine**.

- I want to learn backend engineering and be able to defend the project in interviews; finishing quickly by pasting generated code is not the only goal.
- Explain the concept and reasoning first. Prefer a hint, small example, or focused pseudocode before a complete implementation.
- Let me write the core logic. Review my code, identify the first conceptual/implementation error, and explain how to reason toward a fix.
- When I ask for a full implementation explicitly, you can provide it, but explain the important decisions and failure modes.
- Prefer straightforward Python and clear control flow over unnecessary abstractions.
- Do not redesign a frozen decision without a concrete reason. If a change is justified, explain the tradeoff and update the decision/status docs.
- Do not silently assume something has been implemented. Ask for the relevant code, test output, or repo state when needed.
- Keep each work session scoped to the current day's deliverable. Finish with a commit suggestion, a short learning recap, and a status-log entry.
- Applications/job search continue alongside the project; don't make project work a reason to postpone applications.

## 8. Truthfulness and resume constraints

- Resume bullets are gated by `project_resume_milestones.md`.
- Do not fabricate request counts, test counts, latency, throughput, cache improvements, or deployment status.
- Benchmark Redis against the same dataset and comparable request conditions; record the methodology and results.
- The concurrency test must use real PostgreSQL. It should prove exactly one success for parallel attempts at the same slot and should fail if the exclusion constraint is removed. Shared setup must be committed so concurrent workers can see it.
- “CI green” means the actual GitHub Actions workflow passed on the current commit.
- “Deployed” means a reachable deployment with a known revision. If blocked after a reasonable effort, retain a local Docker Compose demo and state the limitation honestly.

## 9. First response in a new session

First check `PROJECT_STATUS.md` and ask me for the smallest missing piece of evidence only if necessary. If the status still shows Day 0, help me implement the Day 0 foundation incrementally. Do not ask me to paste the whole project plan again.
