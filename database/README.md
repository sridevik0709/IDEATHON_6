# GridGuard Nexus X - Persistent Database Architecture

## 1. Technology Overview

**GridGuard Nexus X** uses **PostgreSQL** as its enterprise persistent storage engine. PostgreSQL was selected for:
- **ACID Transaction Guarantees**: Essential for high-integrity energy accounting and billing reconciliation.
- **Relational Rigor & Integrity**: Strict foreign key constraints across electrical grid topologies (Feeders, Transformers, Substations, Consumer Meters).
- **Semi-Structured Telemetry**: Native `JSONB` support for schema-flexible telemetry envelopes and diagnostic event traces.
- **High-Performance Driver**: Connected via modern `psycopg` (v3) and `SQLAlchemy 2.0` with connection pooling and pre-ping health probes.

---

## 2. Running PostgreSQL

### Option A: Via Docker Compose (Recommended)
From the project root:
```bash
docker compose up -d db
```
This automatically boots PostgreSQL 16 on port `5432`, creates the `gridguard_nexus` database, and executes `database/init.sql`.

### Option B: Local Native PostgreSQL
1. Create database:
   ```sql
   CREATE DATABASE gridguard_nexus;
   ```
2. Initialize tables:
   ```bash
   psql -U postgres -d gridguard_nexus -f database/init.sql
   ```
3. Set your connection string in `backend/.env`:
   ```env
   DATABASE_URL="postgresql+psycopg://postgres:yourpassword@localhost:5432/gridguard_nexus"
   ```

---

## 3. Practical Development Fallback

If PostgreSQL or Docker is not installed on the developer's workstation:
- The backend automatically activates its built-in SQLite development fallback (`gridguard_dev.db`).
- The `/api/v1/health` probe transparently reports `operational_fallback` status:
  ```json
  {
    "database": {
      "name": "PostgreSQL Persistent Storage",
      "status": "operational",
      "details": "Connected to SQLITE persistent storage [Dialect: sqlite]",
      "ready": true
    }
  }
  ```
- This ensures zero developer friction and 100% offline development continuity.
