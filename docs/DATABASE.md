# Database & Migration Strategy

## Engine & Persistence

- **Primary Database Engine:** PostgreSQL 15.
- **Driver:** `psycopg` (version 3).
- **Environment Targeting:**
  - **Local Development:** runs via `postgres:15` Docker container (see `.devcontainer/docker-compose.yml`).
  - **Production:** Managed PostgreSQL service (e.g., Render PostgreSQL).
- **Connection Configuration:** Configured dynamically via environment variables (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`). See `.env.example`.

## V1 Shop Tenancy and Legacy Tenant Input

- **Business boundary:** Shop is the V1 tenant/workspace and owns its permitted business records, including External Supplier records.
- **Top-level owner:** V1 has exactly one Supplier / Main Admin above the Shops; this is not a multi-supplier tenancy model.
- **External Suppliers:** An External Supplier is a non-user, non-tenant, shop-owned business record. It belongs to exactly one Shop and is never a global/shared supplier record.
- **Technical Mapping:** The existing `Tenant` model serves as the technical representation for the `Shop` entity. T3-01 verified this structural safety because no data existed to corrupt. A `Supplier` model manages the singleton Main Supplier constraint.
- **Current identity/membership schema:** T3-04A adds immutable `user_code` (unique, `U-` plus 16 unambiguous uppercase characters), nullable unique email, case-insensitive canonical email uniqueness, required nonblank `first_name`, and database guards for User ID format and Main Supplier contacts. Published T3-04B User-Scope migration `accounts.0005_user_shop_ownership` adds nullable-at-schema/required-at-commit `User.owning_shop`, backfills only a determinable single Shop from all membership history, and installs PostgreSQL guards against missing/mismatched or changed ownership. UUID remains unchanged; Main Supplier accounts have no owning Shop. Existing multi-Shop/unowned ordinary accounts stop migration for explicit remediation.
- **Migration `accounts.0004_t304a_global_identity`:** checks existing names, case-insensitive email collisions, E.164 phone shape, active Shop Admin contacts, and Main Supplier contacts before data changes. It canonicalizes email to trimmed lowercase, converts blank email/phone to NULL, and backfills only missing User IDs. It does not invent contacts or names. Preserve UUIDs, password hashes, memberships, audit references, `auth_version`, and session semantics. The inspected local database was empty; other environments require the same preflight before applying.
- **Published migration `accounts.0005_user_shop_ownership`:** scans soft-removed membership history as well as current memberships. It assigns an ordinary User only when exactly one owning Shop is determinable, and aborts with affected UUIDs for multi-Shop or unowned accounts. It adds deferred ownership and User/Shop membership consistency checks plus ownership immutability. Local development preflight was against an empty DB; GitHub CI applied/validated migrations on its disposable PostgreSQL database. Neither is evidence about shared/staging/production data.
- **Isolation:** Shop-scoped foreign keys, querysets, permissions, and APIs must enforce isolation for direct IDs, lists, search, filters, ordering, pagination, counts, aggregates, autocomplete, and nested/foreign-key traversal.

## Migration Strategy & Policies

### Implemented T3-02A schema additions

- `accounts.0003` adds nullable User phone (canonical E.164, database-enforced uniqueness for non-NULL User login phones), nullable preferred locale, `system|light|dark` appearance defaulting to `system`, `must_change_password`, and `auth_version`. Existing phone values remain NULL; UUID identity, required email, and memberships are preserved.
- `tenants.0008` adds nullable Shop locale, timezone, and currency; no defaults are inferred or backfilled. Main Supplier Admin is the current Shop-settings authority. Ordinary globally scoped Shop serializers omit these fields.
- T3-04 adds reusable queryset/permission behavior and test-only proof coverage; it creates no production model, schema change, migration, or dependency. `BaseModelWithTenant.tenant` remains nullable; future concrete Shop-owned models must justify nullability, constraints, and indexes from their domain/data requirements.
- **Current account relationship:** one ordinary `User` is owned by one Shop and has membership in that same Shop; Main Supplier accounts are global and have no Shop membership requirement. `TenantMember` stores the role/lifecycle and remains the future host for membership-scoped Work Functions. T3-04C must analyze function storage, constraints, indexes, lifecycle/history, and safe migration needs before choosing a representation.
- Existing T3-04B rules enforce one or two active ADMIN memberships per Shop, atomic first-account/ADMIN Shop creation, owning-Shop User deactivation protection, and membership lifecycle/capacity behavior. T3-04C still owns Work Function persistence. Shared/staging/production ownership preflight has NOT been performed and no migration has been applied to those environments; never guess ownership if a future preflight finds multi-Shop or unowned ordinary accounts.
- Later business migrations preserve historical measurement versions and financial values. Locale changes must not rewrite canonical source data; theme changes have no business-data effect; currency changes must never reinterpret historical transactions.
- Prefer additive, forward-only migrations. Each task documents empty-database replay, upgrade compatibility, constraints/indexes and recovery. Retention duration, currency changes after finance, and other unresolved policy remain `BUSINESS DECISION REQUIRED`.

### 1. Forward-Only Migrations
- **Policy:** Migrations must strictly move forward in production. Once a migration has been applied and merged into `main`, it **must not** be edited, deleted, or squashed manually in a way that breaks existing databases.
- **Rollback Expectations:** Instead of rolling back applied migrations via `migrate <app> <previous_migration>`, the preferred recovery strategy is a **corrective forward migration** (e.g., adding a field back or reversing a data transformation in a new migration file).

### 2. Schema Modification Rules
- **No Manual Schema Changes:** The database schema is strictly managed by Django's ORM. Direct SQL schema manipulation (e.g., via `psql`) is prohibited unless executed via a `RunSQL` migration operation.
- **Migration Review:** Every PR containing migration files must be reviewed for destructive operations (e.g., dropping columns, changing types unsafely). Destructive operations should be planned carefully to avoid downtime.

### 3. Backup Expectations
- **Production:** The managed PostgreSQL provider must have automated daily backups and Point-in-Time Recovery (PITR) enabled.
- **Before Major Migrations:** A manual snapshot must be triggered before applying migrations that contain significant data transformations.

### 4. Test Database
- The test suite uses the standard Django test runner which dynamically creates a separate `test_<DB_NAME>` database during test execution. 
- The test database relies on the same base `DATABASES` configuration defined in `backend/config/settings/base.py`, ensuring environment parity.

## Validation & State

- **Empty Database Setup:** Verified. Running `python manage.py migrate` on a fresh, empty PostgreSQL database successfully applies all foundational migrations (Auth, Tenants, Token Blacklist) without error.
- **Current Data Models:** 
  - `User` (TimeStamped, no soft-delete)
  - `Tenant` (TimeStamped, soft-delete enabled)
  - The Shop entity/settings foundation exists; tailoring, Client, Work, Billing, and other business models remain pending Phase 3-5 tasks.
