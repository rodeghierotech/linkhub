# LinkShort V2 Design

## Goal

Evolve the existing FastAPI/Jinja2 URL shortener into a local, multi-user link management application without replacing the current stack or discarding V1 data.

## Architecture

The application keeps the existing router, service, and repository boundaries. Authentication lives in `app/auth`, analytics queries live in `app/analytics`, and link ownership remains in `app/links`. SQLAlchemy models remain centralized so relationships and migrations are easy to inspect.

Authentication uses a signed client-side session cookie containing only `user_id` and a CSRF token. Passwords use Argon2 through `pwdlib`. Every private query includes the authenticated user id, so authorization is enforced below the template layer.

## Data migration

Alembic upgrades the V1 `links` table in place, adds `users` and `clicks`, and preserves the old aggregate counter as `legacy_click_count`. Existing links remain temporarily unowned and are claimed by the first registered user. This avoids inventing click timestamps or analytics dimensions that V1 never collected.

New redirects create one `Click` row containing timestamp, normalized referrer category, raw referrer, raw User-Agent, browser, operating system, and device type. No IP address is stored.

## Routes and flows

- `/` redirects authenticated users to `/dashboard` and guests to `/login`.
- `/register`, `/login`, and `/logout` manage session authentication.
- `/dashboard` shows owner-scoped totals, seven-day series, device/browser/referrer distributions, and recent links.
- `/links` lists and creates owner-scoped links.
- `/links/{id}` shows analytics only when the authenticated user owns the link.
- POST routes create, toggle, and delete links with CSRF validation.
- `/r/{short_code}` remains public, rejects inactive links, records a detailed click, and redirects.

## Validation and security

Emails are normalized and unique. Passwords are never persisted directly. Alias validation permits lowercase letters, numbers, hyphens, and underscores, requires 3-32 characters, and rejects reserved route names. URL validation continues to use Pydantic `HttpUrl`. Jinja2 escaping remains enabled. Session cookies are HTTP-only, SameSite=Lax, and optionally Secure through configuration.

## Interface

The existing indigo visual language is retained and expanded into a responsive SaaS-style shell with sidebar navigation. Chart.js is loaded from its CDN only on authenticated analytics pages. Templates receive already-aggregated chart data; they do not perform database work.

## Testing

Pytest integration tests use a temporary SQLite database and the real FastAPI application. They cover registration, login, link creation, aliases, redirects and click recording, inactive links, missing links, and cross-user authorization.

