# GRIDGUARD NEXUS X
### Software-Only Electricity Intelligence and Investigation Platform

[![Milestone](https://img.shields.io/badge/Milestone-Level%202%3A%20Data%20Foundation-cyan)](#)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.14-009688)](#)
[![Validation](https://img.shields.io/badge/Validation-Pydantic%20v2-e91e63)](#)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2016%20%7C%20React%2019-black)](#)
[![Database](https://img.shields.io/badge/Storage-PostgreSQL%20%7C%20SQLAlchemy%202.0-336791)](#)
[![Tests](https://img.shields.io/badge/Tests-Pytest%20(26)%20%2B%20Vitest%20(6)%20Passing-brightgreen)](#)

---

## 1. Project Overview

**GridGuard Nexus X** is an enterprise-grade software intelligence platform developed for national-level electrical distribution networks. The platform identifies non-technical losses (electricity theft, meter tampering, and unmetered loads), reconciles substation energy balances, and produces evidence-backed audit trails for utility investigators.

> **Active Milestone**: **LEVEL 2: DATA FOUNDATION & REPEATABLE DEMONSTRATION SCENARIOS**  
> Features 15 PostgreSQL relational entities, deterministic synthetic data generation for substations, feeders, distribution transformers, and household aggregate meters, a multi-source data adapter architecture, data quality audit rules, and 5 repeatable demonstration scenarios with interactive UI execution.

---

## 2. Technology Stack

| Layer | Technologies Selected | Role |
| :--- | :--- | :--- |
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript 5, Tailwind CSS 4, Lucide Icons | Responsive electricity intelligence dashboard shell |
| **Backend** | Python 3.14, FastAPI 0.162, Uvicorn | High-throughput asynchronous ASGI API gateway |
| **Validation** | Pydantic v2, Pydantic Settings | Strict input schema validation & environment contracts |
| **Database** | PostgreSQL 16 (via `psycopg` 3.3 and `SQLAlchemy 2.0`) with offline SQLite dev fallback | Persistent telemetry and audit log storage |
| **Testing** | Pytest 9.2 (Backend) & Vitest 5 + Testing Library (Frontend) | Unit, integration, and contract tests |

---

## 3. Project Structure

```text
IDEATHON/
├── backend/                        # Python FastAPI Application
│   ├── app/
│   │   ├── main.py                 # FastAPI application factory and ASGI entrypoint
│   │   ├── config.py               # Pydantic Settings & environment validation
│   │   ├── api/                    # API Routing Layer
│   │   │   ├── router.py           # Top-level API router
│   │   │   └── v1/
│   │   │       ├── api.py          # API v1 router aggregation
│   │   │       └── endpoints/
│   │   │           ├── health.py   # System health, storage status & uptime
│   │   │           ├── version.py  # Platform version & capability introspection
│   │   │           └── validation.py # Request validation & error demonstration
│   │   ├── core/                   # Centralized Error & Exception Handling
│   │   │   ├── exceptions.py       # Custom application exceptions
│   │   │   ├── handlers.py         # 100% consistent JSON error handlers
│   │   │   └── responses.py        # Standardized success response envelopes
│   │   ├── schemas/                # Pydantic Request/Response Models
│   │   │   ├── common.py           # Standard envelope schemas (success/error/meta)
│   │   │   └── health.py           # Subsystem health & validation schemas
│   │   ├── database/               # Database Engine & Session Management
│   │   │   ├── base.py             # Declarative Base & Timestamp mixins
│   │   │   └── session.py          # Engine pool & connection probe
│   │   ├── accounting/             # [RESERVED LEVEL 2] Energy Accounting Engine
│   │   │   └── placeholder.py      # Strict boundary guard
│   │   ├── data_processing/        # [RESERVED LEVEL 2] Telemetry Stream Processing
│   │   │   └── placeholder.py      # Strict boundary guard
│   │   └── ai_services/            # [RESERVED LEVEL 3] Forensic Theft Investigator
│   │       └── placeholder.py      # Strict boundary guard
│   ├── tests/                      # Pytest Test Suite
│   │   ├── conftest.py             # Test client fixtures
│   │   ├── test_health.py          # Health check endpoint tests
│   │   ├── test_version.py         # Version endpoint tests
│   │   ├── test_errors.py          # Error envelope and validation tests
│   │   └── test_config.py          # Configuration and settings tests
│   ├── requirements.txt            # Python dependencies
│   ├── pyproject.toml              # Pytest and build configuration
│   └── .env.example                # Backend environment template
├── frontend/                       # Next.js 16 + React 19 Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx          # Root layout & mission-control typography
│   │   │   ├── page.tsx            # Main page routing to OverviewDashboard
│   │   │   └── globals.css         # Tailwind CSS styling & dark grid theme
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx      # Top bar with live connection pill & clock
│   │   │   │   └── Sidebar.tsx     # Navigation & subsystem status drawer
│   │   │   ├── dashboard/
│   │   │   │   ├── OverviewDashboard.tsx # Main dashboard orchestrator
│   │   │   │   ├── SystemHealthCard.tsx  # Live backend latency & storage metrics
│   │   │   │   ├── ReadinessGrid.tsx     # Subsystem readiness matrix
│   │   │   │   └── ValidationConsole.tsx # Interactive live validation test bench
│   │   │   └── ui/
│   │   │       ├── Badge.tsx       # Status pill badges
│   │   │       ├── LoadingSpinner.tsx # Grid pulse loading states
│   │   │       └── ErrorAlert.tsx  # Consistent error presentation
│   │   ├── lib/
│   │   │   ├── api.ts              # Typed API client with latency tracking
│   │   │   └── config.ts           # Safe public environment configuration
│   │   └── types/
│   │       └── api.ts              # TypeScript interfaces mirroring Pydantic models
│   ├── tests/                      # Frontend Vitest Suite
│   │   ├── api.test.ts             # API client & error handling tests
│   │   └── components.test.tsx     # Component render tests
│   ├── package.json
│   ├── tsconfig.json
│   └── vitest.config.ts
├── database/                       # PostgreSQL Storage Layer
│   ├── init.sql                    # Initial schema, extensions, and tables
│   └── README.md                   # Database setup & connection guide
├── documentation/                  # Project Specifications
│   ├── ARCHITECTURE.md             # Architecture diagram & module decoupling
│   ├── API_SPECIFICATION.md        # REST API endpoints & response schemas
│   └── ACCEPTANCE_REPORT.md        # Level 1 acceptance test verification records
├── docker-compose.yml              # PostgreSQL container configuration
├── .env.example                    # Monorepo environment template
├── .gitignore                      # Git exclusion rules
└── README.md                       # Main documentation
```

---

## 4. Quickstart: Installation & Development Run

### Prerequisites
- **Python**: 3.11+ (Python 3.14 verified)
- **Node.js**: v20+ (Node.js v24.11 verified)
- **Docker** (Optional, for running PostgreSQL locally)

---

### Step 1: Set Up Backend

1. Navigate to the backend directory and create a virtual environment:
   ```bash
   cd backend
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     source .venv/bin/activate
     ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create configuration file:
   ```bash
   cp .env.example .env
   ```

5. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *The backend will be running at `http://localhost:8000`.*  
   *Interactive OpenAPI docs: `http://localhost:8000/docs`.*

---

### Step 2: Set Up Frontend

1. In a new terminal window, navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   ```

2. Configure environment:
   ```bash
   cp .env.example .env.local
   ```

3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
   *The frontend dashboard will be available at `http://localhost:3000`.*

---

### Step 3: Run Acceptance Tests

#### Backend Pytest Suite
```bash
cd backend
.\.venv\Scripts\pytest tests -v
```
*(All 9 tests pass with 100% coverage of health, version, Pydantic validation, and error envelopes).*

#### Frontend Vitest Suite
```bash
cd frontend
npm test
```
*(All 6 component and API client tests pass).*

#### Frontend Production Build Verification
```bash
cd frontend
npm run build
```

---

## 5. Architectural Boundaries & Level 1 Compliance

1. **Software-Only Intelligence**: Zero physical hardware or appliance-level monitoring is required or assumed.
2. **Zero Fabricated Statistics**: The Level 1 Overview Dashboard explicitly avoids fake statistics or mocked theft charts, strictly displaying live system telemetry, persistent storage states, and real-time Pydantic validation consoles.
3. **Strict Separation of Concerns**:
   - `accounting` logic is isolated in `backend/app/accounting/` (guarded for Level 2).
   - `data_processing` streams are isolated in `backend/app/data_processing/` (guarded for Level 2).
   - `ai_services` forensic detection is isolated in `backend/app/ai_services/` (guarded for Level 3).
   - `database` session and persistence operations are isolated in `backend/app/database/`.
4. **Secrets Protection**: Frontend code only consumes public `NEXT_PUBLIC_` variables. No database credentials or signing keys are exposed to the client.
