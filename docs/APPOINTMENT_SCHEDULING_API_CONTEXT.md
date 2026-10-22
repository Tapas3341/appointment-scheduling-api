# Appointment Scheduling API — Canonical Project Context

**Status:** Canonical context, created 21 Oct 2026  
**Project:** Appointment Scheduling API  
**Current state:** Day 0 / Pre-M1 / not started  
**Primary purpose:** Build a real backend project that closes Tapas's hands-on backend gap while creating defensible resume and interview evidence.

---

## 1. Why this project exists

Tapas is a strong Python/automation-oriented software engineer with substantial internship experience, but comparatively little hands-on backend engineering experience and limited backend theory.

The project is therefore **not** intended to prove that he can make a large application. It is intended to demonstrate that he can:

- design a relational backend;
- build and explain REST APIs;
- model real business rules;
- use PostgreSQL correctly;
- work with an ORM and migrations;
- implement authentication and authorization;
- reason about race conditions and concurrency;
- write meaningful tests;
- productionize a service with Docker and CI;
- introduce caching and background work for real reasons;
- reason about retries and idempotency;
- measure performance rather than invent numbers;
- deploy and defend the resulting system.

The chosen project is deliberately a **small domain with a genuinely difficult core problem**, rather than a large CRUD application. The central interview story is database-enforced prevention of overlapping appointments.

The project is API-only. A frontend is explicitly out of scope.

The project was chosen instead of a rate limiter / generic infrastructure component because Tapas already has a build/tooling/CI profile. The scheduler broadens the profile into application backend engineering while still giving a strong concurrency/database story.

---

## 2. Target outcome

By the end of the project, the target is a small but production-minded appointment scheduling service that can be discussed in an interview at the level of:

- API design
- authentication / authorization
- relational data modeling
- PostgreSQL constraints
- transactions
- concurrency and race conditions
- testing
- query performance
- caching
- background jobs
- retries / idempotency
- containerization
- CI
- deployment
- security
- observability / failure modes
- tradeoffs and scalability

The project must remain small enough to finish.

**Depth is preferred over feature count.**

---

## 3. Core problem

The domain is appointment scheduling.

There are three user roles:

- **Customer** — books appointments.
- **Provider** — defines availability and receives appointments.
- **Admin** — administrative access.

The central invariant is:

> Two overlapping appointments for the same provider must never both be accepted.

The important implementation decision is that this invariant is enforced by **PostgreSQL itself**, using a time-range representation and an exclusion constraint, rather than relying only on an application-level "check then insert."

This is the project's primary interview hook.

The expected concurrency demonstration is:

> Multiple parallel requests attempt to book the same slot; exactly one booking succeeds and the others are rejected by the database constraint.

The concurrency test must use committed setup data rather than a rollback-per-test pattern, because concurrent workers need to see the same committed state. It should also be repeated in a loop (the review recommends 20 runs) to establish that the test is not merely passing once by luck.

---

## 4. Scope philosophy

### Must have

The project must eventually cover:

1. FastAPI REST API
2. PostgreSQL
3. SQLAlchemy
4. Alembic migrations
5. JWT authentication
6. Role-based authorization
7. Provider availability
8. Customer booking
9. PostgreSQL exclusion constraint for no-overlap
10. Concurrency test
11. pytest test suite
12. Docker Compose
13. GitHub Actions CI
14. Redis caching
15. Background jobs with RQ + Redis
16. Idempotent booking requests
17. Deployment

### Explicitly out of scope

Do not add features merely because they make the application look larger.

Examples of things not required:

- frontend
- real payment integration
- chat
- email/SMS provider integration
- social login
- recommendation engine
- microservices
- Kubernetes
- Kafka
- GraphQL
- elaborate admin dashboard
- unnecessary tables
- unnecessary abstractions

The project should not become an attempt to demonstrate every technology in existence.

---

## 5. Target technology stack

### Application

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

### Database

- PostgreSQL

### Authentication

- JWT
- password hashing
- role-based access control

### Caching / background work

- Redis
- RQ

### Testing / quality

- pytest
- concurrency testing
- API/integration tests
- unit tests where appropriate

### Infrastructure

- Docker
- Docker Compose
- GitHub Actions

### Deployment

- A suitable host selected when deployment begins, based on current availability/free-tier constraints.

Technology is added to the resume **only after it has actually been used and understood**.

Canonical tech line target:

`Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Redis, RQ, Docker, pytest, GitHub Actions`

---

## 6. Architecture

The intended architecture is deliberately simple:

```text
Client
  |
  v
FastAPI application
  |
  +------------------> Redis
  |                     |
  |                     +--> cache
  |                     +--> RQ queue
  |
  v
PostgreSQL

RQ worker
  |
  +--> Redis
  |
  +--> PostgreSQL
```

The application is initially a single backend service.

Redis is not introduced merely for the keyword. It must solve an actual performance/use-case problem: caching availability queries, with invalidation when booking changes make cached availability stale.

RQ is used for background work such as:

- expiring unpaid holds;
- sending appointment reminders.

The exact scheduling mechanics for delayed RQ jobs must be checked against current RQ documentation when implementation reaches that stage.

---

## 7. Data-model decisions

The canonical design uses **four tables**, not six.

Important decisions from the plan review:

- `provider_profiles` is intentionally dropped.
- A separate `idempotency_keys` table is intentionally dropped.
- Provider timezone is stored on `users`.
- Public identifiers should be UUIDs.
- Idempotency information belongs on the booking record: an idempotency key plus a hash of the request body.
- A retry with the same key should return the original booking rather than creating a duplicate.

### Canonical scheduling concepts

The model needs to represent:

- users and roles;
- provider availability;
- appointments/bookings;
- the remaining scheduling-related state required by the four-table design.

The exact table names, columns, foreign keys and constraints should be taken from the canonical execution plan rather than invented during implementation.

**Important:** the currently recovered Claude-session material confirms the four-table decision and the major modeling rules, but does not reproduce the full table-by-table schema. Therefore, the exact schema is a plan-level detail that must be preserved when the master project plan is created.

---

## 8. Booking lifecycle

Appointments need explicit status transitions rather than scattered boolean flags.

The project should document the allowed lifecycle and test the transitions.

The planned concepts include:

- an unpaid **held** booking;
- a confirmed booking;
- cancellation;
- expiration of an unpaid hold.

Hold duration is:

**10 minutes, configurable through application configuration.**

Tests should use a much shorter duration (for example, a few seconds) so expiration behavior can be tested without waiting ten minutes.

The system should define and enforce rules for:

- who can create a booking;
- who can cancel it;
- when a held booking expires;
- when a booking becomes confirmed;
- what happens to availability after cancellation;
- what happens when a booking request races another booking request.

---

## 9. Scheduling rules

The project should include explicit rules rather than leaving behavior implicit.

Canonical rules identified by the plan review include:

- provider timezone is stored on the user;
- booking has a slot-granularity rule;
- booking is restricted to a 30-day horizon;
- overlapping bookings for the same provider are prohibited at the database level;
- booking requests need authorization checks;
- cancellation rules must be explicit;
- status transitions must be represented and unit-tested.

Time handling must be treated carefully. The goal is to understand the difference between:

- local provider time;
- timezone-aware timestamps;
- stored database timestamps;
- appointment duration;
- range overlap.

---

## 10. API design principles

The API uses an `/api/v1` prefix.

The planned API surface contains approximately 15 endpoints covering:

- authentication;
- provider availability;
- availability retrieval;
- appointment creation;
- appointment retrieval;
- appointment cancellation;
- role-specific operations;
- administrative operations required by the design.

The exact endpoint table belongs in the master execution plan. The important rule is that endpoints are not added simply to increase the count.

API design should cover:

- appropriate HTTP methods;
- status codes;
- request validation;
- response schemas;
- authentication;
- authorization;
- consistent error responses;
- pagination where collections can grow;
- public UUIDs rather than exposing internal sequential identifiers.

For pagination, the project should explicitly understand the tradeoff between **offset pagination and keyset pagination**, even if the final implementation only requires one.

---

## 11. Database engineering depth

The database is one of the most important learning areas.

Topics to understand while building:

### Constraints

Why application checks alone are insufficient for the double-booking invariant.

### Transactions

Understand what must happen atomically and why.

### Concurrency

Understand the race:

```text
Request A: check availability
Request B: check availability
Request A: insert
Request B: insert
```

and why "check first, then insert" is not sufficient protection by itself.

### PostgreSQL range types

Understand how an appointment's time interval is represented and how PostgreSQL can enforce non-overlap.

### Indexes

Understand:

- why indexes exist;
- what query they help;
- when an index is harmful;
- how to inspect a query with `EXPLAIN`;
- how the availability query can be improved.

