# Appointment Scheduling API — Canonical Project Plan

**Status:** Reconciled execution plan  
**Created:** 21 October 2026  
**Project day 0:** 21 October 2026  
**Target duration:** 10 project days (Days 0–10)  
**Current state:** Day 0 / Pre-M1 / not started  
**Companion documents:** `APPOINTMENT_SCHEDULING_API_CONTEXT.md`, `PROJECT_STATUS.md`, `AI_HANDOFF.md`, `project_resume_milestones.md`

> **Source note:** The user has now supplied both source plans in full. This revision uses the newer **“Project Plan — Complete”** as the primary specification where the plans conflict, while retaining useful learning scaffolding from the older plan. The older plan and the supplied resume-milestone notes conflict with the newer plan on the schema (four vs. six tables), hold duration (10 vs. 5 minutes), and M1 timing (Day 4 vs. Day 3). Those conflicts are called out explicitly in §3. `project_resume_milestones.md` has now been reconciled to this specification; `PROJECT_STATUS.md` and `AI_HANDOFF.md` provide the live status ledger and portable continuation context.

---

## 1. Project goal and operating principles

Build a small, API-only appointment scheduling backend that broadens the developer's profile from Python automation/build tooling into conventional backend engineering.

The project should demonstrate both breadth and depth:

- **Breadth:** REST, HTTP, relational data modeling, ORM, migrations, authentication, authorization, validation, testing, containers, CI, deployment.
- **Depth:** PostgreSQL-enforced prevention of overlapping bookings, transactions, concurrency testing, cache invalidation, retries/idempotency, and background-job failure handling.

The core engineering claim is:

> Two overlapping appointments for the same provider cannot both be accepted, because PostgreSQL enforces the no-overlap invariant—not merely an application-level availability check.

The aim is not to maximize features or technologies. The aim is to build a small system well enough to explain and defend it.

### Non-negotiable working rules

1. The AI acts as a tutor/reviewer, not a code vending machine.
2. Do not generate core logic wholesale unless explicitly asked.
3. Explain the concept and reasoning before giving a fix when learning is the goal.
4. Prefer hints and small examples before complete solutions.
5. Type and understand tutorial code instead of blindly pasting it.
6. Do not redesign frozen decisions without a concrete reason.
7. Keep resume claims tied to code, tests, measurements, and deployment evidence.
8. Never invent benchmark numbers or claim a technology that was only studied.
9. Each day ends with a commit, a three-line progress log, and a short explanation of what was learned.
10. Applications continue throughout the project; the project must not delay the job search.

---

## 2. Canonical stack

| Area | Technology | Why it is in scope |
|---|---|---|
| Language/API | Python, FastAPI, Pydantic | Build and validate an HTTP API |
| Persistence | PostgreSQL, SQLAlchemy | Relational model, transactions, constraints, queries |
| Schema evolution | Alembic | Reproducible database migrations |
| Authentication | JWT, password hashing | Authentication and role-based authorization |
| Tests | pytest | Unit, API/integration, database, and concurrency tests |
| Local environment | Docker, Docker Compose | Repeatable local startup |
| CI | GitHub Actions | Automatically run checks and tests |
| Cache/queue | Redis | Availability cache and RQ queue |
| Background work | RQ | Expiring holds and reminder jobs |
| Deployment | A host selected when deployment begins | Demonstrate a running service without assuming today's free-tier availability |

Target resume technology line, **only once each technology has actually been used**:

`Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Redis, RQ, Docker, pytest, GitHub Actions`

Do not add a frontend, Kubernetes, Kafka, GraphQL, microservices, payments, real SMS/email integrations, or unrelated features.

---

## 3. Frozen product and design decisions

**Precedence rule:** where the supplied plans conflict, use the newer document labelled **“New plan — Complete”** as the implementation specification. Do not blend conflicting details silently.

- Project: Appointment Scheduling API; API-only, no frontend.
- Single backend service, not microservices; API prefix `/api/v1`.
- Roles: `customer`, `provider`, `admin`.
- PostgreSQL exclusion constraint prevents overlapping appointments for the same provider.
- **Canonical schema: six tables** — `users`, `provider_profiles`, `services`, `availability_rules`, `appointments`, and `idempotency_keys`.
- Provider timezone belongs on `provider_profiles`, not `users`.
- Idempotency uses a dedicated `idempotency_keys` table, unique by user and key, storing a request hash and the saved response. This supersedes the older plan's dedicated-table idempotency fields.
- Public IDs should be UUIDs.
- **Canonical hold duration: five minutes**, configurable for tests. This supersedes the older plan's ten-minute default.
- Customer cancellation is allowed only more than two hours before the appointment starts; providers/admins may cancel at any time.
- Appointment lifecycle: `held` → `confirmed`, `expired`, or `cancelled`; `confirmed` → `cancelled`. A timed-out hold must be changed to `expired` before it stops blocking the exclusion constraint.
- Booking horizon: 30 days.
- All stored appointment instants use timezone-aware timestamps and UTC semantics; provider-local timezone is used to convert weekly rules into actual slots.
- Use half-open ranges `[start, end)` so adjacent appointments do not conflict.
- Only `held` and `confirmed` appointments participate in the partial exclusion constraint.
- Handle stale holds both lazily inside the booking transaction and with a background sweep/job.
- Redis is introduced on Day 8 for measured availability caching; RQ is introduced on Day 9 for background work.
- Docker Compose runs the local stack; GitHub Actions runs lint/tests.
- Repository is public from Day 0, and README must distinguish implemented behavior from planned behavior.
- Deployment comes after local correctness, tests, and CI are stable.

