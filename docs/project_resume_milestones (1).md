# Appointment Scheduling API: resume content by milestone

**Purpose:** Keep resume claims synchronized with the canonical project plan and the actual repository state.

**Hard rule:** A bullet goes on the resume only when its trigger is demonstrably true. A planned task, tutorial completed, or code that has not been tested is not implementation evidence. Keep links, test counts, benchmark numbers, and deployment claims factual.

**Canonical design:** Six tables (`users`, `provider_profiles`, `services`, `availability_rules`, `appointments`, `idempotency_keys`); provider timezone on `provider_profiles`; five-minute configurable holds; separate idempotency table introduced in the later milestone; PostgreSQL exclusion constraint; M1 target is the end of Day 3. This document follows `APPOINTMENT_SCHEDULING_API_PROJECT_PLAN.md` where older notes differ.

**Target technology line** (add a technology only after actually using it in the project):

`Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Redis, RQ, Docker, pytest, GitHub Actions`

Do not list the full target line at M1. Each milestone below specifies the technologies that are eligible at that stage.

---

## M1: core booking works locally (target: end of Day 3)

**Trigger:** A user can register and log in, a provider can configure a profile and service, a customer can create a basic booking hold, and PostgreSQL rejects a second overlapping booking for the same provider. Adjacent appointments are allowed. This is the core scheduling milestone; the complete weekly-availability/slot-generation flow is scheduled for Day 4, so do not imply that full availability scheduling is complete at M1.

**Heading:** `Appointment Scheduling API (in progress)`

**Eligible tech line:** `Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic` — include each only if used.

- Building an API-only appointment scheduling service with FastAPI and PostgreSQL, using SQLAlchemy/Alembic for persistence and schema migrations.
- Implementing JWT authentication and role-based access for customers, providers, and admins. Keep this bullet only if the relevant flows and access checks are implemented; otherwise describe the narrower work actually completed.
- Enforcing conflict-free bookings with a PostgreSQL exclusion constraint on appointment time ranges, so overlapping appointments for the same provider are rejected by the database.

**M1 evidence checklist:**
- [ ] Public GitHub repository and README exist.
- [ ] README separates implemented behavior from planned work.
- [ ] Registration/login and provider profile/service setup work locally.
- [ ] PostgreSQL exclusion constraint is present in a migration and in the database.
- [ ] Repeated overlapping booking is rejected; adjacent bookings are accepted.
- [ ] Five-minute hold behavior is used/configurable as specified.
- [ ] Resume bullets above accurately match the implemented code.

Do not claim the concurrency-test result at M1 unless that test has actually been written and passed; the formal concurrency proof is an M2 trigger.

---

## M2: tested, containerized, and continuous integration (target: Day 7)

**Trigger:** The database-backed concurrency test passes, Docker Compose starts the required local stack with one command, and GitHub Actions runs the project checks successfully.

**Heading:** `Appointment Scheduling API` (drop “in progress” only if the core is genuinely complete; it is fine to retain it while later scope remains unfinished).

**Eligible additional technologies:** `Docker, pytest, GitHub Actions`, once actually used.

- Designed and built an API-only appointment scheduling service with FastAPI and PostgreSQL, including JWT authentication and role-based access control for customers, providers, and admins.
- Enforced no-overlap booking at the database level with a PostgreSQL exclusion constraint; validated it with a concurrency test in which **[N]** parallel requests for the same slot produce exactly one successful booking and the remaining requests are rejected.
- Containerized the application and its required services with Docker Compose; **[N]** pytest tests run in GitHub Actions CI.

**M2 evidence checklist:**
- [ ] Test uses real PostgreSQL, not SQLite, for the exclusion-constraint/concurrency behavior.
- [ ] Test setup is committed and visible to concurrent workers; cleanup is reliable.
- [ ] Test proves exactly one success for competing requests and fails if the constraint is removed.
- [ ] Record the actual concurrency level **N** and actual pytest count **N** from the final run.
- [ ] Docker Compose starts the documented stack from a clean checkout.
- [ ] GitHub Actions is green on the repository's current commit.
- [ ] Do not fill placeholders with estimates.

---

## M3: measured, background-enabled, idempotent, and deployed (target: Day 10)

**Trigger:** Availability caching has been benchmarked on comparable data, RQ jobs run, booking idempotency is implemented and tested, the automated test suite/CI is green, and the service is deployed. If deployment is blocked, state that honestly and use the local Compose demo; do not say “deployed.”

Use the full set of bullets in the commented M3 block of `resume_A_backend.tex` only after checking each statement against code, tests, benchmark output, and deployment evidence. Suggested content structure:

1. **API/auth:** REST API, JWT authentication, role-based access control.
2. **Concurrency:** PostgreSQL exclusion constraint, supported by the concurrency test.
3. **Caching:** Redis availability caching; latency improved from **[X] ms** to **[Y] ms** under the documented benchmark conditions.
4. **Background work/retries:** RQ jobs for expiring stale holds and simulated reminders; idempotency keys backed by a dedicated table.
5. **Delivery:** Docker Compose, **[N]** tests, GitHub Actions CI, deployed on **[host]**.

**M3 evidence checklist:**
- [ ] Benchmark records dataset/setup, request method, sample count, median/p95 (where measured), and before/after conditions.
- [ ] Cache invalidation covers booking/availability changes; Redis failure has the documented fallback behavior.
- [ ] RQ jobs are repeat-safe and failures/retries are understood.
- [ ] Same idempotency key + same request replays the saved response; same key + different request is rejected; concurrent key use is protected by a unique constraint.
- [ ] Test count is taken from the actual final run.
- [ ] Deployment URL is reachable and the deployed revision matches the claimed code.
- [ ] You can explain every bullet without notes.

---

## Interview-defence checklist (for every bullet)

For each resume bullet, be able to answer without notes:

- **Data flow:** What happens from the incoming HTTP request through validation, business logic, database/cache/job interaction, and response?
- **Design:** Why was this approach chosen? What alternative did you consider, and why not use it?
- **Failure modes:** What can fail or race? What protects correctness? How would you detect and debug the failure?
- **Evidence:** Which file, migration, test, CI run, benchmark, or deployment proves the claim?

If you cannot answer these questions, narrow the bullet or leave it off until you can. Resume language must never get ahead of the implementation.
