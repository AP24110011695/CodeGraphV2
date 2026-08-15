# CodeGraph v2 — Backend Implementation Roadmap

> **Execution model:** Each day, run: `Read BACKEND.md and execute Phase N.`
> The coding agent must read this file, inspect the actual repository, determine what has already been implemented, execute the requested phase completely, verify its own work, update the phase status table, and stop — without waiting for a human to review ordinary implementation details. See **Autonomous Execution Protocol** below for the full procedure the agent must follow on every invocation.

---

## What CodeGraph v2 Does

CodeGraph v2 is an AI-powered codebase intelligence platform. Users upload or connect a Git repository. The backend:

1. Ingests the repository (zip upload or Git clone).
2. Parses every source file — extracting functions, classes, imports, exports, call graphs.
3. Detects language/frameworks and builds a dependency graph.
4. Generates vector embeddings for semantic code search.
5. Exposes a RAG-based AI assistant that can answer questions about the codebase with code-grounded context.
6. Streams AI responses and exposes real-time processing status.

**Core user workflows:**
- Upload repo → wait for indexing → explore dependency graph
- Ask AI questions about the repo ("What does `AuthService` do?", "Where is rate limiting implemented?")
- Browse files with semantic search
- View architecture diagrams auto-generated from the dependency graph

---

## Autonomous Execution Protocol

This roadmap is built to be executed by an AI coding agent without a human reviewing every phase. When instructed to execute a phase, the coding agent must, in order:

1. Read this entire file (or at minimum this section, the Phase Dependency Map, the API Contract, and the target phase).
2. Locate the requested phase.
3. Read the phase completely, including Prerequisites and Current Repository Expectations.
4. Inspect the actual repository on disk — do not assume it matches the roadmap. The repository is the source of truth for what is physically implemented; this roadmap is the source of truth for the architectural plan.
5. Determine what has actually been completed, including work that may have been done out of order or differently than described.
6. Compare repository state against this roadmap and identify inconsistencies.
7. Adapt to the actual repository where it differs from the roadmap in a sound way — reuse working code, don't blindly overwrite it because a filename or structure differs from what's written here.
8. Implement the entire phase as scoped below.
9. Write or update the tests specified in the phase's Testing section (and any additional tests genuinely needed to cover the new work).
10. Run the relevant tests.
11. Run lint and type checks.
12. Run build checks where applicable.
13. Fix any failures the agent's own changes caused.
14. Re-run verification after fixes.
15. Perform a final self-review of the diff.
16. Verify every item in Completion Criteria is actually true, not just plausible.
17. Update the API Contract section in this file if the phase changed a request/response schema, error format, auth behavior, or SSE/event format — then note that `FRONTEND.md` should be checked against the change.
18. Update the phase's row in **Phase Status** from `NOT STARTED`/`IN PROGRESS` to `COMPLETED` (or `BLOCKED`, see below).
19. Produce a concise Phase Completion Report (format below).
20. Stop. Do not start the next phase automatically, and do not ask the user to manually re-verify things the agent can verify itself.

### Failure handling

If tests, lint, type checks, or build fail, the agent diagnoses and fixes the problem itself using this loop:

```
IMPLEMENT → TEST → FAIL? → DIAGNOSE → FIX → TEST AGAIN → PASS → FINAL REVIEW
```

Only stop with an unresolved blocker when the problem genuinely requires something the agent cannot provide for itself (e.g. a missing external credential, a service that cannot be reached in this environment). When that happens:
- Mark the phase `BLOCKED` in the Phase Status table, not `COMPLETED`.
- State plainly what is blocking progress and what remains to unblock it.
- Do not fabricate a passing result.

### What the agent should not do

- Should not ask the user to manually verify things the agent can verify itself (running tests, checking a response body, confirming a file exists).
- Should not stop mid-phase to ask permission to continue implementing already-specified work.
- Should not automatically begin the next phase after finishing the requested one — phase progression is user-controlled.
- Should not invent architectural decisions that contradict this roadmap or `API Contract — Source of Truth` below; where a genuine gap exists, the agent should choose the simplest solution consistent with the existing architecture, implement it, and document the decision in its completion report so later phases can rely on it.

### Phase Completion Report format

At the end of every phase execution, produce a concise report:

```
### Phase
Phase N — [Name]

### Implemented
Short list of what was built.

### Files Changed
Short list.

### Tests
What was run.

### Verification
Build/lint/typecheck/manual verification performed.

### Result
COMPLETED / BLOCKED

### Notes
Only important information — architectural decisions made, deviations from the roadmap and why, anything the next phase should know.
```

Do not produce an enormous explanation in addition to this — the roadmap already contains the detailed plan; the report only needs to confirm what happened.

---

## Phase Status

| Phase | Name | Status |
|---|---|---|
| 1 | Project Foundation & Tooling | COMPLETED |
| 2 | Configuration, Logging & App Bootstrap | COMPLETED |
| 3 | Database Connection & Migration Foundation | COMPLETED |
| 4 | Core Domain Data Models & Schema | COMPLETED |
| 5 | Repository Upload Ingestion | COMPLETED |
| 6 | Git Clone Ingestion & Repository CRUD API | COMPLETED |
| 7 | File Extraction, Hashing & Ignore Patterns | COMPLETED |
| 8 | Language & Framework Detection | COMPLETED |
| 9 | Parser Abstraction, Python & Generic Parsing | COMPLETED |
| 10 | TypeScript/JavaScript Parsing & Import Resolution | NOT STARTED |
| 11 | Dependency Graph Construction & API | NOT STARTED |
| 12 | Code Chunking & Embedding Provider Abstraction | NOT STARTED |
| 13 | Vector Indexing & Semantic Search API | NOT STARTED |
| 14 | LLM Provider Abstraction & Prompt Management | NOT STARTED |
| 15 | RAG Pipeline, Chat History & Chat API | NOT STARTED |
| 16 | Files & Status API Completion | NOT STARTED |
| 17 | API Contract Consistency Audit & OpenAPI Docs | NOT STARTED |
| 18 | Background Job System (Celery + Redis) | NOT STARTED |
| 19 | Real-time Updates (SSE) | NOT STARTED |
| 20 | API Key Authentication & Key Management | NOT STARTED |
| 21 | Rate Limiting & Security Hardening | NOT STARTED |
| 22 | Observability, Metrics & Health Checks | NOT STARTED |
| 23 | Unit & Integration Testing Suite | NOT STARTED |
| 24 | End-to-End Testing & Coverage Enforcement | NOT STARTED |
| 25 | Production Readiness & Docker | NOT STARTED |

Update a row to `IN PROGRESS` when starting a phase, and to `COMPLETED` only once every completion criterion and verification step in that phase actually passes. Use `BLOCKED` (with an explanation in the completion report) if a genuine blocker prevents finishing. Do not rewrite historical status entries except to move a phase forward through this lifecycle.

---

## Phase Dependency Map

```
Phase 1  Project Foundation & Tooling
    ↓
Phase 2  Configuration, Logging & App Bootstrap
    ↓
Phase 3  Database Connection & Migration Foundation
    ↓
Phase 4  Core Domain Data Models & Schema             ─── internal: all ORM models
    ↓
Phase 5  Repository Upload Ingestion                   ─── public: upload endpoint
    ↓
Phase 6  Git Clone Ingestion & Repository CRUD API      ─── public: repository CRUD
    ↓
Phase 7  File Extraction, Hashing & Ignore Patterns
    ↓
Phase 8  Language & Framework Detection
    ↓
    ├──→ Phase 9  Parser Abstraction, Python & Generic Parsing
    │        ↓
    │    Phase 10 TypeScript/JavaScript Parsing & Import Resolution
    │        ↓
    │    Phase 11 Dependency Graph Construction & API   ─── public: graph API
    │        ↓
    │    Phase 12 Code Chunking & Embedding Provider Abstraction
    │        ↓
    │    Phase 13 Vector Indexing & Semantic Search API ─── public: search API
    │        ↓
    │    Phase 14 LLM Provider Abstraction & Prompt Management
    │        ↓
    │    Phase 15 RAG Pipeline, Chat History & Chat API ─── public: chat API
    │        ↓
    └──→ Phase 16 Files & Status API Completion
             ↓
         Phase 17 API Contract Consistency Audit & OpenAPI Docs
             ↓
         Phase 18 Background Job System (Celery + Redis)
             ↓
         Phase 19 Real-time Updates (SSE)                ─── public: progress stream
             ↓
         Phase 20 API Key Authentication & Key Management
             ↓
         Phase 21 Rate Limiting & Security Hardening
             ↓
         Phase 22 Observability, Metrics & Health Checks
             ↓
         Phase 23 Unit & Integration Testing Suite
             ↓
         Phase 24 End-to-End Testing & Coverage Enforcement
             ↓
         Phase 25 Production Readiness & Docker
```

Phases 9 and 10 depend on Phase 8; Phase 15 depends on both Phase 14 and Phase 13. Phase 18 wraps Phases 5–15 as automated background tasks. Phase 19 depends on Phase 18. Phases 16–17 depend on the whole 5→15 chain because they consolidate the endpoints those phases already introduced — they are completion/standardization steps, not the phases where REST APIs first appear (see below).

**Phases 16–17 do not "turn on" REST APIs.** Repository CRUD is public since Phase 6, the graph API since Phase 11, search since Phase 13, and chat since Phase 15 — each capability exposes its own endpoint as soon as it exists, so the frontend never has to wait until Phase 17 to start integrating against those. What Phases 16–17 actually do: add the endpoints that don't naturally belong to an earlier capability-phase (files API, status polling), audit every endpoint introduced so far for consistent error/pagination/timestamp formatting, and finalize OpenAPI documentation. In short:

```
Phases 6, 11, 13, 15   → introduce capability-specific public endpoints as those capabilities become available
Phase 16                → adds the remaining endpoints (files, status)
Phase 17                → completes, standardizes, and documents the full REST API surface
```

**Internal capability vs. public API capability:** Several phases build an internal service (a Python function, a DB table) before that service is reachable through a versioned, documented HTTP endpoint. The table below is the authoritative record of when each capability becomes *internally available* (usable only inside the backend process, e.g. via a debug endpoint or direct service call) versus *publicly available* (a stable endpoint the frontend may depend on).

| Capability | Internal since | Public endpoint since | Notes |
|---|---|---|---|
| Repository create/list/get/delete | Phase 6 | Phase 6 | Public from the start — no reason to hide it |
| Optional request authentication | Phase 2 | Phase 2 | Header accepted from Phase 2; **not enforced** until Phase 20 (see Authentication Strategy below) |
| File extraction | Phase 7 | Phase 16 (`files.py`) | Debug-only `POST .../extract` exists Phase 7–16, removed once Phase 18 automates the pipeline |
| Source parsing | Phases 9–10 | Phase 16 (symbols exposed via files API) | Debug-only `POST .../parse` exists Phase 10–16 |
| Dependency graph | Phase 11 | Phase 11 | `GET .../graph` is public as soon as the builder exists |
| Semantic search | Phase 13 | Phase 13 | `POST .../search` is public as soon as embeddings exist |
| RAG chat | Phase 15 | Phase 15 | Chat endpoints are public as soon as the RAG pipeline exists |
| Automatic background processing | — | Phase 18 | Before Phase 18, processing must be triggered manually via debug endpoints |
| Live progress (SSE) | — | Phase 19 | Before Phase 19, the frontend must poll `GET .../status` (public since Phase 16) |
| Enforced authentication | — | Phase 20 | See Authentication Strategy below |
| Rate limiting | — | Phase 21 | See Phase 21 |

The frontend must never be told a phase number as its only dependency — it must be told which of these capabilities it needs. See `FRONTEND.md → Frontend ↔ Backend Dependency Matrix` for the mapping.

---

## API Contract — Source of Truth

> This is the authoritative, versioned contract between backend and frontend. Both roadmaps must stay consistent with it. `FRONTEND.md` references this section instead of duplicating it. Update this section first whenever a contract decision changes, then propagate the change to the phase that implements it. **Any phase that changes a schema, error format, auth behavior, or SSE/event format must update this section as part of that phase** (see `Phase 17` and the API Contract Requirements item in every phase below).

### Versioning & base URL

- All endpoints are namespaced under `{API_BASE_URL}/api/v1/...`. `API_BASE_URL` defaults to `http://localhost:8000` in development.
- Breaking changes bump to `/api/v2`; the v1 surface does not change shape once Phase 17 ships it.

### Endpoint naming

- Plural nouns for collections (`/repositories`), nested resources for ownership (`/repositories/{id}/files/{file_id}`), verbs only where no REST noun fits (`/repositories/clone`).

### Timestamps & UUIDs

- All timestamps: ISO 8601 UTC, e.g. `"2026-08-07T12:00:00Z"`.
- All IDs: UUIDv4, serialized as strings (never raw binary).

### Pagination

All list endpoints return:
```json
{"items": [...], "total": 142, "page": 1, "page_size": 20}
```
`page_size` max 100. Query params: `?page=1&page_size=20`.

### Error format

```json
{"error": {"code": "REPO_NOT_FOUND", "message": "Repository not found", "details": {}}}
```
HTTP status codes: `400` (validation), `401` (auth required/invalid), `403` (forbidden), `404` (not found), `413` (too large), `422` (schema), `429` (rate limit), `500` (server error).

### Authentication strategy (dev vs. production)

CodeGraph v2 is primarily a **local/self-hosted developer tool**, so the roadmap must not force full multi-user auth before it's needed — but it also must not leave a public deployment wide open.

- **From Phase 2**, the backend accepts an optional `X-API-Key` header on every request (the middleware/dependency exists), and `Settings.REQUIRE_AUTH` (bool, default `false`) controls whether it is enforced. In default local/self-hosted developer mode, `REQUIRE_AUTH=false`: requests without a key succeed, so frontend development is never blocked waiting for backend auth.
- **From Phase 20**, real API-key issuance, hashing, and enforcement land (`ApiKey` model, `get_current_key()`); Phase 21 adds per-key rate limiting. Once both ship, `REQUIRE_AUTH` becomes safe to set to `true`. Anyone deploying CodeGraph v2 as a **hosted/multi-user production service** must set `REQUIRE_AUTH=true` and provision real keys before exposing it publicly.
- The frontend never hard-codes an assumption about which mode it's talking to. It sends `X-API-Key` if one is configured, and reacts to a `401 {"error": {"code": "AUTH_REQUIRED", ...}}` response by prompting for a key — it does not block the app on a key up front. See `FRONTEND.md → Phase 6`.
- Required on all mutating (`POST`/`PUT`/`DELETE`) requests once enforced; `GET` requests are optionally authenticated (`REQUIRE_AUTH_FOR_READS`, default `false`).
- Bootstrap key: `ADMIN_API_KEY` env var creates a default key on first startup once Phase 20 lands.