### Conflicts to reconcile in companion documents

The older plan and the earlier resume-milestone notes mention a four-table model, provider timezone on `users`, booking-level idempotency, a ten-minute hold, and M1 on Day 4. The newer complete plan instead specifies six tables, a `provider_profiles` table, a separate `idempotency_keys` table, a five-minute hold, and M1 at the end of Day 3. This plan follows the newer complete plan. `project_resume_milestones.md` has been revised to match this design. Do not claim any milestone merely because its planned day has arrived; use the evidence gates in that document and record actual progress in `PROJECT_STATUS.md`.

---

## 4. Architecture target

```text
Client
  |
  v
FastAPI (/api/v1)
  | \
  |  \---- Redis: availability cache / RQ queue
  |
  v
PostgreSQL

RQ worker
  |---- Redis queue
  |---- PostgreSQL
```

Keep business logic understandable and avoid unnecessary abstractions. Separate API concerns, business rules, and persistence where it makes the code clearer, but do not build a framework inside the project.

---

## 5. Canonical database schema and API contract

The missing specification has now been recovered from the two plans supplied in the conversation. This section is the implementation contract. The names and behaviors below follow the newer complete plan.

### Six-table schema

| Table | Key columns | Purpose / rules |
|---|---|---|
| `users` | `id`, `email`, `password_hash`, `full_name`, `role`, `created_at` | Unique email; role is `customer`, `provider`, or `admin`; never return the password hash. |
| `provider_profiles` | `user_id`, `display_name`, `timezone` | `user_id` is both primary key and foreign key to `users`; timezone is an IANA name such as `Asia/Kolkata`. |
| `services` | `id`, `provider_id`, `name`, `duration_minutes`, `is_active` | A service belongs to one provider. |
| `availability_rules` | `id`, `provider_id`, `weekday`, `start_time`, `end_time` | Weekly rules in provider-local time; weekday is 0–6; reject backwards, overlapping, or cross-midnight blocks. |
| `appointments` | `id`, `provider_id`, `customer_id`, `service_id`, `time_range`, `status`, `hold_expires_at`, `created_at` | `time_range` is a PostgreSQL `tstzrange`; appointment overlap is enforced here. |
| `idempotency_keys` | `id`, `user_id`, `key`, `request_hash`, `response_status`, `response_body`, `created_at` | Added on Day 9; unique constraint on `(user_id, key)`; supports safe request retries. |

The exact SQLAlchemy types, foreign-key delete behavior, and any additional indexes should be decided while implementing the migrations and documented in `DECISIONS.md`; do not add tables or change the six-table model without a concrete reason and an explicit decision record.

### Appointment exclusion constraint

Create the `btree_gist` extension and a partial exclusion constraint on `appointments`:

- for the same `provider_id`, no two rows whose statuses are `held` or `confirmed` may have overlapping `time_range` values;
- use the PostgreSQL range-overlap operator;
- use half-open ranges `[start, end)`;
- cancelled and expired appointments no longer block the slot;
- map an exclusion violation to HTTP `409 Conflict`;
- after a database error, roll back the session before reusing it.

The constraint prevents overlapping appointments; it does **not** prove that an appointment is in the future or inside the provider's availability. Application/service logic must enforce those rules.

### Fifteen-endpoint contract

