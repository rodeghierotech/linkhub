# LinkShort V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add secure multi-user link management and owner-scoped analytics while preserving the working V1 application and database.

**Architecture:** Keep FastAPI, SQLAlchemy, Jinja2, and the existing layered modules. Add focused auth and analytics modules, migrate SQLite in place with Alembic, and render backend-prepared aggregates through responsive templates and Chart.js.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2, Jinja2, SQLite, pwdlib/Argon2, user-agents, Chart.js, pytest.

**Spec:** `docs/superpowers/specs/2026-09-24-linkshort-v2-design.md`

## Global Constraints

- Preserve the existing stack and evolve the V1 incrementally.
- Preserve existing data whenever reasonable; never delete the database as a migration strategy.
- Store no IP address and no plaintext password.
- Keep private data owner-scoped at repository and service boundaries.
- Keep analytics aggregation in SQL/services, not templates.
- Do not add out-of-scope infrastructure or product features.

## Review Focus

- A duplicate email with different casing must be rejected.
- A custom alias containing reserved or unsafe values must be rejected without creating a link.
- An authenticated user must receive 404 rather than learning whether another user's link exists.
- An inactive public link must not redirect or create a click.
- A redirect with no referrer must be categorized as Direct and must not store an IP address.

---

### Task 1: Schema and migration foundation

**Files:**
- Modify: `requirements.txt`, `app/database/database.py`, `app/database/models.py`, `app/main.py`
- Create: `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`, `migrations/versions/20260924_01_linkshort_v2.py`
- Test: `tests/test_migration.py`

**Interfaces:**
- Produces: `User`, owner-aware `Link`, `Click`, `run_migrations()` and a V1-to-V2 migration preserving aggregate counts.

- [ ] Write a temporary V1 database migration test that asserts the link row and counter survive.
- [ ] Run it and confirm failure because migration support does not exist.
- [ ] Add models, Alembic configuration, and the idempotent V1-to-V2 migration.
- [ ] Run the migration test and confirm it passes.

### Task 2: Authentication and request security

**Files:**
- Create: `app/auth/repository.py`, `app/auth/service.py`, `app/auth/schemas.py`, `app/auth/dependencies.py`, `app/auth/router.py`, `app/utils/csrf.py`, `app/templates/login.html`, `app/templates/register.html`
- Modify: `app/main.py`, `app/templates/base.html`, `app/static/css/style.css`
- Test: `tests/conftest.py`, `tests/test_auth.py`

**Interfaces:**
- Consumes: `User`, database session dependency.
- Produces: `get_current_user`, `require_user`, registration/login/logout routes, CSRF helpers, and `AuthService`.

- [ ] Write failing integration tests for registration, duplicate normalized email, login, logout, and private-route redirection.
- [ ] Implement password hashing, session handling, legacy-link claiming, and CSRF validation.
- [ ] Run auth tests until all pass without weakening assertions.

### Task 3: Owner-scoped link management and click capture

**Files:**
- Modify: `app/links/repository.py`, `app/links/service.py`, `app/links/schemas.py`, `app/links/router.py`, `app/utils/short_code.py`, `app/static/js/app.js`
- Create: `app/utils/user_agent.py`, `app/templates/links.html`, `app/templates/link_unavailable.html`
- Test: `tests/test_links.py`

**Interfaces:**
- Consumes: `require_user`, `Link`, `Click`, CSRF validation.
- Produces: owner-scoped create/list/detail/delete/toggle operations, alias validation, and public click recording.

- [ ] Write failing tests for automatic and custom aliases, duplicates, reserved aliases, cross-user access, redirects, click rows, inactive links, and missing links.
- [ ] Implement the smallest repository/service/router changes that satisfy the tests.
- [ ] Run link tests and the full suite.

### Task 4: Analytics and SaaS interface

**Files:**
- Create: `app/analytics/repository.py`, `app/analytics/service.py`, `app/analytics/schemas.py`, `app/templates/link_detail.html`
- Modify: `app/templates/dashboard.html`, `app/templates/base.html`, `app/links/router.py`, `app/static/css/style.css`, `app/static/js/app.js`
- Test: `tests/test_analytics.py`

**Interfaces:**
- Consumes: owner-scoped links and clicks.
- Produces: `AnalyticsService.dashboard(user_id)` and `AnalyticsService.link_detail(user_id, link_id)` with pre-aggregated chart-ready data.

- [ ] Write failing tests using literal expected totals and distributions for two users.
- [ ] Implement SQL aggregate queries and service mapping.
- [ ] Build dashboard and detail templates with responsive cards, tables, and Chart.js datasets.
- [ ] Run analytics tests and the full suite.

### Task 5: Documentation and end-to-end verification

**Files:**
- Modify: `README.md`, `requirements.txt`

**Interfaces:**
- Consumes: all completed routes, migration commands, and test commands.
- Produces: reproducible local setup, migration, run, and test instructions.

- [ ] Document configuration, schema, migration, execution, and tests.
- [ ] Install dependencies and run `alembic upgrade head` against the existing database.
- [ ] Run the complete pytest suite and resolve failures through failing regression tests.
- [ ] Start Uvicorn, request key pages, and confirm startup and HTTP behavior.