### Repository status vs. pipeline phase

Two related but distinct fields are emitted:

- `Repository.status` — coarse lifecycle gate, one of: `pending | ingesting | parsing | indexing | ready | error`. The frontend uses this to decide whether to show the processing UI (`status !== "ready"`) or the ready UI.
- `AnalysisJob.phase` / SSE `phase` — granular pipeline step currently running, one of exactly five canonical values, each with a fixed progress milestone (set in Phase 18):

| `phase` value | Meaning | Progress milestone | Introduced in |
|---|---|---|---|
| `ingestion` | Upload/clone accepted, files landing on disk | 10 | Phase 5–6 |
| `extraction` | Walking the tree, hashing, detecting languages | 25 | Phase 7–8 |
| `parsing` | AST/tree-sitter parsing, symbol + dependency extraction | 50 | Phase 9–10 |
| `graph` | Dependency graph construction + metrics | 70 | Phase 11 |
| `indexing` | Chunking + embedding generation | 100 | Phase 12–13 |

The frontend's five-stage stepper (`FRONTEND.md → Phase 9`) maps 1:1 to this `phase` list — not to the coarser `status` enum. Every phase/service that updates progress (Phases 7–13, wired together in Phase 18) must emit exactly one of these five `phase` strings.

### SSE / event formats — two distinct streams

Repository progress and chat streaming are different event formats and must not be confused:

**Repository progress SSE** (`GET /api/v1/repositories/{id}/events`, introduced Phase 19):
```
data: {"status": "parsing", "progress": 50, "phase": "parsing"}\n\n
```
Auto-closes on `status: "ready"` or `status: "error"`. Keepalive `:ping\n\n` every 15s.

**AI chat streaming** (`POST .../chat/sessions/{sid}/messages`, introduced Phase 15):
```
data: <token text>\n\n
...
data: __sources__:[{"path":"src/auth.py","start_line":12}]\n\n
data: [DONE]\n\n
```
Plain token fragments, not JSON, until the final `__sources__` and `[DONE]` sentinel events.

### Graph response structure

```json
{
  "nodes": [{"id": "uuid", "path": "src/auth.py", "language": "python", "in_degree": 3, "out_degree": 1, "pagerank": 0.04, "is_entry_point": false}],
  "edges": [{"source": "uuid-a", "target": "uuid-b", "import_name": "AuthService"}],
  "metrics": {"total_nodes": 120, "total_edges": 340, "has_cycles": false, "density": 0.024}
}
```

### Search response structure

`POST /api/v1/repositories/{id}/search` — body `{"query": "...", "limit": 10}` — returns a paginated list of `{content, path, start_line, end_line, score}`.

### Chat contract

- `POST .../chat/sessions` → `{session_id}`.
- `POST .../chat/sessions/{sid}/messages` → SSE stream (see above).
- `GET .../chat/sessions/{sid}/messages` → message history, each with `role`, `content`, `sources`.

### LLM / embedding provider independence

`LLM_PROVIDER`/`LLM_MODEL` and `EMBEDDING_PROVIDER`/`EMBEDDING_MODEL` are **independent settings** — the embedding provider is never assumed to equal the LLM provider. See Phase 2 settings and Phase 12.

---

> **Self-contained phase reminder:** every phase below follows the same template — Phase Objective, Why This Phase Exists, Prerequisites, Current Repository Expectations, Implementation Tasks, Files/Directories, Technical Requirements, Integration Requirements, API Contract Requirements, Testing, Verification, Completion Criteria — so the coding agent never needs to ask what to do. If the actual repository differs from "Current Repository Expectations," inspect it and adapt rather than assuming this roadmap is already correct.

---

## Phase 1: Project Foundation & Tooling

### 1. Phase Objective
Establish the project scaffold: directory structure, dependency management, and developer tooling (linting, type-checking, test runner). After this phase, the project structure exists, dependencies install cleanly, and `ruff`/`mypy`/`pytest` all run (even with nothing to check yet beyond a placeholder test).

### 2. Why This Phase Exists
Every later phase needs a consistent place to put code and a way to verify it didn't break anything. Splitting tooling out from configuration/app bootstrap (Phase 2) keeps this phase small: it's pure scaffolding with no business logic, so it's fast to execute and easy to verify in isolation.

### 3. Prerequisites
None. This is the first phase of the backend roadmap.

### 4. Current Repository Expectations
Expect an empty or near-empty repository containing only `BACKEND.md` and `FRONTEND.md` at the project root. If a `backend/` directory already exists with partial scaffolding, inspect it and complete/repair it rather than starting over.

### 5. Implementation Tasks
- Initialize a Python project using **uv** (preferred) or **pip + venv**.
- Install core dependencies: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `python-dotenv`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `redis`, `celery`, `structlog`, `httpx`.
- Create a `pyproject.toml` (or `requirements/` split into `base.txt`, `dev.txt`, `test.txt`).
- Build the application directory tree (see §6).
- Set up `ruff` (linter + formatter) and `mypy` (strict type checking). Config in `pyproject.toml`.
- Set up `pytest` with `pytest-asyncio` and `httpx` test client; add a single placeholder test that always passes so `pytest` has something to run.
- Add a root `.gitignore` covering `__pycache__/`, `.venv/`, `*.pyc`, `.env`, `uploads/`.

### 6. Files / Directories

```
backend/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       └── __init__.py      # Router aggregation (empty for now)
│   ├── core/                    # Domain-agnostic utilities (populated later)
│   │   └── __init__.py
│   ├── db/
│   │   └── __init__.py
│   ├── models/                  # SQLAlchemy ORM models (populated Phase 4)
│   │   └── __init__.py
│   ├── schemas/                 # Pydantic request/response schemas
│   │   └── __init__.py
│   ├── services/                # Business logic
│   │   └── __init__.py
│   ├── tasks/                   # Celery tasks
│   │   └── __init__.py
│   └── workers/                 # Celery app definition
│       └── __init__.py
├── tests/
│   ├── conftest.py
│   └── test_placeholder.py
├── pyproject.toml
└── .gitignore
```

### 7. Technical Requirements
- All async: use `asyncio` mode throughout (set in `pyproject.toml` `[tool.pytest.ini_options]`).
- `ruff` config: enable the standard rule set plus import sorting; `mypy` config: `strict = true`.
- Do not create `app/main.py`, `app/config.py`, or `.env.example` yet — those belong to Phase 2. Keeping this phase to scaffolding only is what keeps it small.

### 8. Integration Requirements
None — this is the foundation. Nothing to integrate with yet.

### 9. API Contract Requirements
None. No endpoints exist yet.

### 10. Testing
- `tests/test_placeholder.py`: a trivial passing test confirming `pytest` is wired up correctly (e.g. `assert 1 + 1 == 2`).

### 11. Verification
```bash
cd backend
pip install -e ".[dev]"   # or the uv equivalent
pytest -v
ruff check .
mypy app/
```

### 12. Completion Criteria
- [ ] `pyproject.toml` (or requirements split) exists and installs cleanly
- [ ] Full directory tree from §6 exists with `__init__.py` files
- [ ] `ruff check .` passes with zero errors
- [ ] `mypy app/` passes with zero errors
- [ ] `pytest` runs and passes the placeholder test
- [ ] `.gitignore` present and covers standard Python + env artifacts


---

## Phase 2: Configuration, Logging & App Bootstrap

### 1. Phase Objective
Implement the `Settings` system, structured logging, the authentication header stub, and a minimal runnable FastAPI application with a `/health` endpoint. After this phase, `uvicorn app.main:app` starts cleanly.

### 2. Why This Phase Exists
Nearly every later phase reads `Settings` or logs through `structlog`, and every endpoint added in later phases mounts onto the FastAPI app created here. This phase establishes those shared foundations once, so later phases only add to `app/api/v1/__init__.py` rather than re-deciding how configuration or logging works.

### 3. Prerequisites
Phase 1 complete: project scaffold, tooling, and directory tree exist.

### 4. Current Repository Expectations
`backend/app/` exists with empty package directories from Phase 1. No `Settings` class, no FastAPI app, no logging config exist yet. If they do (e.g. a prior partial attempt), inspect and reconcile rather than overwriting blindly.

### 5. Implementation Tasks
- Implement a `Settings` class using `pydantic-settings` that reads from `.env`. Required settings:
  - `DATABASE_URL` (PostgreSQL async DSN)
  - `REDIS_URL`
  - `SECRET_KEY`
  - `LLM_PROVIDER` (enum: `openai` | `anthropic` | `groq`)
  - `LLM_API_KEY`
  - `LLM_MODEL`
  - `EMBEDDING_PROVIDER` (enum: `openai` | `anthropic` | `groq` | `custom`; **independent of `LLM_PROVIDER`** — see API Contract → LLM/embedding provider independence)
  - `EMBEDDING_MODEL`
  - `EMBEDDING_DIM` (default 1536)
  - `REQUIRE_AUTH` (bool, default `false`) — when `false` (local/self-hosted developer mode), the optional `X-API-Key` check never rejects a request; set `true` for hosted/production deployments once Phase 20 lands
  - `REQUIRE_AUTH_FOR_READS` (bool, default `false`)
  - `MAX_REPO_SIZE_MB` (default 500)
  - `UPLOAD_DIR` (default `./uploads`)
  - `ENVIRONMENT` (enum: `development` | `staging` | `production`)
  - `LOG_LEVEL` (default `info`)
  - `CORS_ORIGINS` (comma-separated list)
- Implement structured logging with `structlog`. All logs must be JSON in production, pretty in development.
- **Auth foundation stub** (`app/core/auth.py`): create `get_current_key_optional()`, a FastAPI dependency that reads `X-API-Key` if present and returns it (or `None`) without ever raising — because `REQUIRE_AUTH=false` by default, no request is rejected yet. This exists purely so the header contract (`X-API-Key`) is stable from day one; Phase 20 replaces the body of this dependency with real DB-backed enforcement without changing its name or where it's wired in, so no endpoint signatures change later.
- Create a minimal FastAPI `app` in `app/main.py` with:
  - CORS middleware configured from `settings.CORS_ORIGINS`
  - A `/health` endpoint returning `{"status": "ok", "version": "2.0.0"}`
  - Lifespan handler (startup/shutdown hooks — empty for now)
  - Global exception handlers for `HTTPException` and unhandled exceptions
- Create `.env.example` with all required variables documented.
- `app/dependencies.py`: shared FastAPI dependency injection helpers file (starts near-empty, used from Phase 3 onward).
- `app/exceptions.py`: custom exception classes matching the canonical error format from the API Contract.

### 6. Files / Directories

```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory
│   ├── config.py                # Settings (pydantic-settings)
│   ├── logging_config.py        # structlog setup
│   ├── dependencies.py          # FastAPI dependency injection helpers
│   ├── exceptions.py            # Custom exception classes + handlers
│   └── core/
│       └── auth.py              # get_current_key_optional() stub (hardened Phase 20)
├── tests/
│   └── test_health.py
├── .env.example
└── Dockerfile                   # stub — finalized in Phase 25
```

### 7. Technical Requirements
- Use `pydantic-settings` `BaseSettings` with `model_config = SettingsConfigDict(env_file=".env")`.
- FastAPI app created via a factory function `create_app()` so tests can instantiate a separate app.
- CORS should allow all origins in development, explicit list in production.

### 8. Integration Requirements
None yet — later phases register their routers into `app/api/v1/__init__.py`, which this phase creates empty.

### 9. API Contract Requirements
Introduces the `/health` endpoint and the `X-API-Key` header contract described in **API Contract → Authentication strategy**. No other endpoints exist yet; no change to error/pagination formats beyond establishing them in `app/exceptions.py`.

### 10. Testing
- `tests/test_health.py`: assert `GET /health` → 200, body matches `{"status": "ok"}`.
- Confirm `settings` loads correctly from a `.env.test` fixture.

### 11. Verification
```bash
cd backend
uvicorn app.main:app --reload            # must start without errors
curl http://localhost:8000/health        # {"status":"ok","version":"2.0.0"}
pytest tests/test_health.py -v
ruff check .
mypy app/
```

### 12. Completion Criteria
- [ ] `uvicorn app.main:app` starts without errors
- [ ] `/health` returns 200
- [ ] `.env.example` documents every setting, including `REQUIRE_AUTH` and `EMBEDDING_PROVIDER`
- [ ] `get_current_key_optional()` exists and accepts `X-API-Key` without rejecting requests (`REQUIRE_AUTH=false` by default)
- [ ] `ruff check .` and `mypy app/` pass with zero errors
- [ ] `pytest tests/test_health.py` passes


---

## Phase 3: Database Connection & Migration Foundation

### 1. Phase Objective
Configure the async SQLAlchemy engine/session, the declarative base, and Alembic — including enabling the `pgvector` extension — so the project can run migrations against a real PostgreSQL instance before any domain models exist.

### 2. Why This Phase Exists
Splitting database plumbing from the domain models (Phase 4) means the agent can prove the DB connection, async session handling, and Alembic migration machinery all work correctly on their own, before adding the complexity of six interrelated ORM models on top. It also isolates `pgvector` extension setup, which is easy to get wrong, as its own verifiable step.

### 3. Prerequisites
Phase 2 complete: `Settings` (with `DATABASE_URL`) and the FastAPI app exist.

### 4. Current Repository Expectations
PostgreSQL is accessible at `DATABASE_URL`. The `pgvector` extension is available on the server (but not yet enabled in the target database). No SQLAlchemy models, sessions, or Alembic config exist yet.

### 5. Implementation Tasks
- Create `app/db/session.py` with an async SQLAlchemy engine and `AsyncSessionLocal`.
- Create a FastAPI dependency `get_db()` yielding an `AsyncSession`; register it in `app/dependencies.py`.
- Add `app/db/base.py` with a `Base = declarative_base()` (SQLAlchemy 2.x `DeclarativeBase`) and a `TimestampMixin` (`created_at`, `updated_at` with server defaults).
- Configure `alembic/env.py` for async migrations using `asyncpg`.
- Create an initial (empty) migration that enables `pgvector`: `CREATE EXTENSION IF NOT EXISTS vector`.
- Lifespan handler in `app/main.py` should run `alembic upgrade head` on startup (development only).