### Query behavior

Avoid N+1 query patterns.

### Migrations

Alembic should be used to evolve the database schema rather than treating the database as something manually edited.

---

## 12. Authentication and authorization

Authentication uses JWT.

The project should teach the difference between:

- authentication — "who are you?"
- authorization — "are you allowed to do this?"

Role-based access must be enforced at the endpoint/service boundary.

The project should also understand the JWT-versus-session tradeoff and be able to answer:

> What happens if a JWT is stolen?

Security basics are part of the project:

- never commit secrets;
- hash passwords rather than storing plaintext;
- validate input;
- use HTTPS in deployment;
- consider login-attempt limiting if time permits;
- keep secrets in environment/configuration rather than source control.

---

## 13. Redis caching

Redis is introduced only after the core system works.

The target is to cache the availability-query path.

The process should be:

1. Measure the uncached path.
2. Identify what data is safe to cache.
3. Add Redis caching.
4. Measure again.
5. Implement invalidation when booking changes availability.
6. Repeat the benchmark under the same conditions.
7. Record the actual before/after numbers.

The resume must never contain invented numbers.

Target resume claim:

> Cut availability-query latency from `[X] ms` to `[Y] ms` by caching in Redis with invalidation on booking changes.

`[X]` and `[Y]` only become real after measurement.

---

## 14. Background jobs

RQ + Redis is used for work that does not need to block the request.

Planned jobs:

- expire unpaid holds;
- send appointment reminders.

The important learning is not merely "I used RQ."

It is:

- why background work is useful;
- what happens if a worker crashes;
- retries;
- duplicate execution;
- job scheduling;
- failure handling;
- what belongs in the request path versus the worker;
- what must remain transactionally consistent.

RQ scheduling behavior, particularly delayed jobs such as `enqueue_in`, must be verified against current RQ documentation when implemented.

---

## 15. Idempotency

Booking requests should support idempotency.

The design deliberately avoids a separate idempotency table.

Instead, the booking record carries:

- an idempotency key;
- a hash of the request body.

The intended behavior:

```text
First request
    |
    v
Create booking
    |
    v
Store idempotency information


Retry with same key + same request
    |
    v
Return original booking


Same key + different request
    |
    v
Reject as invalid/conflicting
```

This should be understood as protection against client retries and repeated requests, not as a magical guarantee of "exactly once" execution in every distributed failure scenario.

---

## 16. Testing strategy

Testing is not a final-day activity.

The project should progressively test:

### Unit behavior

- business rules;
- status transitions;
- scheduling calculations;
- idempotency behavior where appropriate.

### API/integration behavior

- registration;
- login;
- authorization;
- availability;
- booking;
- cancellation;
- validation;
- error handling.

### Database behavior

Especially:

> overlapping appointments must be rejected by PostgreSQL.

### Concurrency

The most important test:

- create one bookable slot;
- fire N parallel booking requests;
- exactly one succeeds;
- all conflicting requests fail appropriately;
- run the test repeatedly to detect flakiness.

The concurrency test needs its own setup/cleanup because concurrent requests need committed shared data.

### CI

GitHub Actions must run the test suite automatically.

---

## 17. Error handling

The API should expose one consistent error shape rather than every endpoint inventing its own response format.

The implementation should use custom exception types where that makes the behavior clearer.

The goal is to understand:

```text
domain/service failure
        ↓
known exception
        ↓
API exception handler
        ↓
consistent HTTP response
```

Do not over-engineer an elaborate error framework.

---

## 18. Observability

At minimum, understand and implement sensible application logging.

Be able to answer:

- How would I know requests are failing?
- How would I identify slow endpoints?
- How would I identify database problems?
- How would I investigate a booking conflict?
- What would I log without leaking secrets or sensitive data?

Observability is primarily an interview/engineering learning objective here; it does not need to become a full Prometheus/Grafana stack unless the project naturally reaches that point.

---

## 19. Performance and scalability discussion

The project should remain small, but it should provide material for deeper discussion.

Be able to reason about:

- database bottlenecks;
- connection pooling;
- indexes;
- query plans;
- cache hit/miss behavior;
- cache invalidation;
- concurrent booking requests;
- horizontal scaling of the API;
- what Redis does and does not solve;
- what happens if Redis goes down;
- what happens if PostgreSQL goes down;
- background worker scaling;
- duplicate jobs;
- pagination choices.