| # | Method and path | Access | Purpose and important behavior |
|---:|---|---|---|
| 1 | `GET /health` | Anyone | Confirms the app and database are up; `200`. |
| 2 | `POST /auth/register` | Anyone | Creates a customer or provider; `201`, `409` for duplicate email, `422` for invalid input. |
| 3 | `POST /auth/login` | Anyone | Returns a JWT access token; `200`, `401` for invalid credentials. |
| 4 | `GET /users/me` | Logged-in user | Returns the caller's profile; `200`, `401`. |
| 5 | `PUT /providers/me/profile` | Provider | Sets display name and timezone; `200`, `403` for non-provider. |
| 6 | `POST /providers/me/services` | Provider | Creates a service; `201`. |
| 7 | `GET /providers/{id}/services` | Anyone logged in | Lists a provider's active services; `200`. |
| 8 | `PUT /providers/me/availability` | Provider | Replaces weekly availability rules; `200`, `422` for invalid/overlapping rules. |
| 9 | `GET /providers/{id}/slots` | Anyone logged in | Lists open slots for a service over a date range; `200`; cached from Day 8. |
| 10 | `POST /appointments` | Customer | Creates a five-minute hold; accepts `Idempotency-Key` from Day 9; `201`, `409` if taken, `422` outside availability. |
| 11 | `POST /appointments/{id}/confirm` | Owning customer | Confirms a valid held appointment (mock payment); `200`, `403`, `409` if expired/not confirmable. |
| 12 | `POST /appointments/{id}/cancel` | Owner, provider, admin | Cancels subject to the customer's two-hour rule; `200`, `403`. |
| 13 | `GET /appointments` | Logged-in user | Lists the caller's appointments, paginated and filterable by status/date; `200`. |
| 14 | `GET /appointments/{id}` | Owner, provider, admin | Gets one appointment with ownership/access checks; `200`, `403` or `404`. |
| 15 | `GET /admin/appointments` | Admin | Lists all appointments, paginated; `200`, `403`. |

Use the `/api/v1` prefix in the application routing if that remains the project-wide convention, while keeping the resource paths above as the endpoint contract. Validate request/response shapes at the edge, keep routers thin, and place business rules in service functions. The original plan does not specify every request/response field; define those from the table/model and record consequential choices as you implement.

### Ownership and error conventions

- A customer can view/cancel only their own appointments.
- Providers manage only their own profile, services, availability, and relevant appointments.
- Admins can inspect all appointments and cancel as specified.
- Check both role and record ownership; role alone is insufficient.
- Choose consistently between `403` and `404` when a caller addresses another user's record, and document the choice.
- Use limit/offset pagination with a sensible maximum.
- Never return `password_hash`.
- Use one consistent error response shape.

---

## 6. Appointment lifecycle and time rules

Canonical lifecycle from the newer complete plan:

| From | Action | To | Who |
|---|---|---|---|
| None | Create appointment | `held` with a five-minute hold | Customer |
| `held` | Confirm (mock payment) | `confirmed` | Owning customer |
| `held` | Hold expires | `expired` | Booking transaction or background job |
| `held` or `confirmed` | Cancel | `cancelled` | Owner customer subject to the two-hour cutoff; provider/admin at any time |

No other transitions are allowed. A held appointment cannot be confirmed after expiry. A request overlapping an active appointment fails with HTTP `409`.

Important implementation rules:

- A timed-out hold still blocks until its status changes because the exclusion constraint cannot use the current time as a moving predicate. Expire stale holds lazily for the relevant provider inside the booking transaction, and sweep remaining stale holds with background work.
- Store instants as timezone-aware UTC timestamps. Use the provider's IANA timezone to turn weekly local-time rules into concrete UTC slots.
- Use half-open ranges `[start, end)` so a 10:00–10:30 appointment can be followed by a 10:30–11:00 appointment.
- Reject availability rules that cross midnight. Define and document behavior for daylight-saving gaps/repeated local times; the complete plan says to skip a slot whose local time does not exist.
- Generate slots as a pure function first, then subtract active appointments. Do not put database calls inside the slot-generation function.
- The customer cancellation cutoff is two hours before start; providers and admins may cancel at any time.
- Booking is limited to a 30-day horizon.
- The exclusion constraint protects against overlap; service logic checks that the requested slot fits availability and is not in the past.

---

## 7. Ten-day execution plan

This schedule intentionally combines the earlier plan's gentler pacing for Days 0–6 with the complete plan's Days 7–10. Milestone 1 is targeted for the end of Day 3, matching the newer complete plan. Days 1–2 are learning-heavy; Days 9–10 are buffers. If you have not completed setup yet, treat the dates as relative project days rather than rushing to catch up.

The daily durations are targets, not a reason to sacrifice sleep or abandon the plan if a day slips. If a day is missed, continue the next day—do not restart from Day 0.

### Day 0 — Foundation and job-search setup

**Goal:** Make it easy to start building tomorrow and avoid using project planning as a substitute for applications.

**Tasks**
- Create a public GitHub repository.
- Add a README with the project goal, planned stack, current status, and implemented-versus-planned sections.
- Create the project skeleton and a minimal FastAPI application.
- Add `GET /health` returning HTTP 200.
- Create a virtual environment and record the chosen dependency-management approach.
- Add a `.gitignore`; verify that secrets and local environment files are not committed.
- Make the first commit.
- Create `docs/` for concept notes and `PROJECT_STATUS.md` / `AI_HANDOFF.md` for continuity.
- Send applications and message NI contacts; do not wait for the project.
- Update LinkedIn headline/skills to match the resume, pin the repository when presentable, and add it to Featured only when its state is accurately described.

