# Database & Migration Strategy

## Engine & Persistence

- **Primary Database Engine:** PostgreSQL 15.
- **Driver:** `psycopg` (version 3).
- **Environment Targeting:**
  - **Local Development:** runs via `postgres:15` Docker container (see `.devcontainer/docker-compose.yml`).
  - **Production:** Managed PostgreSQL service (e.g., Render PostgreSQL).
- **Connection Configuration:** Configured dynamically via environment variables (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`). See `.env.example`.

## Multi-Tenancy

- **Tenant Isolation Policy:** The target schema enforces strict tenant separation. Most business entities (Shops, Clients, Designs, Orders) will inherit from `backend.core.models.BaseModelWithTenant`, containing a cascading foreign key to `Tenant`.
- **Identity Sharing:** The `User` model is tenant-agnostic to support users belonging to multiple shops (e.g., a supplier admin).

## Migration Strategy & Policies

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
  - Business domain models (Shops, Works, Billing) are currently pending Phase 3-5 implementation.