The project does **not** need to implement every scaling technique.

The goal is to have a real system from which the tradeoffs can be discussed.

---

## 20. Learning philosophy

Tapas is a backend beginner despite being a strong programmer in Python.

Therefore:

### The AI is a tutor, not a code vending machine.

Preferred workflow:

1. Understand the concept.
2. Understand why the project needs it.
3. Decide what needs to be implemented.
4. Attempt the implementation.
5. Ask for a hint if blocked.
6. Debug together.
7. Review the final implementation.
8. Explain the result back without notes.

Tutorial code should be **typed and understood**, not blindly pasted.

Core logic should not be generated wholesale unless explicitly requested.

For each major day's concept, Tapas should be able to explain the idea in roughly five sentences.

Every day should end with a short log and a commit.

---

## 21. AI collaboration rules

When working with any AI on this project:

- Do not redesign the architecture without a concrete reason.
- Do not introduce technologies just to make the project look impressive.
- Do not generate core logic when a hint would teach more.
- Explain the reasoning before fixing something when learning is the objective.
- Prefer simple, readable implementations.
- Verify current library APIs when behavior matters.
- Do not silently change project scope.
- Keep resume claims strictly tied to implemented evidence.
- Never fabricate benchmark numbers.
- Never claim a technology was used when it was only studied.
- If a design decision changes, record why.
- If a session ends, update `PROJECT_STATUS.md` and `AI_HANDOFF.md`.

---

## 22. Interview-defense standard

A resume bullet is considered defensible only when Tapas can answer all three:

### 1. How does the data flow?

From request to API layer to service/business logic to database/cache/worker and back.

### 2. Why did you choose this design?

What alternatives existed and what tradeoff made the chosen design appropriate?

### 3. What breaks first?

What is the first likely bottleneck, race, failure mode, or operational problem?

If a bullet cannot be defended at this level, it does not belong on the resume yet.

---

## 23. Resume strategy

The project is intended to strengthen shortlisting, but the project must not become an excuse to stop applying.

Applications and project work run in parallel.

### Milestone 1 — Core works

Trigger:

- register;
- login;
- availability;
- booking;
- second overlapping booking rejected by PostgreSQL.

Resume:

**Appointment Scheduling API (in progress)**

Technology:

`Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic`

Claims should be limited to what exists.

### Milestone 2 — Tested / containerized / CI

Trigger:

- concurrency test passes;
- Docker Compose starts the application;
- pytest suite runs;
- GitHub Actions is green.

Technology expands to:

`Docker, pytest, GitHub Actions`

### Milestone 3 — Full target

Trigger:

- Redis caching measured;
- background jobs work;
- idempotency works;
- deployment works.

Target technology:

`Python, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Redis, RQ, Docker, pytest, GitHub Actions`

Target bullets are:

1. Designed and built a REST API (FastAPI, PostgreSQL, SQLAlchemy) for appointment booking, with JWT authentication and role-based access control for customers, providers and admins.
2. Made double-booking impossible at the database level with a PostgreSQL exclusion constraint on time ranges; validated by a concurrency test where `[N]` parallel requests for one slot produce exactly one booking.
3. Cut availability-query latency from `[X]` ms to `[Y]` ms by caching in Redis with invalidation on booking changes.
4. Built background jobs (RQ + Redis) to expire unpaid holds and send reminders, and added idempotency keys so retried booking requests never create duplicates.
5. Containerized with Docker Compose; `[N]` pytest tests run in GitHub Actions CI; deployed on `[host]`.

The placeholders remain placeholders until the measurements/evidence exist.

---

## 24. Timeline philosophy

The project is planned as approximately a **10-day beginner-friendly execution**, not an aggressive six-day sprint.

The earlier plan's pacing is preferred for Days 0–6, with the complete plan supplying Days 7–10.

Important pacing decisions:

- Day 1 remains a FastAPI fundamentals day rather than immediately stacking database + authentication.
- M1 is targeted for **Day 4**, not Day 3.
- Days 1–2 are expected to be the heaviest learning days.
- Days 9–10 provide buffer.
- There should be a lighter evening after Milestone 2.
- Missing a day does not mean restarting the whole project.
- Never miss two days in a row.

The exact day-by-day execution belongs in `APPOINTMENT_SCHEDULING_API_PROJECT_PLAN.md`.

---

## 25. Daily operating rules

Every project day:

1. Build/learn the day's project objective.
2. Commit the work.
3. Write a three-line progress log.
4. Record important concepts in `docs/`.
5. Explain the day's main concept back in your own words.
6. Write one "I should now be able to say..." statement.

Applications remain a parallel track.

The review also recommends protecting time for:

- core CS revision;
- DSA/OA preparation;
- applications/referrals.

The project must not consume the entire job-search day.

---

## 26. Stuck protocol

When stuck:

### First 10–15 minutes
Read the error carefully.

Ask:

- What exactly failed?
- What did I expect?
- What actually happened?
- Which layer is likely responsible?

### Next
Reduce the problem to the smallest reproducible case.

### Then
Check:

1. official documentation;
2. error message / traceback;
3. minimal reproduction;
4. project-specific notes;
5. AI tutor.

Do not spend an unlimited amount of time thrashing.

The previous plan's practical rule is:

> If stuck for roughly 45 minutes, ask for help or search, then move forward.

When asking an AI for help, provide:

- what you intended;
- what you implemented;
- the exact error/output;
- what you already tried;
- your current hypothesis.

---

## 27. What this project should NOT become

Do not optimize for:

- number of endpoints;
- number of tables;
- number of technologies;
- number of lines of code;
- fancy architecture diagrams;
- microservices;
- Kubernetes for its own sake;
- AI features for resume keywords;
- a frontend;
- artificial complexity.

The project succeeds if a backend interviewer can spend 30–45 minutes asking increasingly difficult questions and Tapas can reason through the system because he actually built it.

---

## 28. Source-of-truth hierarchy

When information conflicts:

1. **Actual repository/code and tests** — what has really been built.
2. **PROJECT_STATUS.md** — current execution state.
3. **PROJECT_PLAN.md** — intended execution plan.
4. **This context document** — stable project decisions and philosophy.
5. **AI_HANDOFF.md** — current session context.
6. Older AI conversations — historical reference only.

The repository is ultimately the source of truth for implementation.

The resume is a representation of the repository, not the other way around.

---

## 29. Known decisions that are frozen

These should not be reopened casually:

- Project = Appointment Scheduling API.
- API-only; no frontend.
- Small domain, deep core problem.
- Python + FastAPI.
- PostgreSQL + SQLAlchemy + Alembic.
- JWT authentication.
- Customer / provider / admin roles.
- PostgreSQL exclusion constraint for appointment overlap.
- Four-table model.
- No `provider_profiles` table.
- No separate `idempotency_keys` table.
- Idempotency information lives on bookings.
- Provider timezone lives on users.
- 10-minute configurable holds.
- Tests use short hold durations.
- `/api/v1` API prefix.
- UUIDs as public IDs.
- Redis for measured availability caching.
- RQ + Redis for background jobs.
- Docker Compose.
- pytest.
- GitHub Actions.
- Deployment after the local system is solid.
- Public repository from Day 0.
- Resume claims are milestone-based and evidence-based.

---

## 30. Important unresolved implementation details

The recovered project-review material confirms the decisions above, but the exact contents of the previously generated Claude "complete Project Plan" are not fully reproduced in the imported conversation file.

Therefore, these should **not be guessed**:

- exact four table names;
- exact columns;
- exact 15 endpoint names;
- exact endpoint request/response schemas;
- exact day-by-day task wording;
- exact learning-resource URLs;
- exact deployment host.

Those belong in the canonical `PROJECT_PLAN.md` and should be carried over from the actual plan if/when its complete contents are available.

This is intentional: this context document should preserve decisions, not manufacture missing specifications.

---

## 31. Definition of success

The project is successful when Tapas can truthfully say:

> I built an appointment scheduling backend in Python/FastAPI with PostgreSQL and SQLAlchemy. I designed the booking model and used a PostgreSQL exclusion constraint to make overlapping appointments impossible at the database level. I tested concurrent booking attempts rather than assuming the application-level check was sufficient. I then productionized the service with migrations, automated tests, Docker and CI, and extended it with Redis caching, background jobs and idempotent booking requests. I can explain the data flow, the failure modes, and the tradeoffs behind each of those decisions.

The important part is not the sentence.

The important part is that **the repository, tests, measurements and understanding make the sentence true.**

---

## 32. Current state

**Project Day:** 0  
**Milestone:** Pre-M1  
**Completed:** Nothing yet  
**Current objective:** Establish the repository and project foundations.  
**Next major objective:** Begin Day 1 FastAPI fundamentals.