**Done when**
- Public repo exists.
- README explains the project honestly.
- `/health` returns 200 locally.
- No secrets are tracked.
- First commit exists.
- At least one concrete job-search action is completed.

**If stuck**
- Reduce the task to a minimal FastAPI app.
- Check the official FastAPI first-steps documentation.
- Do not begin PostgreSQL, JWT, Redis, or Docker troubleshooting on Day 0.

### Day 1 — Database, models, migrations, and registration

**Goal:** A user can register and the row appears in PostgreSQL. This is a learning-heavy day; time-box reading and prioritize a working vertical slice.

**Learn**
- FastAPI request body, response models, errors, dependencies, and HTTP status codes.
- SQL basics: `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `WHERE`, and joins.
- SQLAlchemy 2.0 engine, session, mapped classes, and `select` statements.
- Alembic revisions, upgrade/downgrade, and model metadata.
- Password hashing and why a raw password must never be stored.

**Build**
- Start PostgreSQL in Docker with a named volume and configure the connection via environment variables.
- Create SQLAlchemy's engine/session factory and a session-per-request dependency.
- Define the `users` model and configure Alembic to see its metadata.
- Generate, inspect, and apply the first migration.
- Implement `POST /auth/register` for customer/provider accounts with validation and password hashing.
- Return `409` for duplicate email; never return the password hash.

**Done when**
- A fresh database can be created from migrations.
- Registration works in `/docs`; the database contains a password hash, not the password.
- Duplicate registration returns `409`.
- You can explain session, commit, rollback, and why migrations beat table creation at app startup.

**If stuck**
- Empty migration: check that Alembic imports the model metadata.
- Connection refused: check container state, port mapping, host, and credentials.
- Hashing mismatch: follow one current official FastAPI security tutorial rather than mixing older library examples.

### Day 2 — Login, roles, providers, and services

**Goal:** Token login works, protected routes identify the caller, and providers can create their profile and services.

**Learn**
- FastAPI OAuth2 with Password and JWT; the jwt.io introduction.
- Authentication (identity) versus authorization (permissions).
- JWT signature, `sub`, expiry, short-lived access tokens, and secret handling.
- `401` versus `403`; role checks versus resource ownership checks.

**Build**
- Implement `POST /auth/login` and a reusable dependency that validates the token and loads the current user.
- Implement `GET /users/me` and a role dependency.
- Add `provider_profiles` and `services` models/migrations.
- Implement `PUT /providers/me/profile`, `POST /providers/me/services`, and `GET /providers/{id}/services`.
- Enforce provider ownership and validate positive service duration.
- Exercise the API using Swagger's Authorize button.

**Done when**
- Login returns a token and `/users/me` returns the current user.
- Missing/invalid token gives `401`; a customer attempting a provider-only action gets `403`.
- Provider A cannot edit Provider B's resources.
- You can explain the token flow and the trade-off if a token is stolen.

**If stuck**
- Swagger's OAuth2 password flow sends form data; that is expected.
- Check that token signing and verification use the same secret/algorithm and that expiry is handled.

### Day 3 — Core scheduling and Milestone 1

**Goal:** PostgreSQL itself rejects overlapping appointments for the same provider.

**Learn**
- PostgreSQL range types, range overlap, exclusion constraints, and `btree_gist`.
- SQLAlchemy's PostgreSQL range type and `ExcludeConstraint` support.
- Why an application-only “check then insert” can race.

**Build**
- In a database client, create a scratch range table and experiment with overlapping and adjacent ranges.
- Add the `appointments` model and a migration for `btree_gist` and the partial exclusion constraint (active statuses only).
- Implement `POST /appointments` in a simple form: provider, service, and start time in; end time computed from service duration; status starts as `held`.
- Convert exclusion violations to HTTP `409`; roll back the session after database errors.
- Use a five-minute configurable hold, per the newer complete plan.
- Try the same booking twice manually; also test adjacent appointments.

**Done when — Milestone 1**
- Register/login, provider profile/service setup, and basic booking work.
- A second overlapping appointment gets `409`; back-to-back appointments both succeed.
- A cancelled/expired appointment no longer blocks once its status changes.
- You can point to the constraint in PostgreSQL and explain why it is stronger than an application check.
- README accurately states what is built versus planned; update the resume only if the milestone evidence exists.

**If stuck**
- “No default operator class for GiST” usually means `btree_gist` or the equality operator configuration is missing.
- Check the database error code: exclusion violation is not the same as unique violation.
- If the next query fails after a database error, check rollback handling.

### Day 4 — Availability and slot generation

**Goal:** Weekly rules become concrete open slots, and a booking must fit inside them.

**Learn**
- Python `zoneinfo`; aware versus naive datetimes; UTC and daylight-saving changes.
- Why slot generation should be a pure function that can be tested without a database.

**Build**
- Add `availability_rules` and its migration.
- Implement `PUT /providers/me/availability` to replace weekly rules and reject backwards, overlapping, or cross-midnight blocks.
- Write a pure slot-generation function: weekly rules + provider timezone + service duration + date range → UTC slots.
- Implement `GET /providers/{id}/slots`, subtracting active appointments from generated slots.
- Make booking reject slots outside availability or in the past; enforce the 30-day booking horizon.
- Expire stale holds for the relevant provider inside the booking transaction (lazy expiry).

**Done when**
- Availability is correct for a provider in `Asia/Kolkata` over a week.
- A daylight-saving timezone retains its local working hours while corresponding UTC times shift.
- Slots disappear after booking and reappear after cancellation/expiry.
- README documents the slot granularity and daylight-saving edge-case decision.

**If stuck**
- Python weekday numbering starts Monday at `0`; document the convention.
- Never compare naive and aware datetimes.
- Skip a slot whose local time does not exist on a daylight-saving transition, and document that choice.

### Day 5 — Confirm, cancel, list, and authorization

**Goal:** Make behavior explicit and reliable, rather than adding features.

**Build/review**
- Write the lifecycle and allowed transitions in `docs/`.
- Implement confirm (owner only, held only, not expired; otherwise `409`).
- Implement cancellation: customer owner may cancel only more than two hours before start; providers/admins may cancel at any time.
- Implement `GET /appointments`, `GET /appointments/{id}`, and `GET /admin/appointments` with status/date filters and limit/offset pagination.
- Enforce ownership and role rules on every appointment operation.
- Test customer/provider/admin access across the relevant endpoints.
- Standardize error response shape using clear exception types/handlers.
- Add tests for invalid transitions, invalid times, unauthorized access, and edge cases.
- Use UUIDs for public identifiers as specified in the schema contract.

**Done when**
- Business rules are documented and tested.
- Error responses are consistent.
- Invalid state transitions are rejected.
- No secrets or sensitive credentials appear in logs.

**If stuck**
- Write the rule as a plain-English sentence and turn it into one test.
- Investigate the failing layer: validation, authorization, service logic, or database.
- Avoid refactoring unrelated code while debugging.

### Day 6 — Integration tests and concurrency proof

**Goal:** Prove correctness under ordinary and concurrent requests.

**Build**
- Add integration tests for the important API paths.
- Add a concurrency test where N parallel requests attempt to book the same provider/time.
- The expected result is exactly one successful booking; conflicting requests fail appropriately.
- Use committed setup data and dedicated setup/cleanup for this test. Do **not** use a rollback-per-test pattern that hides setup rows from concurrent workers.
- Repeat the concurrency test in a loop (the review recommends 20 runs) to check for flakiness.
- Add tests for expired holds using a very short configured duration, if the lifecycle implementation is ready.
- Inspect queries; understand N+1 behavior and when indexes help.
- Learn how to read a basic `EXPLAIN` plan.

**Done when**
- The test suite proves the main business rules.
- The concurrency test passes repeatedly.
- The reason for the database constraint is demonstrated, not merely asserted.
- You can explain test isolation and why committed setup data is required.

**If stuck**
- First reproduce the race with the smallest possible test.
- Confirm every worker uses the intended test database and transaction setup.
- Separate genuine duplicate acceptance from test cleanup or visibility problems.

### Day 7 — Docker Compose, CI, and Milestone 2

**Goal:** Make the project reproducible and automatically tested.

**Build**
- Containerize the API and required local services.
- Use Docker Compose to start the local stack with one command.
- Configure GitHub Actions to install dependencies and run the test suite.
- Ensure CI can reach PostgreSQL and runs migrations/test setup correctly.
- Keep secrets out of committed configuration.
- Improve README setup instructions and add test/CI instructions.

**Done when — Milestone 2**
- Docker Compose starts the full local application stack.
- Tests pass locally.
- GitHub Actions is green on the public repository.
- The concurrency test is included in the appropriate test workflow.
- A clean clone can follow the README to run the service.

**Resume action**
- Remove “in progress” only if you consider the core complete.
- Add Docker, pytest, and GitHub Actions to the technology line only after using them.
- Use only the actual test count and actual concurrency request count.

**Workload**
- Take a lighter evening after reaching this milestone. Do not treat it as a missed productivity day.

**If stuck**
- Test the API container, database container, networking, environment variables, migrations, and tests one layer at a time.
- Compare local and CI environment variables.
- Avoid changing several infrastructure pieces simultaneously.

### Day 8 — Redis availability cache and benchmark

**Goal:** Add caching for a measured reason, not for a keyword.

**Learn**
- Cache-aside pattern.
- Cache key design and TTL.
- Cache invalidation and stale data.
- Cache hit/miss.
- Why cached availability can become wrong after a booking or cancellation.
- Why one benchmark number is not enough without a repeatable method.

**Build**
- Benchmark the uncached availability path using a documented dataset and repeatable procedure.
- Record the method, number of requests, data shape, and observed latency.
- Add Redis caching to the agreed availability query.
- Invalidate/update cache when relevant booking state changes.
- Repeat the benchmark under the same conditions.
- Record real before/after values; do not choose the best-looking run selectively.

**Done when**
- Cache behavior is correct after booking/cancellation.
- The benchmark is reproducible and recorded in `docs/`.
- You can explain when the cache can be stale and what happens if Redis is unavailable.
- The project has a defensible measured result, even if the speed-up is modest.

**Resume action**
- Only write “reduced latency from X ms to Y ms” when X and Y come from your own before-and-after measurements.

**If stuck**
- First test cache hit/miss behavior with a fixed key.
- Then test invalidation independently.
- Never let a cache result override PostgreSQL's booking constraint.

### Day 9 — RQ background jobs, holds, and idempotency

**Goal:** Handle work outside the request path and make retries safe.

**Learn**
- Why a job queue exists.
- Worker lifecycle, retries, duplicate execution, and failure modes.
- What must happen inside a database transaction.
- Idempotency and the limits of “exactly once.”
- RQ scheduling behavior for delayed jobs. Verify current official documentation when implementing delayed jobs; the source review specifically flags that `enqueue_in` may require the scheduler to be enabled.

**Build**
- Add RQ + Redis background work for expiring unpaid holds and appointment reminders.
- Make the hold duration configurable (five-minute default, short duration in tests).
- Implement booking idempotency using the dedicated `idempotency_keys` table, with a key and request-body hash per user.
- Same key + same request returns the saved original response.
- Same key + different request is rejected.
- Test worker/job failure and duplicate execution behavior at a sensible scope.
- Confirm an expired hold no longer blocks availability.

**Done when**
- Background work runs through the worker.
- Hold expiration behaves correctly.
- Idempotent retries do not create duplicate bookings.
- You can explain what happens if a job is retried or executed twice.

**If stuck**
- Verify the current RQ docs for the exact delayed scheduling API and scheduler requirements.
- Test a job directly before debugging scheduling.
- Separate “job was not enqueued,” “worker did not run,” and “job ran but failed.”

### Day 10 — Deployment, review, and buffer

**Goal:** Deploy if practical, finish the documentation, and rehearse interview explanations.

**Build/review**
- Select a host based on current availability, limitations, and cost.
- Deploy only after local behavior, tests, and CI are stable.
- Configure environment variables/secrets safely and use HTTPS where supported.
- Smoke-test health, auth, availability, booking, and conflict rejection.
- Record limitations and known issues in the README.
- Update the resume only with evidence that exists.
- Review the full data flow and the major design decisions.
- Use this day as buffer for tasks that slipped from Days 7–9.

**Deployment time limit**
- Stop after roughly 3 hours if deployment is blocked by host/free-tier issues.
- Keep the project functional locally and in CI.
- If deployment does not work, leave “deployed” off the resume. Do not let hosting consume the project.

**Done when**
- Local and CI workflows are stable.
- Deployment is smoke-tested, or the blocker and local reproducibility are documented.
- README describes setup, architecture, API behavior, testing, design decisions, and limitations.
- You can defend each resume bullet without notes.

---

## 8. Milestones and resume claims

Resume claims are based on actual state, not the calendar. The date targets are planning aids only.

**Important:** `project_resume_milestones.md` was prepared against a conflicting earlier design. Before using it as-is, reconcile its four-table/10-minute-hold assumptions with this canonical six-table/five-minute-hold design. Keep the resume bullet themes, but do not let a stale companion file override the implemented project.

### M1 — Core works (target: Day 3)

Required evidence:
- registration/login;
- availability;
- booking;
- database rejection of overlapping bookings;
- public repo and honest README.

Technology line at this point:
`Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic`

### M2 — Tests, Docker, CI (target: Day 7)

Required evidence:
- concurrency test passes;
- Docker Compose starts the full local stack;
- pytest suite runs;
- GitHub Actions is green.

Add only the technologies actually used:
`Docker, pytest, GitHub Actions`

### M3 — Full target (target: Day 10)

Required evidence:
- Redis caching works and is measured;
- RQ background jobs work;
- booking idempotency works;
- deployment works, if claiming deployment.

Target project bullets (replace placeholders only with real evidence):

1. Designed and built a REST API (FastAPI, PostgreSQL, SQLAlchemy) for appointment booking, with JWT authentication and role-based access control for customers, providers and admins.
2. Made double-booking impossible at the database level with a PostgreSQL exclusion constraint on time ranges; validated by a concurrency test where **[N]** parallel requests for one slot produce exactly one booking.
3. Cut availability-query latency from **[X] ms** to **[Y] ms** by caching in Redis with invalidation on booking changes.
4. Built background jobs (RQ + Redis) to expire unpaid holds and send reminders, and added idempotency keys so retried booking requests do not create duplicate bookings.
5. Containerized with Docker Compose; **[N]** pytest tests run in GitHub Actions CI; deployed on **[host]**.

Use “Oct 2026” rather than “Nov 2026” if the project is genuinely completed in October. If it is not complete by then, use the truthful current state/date; do not backdate the work.

---

## 9. Learning resources and source-of-truth rule

Follow the newer complete plan's just-in-time approach. Use official documentation for implementation details and verify version-sensitive APIs at the point of use.

| Phase | Resource / topic | Time-box | Expected takeaway |
|---|---|---:|---|
| Day 0 | MDN HTTP overview; SQLBolt lessons 1–12; PostgreSQL JOIN/GROUP BY tutorial; FastAPI First Steps through Request Body | About 2–3 hours total; defer unfinished reading rather than block setup | HTTP methods/status codes, basic SQL, request validation |
| Day 1 | SQLAlchemy 2.0 Unified Tutorial; Alembic tutorial; FastAPI SQL Databases page for session-per-request shape | About 3–4 hours | Models, sessions, migrations, registration |
| Day 2 | FastAPI OAuth2 with Password and JWT; jwt.io introduction | About 2 hours | Login, token validation, role checks |
| Day 3 | PostgreSQL Range Types and Constraints; `btree_gist`; SQLAlchemy PostgreSQL dialect (`tstzrange`, `ExcludeConstraint`) | About 2–3 hours | Implement and prove the exclusion constraint |
| Day 4 | Python `zoneinfo` | About 1 hour | Convert weekly local rules to UTC slots |
| Day 6 | pytest fixtures and FastAPI testing | About 2 hours | Isolated API/database tests |
| Day 7 | Docker Compose; GitHub Actions PostgreSQL service containers | About 2 hours | Reproducible local stack and CI |
| Day 8 | Redis strings/TTL; a simple load tool such as Locust or `hey` | About 2 hours | Benchmark before/after cache |
| Day 9 | RQ queue/worker/scheduling documentation | About 2 hours | Delayed jobs and safe retries |

Optional video: freeCodeCamp's Python API development course may help with concepts, but it uses an older library set. Cap it at three hours and follow current official docs for code and package choices.

After each resource, close it and write five lines in `NOTES.md` in your own words. The official docs are the authority for current package APIs. In particular, verify the current RQ scheduler requirements before relying on delayed jobs. Do not read ahead for its own sake; learn what the next build step requires.

---

## 10. Daily routine outside project work

The project is not the entire job-search strategy.

A practical target is to protect time for:
- project learning/building;
- applications and recruiter follow-ups;
- referral messages;
- DSA/OA preparation;
- core CS revision.

The review warns that 4 hours of project work + 2 hours of applications + 1 hour of DSA every day is a roughly 7-hour workload over 11 days with no rest day. That can be unsustainable. Protect sleep and use a minimum-day rule rather than abandoning the whole plan after one difficult day.

Recommended ongoing baseline:
- Apply consistently while building; do not wait for M1/M2/M3.
- Revise core CS for about 20 minutes daily or use three focused slots per week.
- Complete DSA practice and add one timed OA practice each week.
- Take one lighter evening after M2.
- Never miss two days in a row if it can be avoided; if a day is missed, resume rather than restarting.

---

## 11. Stuck protocol

When blocked:

1. **Spend 10–15 minutes understanding the failure.**
   - What did I expect?
   - What happened?
   - What exact layer failed?
   - What does the traceback actually say?
2. **Reduce the problem** to the smallest reproducible example.
3. **Inspect one layer at a time:** request validation, auth, service/business logic, database, cache, worker, container/network, or CI.
4. **Check the official documentation** for the exact library/API involved.
5. **Ask for help/search if stuck for about 45 minutes.** Do not thrash indefinitely.
6. When asking an AI, include:
   - intended behavior;
   - current implementation or relevant snippet;
   - exact error/output;
   - what you tried;
   - current hypothesis.

The AI should explain the likely cause, give a hint first, and only provide a full replacement when requested or when a small focused fix is more useful.

### Symptom-to-layer guide

| Symptom | First things to check |
|---|---|
| 422 response | Request schema, body shape, path/query parameter types |
| 401 response | Missing/invalid token, token expiry, password verification |
| 403 response | Role/ownership/authorization check |
| Database connection failure | Service status, host/port, credentials, environment variables |
| Migration mismatch | Current revision, migration history, database URL |
| Double booking accepted | Exclusion constraint, range boundaries, migration actually applied |
| Conflict becomes 500 | Database exception mapping and rollback behavior |
| Test sees missing setup data | Transaction scope and committed fixture/setup data |
| Stale availability | Cache key, TTL, invalidation on booking/cancellation |
| Background job never runs | Enqueue result, queue name, worker process, scheduler configuration |
| Works locally, fails in CI | Environment variables, service readiness, migrations, test setup |
| Works locally, fails in container | Bind address, service DNS, ports, mounted files, environment |

---

## 12. Quality checklist

### API
- [ ] Request validation is explicit.
- [ ] HTTP methods/status codes are appropriate.
- [ ] Authentication and authorization are distinct and tested.
- [ ] Error responses have a consistent shape.
- [ ] Public IDs are UUIDs.
- [ ] Collection endpoints have a sensible pagination plan; understand offset versus keyset tradeoffs.

### Database
- [ ] Alembic migrations recreate the schema.
- [ ] Foreign keys and constraints reflect real rules.
- [ ] The exclusion constraint prevents overlapping bookings for the same provider.
- [ ] Booking and cancellation changes are transactionally correct.
- [ ] Important status transitions are documented and tested.
- [ ] Queries avoid avoidable N+1 behavior.
- [ ] At least one relevant query has been inspected with `EXPLAIN`.

### Security
- [ ] No secrets in Git.
- [ ] Passwords are hashed.
- [ ] Input is validated.
- [ ] Protected routes enforce roles/ownership.
- [ ] Deployment uses HTTPS where supported.
- [ ] Consider login-attempt limiting only if time permits.

### Tests/operations
- [ ] Unit and API/integration tests cover core rules.
- [ ] Concurrency test uses committed setup and dedicated cleanup.
- [ ] Concurrency test is repeated 20 times as a flakiness check.
- [ ] Docker Compose starts the stack.
- [ ] GitHub Actions runs tests.
- [ ] Logs help diagnose failures without leaking secrets.
- [ ] Redis invalidation is tested.
- [ ] Background job retry/duplicate behavior is understood.
- [ ] README documents local setup and known limitations.

---

## 13. Interview-defense questions

For every resume bullet, answer all three without notes:

1. **How does the data flow?** Explain request → API → validation/auth → business logic → database/cache/worker → response.
2. **Why this design?** Explain the alternatives and the tradeoff.
3. **What breaks first?** Explain the likely failure mode, bottleneck, race, or operational issue.

Practice these 15 questions:

1. Why use FastAPI for this project?
2. What happens between an HTTP request arriving and a response being returned?
3. What does SQLAlchemy do, and what does it not do?
4. Why use Alembic migrations?
5. Why is checking availability in Python and then inserting insufficient?
6. How does the PostgreSQL exclusion constraint work conceptually?
7. What happens if two transactions attempt overlapping bookings concurrently?
8. What is the difference between authentication and authorization?
9. What happens if a JWT is stolen?
10. Why use a transaction for booking/cancellation?
11. How would you investigate a slow availability query?
12. Why can caching availability create stale data, and how do you invalidate it?
13. What happens if a background job runs twice or a worker crashes?
14. What does idempotency guarantee, and what does it not guarantee?
15. What happens if Redis or PostgreSQL is unavailable?

Do not memorize polished answers. Explain what your implementation actually does, what it does not do, and what you would improve next.

---

## 14. Cut list if the schedule slips

Keep the core invariant, auth, tests, and reproducibility. Cut in this order:

1. Real email/SMS delivery; keep a logged or simulated reminder if needed.
2. Elaborate admin functionality beyond the agreed contract.
3. Optional login-attempt limiting.
4. Extra performance tooling beyond a repeatable small benchmark.
5. Hosting experiments after the 3-hour limit.
6. Any nonessential endpoint or abstraction not required by the recovered contract.

Do **not** cut:
- database-enforced no-overlap;
- a meaningful concurrency test;
- authentication/authorization checks;
- schema migrations;
- the ability to run and test the project reproducibly;
- honest resume claims.

If scope must change, record the decision in `DECISIONS.md` with the reason.

---

## 15. End-of-day log template

Add a short entry to `PROJECT_STATUS.md` or a dated daily log:

```text
Date / Project Day:
Goal:
Completed:
Commit:
Main concept explained in my own words:
“I should now be able to say…”
Blocker:
Next smallest task:
Applications/referrals completed:
```

A three-line summary is enough on a difficult day. The purpose is continuity, not paperwork.

---

## 16. Definition of success

The project is complete when:
- the core scheduling API works;
- PostgreSQL prevents overlapping appointments;
- concurrent requests are tested;
- authentication and authorization work;
- migrations, tests, Docker, and CI are reproducible;
- Redis caching is correct and measured;
- background jobs and idempotency work;
- deployment works, or the limitation is documented and deployment is not claimed;
- the README accurately describes the system;
- each resume bullet can be defended from implementation evidence.

**The repository is the truth. The plan is a guide. The resume is a claim about what the repository proves.**