### 6. Files / Directories

```
backend/
├── app/
│   └── db/
│       ├── base.py          # Base, TimestampMixin
│       └── session.py       # engine, AsyncSessionLocal, get_db
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0000_enable_pgvector.py
├── alembic.ini
└── tests/
    └── test_db.py
```

### 7. Technical Requirements
- Use `sqlalchemy.orm.DeclarativeBase` (SQLAlchemy 2.x style).
- Async engine created from `settings.DATABASE_URL` with `asyncpg` driver.
- `alembic/env.py` must run migrations in async mode (`run_sync` wrapping).

### 8. Integration Requirements
- `get_db` dependency registered in `app/dependencies.py` so Phase 4 onward can `Depends(get_db)`.
- Lifespan handler wired in `app/main.py`.

### 9. API Contract Requirements
None. This phase has no HTTP-visible effect beyond the existing `/health` endpoint continuing to work.

### 10. Testing
- `tests/test_db.py`: connect using `AsyncSessionLocal`, run a trivial `SELECT 1`, and confirm the `vector` extension is enabled (`SELECT * FROM pg_extension WHERE extname = 'vector'`).

### 11. Verification
```bash
alembic upgrade head        # no errors
alembic current             # shows head revision
pytest tests/test_db.py -v
```
Also verify in `psql`: `\dx` lists `vector` as an installed extension.

### 12. Completion Criteria
- [ ] Async engine + `AsyncSessionLocal` + `get_db()` work in tests
- [ ] `alembic upgrade head` succeeds against a real PostgreSQL instance
- [ ] `pgvector` extension enabled in the target database
- [ ] `pytest tests/test_db.py` passes


---

## Phase 4: Core Domain Data Models & Schema

### 1. Phase Objective
Define all SQLAlchemy ORM models for the domain, generate the initial schema migration from them, and add the indexes the rest of the system depends on (including the pgvector `ivfflat` index).

### 2. Why This Phase Exists
Every later phase — ingestion, extraction, parsing, graph, embeddings, chat — reads or writes one or more of these tables. Defining the complete schema in one deliberate phase (on top of the connection/migration plumbing from Phase 3) means later phases never need to design new tables from scratch, only extend this schema with focused migrations.

### 3. Prerequisites
Phase 3 complete: async session, `Base`, `TimestampMixin`, and working Alembic migrations against a real database with `pgvector` enabled.

### 4. Current Repository Expectations
`app/db/base.py` and `app/db/session.py` exist and work. `app/models/` contains only an empty `__init__.py`. No domain tables exist in the database yet beyond the `pgvector` extension.

### 5. Implementation Tasks
Create one file per domain in `app/models/`:

- `repository.py`:
  - `Repository`: `id` (UUID PK), `name`, `slug` (unique), `description`, `source` (enum: `upload`|`git_clone`), `git_url` (nullable), `status` (enum: `pending`|`ingesting`|`parsing`|`indexing`|`ready`|`error`), `error_message`, `size_bytes`, `primary_language`, `detected_languages` (JSONB), `file_count`, timestamps.
- `code_file.py`:
  - `CodeFile`: `id` (UUID PK), `repository_id` (FK), `path` (relative), `language`, `size_bytes`, `content_hash` (SHA-256), `line_count`, `is_binary`, timestamps.
- `symbol.py`:
  - `Symbol`: `id` (UUID PK), `file_id` (FK), `repository_id` (FK), `name`, `kind` (enum: `function`|`class`|`method`|`variable`|`interface`|`type`|`module`), `start_line`, `end_line`, `signature`, `docstring`, `is_exported`.
- `dependency.py`:
  - `Dependency`: `id` (UUID PK), `repository_id` (FK), `from_file_id` (FK), `to_file_id` (FK nullable — null for external), `import_name`, `import_path`, `dependency_type` (enum: `internal`|`external`|`stdlib`).
- `code_chunk.py`:
  - `CodeChunk`: `id` (UUID PK), `file_id` (FK), `repository_id` (FK), `content` (text), `start_line`, `end_line`, `chunk_type` (enum: `symbol`|`block`), `symbol_id` (FK nullable), `embedding` (Vector(1536) — pgvector column).
- `analysis_job.py`:
  - `AnalysisJob`: `id` (UUID PK), `repository_id` (FK), `phase` (text), `status` (enum: `pending`|`running`|`done`|`failed`), `progress` (integer 0–100), `error`, timestamps.

**Indexes:**
- `code_chunk.embedding` — `ivfflat` index for vector similarity.
- `code_file.repository_id` + `code_file.path` — composite unique index.
- `symbol.repository_id`, `symbol.file_id`.
- `dependency.repository_id`, `dependency.from_file_id`.

Generate the initial migration from these models.

### 6. Files / Directories

```
backend/
├── app/
│   └── models/
│       ├── repository.py
│       ├── code_file.py
│       ├── symbol.py
│       ├── dependency.py
│       ├── code_chunk.py
│       └── analysis_job.py
├── alembic/versions/
│   └── 0001_initial_schema.py
└── tests/
    └── test_models.py
```

### 7. Technical Requirements
- `Vector(1536)` type from `pgvector.sqlalchemy`.
- All FK relationships defined with `relationship()` and `lazy="selectin"` where eager loading is safe.
- Enum types should use Python `enum.Enum` and `sqlalchemy.Enum`.

### 8. Integration Requirements
- Models imported into `app/db/base.py`'s metadata (directly or via `app/models/__init__.py`) so Alembic autogenerate can see them.

### 9. API Contract Requirements
None directly — these models back every schema described in **API Contract — Source of Truth**, but no endpoints exist yet.

### 10. Testing
- `tests/test_models.py`: insert a `Repository` row and read it back; insert a `CodeChunk` with a 1536-dim embedding vector and confirm it round-trips.

### 11. Verification
```bash
alembic upgrade head
pytest tests/test_models.py -v
```
Also verify in `psql`: `\dt` lists all six expected tables; `\d code_chunk` shows `embedding vector(1536)` column.

### 12. Completion Criteria
- [ ] All 6 models exist with correct columns and relationships
- [ ] `alembic upgrade head` succeeds
- [ ] `ivfflat` index on `code_chunk.embedding` created
- [ ] Remaining indexes listed above created
- [ ] `pytest tests/test_models.py` passes


---

## Phase 5: Repository Upload Ingestion

### 1. Phase Objective
Implement the ZIP-upload ingestion path: validate and store an uploaded archive, extract it to disk, and create the corresponding `Repository` DB record. Expose `POST /api/v1/repositories`.

### 2. Why This Phase Exists
Upload is the simpler and more common of the two ingestion paths, and getting file-safety validation right (path traversal, size limits, file-count limits) is enough work on its own to warrant its own phase, separate from Git cloning (Phase 6) which has a different set of concerns (subprocess handling, URL validation, timeouts).

### 3. Prerequisites
Phase 4 complete: `Repository` model and migrations exist.

### 4. Current Repository Expectations
Database has the `repository` table. `UPLOAD_DIR` may not exist on disk yet — create it if missing. No ingestion service or repository endpoints exist yet.

### 5. Implementation Tasks
**Service: `app/services/ingestion.py`**
- `ingest_zip(file: UploadFile, db: AsyncSession) -> Repository`: validate file is a zip, check size ≤ `MAX_REPO_SIZE_MB`, save to `UPLOAD_DIR/{repo_id}/raw.zip`, extract to `UPLOAD_DIR/{repo_id}/source/`, create `Repository` DB record with `status=pending`, return it.
- `detect_repo_name(path: Path) -> str`: infer a human-readable name from the top-level directory.

**Validation:**
- Reject zip files containing path traversal (`../`) or symlinks outside root.
- Maximum file count: 50,000 files.
- Ignore `.git/`, `node_modules/`, `__pycache__/`, `*.pyc`, build artifacts (a first-pass ignore list; the full configurable version lands in Phase 7).

**API endpoint** in `app/api/v1/repositories.py`:
- `POST /api/v1/repositories` — multipart form, field `file` (zip). Returns `RepositoryResponse` (id, name, status, created_at).

**Schemas** in `app/schemas/repository.py`:
- `RepositoryCreate`, `RepositoryResponse`.

### 6. Files / Directories

```
backend/
├── app/
│   ├── api/v1/
│   │   └── repositories.py
│   ├── services/
│   │   └── ingestion.py
│   └── schemas/
│       └── repository.py
└── tests/
    ├── fixtures/
    │   └── sample_repo.zip         # minimal zip for tests
    └── test_ingestion_upload.py
```

### 7. Technical Requirements
- Use `python-multipart` for file uploads (already included via FastAPI).
- Use `zipfile.ZipFile` for extraction. Check `ZipInfo.filename` for traversal attacks before extracting.
- Store repo files at `{UPLOAD_DIR}/{repo_id}/source/`. Keep raw zip at `{UPLOAD_DIR}/{repo_id}/raw.zip`.
- After ingestion, update `Repository.status = "ingesting"`, create an `AnalysisJob` row with `phase="ingestion"`, `progress=10` (the automated task wiring happens in Phase 18 — for now this just records the row).

### 8. Integration Requirements
- Import and include `router` from `app/api/v1/repositories.py` in `app/api/v1/__init__.py`.
- Include v1 router in `app/main.py` at `/api/v1` (if not already mounted from an earlier phase).

### 9. API Contract Requirements
Introduces `POST /api/v1/repositories` per **API Contract — Source of Truth**. Response uses the standard `RepositoryResponse` shape and the canonical error format for `400`/`413` failures.

### 10. Testing
- `test_ingestion_upload.py`:
  - Upload the `sample_repo.zip` fixture → assert 200, `status=pending`.
  - Test zip with path traversal → assert 400.
  - Test zip exceeding size limit → assert 413.

### 11. Verification
```bash
pytest tests/test_ingestion_upload.py -v
curl -X POST http://localhost:8000/api/v1/repositories -F "file=@tests/fixtures/sample_repo.zip"
```

### 12. Completion Criteria
- [ ] `POST /api/v1/repositories` accepts zip, extracts, creates DB record
- [ ] Path traversal attack rejected with 400
- [ ] Oversized zip rejected with 413
- [ ] Source files exist on disk after upload
- [ ] `pytest tests/test_ingestion_upload.py` passes


---

## Phase 6: Git Clone Ingestion & Repository CRUD API

### 1. Phase Objective
Implement the Git-clone ingestion path and complete the repository CRUD surface (list, get, delete) alongside the upload endpoint from Phase 5.

### 2. Why This Phase Exists
Git cloning has a distinct risk surface (arbitrary URL schemes, subprocess timeouts, network failures) from ZIP upload, and CRUD completion is a natural pairing with it since both are needed before any repository is genuinely usable end-to-end. This phase is what makes repository management "publicly complete" — see **Phase Dependency Map → Internal capability vs. public API capability**.

### 3. Prerequisites
Phase 5 complete: upload ingestion, `Repository` model, and `app/schemas/repository.py` exist.

### 4. Current Repository Expectations
`POST /api/v1/repositories` (upload) works. No clone/list/get/delete endpoints exist yet.

### 5. Implementation Tasks
**Service addition to `app/services/ingestion.py`:**
- `ingest_git(git_url: str, db: AsyncSession) -> Repository`: validate URL format, clone (shallow `--depth 1`) into `UPLOAD_DIR/{repo_id}/source/` using `subprocess` + `git clone`, handle timeout (30s), create `Repository` DB record, return it.

**Validation:**
- Reject git URLs that aren't `https://` (block `file://`, `git://` etc.).

**API endpoints** in `app/api/v1/repositories.py`:
- `POST /api/v1/repositories/clone` — JSON body `{"git_url": "..."}`. Returns same shape as upload.
- `GET /api/v1/repositories` — list all repos (id, name, status, primary_language, file_count, created_at), paginated per **API Contract → Pagination**.
- `GET /api/v1/repositories/{repo_id}` — full repository detail.
- `DELETE /api/v1/repositories/{repo_id}` — delete repo record + files from disk.

**Schemas addition** in `app/schemas/repository.py`:
- `RepositoryCloneRequest`, `RepositoryListItem`.

### 6. Files / Directories

```
backend/
├── app/
│   ├── api/v1/
│   │   └── repositories.py      # extended
│   ├── services/
│   │   └── ingestion.py         # extended
│   └── schemas/
│       └── repository.py        # extended
└── tests/
    └── test_ingestion_git_and_crud.py
```

### 7. Technical Requirements
- Use `asyncio.create_subprocess_exec` for git clone to avoid blocking the event loop.
- Common `PaginationParams` dependency (`page`, `page_size`) — full standardization happens in Phase 17, but `GET /repositories` should already return the `{"items": [...], "total": ...}` shape.

### 8. Integration Requirements
- Router already mounted from Phase 5; this phase only adds routes to the same router.

### 9. API Contract Requirements
Introduces `POST /api/v1/repositories/clone`, `GET /api/v1/repositories`, `GET /api/v1/repositories/{id}`, `DELETE /api/v1/repositories/{id}` per **API Contract — Source of Truth**. Repository CRUD is now fully public (see Phase Dependency Map capability table).

### 10. Testing
- `test_ingestion_git_and_crud.py`:
  - Clone a local test git repo (create a throwaway repo in a temp dir as the fixture, or mock the subprocess call) → assert 200, `status=pending`.
  - Reject a `file://` URL → assert 400.
  - Test `GET /api/v1/repositories` → assert list contains created repos, correctly paginated.
  - Test `GET /api/v1/repositories/{id}` → correct detail.
  - Test `DELETE` → 200, then `GET` → 404.

### 11. Verification
```bash
pytest tests/test_ingestion_git_and_crud.py -v
curl http://localhost:8000/api/v1/repositories
```

### 12. Completion Criteria
- [ ] `POST /api/v1/repositories/clone` clones repo via git
- [ ] Non-`https://` URLs rejected with 400
- [ ] CRUD endpoints work (list with pagination, get, delete)
- [ ] `pytest tests/test_ingestion_git_and_crud.py` passes


---

