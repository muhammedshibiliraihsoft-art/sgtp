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
- **Identity sharing:** The `User` model supports users belonging to multiple Shops through the `TenantMember` membership model; ordinary Shop users do not receive cross-Shop visibility. Main Supplier cross-Shop access is explicitly backend-authorized via `ShopRolePolicy`.
- **Isolation:** Shop-scoped foreign keys, querysets, permissions, and APIs must enforce isolation for direct IDs, lists, search, filters, ordering, pagination, counts, aggregates, autocomplete, and nested/foreign-key traversal.

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
