# GRIDGUARD NEXUS X
### Software-Only Electricity Intelligence and Investigation Platform

[![Milestone](https://img.shields.io/badge/Milestone-Level%205%3A%20Evidence%20Traceability%20%26%20What--If%20Analysis-indigo)](#)
[![Backend](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.14-009688)](#)
[![Validation](https://img.shields.io/badge/Validation-Pydantic%20v2-e91e63)](#)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2016%20%7C%20React%2019-black)](#)
[![Database](https://img.shields.io/badge/Storage-PostgreSQL%20%7C%20SQLAlchemy%202.0-336791)](#)
[![Tests](https://img.shields.io/badge/Tests-Pytest%20(59)%20%2B%20Vitest%20(11)%20Passing-brightgreen)](#)

---

## 1. Project Overview

**GridGuard Nexus X** is an enterprise-grade software intelligence platform developed for national-level electrical distribution networks. The platform identifies non-technical losses (electricity theft, meter tampering, and unmetered loads), reconciles substation energy balances, and produces evidence-backed audit trails for utility investigators.

> **Active Milestone**: **LEVEL 5: EVIDENCE TRACEABILITY AND WHAT-IF ANALYSIS**  
> Features an interactive **Evidence Investigation Graph** linking detected discrepancies through source measurements, data-quality findings, competing hypotheses, and verification actions to confirmed outcomes; a **What-If Simulation Sandbox** supporting 5 repeatable operational scenarios; **Before-and-After Differential Reporting** tracking mathematical energy balance shifts; and strict **Data Protection Immutability Firewalls** guaranteeing production telemetry is never altered by hypothetical simulations.

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
│   │   │           ├── validation.py # Request validation & error demonstration
│   │   │           ├── accounting.py # Level 3 Energy Accounting & Discrepancy Explorer
│   │   │           ├── investigation.py # Level 4 Multi-Hypothesis & AI Assistant
│   │   │           └── what_if.py  # Level 5 Evidence Graph & What-If Simulation
│   │   ├── core/                   # Centralized Error & Exception Handling
│   │   │   ├── exceptions.py       # Custom application exceptions
│   │   │   ├── handlers.py         # 100% consistent JSON error handlers
│   │   │   └── responses.py        # Standardized success response envelopes
│   │   ├── schemas/                # Pydantic Request/Response Models
│   │   │   ├── common.py           # Standard envelope schemas (success/error/meta)
│   │   │   ├── health.py           # Subsystem health & validation schemas
│   │   │   ├── accounting.py       # Energy accounting & meter lookup schemas
│   │   │   ├── investigation.py    # Hypotheses & AI inquiry schemas
│   │   │   └── what_if.py          # Level 5 Graph & What-If simulation schemas
│   │   ├── database/               # Database Engine & Session Management
│   │   │   ├── base.py             # Declarative Base & Timestamp mixins
│   │   │   ├── models.py           # 15 Core Level 2 database entities
│   │   │   └── session.py          # Engine pool & connection probe
│   │   ├── accounting/             # Level 3 Deterministic Accounting & Audit Engine
│   │   │   ├── engine.py           # Energy balancing equations
│   │   │   └── audit_rules.py      # 10-point data quality audit engine
│   │   ├── ai_services/            # Level 4 AI-Assisted Investigation
│   │   │   ├── hypothesis_engine.py# 6-cause forensic hypothesis generator
│   │   │   ├── prioritization.py   # Explainable 6-factor ranking engine
│   │   │   ├── assistant.py        # Natural language inquiry & rule fallback
│   │   │   └── guardrails.py       # Safety interceptor & hallucination defense
│   │   └── investigation/          # Level 5 Traceability & What-If Sandbox
│   │       ├── graph_engine.py     # Directed evidence graph builder
│   │       └── what_if_engine.py   # Isolated simulation & delta calculation engine
│   ├── tests/                      # Pytest Test Suite (59 Tests)
│   │   ├── conftest.py             # Test client fixtures
│   │   ├── test_health.py          # Health check endpoint tests
│   │   ├── test_version.py         # Version endpoint tests
│   │   ├── test_errors.py          # Error envelope and validation tests
│   │   ├── test_config.py          # Configuration and settings tests
│   │   ├── test_database_schema.py # Schema entities persistence tests
│   │   ├── test_synthetic_generator.py # Synthetic generator tests
│   │   ├── test_scenarios.py       # 5 demonstration scenarios tests
│   │   ├── test_data_integrity.py  # Data integrity audit tests
│   │   ├── test_accounting_engine.py # Level 3 accounting engine tests
│   │   ├── test_ai_investigation.py # Level 4 hypothesis & AI assistant tests
│   │   └── test_what_if.py         # Level 5 Evidence graph & what-if tests
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
│   │   │   │   ├── ValidationConsole.tsx # Interactive live validation test bench
│   │   │   │   ├── MeterLookupView.tsx   # Level 3 Cluster Meter Lookup
│   │   │   │   ├── DiscrepancyExplorerView.tsx # Level 3 Energy Balance Explorer
│   │   │   │   ├── ScenariosExplorerView.tsx # Level 2 Scenarios Explorer
│   │   │   │   ├── AiInvestigationView.tsx # Level 4 Multi-Hypothesis & AI Assistant
│   │   │   │   ├── EvidenceGraphView.tsx # Level 5 Interactive Evidence Graph
│   │   │   │   └── WhatIfSimulatorView.tsx # Level 5 What-If Simulation Sandbox
│   │   │   └── ui/
│   │   │       ├── Badge.tsx       # Status pill badges
│   │   │       ├── LoadingSpinner.tsx # Grid pulse loading states
│   │   │       └── ErrorAlert.tsx  # Consistent error presentation
│   │   ├── lib/
│   │   │   ├── api.ts              # Typed API client with latency tracking
│   │   │   └── config.ts           # Safe public environment configuration
│   │   └── types/
│   │       └── api.ts              # TypeScript interfaces mirroring Pydantic models
│   ├── tests/                      # Frontend Vitest Suite (11 Tests)
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
│   └── ACCEPTANCE_REPORT.md        # Level 1-5 acceptance test verification records
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
*(All 59 tests pass across Levels 1 through 5 in < 1.5s).*

#### Frontend Vitest Suite
```bash
cd frontend
npm test
```
*(All 11 component and API client tests pass).*

#### Frontend Production Build Verification
```bash
cd frontend
npm run build
```

---

## 5. Architectural Boundaries & Data Protection Guarantees

1. **Software-Only Intelligence**: Zero physical hardware or appliance-level monitoring is required or assumed.
2. **Deterministic Energy Accounting**: Unaccounted energy is computed via strictly audited equations ($E_{\text{unaccounted}} = E_{\text{in}} - E_{\text{downstream}} - E_{\text{technical}}$) with nested boundary double-counting guards.
3. **Multi-Hypothesis Forensic Matrix**: Discrepancies are evaluated across 6 competing causes (telemetry lag, GIS mapping errors, unit/interval mismatches, technical losses, and unmetered consumption) without premature accusations.
4. **Data Protection & Telemetry Immutability**:
   - Production measurements in `distribution_boundary_readings` and `consumption_readings` are **never overwritten** during what-if analysis.
   - What-if simulations run in isolated memory contexts and persist results separately in `scenario_runs` and `audit_logs`.
   - Hypothetical simulations cannot automatically resolve or close real utility cases (`InvestigationCase`).
5. **Secrets Protection**: Frontend code only consumes public `NEXT_PUBLIC_` variables. No database credentials or LLM signing keys are exposed to the browser.