## Phase 7: File Extraction, Hashing & Ignore Patterns

### 1. Phase Objective
Walk the extracted source tree, record every file in `CodeFile`, compute hashes, detect binaries, and apply ignore patterns (including `.gitignore`). Produces the file inventory that language detection (Phase 8) and parsing (Phases 9–10) consume.

### 2. Why This Phase Exists
File-tree walking, hashing, and ignore-pattern handling is meaningfully different work from language/framework detection, and separating them keeps each phase's testing surface focused: this phase's tests are about "did we record the right files," Phase 8's are about "did we label them correctly."

### 3. Prerequisites
Phase 6 complete: a `Repository` record can exist with source files on disk (from either upload or clone).

### 4. Current Repository Expectations
Source files for a repository exist at `UPLOAD_DIR/{repo_id}/source/`. No `CodeFile` model rows exist yet; no extraction service exists yet.

### 5. Implementation Tasks
**Service: `app/services/file_extractor.py`**
- `extract_files(repo: Repository, db: AsyncSession) -> list[CodeFile]`: walk `source/` directory. For each file:
  - Compute relative path, size, SHA-256 hash.
  - Detect if binary (read first 8KB, check for null bytes).
  - Upsert `CodeFile` row (on conflict by `repo_id + path`, update hash/size).
  - Return list of all `CodeFile` objects.
- Update `Repository.file_count`.

**Ignore patterns** (`app/core/ignore_patterns.py`):
- Default ignore list: `node_modules/`, `__pycache__/`, `.git/`, `dist/`, `build/`, `target/`, `*.min.js`, `*.map`, `vendor/`, `*.lock`, `*.pyc`, `.DS_Store`, `coverage/`, `.next/`, `.nuxt/`.
- If a `.gitignore` is present in the repo root, parse and apply it (use `pathspec` library).

Language and framework detection are deliberately deferred to Phase 8 — this phase only records file existence, hash, size, and binary status.

### 6. Files / Directories

```
backend/
├── app/
│   ├── core/
│   │   └── ignore_patterns.py
│   └── services/
│       └── file_extractor.py
└── tests/
    └── test_file_extractor.py
```

### 7. Technical Requirements
- Walk with `os.walk()` or `pathlib.Path.rglob()`.
- Hash computation: `hashlib.sha256` in chunks.
- Keep `pathspec` in dependencies for gitignore parsing.
- File extraction should be synchronous (CPU-bound) — run in `asyncio.get_event_loop().run_in_executor(None, ...)` to avoid blocking.

### 8. Integration Requirements
- `extract_files()` will be called by the Celery task in Phase 18. For now, expose a debug endpoint `POST /api/v1/repositories/{repo_id}/extract` (unauthenticated in local/self-hosted mode; gated behind auth once Phase 20 lands) to trigger it synchronously for testing.
- While running, update `AnalysisJob.phase = "extraction"`, `progress = 25`. After extraction completes, update `Repository.status = "parsing"` (the coarse status jumps straight to the next gate — see API Contract → Repository status vs. pipeline phase).

### 9. API Contract Requirements
Adds the debug-only `POST /api/v1/repositories/{repo_id}/extract` endpoint (not part of the stable public surface — see Phase Dependency Map capability table; it is removed once Phase 18 automates the pipeline).

### 10. Testing
- `test_file_extractor.py`:
  - Create a temporary directory with several files and a binary file.
  - Run `extract_files()` → assert correct `CodeFile` rows created.
  - Assert binary files are marked `is_binary=True`.
  - Assert ignored paths (including a `.gitignore`-driven exclusion) not recorded.
  - Assert SHA-256 hash stored correctly.

### 11. Verification
```bash
pytest tests/test_file_extractor.py -v
curl -X POST http://localhost:8000/api/v1/repositories/{id}/extract
psql $DATABASE_URL -c "SELECT path, is_binary FROM code_file WHERE repository_id = '...' LIMIT 20;"
```

### 12. Completion Criteria
- [ ] Every non-ignored file in source tree recorded in `CodeFile`
- [ ] Binary files correctly identified
- [ ] Ignored patterns respected (including `.gitignore`)
- [ ] SHA-256 hash stored correctly
- [ ] `pytest tests/test_file_extractor.py` passes


---

## Phase 8: Language & Framework Detection

### 1. Phase Objective
Detect each file's programming language, compute the repository's primary/detected languages, and detect frameworks from manifest files (`package.json`, `requirements.txt`, etc.).

### 2. Why This Phase Exists
Language detection feeds directly into parser selection (Phase 9–10) and UI badges, so it needs to be correct and independently testable. Splitting it from raw file extraction (Phase 7) lets this phase focus purely on classification logic and its many edge cases (ambiguous extensions, multi-language repos) without re-testing the file-walking logic already covered.

### 3. Prerequisites
Phase 7 complete: `CodeFile` rows exist with path/hash/binary metadata for a repository.

### 4. Current Repository Expectations
`CodeFile` rows exist but have no `language` value set yet. `Repository.primary_language`, `detected_languages`, and `frameworks` are unset.

### 5. Implementation Tasks
**Language detection** (`app/core/language_detector.py`):
- Map file extensions to language strings. Support at minimum: Python, JavaScript, TypeScript, Java, Go, Rust, C, C++, C#, Ruby, PHP, Swift, Kotlin, Scala, Shell, HTML, CSS, SCSS, JSON, YAML, TOML, Markdown, SQL.
- Use `pygments.lexers.guess_lexer_for_filename()` as a fallback for ambiguous cases.
- Primary language = the language with the most non-blank lines of code (excluding JSON/YAML/Markdown).

**Framework detection** (`app/core/framework_detector.py`):
- Scan `package.json`, `requirements.txt`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `pyproject.toml` for known framework/library names.
- Store detected frameworks in `Repository` (add a `frameworks` JSONB column via new migration).

**Wiring:**
- Extend `app/services/file_extractor.py` (or call this as a follow-up step) to set `CodeFile.language` for every row, and update `Repository.detected_languages`, `Repository.primary_language`, `Repository.frameworks`.

### 6. Files / Directories

```
backend/
├── app/
│   └── core/
│       ├── language_detector.py
│       └── framework_detector.py
├── alembic/versions/
│   └── 0002_add_frameworks_column.py
└── tests/
    └── test_language_detection.py
```

### 7. Technical Requirements
- Keep `pygments` in dependencies.
- Framework detection reads manifest files directly from `source/` on disk; no new DB table needed beyond the `frameworks` JSONB column.

### 8. Integration Requirements
- Called as part of the same extraction step (Phase 7's debug `/extract` endpoint now also populates language/framework fields); `AnalysisJob.phase` stays `"extraction"` for this sub-step.

### 9. API Contract Requirements
No new endpoints. `RepositoryResponse` gains populated `primary_language`, `detected_languages`, and `frameworks` fields (already reserved in the schema).

### 10. Testing
- `test_language_detection.py`:
  - All supported extensions map to the correct language.
  - Ambiguous/ungrouped extension falls back to `pygments` guess.
  - `primary_language` correctly computed for a multi-language fixture.
  - Frameworks correctly detected from a sample `package.json` and `requirements.txt`.

### 11. Verification
```bash
pytest tests/test_language_detection.py -v
curl -X POST http://localhost:8000/api/v1/repositories/{id}/extract
psql $DATABASE_URL -c "SELECT path, language FROM code_file WHERE repository_id = '...' LIMIT 20;"
```

### 12. Completion Criteria
- [ ] Language detected for all non-binary files
- [ ] `primary_language` and `detected_languages` set on `Repository`
- [ ] Frameworks detected from manifest files and stored
- [ ] `pytest tests/test_language_detection.py` passes


---

## Phase 9: Parser Abstraction, Python & Generic Parsing

### 1. Phase Objective
Define the parser abstraction and implement it for Python (via the standard library `ast` module) and a generic fallback for unsupported languages, producing `Symbol` rows.

### 2. Why This Phase Exists
Establishing the `BaseParser`/`ParseResult` abstraction alongside the first concrete parser (Python, which needs no external grammar dependency) is a self-contained, verifiable milestone. Splitting tree-sitter-based TypeScript/JavaScript parsing into Phase 10 isolates a riskier external dependency from this simpler, dependency-light phase.

### 3. Prerequisites
Phase 8 complete: `CodeFile.language` populated for all files.

### 4. Current Repository Expectations
`CodeFile` rows exist with correct `language` values. No `Symbol` rows exist yet; no parser code exists yet.

### 5. Implementation Tasks
**Parser abstraction** (`app/core/parsers/base.py`):
- Abstract base class `BaseParser` with method `parse(file_path: Path, code_file: CodeFile) -> ParseResult`.
- `ParseResult` dataclass: `symbols: list[SymbolData]`, `imports: list[ImportData]`.
- `SymbolData`: name, kind, start_line, end_line, signature, docstring, is_exported.
- `ImportData`: import_name, import_path, is_relative.

**Concrete parsers:**
- `app/core/parsers/python_parser.py`: use Python's built-in `ast` module. Extract functions (`ast.FunctionDef`, `ast.AsyncFunctionDef`), classes (`ast.ClassDef`), imports (`ast.Import`, `ast.ImportFrom`). Extract docstrings from first `ast.Constant` of body.
- `app/core/parsers/generic_parser.py`: fallback — extract line count, no symbol extraction. Used for unsupported languages.

**Service: `app/services/code_parser.py`**
- `parse_repository(repo: Repository, files: list[CodeFile], db: AsyncSession)`: for each non-binary file, select the appropriate parser (Python or generic for now — Phase 10 adds TS/JS selection), run it, bulk-insert `Symbol` rows.
- Batch DB inserts (1000 rows at a time) for performance.
- Track parse errors per file; store in `CodeFile.parse_error` (add column via migration).

### 6. Files / Directories

```
backend/
├── app/
│   ├── core/
│   │   └── parsers/
│   │       ├── base.py
│   │       ├── python_parser.py
│   │       └── generic_parser.py
│   └── services/
│       └── code_parser.py
├── alembic/versions/
│   └── 0003_add_parse_error_column.py
└── tests/
    ├── fixtures/
    │   └── sample.py
    └── test_code_parser_python.py
```

### 7. Technical Requirements
- Run parsers in `run_in_executor` for CPU-bound work.
- Limit per-file parse time to 10 seconds (via `concurrent.futures.ThreadPoolExecutor` with timeout).

### 8. Integration Requirements
- Not yet wired to `Dependency` population — import resolution is Phase 10. This phase only produces `Symbol` rows.

### 9. API Contract Requirements
No new endpoints yet — the debug `/parse` endpoint is introduced in Phase 10 once import resolution is also in place.

### 10. Testing
- `test_code_parser_python.py`:
  - Parse `sample.py` → assert expected function and class symbols extracted, with correct `kind`, line ranges, and docstrings.
  - Parse a file with a syntax error → assert `CodeFile.parse_error` set, pipeline does not crash.
  - Parse an unsupported-language file → assert generic parser runs without error and no symbols are extracted.

### 11. Verification
```bash
pytest tests/test_code_parser_python.py -v
psql $DATABASE_URL -c "SELECT name, kind, start_line FROM symbol WHERE repository_id = '...' LIMIT 20;"
```

### 12. Completion Criteria
- [ ] `BaseParser`/`ParseResult`/`SymbolData`/`ImportData` abstraction defined
- [ ] Python AST parser extracts functions, classes, methods, imports correctly
- [ ] Generic fallback parser handles unsupported languages without crashing
- [ ] Parse errors captured per-file without crashing the pipeline
- [ ] `pytest tests/test_code_parser_python.py` passes


---

## Phase 10: TypeScript/JavaScript Parsing & Import Resolution

### 1. Phase Objective
Add tree-sitter-based TypeScript and JavaScript parsers, and implement import resolution so `Dependency` rows link files together (internal, external, or stdlib).

### 2. Why This Phase Exists
Tree-sitter grammars are a heavier, less predictable dependency than the standard-library `ast` module used in Phase 9, and import resolution (turning raw import strings into resolved `Dependency` rows) is a distinct algorithmic problem worth isolating and testing on its own — it's what the dependency graph (Phase 11) is built from.

### 3. Prerequisites
Phase 9 complete: parser abstraction, Python parser, generic parser, and `code_parser` service exist.

### 4. Current Repository Expectations
`Symbol` rows exist for Python files. TypeScript/JavaScript files still fall through to the generic parser (no symbols extracted). No `Dependency` rows exist yet.

### 5. Implementation Tasks
**Concrete parsers:**
- `app/core/parsers/typescript_parser.py`: use `tree-sitter` Python bindings + `tree-sitter-typescript` grammar. Extract functions, classes, interfaces, type aliases, imports/exports.
- `app/core/parsers/javascript_parser.py`: same tree-sitter approach with `tree-sitter-javascript`.

> **Architectural freedom:** If `tree-sitter` proves unstable for a language, substitute with a regex-based heuristic parser as a fallback. Document the decision in the phase completion report. Do not block the whole pipeline on one language.

**Import resolution** (`app/core/import_resolver.py`):
- For each `ImportData`, attempt to resolve `import_path` to a `CodeFile.id` in the same repository (internal) or mark as external/stdlib.
- Python: resolve relative imports (`from . import x`) using file path arithmetic.
- JS/TS: resolve `./`, `../` paths; detect node_modules as external.
- Populate `Dependency` table.

**Wire into `app/services/code_parser.py`:**
- Extend `parse_repository()` to select TS/JS parsers by language and to call `import_resolver` after symbol extraction, bulk-inserting `Dependency` rows.

### 6. Files / Directories

```
backend/
├── app/
│   └── core/
│       ├── parsers/
│       │   ├── typescript_parser.py
│       │   └── javascript_parser.py
│       └── import_resolver.py
└── tests/
    ├── fixtures/
    │   ├── sample.ts
    │   └── sample.js
    └── test_code_parser_ts_js.py
```

### 7. Technical Requirements
- Install: `tree-sitter`, `tree-sitter-python`, `tree-sitter-javascript`, `tree-sitter-typescript` (verify current PyPI package names at implementation time).

### 8. Integration Requirements
- Expose debug endpoint `POST /api/v1/repositories/{repo_id}/parse` (calls extract then parse synchronously; unauthenticated in local/self-hosted mode, gated behind auth once Phase 20 lands).
- While running, update `AnalysisJob.phase = "parsing"`, `progress = 50`. `Repository.status` stays `"parsing"` through this phase.

### 9. API Contract Requirements
Adds the debug-only `POST /api/v1/repositories/{repo_id}/parse` endpoint (not part of the stable public surface — removed once Phase 18 automates the pipeline; see Phase Dependency Map capability table).

### 10. Testing
- `test_code_parser_ts_js.py`:
  - Parse `sample.ts` → assert interface, function, import symbols.
  - Parse `sample.js` → assert arrow functions and imports.
  - Assert `Dependency` rows created with correct `dependency_type` for both internal and external imports.

### 11. Verification
```bash
pytest tests/test_code_parser_ts_js.py -v
psql $DATABASE_URL -c "SELECT import_name, dependency_type FROM dependency WHERE repository_id = '...' LIMIT 20;"
```

### 12. Completion Criteria
- [ ] TypeScript/JavaScript parser extracts symbols via tree-sitter
- [ ] `Dependency` table populated with internal + external imports
- [ ] Import resolution correctly links internal imports to `CodeFile.id`
- [ ] `pytest tests/test_code_parser_ts_js.py` passes


---

## Phase 11: Dependency Graph Construction & API

### 1. Phase Objective
Build an in-memory (and serialized) directed graph of file-level dependencies with computed metrics, persist a graph summary, and expose it via the graph API.

### 2. Why This Phase Exists
The graph is a single coherent capability — construction and its API are tightly coupled (the API just serializes what the builder produces) — so it remains one phase, matching the original roadmap's scoping, which was already appropriately sized.

### 3. Prerequisites
Phase 10 complete: `Dependency` and `Symbol` tables populated for both Python and TS/JS files.

### 4. Current Repository Expectations
`Dependency` rows exist linking files. No `RepositoryGraph` model or graph endpoints exist yet.

### 5. Implementation Tasks
**Graph builder** (`app/services/graph_builder.py`):
- Use `networkx` to build a `DiGraph`.
- Nodes: each `CodeFile` (id, path, language, symbol count).
- Edges: each `Dependency` (from_file → to_file, with `import_name` as edge attribute). Skip external deps for main graph (add them as metadata).
- Compute graph metrics per node: `in_degree`, `out_degree`, `pagerank`, `is_entry_point` (in_degree=0 and out_degree>0), `is_leaf` (out_degree=0).
- Detect cycles (`networkx.find_cycle`); record in `Repository` (add `has_cycles: bool`, `cycle_count: int` columns via migration).
- Serialize the graph to a compact JSON format stored in the DB (new model `RepositoryGraph`) and/or on disk.

**Model: `app/models/repository_graph.py`**
- `RepositoryGraph`: `id` (UUID PK), `repository_id` (FK, unique), `nodes` (JSONB), `edges` (JSONB), `metrics` (JSONB), `generated_at`.

Graph format matches **API Contract — Source of Truth → Graph response structure**.

**API endpoint** in `app/api/v1/graph.py`:
- `GET /api/v1/repositories/{repo_id}/graph` — returns full `RepositoryGraph` JSON.
- `GET /api/v1/repositories/{repo_id}/graph/node/{file_id}` — returns node detail: the file's symbols, its direct dependencies, and files that depend on it.

### 6. Files / Directories

```
backend/
├── app/
│   ├── models/
│   │   └── repository_graph.py
│   ├── services/
│   │   └── graph_builder.py
│   ├── api/v1/
│   │   └── graph.py
│   └── schemas/
│       └── graph.py
├── alembic/versions/
│   └── 0004_repository_graph.py
└── tests/
    └── test_graph_builder.py
```

### 7. Technical Requirements
- `networkx` ≥ 3.x. Install it. PageRank: `networkx.pagerank(G, alpha=0.85)`.
- For large repos (>5000 files), serialize only the top 500 nodes by pagerank + all their edges to keep JSON size manageable. Store full graph on disk (`{UPLOAD_DIR}/{repo_id}/graph.json`).

### 8. Integration Requirements
- `build_graph()` called after parsing in the pipeline. While running, update `AnalysisJob.phase = "graph"`, `progress = 70`. `Repository.status` stays `"parsing"` through this step (there is no separate coarse status for graph building — see API Contract → Repository status vs. pipeline phase).
- Graph endpoints registered in `app/api/v1/__init__.py`.

### 9. API Contract Requirements
Introduces `GET /api/v1/repositories/{id}/graph` and `GET .../graph/node/{file_id}` per **API Contract → Graph response structure**. Graph is now publicly available (see Phase Dependency Map capability table).

### 10. Testing
- `test_graph_builder.py`: create a small synthetic set of `CodeFile` + `Dependency` rows, build graph, assert correct in/out degrees, pagerank scores, cycle detection, and that the API endpoints return valid JSON matching the contract.

### 11. Verification
```bash
pytest tests/test_graph_builder.py -v
curl http://localhost:8000/api/v1/repositories/{id}/graph | python -m json.tool | head -50
```

### 12. Completion Criteria
- [x] `RepositoryGraph` stored in DB after pipeline runs
- [x] Graph nodes have correct in/out degree + pagerank
- [x] Cycle detection working
- [x] `GET /api/v1/repositories/{id}/graph` returns valid JSON matching the contract
- [x] `GET .../graph/node/{file_id}` returns node detail
- [x] `pytest tests/test_graph_builder.py` passes


---

## Phase 12: Code Chunking & Embedding Provider Abstraction

### 1. Phase Objective
Implement the chunking strategy that turns parsed files into embeddable pieces, and build the embedding provider abstraction (OpenAI, Anthropic-stub, Groq-stub) — without yet wiring up the indexing pipeline or search endpoint (Phase 13).

### 2. Why This Phase Exists
Chunking strategy and provider abstraction are both meaningful design decisions worth testing independently of the bulk-indexing and search-query logic that consumes them. Isolating them means chunking edge cases (oversized symbols, files with no symbols) and provider selection logic each get focused, fast-running unit tests before the heavier indexing phase.

### 3. Prerequisites
Phase 11 complete (pipeline order established through graph construction); `Symbol` rows exist.

### 4. Current Repository Expectations
`Symbol` and `CodeFile` rows exist. No `CodeChunk` rows populated yet (the column exists from Phase 4's migration). No embedding provider code exists yet.

### 5. Implementation Tasks
**Chunker** (`app/core/chunker.py`):
- Strategy: prefer symbol-level chunks (one chunk per function/class with its full source). For files with no extracted symbols, fall back to 50-line sliding window chunks with 10-line overlap.
- `chunk_file(code_file: CodeFile, symbols: list[Symbol], source: str) -> list[ChunkData]`: returns list of `ChunkData` (content, start_line, end_line, chunk_type, symbol_id).
- Max chunk size: 8000 characters. If a single symbol is larger, split at logical boundaries (inner function defs or every 100 lines).
- Prepend file path + symbol name to each chunk content for context: `# File: src/auth.py\n# Symbol: AuthService.login\n\n<code>`.

**Embedding service** (`app/services/embedding_service.py`):
- Abstract interface `EmbeddingProvider` with method `embed(texts: list[str]) -> list[list[float]]`.
- Concrete implementations:
  - `OpenAIEmbeddingProvider`: uses `text-embedding-3-small` (1536 dims) via `openai` SDK.
  - `AnthropicEmbeddingProvider`: stub (Anthropic doesn't have a standalone embeddings API as of now; either use a third-party or fall back to OpenAI). Document this clearly.
  - `GroqEmbeddingProvider`: stub (Groq uses third-party embedding models; configure `EMBEDDING_BASE_URL` override).
- Factory: `get_embedding_provider(settings) -> EmbeddingProvider` selects based on `settings.EMBEDDING_PROVIDER` only — it must never fall back to or infer from `settings.LLM_PROVIDER`. The two are configured independently (e.g. `LLM_PROVIDER=anthropic` with `EMBEDDING_PROVIDER=openai` is the expected common case, since Anthropic has no first-party embeddings API — see the `AnthropicEmbeddingProvider` stub above).
- Batch API calls: process chunks in batches of 100.
- Retry with exponential backoff on rate limit (429) errors.

### 6. Files / Directories

```
backend/
├── app/
│   ├── core/
│   │   └── chunker.py
│   └── services/
│       └── embedding_service.py
└── tests/
    ├── test_chunker.py
    └── test_embedding_service.py
```

### 7. Technical Requirements
- Install `openai` SDK.
- For tests, mock the embedding API with a fixed fake embedding vector — no real network calls in unit tests.

### 8. Integration Requirements
- Not yet wired to `CodeChunk` DB inserts or the pipeline — that's Phase 13 (`indexer.py`). This phase only produces chunk data and embeddings in isolation.

### 9. API Contract Requirements
None yet. No endpoints change in this phase.

### 10. Testing
- `test_chunker.py`: edge cases — empty file, huge function needing a split, file with no symbols falling back to sliding window.
- `test_embedding_service.py`: mock `EmbeddingProvider.embed`, assert the factory selects the correct provider based on `EMBEDDING_PROVIDER` independent of `LLM_PROVIDER`, and assert retry-on-429 behavior.

### 11. Verification
```bash
pytest tests/test_chunker.py tests/test_embedding_service.py -v
```

### 12. Completion Criteria
- [x] Chunker produces symbol-level chunks with correct fallback to sliding-window for symbol-less files
- [x] Embedding provider abstraction implemented for OpenAI, with documented Anthropic/Groq stubs
- [x] Provider selection is independent of `LLM_PROVIDER`
- [x] Retry-with-backoff implemented for rate limit errors
- [x] `pytest tests/test_chunker.py tests/test_embedding_service.py` passes (mocked embeddings)


---

## Phase 13: Vector Indexing & Semantic Search API

### 1. Phase Objective
Wire chunking and embeddings (Phase 12) into a full indexing service that populates `CodeChunk`, and expose the semantic search endpoint backed by pgvector cosine similarity.

### 2. Why This Phase Exists
This is where chunking and embeddings actually become a usable, queryable capability — the natural conclusion of Phase 12's building blocks. Keeping it separate from Phase 12 means the provider-abstraction unit tests stay fast and mocked, while this phase's tests focus on end-to-end indexing and ranking behavior.

### 3. Prerequisites
Phase 12 complete: `chunker.py` and `embedding_service.py` exist and are independently tested.

### 4. Current Repository Expectations
Chunking and embedding provider code exists but is not yet invoked against real repository data; `CodeChunk` table is empty.

### 5. Implementation Tasks
**Service: `app/services/indexer.py`**
- `index_repository(repo: Repository, db: AsyncSession)`: chunk all non-binary files, batch-embed, bulk-insert `CodeChunk` rows.
- Track progress: update `AnalysisJob` with percentage complete.
- After indexing, set `Repository.status = "ready"`.

**Semantic search endpoint:**
- `POST /api/v1/repositories/{repo_id}/search` — body `{"query": "...", "limit": 10}`.
- Embed the query, run pgvector cosine similarity search: `SELECT ... ORDER BY embedding <=> $1 LIMIT $2`.
- Return `list[SearchResult]`: chunk content, file path, start_line, end_line, score.

### 6. Files / Directories

```
backend/
├── app/
│   ├── services/
│   │   └── indexer.py
│   ├── api/v1/
│   │   └── search.py
│   └── schemas/
│       └── search.py
└── tests/
    └── test_indexing_and_search.py
```

### 7. Technical Requirements
- pgvector query: use `sqlalchemy` with raw SQL or the `pgvector` SQLAlchemy extension's `cosine_distance` operator.
- Store embedding dimension in `settings.EMBEDDING_DIM` (default 1536). If using a different model, adjust the `Vector(N)` column via migration.

### 8. Integration Requirements
- `index_repository()` called at end of pipeline after graph construction. While running, update `AnalysisJob.phase = "indexing"`, `progress` climbing to `100`; `Repository.status = "indexing"`.
- After indexing, `Repository.status` → `"ready"`, `AnalysisJob.status = "done"`.
- Search endpoint registered in router.

### 9. API Contract Requirements
Introduces `POST /api/v1/repositories/{id}/search` per **API Contract → Search response structure**. Search is now publicly available (see Phase Dependency Map capability table). `Repository.status = "ready"` becomes reachable for the first time.

### 10. Testing
- `test_indexing_and_search.py`:
  - Mock `EmbeddingProvider.embed` to return deterministic vectors.
  - Run chunker + indexer on `sample.py` fixture → assert correct `CodeChunk` rows.
  - Run semantic search → assert correct result ranking.

### 11. Verification
```bash
pytest tests/test_indexing_and_search.py -v
curl -X POST http://localhost:8000/api/v1/repositories/{id}/search \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication login", "limit": 5}'
psql $DATABASE_URL -c "SELECT count(*) FROM code_chunk WHERE repository_id = '...';"
```

### 12. Completion Criteria
- [x] Embeddings generated and stored in `CodeChunk.embedding`
- [x] Semantic search returns ranked results matching the contract
- [x] `Repository.status = "ready"` after indexing completes
- [x] `pytest tests/test_indexing_and_search.py` passes (mocked embeddings)


---

## Phase 14: LLM Provider Abstraction & Prompt Management

### 1. Phase Objective
Build the LLM provider abstraction (OpenAI, Anthropic, Groq) with streaming support, and the prompt templates the RAG pipeline (Phase 15) will use — without yet wiring retrieval or chat endpoints.

### 2. Why This Phase Exists
Provider abstraction and prompt design are self-contained decisions that don't require a working retrieval pipeline to test — they can be verified against mocked chat calls. Separating them from Phase 15 keeps this phase's tests fast (no DB retrieval involved) and lets the RAG phase focus purely on retrieval-and-generation orchestration.

### 3. Prerequisites
Phase 2 complete (`Settings` with `LLM_PROVIDER`/`LLM_API_KEY`/`LLM_MODEL`). Does not require the indexing pipeline.

### 4. Current Repository Expectations
No LLM provider code exists yet. `Settings` already has the relevant fields from Phase 2.

### 5. Implementation Tasks
**LLM provider abstraction** (`app/core/llm/base.py`):
- `BaseLLMProvider` abstract class with:
  - `chat(messages: list[Message], stream: bool = False) -> AsyncIterator[str] | str`
  - `model_name: str`
  - `max_context_tokens: int`
- `Message` dataclass: `role` (system|user|assistant), `content`.

**Concrete providers:**
- `app/core/llm/openai_provider.py`: uses `openai.AsyncOpenAI`, supports streaming.
- `app/core/llm/anthropic_provider.py`: uses `anthropic.AsyncAnthropic`, supports streaming.
- `app/core/llm/groq_provider.py`: uses `groq.AsyncGroq` (OpenAI-compatible), supports streaming.
- Factory: `get_llm_provider(settings) -> BaseLLMProvider`.

**Prompt management** (`app/core/llm/prompts.py`):
- Store all system/user prompt templates as Python constants (not in DB). Use f-strings or Jinja2.
- System prompt for code assistant: establishes role, instructs to cite files, instructs to say "I don't know" if context is insufficient.
- Context injection template: formats retrieved chunks into numbered context blocks.

### 6. Files / Directories

```
backend/
├── app/
│   └── core/
│       └── llm/
│           ├── base.py
│           ├── openai_provider.py
│           ├── anthropic_provider.py
│           ├── groq_provider.py
│           └── prompts.py
└── tests/
    └── test_llm_providers.py
```

### 7. Technical Requirements
- Install `openai`, `anthropic`, `groq` SDKs.
- Token counting: use `tiktoken` for OpenAI models; estimate for others (chars / 4).
- For tests, mock each SDK client — no real network calls.

### 8. Integration Requirements
- Not yet wired into any endpoint — Phase 15 injects `get_llm_provider()` via FastAPI dependency into the chat endpoints.

### 9. API Contract Requirements
None yet. No endpoints change in this phase.

### 10. Testing
- `test_llm_providers.py`: mock each SDK, assert `chat()` returns/streams expected content for each of the three providers, assert `get_llm_provider()` selects correctly based on `LLM_PROVIDER`, assert prompt templates render with sample context correctly.

### 11. Verification
```bash
pytest tests/test_llm_providers.py -v
```

### 12. Completion Criteria
- [x] LLM provider abstraction implemented and mock-tested for OpenAI, Anthropic, and Groq
- [x] Factory selects provider based on `LLM_PROVIDER`
- [x] System + context-injection prompt templates implemented
- [x] `pytest tests/test_llm_providers.py` passes


---

## Phase 15: RAG Pipeline, Chat History & Chat API

### 1. Phase Objective
Build the RAG pipeline that retrieves relevant chunks and generates grounded, streamed answers with citations, persist chat history, and expose the chat endpoints.

### 2. Why This Phase Exists
This is where search (Phase 13) and the LLM abstraction (Phase 14) combine into the product's headline AI-assistant feature. It's kept as one phase because retrieval, generation, and persistence are tightly interdependent here — splitting them further would create phases that can't be meaningfully tested in isolation.

### 3. Prerequisites
Phase 13 complete (search/embeddings) and Phase 14 complete (LLM provider abstraction + prompts).

### 4. Current Repository Expectations
`CodeChunk` rows are searchable. LLM provider abstraction exists and is independently tested. No chat models, RAG service, or chat endpoints exist yet.

### 5. Implementation Tasks
**RAG pipeline** (`app/services/rag_service.py`):
- `answer(repo_id: UUID, question: str, db: AsyncSession, stream: bool) -> AsyncIterator[str]`:
  1. Embed question using `EmbeddingService`.
  2. Retrieve top-K chunks via vector search (K=8 default, configurable).
  3. Optionally retrieve graph neighbors of the most relevant file nodes.
  4. Deduplicate and rank chunks by relevance.
  5. Build prompt: system prompt + formatted context + question.
  6. Token counting: trim context if it would exceed `max_context_tokens * 0.7` (leave room for answer).
  7. Call LLM with streaming.
  8. Yield answer tokens. At the end, append a `__sources__` JSON block with cited file paths and line numbers.

**Chat history** (`app/models/chat_session.py`, `app/models/chat_message.py` + `app/services/chat_service.py`):
- `ChatSession`: `id`, `repository_id`, `created_at`.
- `ChatMessage`: `id`, `session_id`, `role`, `content`, `sources` (JSONB), timestamps.
- Multi-turn: include last N messages in the prompt (N=6 or until token budget exceeded).

**API endpoints** in `app/api/v1/chat.py`:
- `POST /api/v1/repositories/{repo_id}/chat/sessions` — create a new chat session, returns `{session_id}`.
- `POST /api/v1/repositories/{repo_id}/chat/sessions/{session_id}/messages` — send a message. Body: `{"question": "..."}`. Returns streaming SSE response.
- `GET /api/v1/repositories/{repo_id}/chat/sessions/{session_id}/messages` — retrieve message history.

### 6. Files / Directories

```
backend/
├── app/
│   ├── models/
│   │   ├── chat_session.py
│   │   └── chat_message.py
│   ├── services/
│   │   ├── rag_service.py
│   │   └── chat_service.py
│   ├── api/v1/
│   │   └── chat.py
│   └── schemas/
│       └── chat.py
├── alembic/versions/
│   └── 0005_chat_tables.py
└── tests/
    └── test_rag.py
```

### 7. Technical Requirements
- Streaming: FastAPI `StreamingResponse` with `media_type="text/event-stream"`. Each SSE event: `data: <token>\n\n`. Final event: `data: [DONE]\n\n`.
- Sources format in stream: at stream end, emit a special event `data: __sources__:<json_array>\n\n`.

### 8. Integration Requirements
- Chat endpoints registered in router.
- `EmbeddingService` and `LLMProvider` injected via FastAPI dependencies.

### 9. API Contract Requirements
Introduces the full chat contract from **API Contract → Chat contract** and **SSE / event formats — AI chat streaming**. Chat is now publicly available (see Phase Dependency Map capability table).

### 10. Testing
- `test_rag.py`:
  - Mock both `EmbeddingProvider` and `LLMProvider`.
  - Insert a fake `CodeChunk` with a deterministic embedding.
  - Call `answer()` with a matching question → assert response stream contains content.
  - Assert `ChatMessage` rows saved, including `sources`.

### 11. Verification
```bash
pytest tests/test_rag.py -v
curl -N -X POST http://localhost:8000/api/v1/repositories/{id}/chat/sessions \
  -H "Content-Type: application/json" -d '{}'
curl -N -X POST http://localhost:8000/api/v1/repositories/{id}/chat/sessions/{sid}/messages \
  -H "Content-Type: application/json" \
  -d '{"question": "What does the authentication service do?"}'
```

### 12. Completion Criteria
- [x] RAG pipeline retrieves relevant chunks and builds grounded prompts
- [x] SSE streaming response works end-to-end
- [x] Sources cited in stream response
- [x] Chat history persisted in DB
- [x] Multi-turn conversation context included in prompt
- [x] `pytest tests/test_rag.py` passes


---

## Phase 16: Files & Status API Completion

### 1. Phase Objective
Add the remaining public endpoints that don't naturally belong to an earlier capability-phase: the files API (list/detail/symbols) and the status-polling endpoint.

### 2. Why This Phase Exists
Files and status are needed by the frontend but weren't a natural fit for any single capability phase above — they surface data already produced by extraction, parsing, and the analysis job, rather than introducing new backend logic. Grouping them here keeps this a small, focused "surface the remaining data" phase ahead of the broader consistency audit in Phase 17.

### 3. Prerequisites
Phases 6–15 complete: repository CRUD, graph, search, and chat endpoints already exist and are public. `CodeFile`, `Symbol`, and `AnalysisJob` tables are populated by the pipeline.

### 4. Current Repository Expectations
Files and status data exist in the database (via debug endpoints run manually, or the full pipeline if already automated) but are not yet exposed through dedicated endpoints.

### 5. Implementation Tasks
**API endpoints** in `app/api/v1/files.py` (new):
- `GET /api/v1/repositories/{id}/files` — list files (paginated).
- `GET /api/v1/repositories/{id}/files/{file_id}` — returns `{path, language, content, line_count, symbols: [...]}`. Content read directly from disk. Binary files: `{"error": "Binary file — no content preview"}`.
- `GET /api/v1/repositories/{id}/files/{file_id}/symbols` — symbols in file.

**API endpoint** in `app/api/v1/repositories.py`:
- `GET /api/v1/repositories/{id}/status` — returns `{status, progress, phase, error_message}` — pulled from the latest `AnalysisJob` row, using the same `status`/`phase` vocabulary as the SSE stream (API Contract → Repository status vs. pipeline phase). This is the polling fallback the frontend uses before Phase 19 (SSE) exists, and whenever an SSE connection drops.

**Schemas** in `app/schemas/file.py` (new): `FileListItem`, `FileDetail`, `SymbolResponse`.

### 6. Files / Directories

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── files.py             # new
│   │   └── repositories.py      # extended with /status
│   └── schemas/
│       └── file.py              # new
└── tests/
    └── test_files_and_status_api.py
```

### 7. Technical Requirements
- Sanitize file paths — never return files outside the repo's source directory (full security hardening lands in Phase 21, but basic path containment must exist here).
- Use the shared pagination pattern established in Phase 6.

### 8. Integration Requirements
All routers included in `app/api/v1/__init__.py` and mounted in `app/main.py`.

### 9. API Contract Requirements
Introduces `GET /repositories/{id}/files`, `GET .../files/{file_id}`, `GET .../files/{file_id}/symbols`, and `GET /repositories/{id}/status`. These complete the endpoint table in **Phase Dependency Map → Internal capability vs. public API capability**.

### 10. Testing
- `test_files_and_status_api.py`: list files, get file detail (text and binary cases), get symbols for a file, and poll status at various pipeline stages.

### 11. Verification
```bash
pytest tests/test_files_and_status_api.py -v
curl http://localhost:8000/api/v1/repositories/{id}/files
curl http://localhost:8000/api/v1/repositories/{id}/status
```

### 12. Completion Criteria
- [x] Files list/detail/symbols endpoints implemented
- [x] Status polling endpoint returns the same vocabulary as the future SSE stream
- [x] Path sanitization prevents escaping the repo's source directory
- [x] `pytest tests/test_files_and_status_api.py` passes


---

## Phase 17: API Contract Consistency Audit & OpenAPI Docs

### 1. Phase Objective
Audit every endpoint introduced since Phase 5 for consistent error/pagination/timestamp formatting, and finalize OpenAPI documentation. This phase does not introduce REST APIs for the first time — it completes and standardizes what surrounds the capability-specific endpoints already public.

### 2. Why This Phase Exists
Endpoints built incrementally across many phases can drift from the canonical formats. A dedicated audit phase, run once all endpoints exist, is the cheapest place to catch and fix inconsistencies — and it produces the OpenAPI documentation the frontend and any external consumer will rely on.

### 3. Prerequisites
Phase 16 complete: all endpoints listed in the audit table below exist.

### 4. Current Repository Expectations
All endpoints exist but response formatting (pagination, errors, timestamps) may be inconsistent across endpoints built in earlier phases.

### 5. Implementation Tasks
**Audit & complete all endpoints:**

| Route | Method | Description |
|---|---|---|
| `/api/v1/repositories` | GET | List repos |
| `/api/v1/repositories` | POST | Upload zip |
| `/api/v1/repositories/clone` | POST | Git clone |
| `/api/v1/repositories/{id}` | GET | Get repo detail |
| `/api/v1/repositories/{id}` | DELETE | Delete repo |
| `/api/v1/repositories/{id}/status` | GET | Polling status |
| `/api/v1/repositories/{id}/files` | GET | List files (paginated) |
| `/api/v1/repositories/{id}/files/{file_id}` | GET | File detail + content |
| `/api/v1/repositories/{id}/files/{file_id}/symbols` | GET | Symbols in file |
| `/api/v1/repositories/{id}/graph` | GET | Full graph JSON |
| `/api/v1/repositories/{id}/graph/node/{file_id}` | GET | Node detail |
| `/api/v1/repositories/{id}/search` | POST | Semantic search |
| `/api/v1/repositories/{id}/chat/sessions` | POST | Create session |
| `/api/v1/repositories/{id}/chat/sessions/{sid}` | GET | Session detail |
| `/api/v1/repositories/{id}/chat/sessions/{sid}/messages` | POST | Send message (SSE) |
| `/api/v1/repositories/{id}/chat/sessions/{sid}/messages` | GET | Message history |
| `/health` | GET | Health check |

**Consistency requirements:**
- All error responses: `{"error": {"code": "REPO_NOT_FOUND", "message": "...", "details": {}}}`.
- All list endpoints: `{"items": [...], "total": N, "page": 1, "page_size": 20}`.
- All timestamps: ISO 8601 UTC.
- UUIDs as strings in responses.

**Common schemas** — extract `app/schemas/common.py`: `PaginationParams`, `ErrorResponse`, `PaginatedResponse`; refactor existing endpoints to use them.

**OpenAPI:**
- Set `FastAPI(title="CodeGraph v2 API", version="2.0.0", description="...")`.
- All endpoints have `summary`, `description`, `tags`.
- All schemas have field descriptions.
- Accessible at `/docs` (Swagger) and `/redoc`.

### 6. Files / Directories

```
backend/
├── app/
│   ├── api/v1/
│   │   └── __init__.py       # aggregates all routers, confirmed complete
│   └── schemas/
│       └── common.py         # new: PaginationParams, ErrorResponse, PaginatedResponse
└── tests/
    └── test_api_consistency.py
```

### 7. Technical Requirements
- Use FastAPI `APIRouter` with `prefix` and `tags` consistently across all routers.
- Common `PaginationParams` dependency: `page: int = 1`, `page_size: int = 20` (max 100), applied to every list endpoint.

### 8. Integration Requirements
All routers already included from earlier phases; this phase only refactors their internals for consistency, without changing route paths.

### 9. API Contract Requirements
This phase is the authoritative point at which every endpoint conforms to **API Contract — Source of Truth**. If any endpoint's actual shape needed adjusting to match the contract, update the API Contract section to reflect the final, agreed-upon shape and note the change.

### 10. Testing
- `test_api_consistency.py`: for every endpoint in the audit table, assert error responses use the canonical shape, list endpoints use the canonical pagination shape, and timestamps/UUIDs are serialized correctly.

### 11. Verification
```bash
pytest tests/test_api_consistency.py -v
# Visit http://localhost:8000/docs — all endpoints documented
# Run a full happy-path curl flow: upload → wait → search → chat
```

### 12. Completion Criteria
- [x] All endpoints in the table above implemented and documented
- [x] Error responses consistently formatted across every endpoint
- [x] List endpoints paginated with the canonical shape
- [x] OpenAPI docs accessible and complete at `/docs` and `/redoc`
- [x] `pytest tests/test_api_consistency.py` passes


---

## Phase 18: Background Job System (Celery + Redis)

### 1. Phase Objective
Wire ingestion through indexing into an automated Celery pipeline. A single task chain runs: ingest → extract → parse → build_graph → index. Progress is tracked in `AnalysisJob`.

### 2. Why This Phase Exists
Until now, the pipeline has been triggered manually via debug endpoints for testability. This phase is what makes CodeGraph actually usable end-to-end without a human running each step by hand — it's the automation layer the whole product depends on, matching the original roadmap's scoping for this milestone.

### 3. Prerequisites
Phases 5–17 complete: every pipeline stage works individually (via debug endpoints), and the full public API surface is documented and consistent.

### 4. Current Repository Expectations
Redis is running at `REDIS_URL`. Ingestion, extraction, parsing, graph, and indexing all work when triggered manually via debug endpoints, but nothing runs automatically after upload/clone yet.

### 5. Implementation Tasks
**Celery app** (`app/workers/celery_app.py`):
- Create `Celery` instance configured with Redis as both broker and result backend.
- Configure: `task_serializer="json"`, `result_expires=3600`, `worker_prefetch_multiplier=1`.
- Task routing: analysis tasks → `"analysis"` queue.

**Task chain** (`app/tasks/analysis.py`):
```
chain(
  ingest_repository.s(repo_id),
  extract_files.s(),
  parse_repository.s(),
  build_repository_graph.s(),
  index_repository.s(),
)
```
- Each task: loads repo from DB, runs the corresponding service, updates `AnalysisJob.phase` and `AnalysisJob.progress`, passes `repo_id` to next task, and publishes the same `{status, progress, phase}` payload to Redis for Phase 19 to relay over SSE.
- On any failure: mark `AnalysisJob.status = "failed"`, set `Repository.status = "error"` + `error_message`.
- `AnalysisJob.phase` / progress increments, matching the canonical five-phase list in **API Contract — Source of Truth → Repository status vs. pipeline phase**: `ingestion`=10, `extraction`=25, `parsing`=50, `graph`=70, `indexing`=100.

**Trigger:**
- After `POST /api/v1/repositories` or `/clone` succeeds, immediately call `analysis_chain.delay(repo_id)`.
- Remove the debug `/extract` and `/parse` endpoints (or leave as `admin_only` flag).

**Retry policy:**
- Max 3 retries with exponential backoff for transient failures.
- Do NOT retry on validation errors (e.g., corrupted zip).

### 6. Files / Directories

```
backend/
├── app/
│   ├── workers/
│   │   └── celery_app.py
│   └── tasks/
│       └── analysis.py
└── tests/
    └── test_tasks.py
```

### 7. Technical Requirements
- Use `celery.canvas.chain`.
- Tasks use a synchronous DB session (not async) — Celery workers are synchronous. Use `sqlalchemy` with `create_engine` (sync) inside tasks, or `asyncio.run()` inside each task to call async service functions. Either approach is acceptable; document the decision in the completion report.

### 8. Integration Requirements
- `POST /api/v1/repositories` → triggers `analysis_chain.delay(str(repo.id))` before returning response.
- `GET /api/v1/repositories/{id}/status` (Phase 16) reads from `AnalysisJob` for live progress.

### 9. API Contract Requirements
No new endpoints. Removes the debug `/extract` and `/parse` endpoints from the stable surface (they were never part of the documented public contract — see Phase Dependency Map capability table).

### 10. Testing
- `test_tasks.py`: use `celery.contrib.pytest` to run tasks eagerly (`CELERY_TASK_ALWAYS_EAGER=True`). Test that the chain runs on a test zip and all DB records end up correct.

### 11. Verification
```bash
celery -A app.workers.celery_app worker -Q analysis -l info
curl -X POST http://localhost:8000/api/v1/repositories -F "file=@tests/fixtures/sample_repo.zip"
watch -n2 "curl -s http://localhost:8000/api/v1/repositories/{id}/status"
```

### 12. Completion Criteria
- [ ] Celery app configured with Redis
- [ ] Full pipeline chain runs automatically after upload
- [ ] `AnalysisJob` progress updated at each stage
- [ ] Failed tasks set `Repository.status = "error"`
- [ ] `pytest tests/test_tasks.py` passes (eager mode)


---

## Phase 19: Real-time Updates (SSE)

### 1. Phase Objective
Push repository processing progress to the frontend in real-time using Server-Sent Events so users don't need to poll.

### 2. Why This Phase Exists
This phase depends directly on Phase 18's Redis pub/sub publishing, and delivers the live-progress capability the frontend's processing UI (`FRONTEND.md → Phase 9`) is built around. It remains its own phase because it's a distinct transport-layer concern from the background job orchestration itself.

### 3. Prerequisites
Phase 18 complete: Redis is available, Celery workers publish progress events.

### 4. Current Repository Expectations
The automated pipeline runs and updates `AnalysisJob`, but nothing publishes to Redis pub/sub yet; no SSE endpoint exists.

### 5. Implementation Tasks
**Event publishing** (in Celery tasks from Phase 18):
- After each pipeline stage, publish a Redis pub/sub message using the exact `phase` values from **API Contract — Source of Truth**: `{"repo_id": "...", "status": "...", "progress": N, "phase": "ingestion"|"extraction"|"parsing"|"graph"|"indexing"}`.
- Channel: `repo_events:{repo_id}`.

**SSE endpoint** (`app/api/v1/events.py`):
- `GET /api/v1/repositories/{repo_id}/events` — SSE stream.
- Subscribe to Redis channel `repo_events:{repo_id}` using `redis.asyncio`.
- Yield SSE events as they arrive, including `phase`: `data: {"status": "parsing", "progress": 50, "phase": "parsing"}\n\n`.
- Send a keepalive `:ping\n\n` every 15 seconds.
- Auto-close stream when `status = "ready"` or `status = "error"`.

### 6. Files / Directories

```
backend/
├── app/
│   ├── api/v1/
│   │   └── events.py
│   └── core/
│       └── redis_client.py
└── tests/
    └── test_sse.py
```

### 7. Technical Requirements
- `redis.asyncio.from_url(settings.REDIS_URL)` for the async Redis client.
- FastAPI `StreamingResponse(event_generator(), media_type="text/event-stream")`.
- Handle client disconnect: `asyncio.CancelledError` → unsubscribe cleanly.

### 8. Integration Requirements
- SSE endpoint included in router.
- Redis client created in lifespan and stored in `app.state.redis`.

### 9. API Contract Requirements
Introduces `GET /api/v1/repositories/{id}/events` per **API Contract → SSE / event formats — Repository progress SSE**. Live progress is now publicly available (see Phase Dependency Map capability table).

### 10. Testing
- `test_sse.py`: use `httpx` async client with `stream()` to connect to SSE; publish a mock event to Redis; assert it appears in the stream.

### 11. Verification
```bash
pytest tests/test_sse.py -v
curl -N http://localhost:8000/api/v1/repositories/{id}/events
```

### 12. Completion Criteria
- [ ] SSE endpoint streams processing events
- [ ] Keepalive pings sent every 15 seconds
- [ ] Stream closes automatically on `ready`/`error`
- [ ] Redis pub/sub wired from Celery tasks
- [ ] `pytest tests/test_sse.py` passes


---

## Phase 20: API Key Authentication & Key Management

### 1. Phase Objective
Replace the Phase 2 auth stub with real, enforceable API-key authentication and key management — the first half of the security foundation required before CodeGraph v2 can be safely exposed as a hosted/multi-user service.

### 2. Why This Phase Exists
Splitting authentication (identity) from rate limiting and input hardening (abuse prevention, Phase 21) keeps each phase testable against a single concern: this phase asks "is the request from someone with a valid key," Phase 21 asks "is this request-rate/shape acceptable." Combining them made the original single phase harder to verify cleanly.

### 3. Prerequisites
Phase 2 complete (auth stub exists). Does not require Phases 3-19, though it's sequenced after them because it hardens endpoints they created.

### 4. Current Repository Expectations
Since Phase 2, every request has accepted an optional `X-API-Key` header via `get_current_key_optional()`, but `REQUIRE_AUTH=false` by default means nothing has been enforced yet — all APIs have been open in local/self-hosted developer mode.

### 5. Implementation Tasks
### Local/self-hosted developer mode vs. hosted/production mode

- **Local/self-hosted (default):** `REQUIRE_AUTH=false`. A single developer runs CodeGraph v2 against their own machine or trusted network; there is no meaningful attacker model, so this phase does not force key management on them. This remains the default after this phase ships — nothing changes for existing local users unless they opt in.
- **Hosted/multi-user production:** `REQUIRE_AUTH=true` (and typically `REQUIRE_AUTH_FOR_READS=true`). This phase is what makes that mode *safe* to turn on. Do not build multi-tenant user accounts, OAuth, or per-user billing here — that is out of scope for v2; API keys are the entire auth model.

**API key auth** (`app/core/auth.py` — replaces the Phase 2 stub body, same function name/signature):
- Simple API-key scheme (no OAuth for v2 — overkill for a developer tool). API keys stored in DB (`ApiKey` model: `id`, `key_hash`, `label`, `owner_id` (nullable), `created_at`, `last_used_at`).
- `X-API-Key` header checked on all `POST`, `PUT`, `DELETE` endpoints when `REQUIRE_AUTH=true`. `GET` endpoints are optionally authenticated (read-only public by default, configurable via `REQUIRE_AUTH_FOR_READS` setting).
- `get_current_key()` FastAPI dependency: hashes incoming key, looks up DB, returns `ApiKey`. Raises `401 {"error": {"code": "AUTH_REQUIRED", ...}}` if missing/invalid **only when `REQUIRE_AUTH=true`**; otherwise behaves exactly like the Phase 2 stub.
- Bootstrap: a `ADMIN_API_KEY` env var creates a default key on startup if no keys exist.

### 6. Files / Directories

```
backend/
├── app/
│   ├── core/
│   │   └── auth.py           # replaces stub body
│   └── models/
│       └── api_key.py
├── alembic/versions/
│   └── 0006_api_keys.py
└── tests/
    └── test_auth.py
```

### 7. Technical Requirements
- Hashing: `hashlib.sha256(key.encode()).hexdigest()` — store hash, never plaintext.
- Key generation: `secrets.token_urlsafe(32)`.

### 8. Integration Requirements
- `get_current_key` dependency applied to all mutating endpoints (replacing `get_current_key_optional` from Phase 2 without changing call sites).

### 9. API Contract Requirements
No new endpoints. Activates the `401 {"error": {"code": "AUTH_REQUIRED"}}` response described in **API Contract → Authentication strategy** whenever `REQUIRE_AUTH=true`.

### 10. Testing
- `test_auth.py`:
  - With `REQUIRE_AUTH=false` (default): request without API key → 200 (unchanged from earlier phases).
  - With `REQUIRE_AUTH=true`: request without API key → 401; request with invalid key → 401; request with valid key → 200.

### 11. Verification
```bash
pytest tests/test_auth.py -v
curl -X POST http://localhost:8000/api/v1/repositories -F "file=@..." # 200 (default mode)
curl -X POST http://localhost:8000/api/v1/repositories -F "file=@..." # 401 (REQUIRE_AUTH=true)
curl -X POST http://localhost:8000/api/v1/repositories -H "X-API-Key: your_key" -F "file=@..." # 200
```

### 12. Completion Criteria
- [ ] With `REQUIRE_AUTH=false`, behavior is unchanged from earlier phases (still open, still accepts an optional key)
- [ ] With `REQUIRE_AUTH=true`, all mutating endpoints require a valid `X-API-Key`
- [ ] Invalid keys return 401 with the canonical error format
- [ ] Bootstrap key created from `ADMIN_API_KEY` on first startup
- [ ] `pytest tests/test_auth.py` passes for both `REQUIRE_AUTH` modes


---

## Phase 21: Rate Limiting & Security Hardening

### 1. Phase Objective
Add per-key rate limiting, input validation hardening, and security headers — completing the security foundation started in Phase 20.

### 2. Why This Phase Exists
Rate limiting and request-shape hardening are abuse-prevention concerns distinct from identity verification (Phase 20), and can be implemented and tested independently once `get_current_key()` exists to key rate limits off of.

### 3. Prerequisites
Phase 20 complete: `get_current_key()` and the `ApiKey` model exist.

### 4. Current Repository Expectations
Authentication is enforced when `REQUIRE_AUTH=true`, but there is no rate limiting, and request-size/path-sanitization hardening beyond Phase 16's basic containment is not yet in place.

### 5. Implementation Tasks
**Rate limiting** (`app/core/rate_limiter.py`):
- Use `slowapi` (or Redis-backed custom implementation). Limits per API key:
  - 100 requests/minute for general endpoints.
  - 10 repository uploads/hour.
  - 60 chat messages/hour.

**Input validation hardening:**
- Validate all UUIDs via Pydantic `UUID` type (prevents SQL injection via path params).
- Max request body size: 600MB (overriding uvicorn default). Configure via `app.add_middleware(RequestSizeLimitMiddleware, max_content_size=...)`.
- Sanitize file paths in `GET .../files/{file_id}` — never return files outside the repo's source directory (harden the basic containment added in Phase 16).

**Security headers** (add middleware):
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`: strict policy for API (no HTML served).

### 6. Files / Directories

```
backend/
├── app/
│   └── core/
│       └── rate_limiter.py
└── tests/
    └── test_rate_limiting.py
```

### 7. Technical Requirements
- `slowapi`: `from slowapi import Limiter; limiter = Limiter(key_func=get_api_key)`.

### 8. Integration Requirements
- Rate limiter state attached to app; limits applied per-route via decorator or dependency.
- Security header middleware added in `app/main.py` `create_app()`.

### 9. API Contract Requirements
No new endpoints. Activates `429` responses per **API Contract → Error format** when limits are exceeded.

### 10. Testing
- `test_rate_limiting.py`: exceed rate limit → assert 429; assert security headers present on responses; assert oversized request body rejected; assert path traversal in file requests rejected.

### 11. Verification
```bash
pytest tests/test_rate_limiting.py -v
```

### 12. Completion Criteria
- [ ] Rate limits enforced (429 when exceeded) per the limits above
- [ ] Security headers present on all responses
- [ ] Request body size limit enforced
- [ ] File path sanitization confirmed to prevent directory escape
- [ ] `pytest tests/test_rate_limiting.py` passes


---

## Phase 22: Observability, Metrics & Health Checks

### 1. Phase Objective
Add structured logging throughout the pipeline, Prometheus metrics, detailed health checks, and request tracing.

### 2. Why This Phase Exists
With the full feature set and security model in place, this phase makes the system operable — the last piece needed before the production-readiness and testing phases that close out the roadmap.

### 3. Prerequisites
Phase 21 complete: the full API surface exists and is secured.

### 4. Current Repository Expectations
Basic `structlog` setup exists from Phase 2, but no per-request context binding, metrics, or enhanced health checks exist yet.

### 5. Implementation Tasks
**Structured logging:**
- Add `structlog` context: every request gets a `request_id` (UUID) bound to the log context via middleware.
- Log: request start/end (method, path, status, duration), Celery task start/complete/fail, LLM call (provider, model, tokens, duration — no content), embedding call (count, duration), DB query duration (slow query log > 500ms).

**Prometheus metrics** (`app/core/metrics.py`):
- Use `prometheus-fastapi-instrumentator` for automatic HTTP metrics.
- Custom metrics:
  - `codegraph_repositories_total{status}` (Counter)
  - `codegraph_analysis_duration_seconds{phase}` (Histogram)
  - `codegraph_llm_tokens_total{provider,type}` (Counter — prompt vs completion)
  - `codegraph_chunks_indexed_total` (Counter)
- Expose `/metrics` endpoint (Prometheus scrape target).

**Health check enhancement:**
- `GET /health` returns:
```json
{
  "status": "ok",
  "version": "2.0.0",
  "checks": {
    "database": "ok",
    "redis": "ok",
    "celery": "ok"
  }
}
```
- Each check makes a real probe (DB ping, Redis ping, Celery inspect ping).

**Request tracing:**
- Generate `X-Request-ID` header on every response. Log the same ID. Return it to clients.

### 6. Files / Directories

```
backend/
├── app/
│   ├── core/
│   │   └── metrics.py
│   └── middleware/
│       ├── request_id.py
│       └── logging_middleware.py
└── tests/
    └── test_health_observability.py
```

### 7. Technical Requirements
- `prometheus-fastapi-instrumentator`: `Instrumentator().instrument(app).expose(app)`.
- Request ID middleware: before route handling, generate UUID, store in `request.state.request_id`, add to response headers.

### 8. Integration Requirements
- All middleware added in `app/main.py` `create_app()`.
- Metrics endpoint at `/metrics`.

### 9. API Contract Requirements
Extends the existing `/health` response shape (additive — adds `checks`, does not remove existing fields). Adds `/metrics` (not versioned under `/api/v1`, Prometheus convention).

### 10. Testing
- Extend health tests: assert `/health` includes `checks` dict with all services; assert `X-Request-ID` present in response headers.

### 11. Verification
```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics | grep codegraph
pytest tests/test_health_observability.py -v
```

### 12. Completion Criteria
- [ ] Every request logs `request_id`, path, status, duration as JSON
- [ ] `/metrics` returns Prometheus data including the four custom metrics
- [ ] `/health` checks DB + Redis + Celery
- [ ] `X-Request-ID` in all responses
- [ ] `pytest tests/test_health_observability.py` passes


---

## Phase 23: Unit & Integration Testing Suite

### 1. Phase Objective
Fill remaining coverage gaps with a deliberate unit and integration testing pass: shared fixtures, edge-case unit tests for core algorithms, and integration tests exercising real DB + mocked external APIs.

### 2. Why This Phase Exists
Every prior phase already wrote focused tests for its own scope; this phase is where the agent steps back and closes gaps across the whole system — shared fixtures, cross-cutting edge cases, and integration-level assertions that no single earlier phase owned. Splitting end-to-end/coverage-gating into Phase 24 keeps this phase's runtime fast (no real services required).

### 3. Prerequisites
Phase 22 complete. Individual test files exist from every earlier phase.

### 4. Current Repository Expectations
Per-phase test files exist and pass, but there is no shared `conftest.py` fixture set, and coverage has not been measured holistically.

### 5. Implementation Tasks
**Test infrastructure:**
- `conftest.py`: async test client fixture, test database fixture (creates fresh schema, drops after test session), mock Redis fixture, mock LLM provider fixture.
- Separate `.env.test` for test settings (in-memory SQLite is NOT suitable — use a real Postgres test DB for pgvector).

**Unit tests** (mock all I/O) — fill gaps not already covered by earlier phases:
- `test_chunker.py`: edge cases — empty file, huge function, file with no symbols (extend Phase 12's tests if needed).
- `test_language_detector.py`: all supported extensions + ambiguous cases (extend Phase 8's tests if needed).
- `test_import_resolver.py`: relative imports, external packages, stdlib detection (extend Phase 10's tests if needed).
- `test_graph_builder.py`: cycle detection, pagerank correctness, disconnected subgraphs (extend Phase 11's tests if needed).
- `test_rag_pipeline.py`: context truncation, source extraction from stream (extend Phase 15's tests if needed).

**Integration tests** (real DB, mocked external APIs):
- `test_full_pipeline.py`: upload `sample_repo.zip` → trigger pipeline in eager mode → assert `Repository.status = "ready"`, correct file count, symbol count, graph exists, chunks indexed.
- `test_search_integration.py`: index sample repo, run semantic search, assert results.
- `test_chat_integration.py`: create session, send message (mocked LLM), assert message saved, stream received.

### 6. Files / Directories

```
backend/
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_chunker.py
    │   ├── test_language_detector.py
    │   ├── test_import_resolver.py
    │   ├── test_graph_builder.py
    │   └── test_rag_pipeline.py
    └── integration/
        ├── test_full_pipeline.py
        ├── test_search_integration.py
        └── test_chat_integration.py
```

### 7. Technical Requirements
- `pytest-cov` for coverage.
- `pytest-asyncio` in `asyncio_mode = "auto"`.
- `respx` or `pytest-httpx` for mocking external HTTP calls (OpenAI, Anthropic).
- `freezegun` for time-sensitive tests.

### 8. Integration Requirements
None — this phase only adds/consolidates tests; it does not change application code except to fix bugs the new tests reveal.

### 9. API Contract Requirements
None. If a test reveals a genuine contract inconsistency, fix the implementation to match **API Contract — Source of Truth** (or update that section and note the change) rather than changing the test to match broken behavior.

### 10. Testing
This entire phase is testing — see Implementation Tasks above for the full list.

### 11. Verification
```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest --cov=app --cov-report=term-missing
```

### 12. Completion Criteria
- [ ] Shared `conftest.py` fixtures in place (test DB, mock Redis, mock LLM provider)
- [ ] All unit test files created and passing
- [ ] All integration tests passing against a real test database with mocked external APIs
- [ ] No flaky tests (run suite 3 times, all pass)


---

## Phase 24: End-to-End Testing & Coverage Enforcement

### 1. Phase Objective
Add an end-to-end smoke test against real running services, and enforce the ≥80% coverage gate across the whole test suite.

### 2. Why This Phase Exists
E2E tests need real services (DB, Redis, worker) running and are slow and environment-dependent, unlike the mocked unit/integration suite from Phase 23. Isolating them means the fast suite (Phase 23) can run in any environment, while this phase's slower, more fragile tests are clearly separated and explicitly skippable.

### 3. Prerequisites
Phase 23 complete: unit and integration suites pass.

### 4. Current Repository Expectations
Unit and integration tests pass. No E2E smoke test or coverage gate exists yet.

### 5. Implementation Tasks
**End-to-end smoke test** (`tests/e2e/test_smoke.py`):
- Requires real services running. Skipped if `E2E=false` env var.
- Upload → poll status to `ready` → search → chat.

**Coverage enforcement:**
```bash
pytest --cov=app --cov-report=html --cov-fail-under=80
```
Wire this into the project's standard test command (e.g. a `make test` target or CI script reference) so ≥80% becomes a hard gate going forward.

### 6. Files / Directories

```
backend/
└── tests/
    └── e2e/
        └── test_smoke.py
```

### 7. Technical Requirements
- `pytest-cov` `--cov-fail-under=80` as the enforced gate.
- E2E test should be clearly marked (e.g. `@pytest.mark.e2e`) and excluded from the default fast test run.

### 8. Integration Requirements
None — this phase only adds a test and a coverage gate.

### 9. API Contract Requirements
None.

### 10. Testing
- `tests/e2e/test_smoke.py`: full happy-path flow against real running services (or skip cleanly if `E2E=false`).

### 11. Verification
```bash
E2E=true pytest tests/e2e/ -v      # requires real services running
pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

### 12. Completion Criteria
- [ ] E2E smoke test implemented and skippable via `E2E=false`
- [ ] Code coverage ≥ 80% across the full suite
- [ ] Coverage gate wired into the standard test command


---

## Phase 25: Production Readiness & Docker

### 1. Phase Objective
Containerize the entire backend stack (API, Celery worker, Redis, PostgreSQL) with Docker Compose. Add production configuration. Ensure the system is deployable.

### 2. Why This Phase Exists
This is the final phase of the backend roadmap — it packages everything built in Phases 1–24 into a deployable unit and documents how to run it, matching the original roadmap's closing milestone.

### 3. Prerequisites
Phases 1–24 complete. All tests passing.

### 4. Current Repository Expectations
The full application works when run manually (`uvicorn` + `celery worker` + local Postgres/Redis), but there is no Dockerfile, Compose file, or production configuration yet.

### 5. Implementation Tasks
**Dockerfile** (`backend/Dockerfile`):
- Multi-stage build: `builder` stage installs dependencies; `runtime` stage is slim.
- Non-root user.
- Health check: `CMD curl -f http://localhost:8000/health || exit 1`.

**Docker Compose** (`docker-compose.yml` at project root):
```yaml
services:
  postgres:      # postgres:16 with pgvector extension
  redis:         # redis:7-alpine
  api:           # backend image, PORT=8000
  worker:        # same image, CMD = celery worker
  flower:        # celery flower monitoring (optional)
```

**Production configuration:**
- `uvicorn` with `--workers 4` (or `gunicorn` with uvicorn workers).
- `ENVIRONMENT=production` disables debug, enables JSON logging, disables auto-migration on startup.
- Database connection pooling: `pool_size=10`, `max_overflow=20`.
- Alembic migration run as a separate startup step (not inside API process in production).

**`Makefile`** (developer convenience):
```makefile
make dev          # start docker-compose dev stack
make migrate      # run alembic upgrade head
make test         # run pytest
make lint         # run ruff + mypy
make worker       # start celery worker locally
```

**`README.md`** (backend):
- Setup instructions, env vars, how to run, how to run tests, API docs URL.

### 6. Files / Directories

```
backend/
├── Dockerfile
├── docker-compose.yml    # at project root (shared with frontend)
├── Makefile
└── README.md
```

### 7. Technical Requirements
- Use `pgvector/pgvector:pg16` Docker image (includes pgvector).
- Redis: `redis:7-alpine`.
- Use Docker secrets or environment variables from `.env`.

### 8. Integration Requirements
- Frontend's `docker-compose.yml` will add a `frontend` service to the same file (`FRONTEND.md → Phase 18`).

### 9. API Contract Requirements
None — this phase is packaging only. Confirms operational details in **Backend → Frontend Handoff** below.

### 10. Testing
```bash
docker-compose up --build
curl http://localhost:8000/health
make test
```

### 11. Verification
```bash
docker-compose up -d
docker-compose ps                    # all services healthy
curl http://localhost:8000/health    # {"status":"ok","checks":{...}}
docker-compose logs worker           # no errors
```

### 12. Completion Criteria
- [ ] `docker-compose up` starts all services without errors
- [ ] API reachable at `localhost:8000`
- [ ] Celery worker running and processing tasks
- [ ] `alembic upgrade head` runs in container
- [ ] All tests pass inside Docker (`docker-compose run api pytest`)
- [ ] `README.md` complete and accurate


---

## Backend → Frontend Handoff

> This section documents how to run the backend and confirms the final, shipped contract. For request/response schemas, error format, pagination, status/phase vocabulary, and SSE formats, see **API Contract — Source of Truth** above — this section does not repeat them, only confirms operational details and anything that only becomes true once all 25 phases are complete.

### Backend Startup

```bash
# Development (local):
cd backend
cp .env.example .env   # fill in values
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Celery worker (separate terminal):
celery -A app.workers.celery_app worker -Q analysis -l info

# Or via Docker Compose:
docker-compose up
```

### Environment Variables (Frontend needs to know)

| Variable | Value |
|---|---|
| `API_BASE_URL` | `http://localhost:8000` (dev) |
| `API_VERSION` | `v1` |

### Authentication

- Header: `X-API-Key: <key>`.
- **Local/self-hosted mode (default, `REQUIRE_AUTH=false`):** no key is required for any request; the frontend does not need one configured to use the app.
- **Hosted/production mode (`REQUIRE_AUTH=true`, available once Phase 20 ships):** required on all `POST`, `PUT`, `DELETE` requests (and on `GET` too if `REQUIRE_AUTH_FOR_READS=true`).
- The frontend sends `X-API-Key` on every request whenever a key is configured, but must not assume one is required — see `FRONTEND.md → Phase 6` for the reactive-401 flow that works in both modes without the frontend knowing in advance which mode the backend is running in.
- Bootstrap key available via `ADMIN_API_KEY` env var (shown in server logs on first startup) once auth is enforced.
- **Do not store a long-lived API key in browser `localStorage` for a hosted/production deployment** — see `FRONTEND.md → API Key Storage` for the local-vs-hosted boundary.

### API Base URL

All endpoints: `{API_BASE_URL}/api/v1/...` (development: `http://localhost:8000`).

### CORS

`CORS_ORIGINS` must include the frontend origin. In development: `http://localhost:5173`.

### WebSocket/SSE

Only SSE is used (no WebSocket). Because `EventSource` cannot send custom headers, the frontend uses `fetch` with `ReadableStream` for **both** the progress stream and chat streaming, so `X-API-Key` (when configured) reaches the server the same way for either stream. See `FRONTEND.md → Phase 9`.

### OpenAPI Documentation

Available at `http://localhost:8000/docs` once the backend is running.