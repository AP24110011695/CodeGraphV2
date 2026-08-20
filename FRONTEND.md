# CodeGraph v2 — Frontend Implementation Roadmap

> **Execution model:** Each day, run: `Read FRONTEND.md and execute Phase N.`
> The coding agent must read this file, inspect the actual repository, determine what has already been implemented, execute the requested phase completely, verify its own work, update the phase status table, and stop. This mirrors `BACKEND.md`'s Autonomous Execution Protocol exactly — see that file for the full step-by-step procedure (read phase → inspect repo → implement → test → lint/typecheck → build → fix failures → self-review → update status → report → stop, without automatically starting the next phase). It is not duplicated here to avoid the two files drifting out of sync; both roadmaps use the identical protocol and Phase Completion Report format.

## What the CodeGraph v2 Frontend Does

A single-page React application that lets a developer:

1. Upload a zip or paste a Git URL to ingest a repository.
2. Watch live processing progress (ingestion → extraction → parsing → graph → indexing).
3. Browse the file tree with a code viewer and symbol panel.
4. Explore an interactive dependency graph visualization.
5. Run semantic search across the codebase.
6. Chat with an AI assistant that answers questions grounded in the actual code, with streamed responses and cited sources.

---

## Autonomous Execution Protocol

Identical to `BACKEND.md → Autonomous Execution Protocol` — read it there. In short: on `Read FRONTEND.md and execute Phase N`, the coding agent reads this file, inspects the actual repository, implements the phase completely and self-verifies (tests, lint, typecheck, build), fixes its own failures, updates the phase status table, produces a Phase Completion Report in the same format as `BACKEND.md`, and stops without starting the next phase or asking the user to manually verify things it can verify itself. If a genuine blocker exists, mark the phase `BLOCKED` and explain it rather than falsely marking it complete.

---

## Phase Status

| Phase | Name                                              | Status      |
| ----- | ------------------------------------------------- | ----------- |
| 1     | Project Scaffold & Tooling                        | COMPLETED   |
| 2     | API Client Layer & Mock API Foundation            | COMPLETED   |
| 3     | Design Tokens & Core Primitives                   | COMPLETED   |
| 4     | Composite UI Components & Kitchen Sink            | COMPLETED   |
| 5     | Routing & Application Shell Layout                | COMPLETED   |
| 6     | Global State, Connection Settings & Reactive Auth | COMPLETED   |
| 7     | Repository List & Upload/Clone UI                 | COMPLETED   |
| 8     | Repository Overview Page & API Hooks              | COMPLETED   |
| 9     | Processing Status UI (Live Progress)              | COMPLETED   |
| 10    | File Tree & Code Viewer                           | COMPLETED   |
| 11    | Symbol Panel & Resizable Explorer Layout          | COMPLETED   |
| 12    | Dependency Graph Visualization                    | COMPLETED   |
| 13    | Semantic Search UI                                | COMPLETED   |
| 14    | Chat Layout, Sessions & Message Rendering         | COMPLETED   |
| 15    | Streaming, Sources & Starter Suggestions          | NOT STARTED |
| 16    | Polish, Accessibility & Responsive Design         | NOT STARTED |
| 17    | Frontend Testing Suite                            | NOT STARTED |
| 18    | Production Build & Docker                         | NOT STARTED |

Update a row to `IN PROGRESS` when starting a phase, and to `COMPLETED` only once every completion criterion and verification step in that phase actually passes. Use `BLOCKED` (with an explanation in the completion report) if a genuine blocker prevents finishing. Do not rewrite historical status entries except to move a phase forward through this lifecycle.

---

## Phase Dependency Map

```
Phase 1  Project Scaffold & Tooling
    ↓
Phase 2  API Client Layer & Mock API Foundation
    ↓
Phase 3  Design Tokens & Core Primitives
    ↓
Phase 4  Composite UI Components & Kitchen Sink
    ↓
Phase 5  Routing & Application Shell Layout
    ↓
Phase 6  Global State, Connection Settings & Reactive Auth
    ↓
Phase 7  Repository List & Upload/Clone UI
    ↓
Phase 8  Repository Overview Page & API Hooks
    ↓
Phase 9  Processing Status UI (Live Progress)
    ↓
    ├──→ Phase 10 File Tree & Code Viewer
    │        ↓
    │    Phase 11 Symbol Panel & Resizable Explorer Layout
    │
    ├──→ Phase 12 Dependency Graph Visualization
    │
    ├──→ Phase 13 Semantic Search UI
    │
    └──→ Phase 14 Chat Layout, Sessions & Message Rendering
             ↓
         Phase 15 Streaming, Sources & Starter Suggestions
             ↓
         Phase 16 Polish, Accessibility & Responsive Design
             ↓
         Phase 17 Frontend Testing Suite
             ↓
         Phase 18 Production Build & Docker
```

Phases 10–14 all depend on Phase 9 (a repository must exist and be processable) but not on each other — they can be executed in any order once Phase 9 is done, since each is a self-contained product surface (file explorer, graph, search, chat) built against the mock API from Phase 2 and, opportunistically, the real backend if it's available.

---

## Frontend ↔ Backend Dependency Matrix

Per `BACKEND.md`'s instruction, every frontend dependency below is expressed as a **capability + contract**, not a bare phase number. Backend phase numbers are included only as an informational cross-reference.

| Frontend needs                     | Capability                             | Contract                                                                                                                | Backend phase (informational)                          |
| ---------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| Phase 7 — Upload/clone UI          | Repository create (upload + git clone) | `POST /repositories`, `POST /repositories/clone` → `RepositoryResponse`                                                 | Backend Phase 5–6                                      |
| Phase 8 — Repository overview      | Repository CRUD                        | `GET/DELETE /repositories`, `GET /repositories/{id}` → `RepositoryResponse`, paginated list                             | Backend Phase 6                                        |
| Phase 9 — Processing status        | Live progress + status polling         | `GET /repositories/{id}/status` (polling fallback), `GET /repositories/{id}/events` (SSE) → `{status, progress, phase}` | Backend Phase 16 (polling), Phase 19 (SSE)             |
| Phase 10 — File tree & code viewer | File listing + content                 | `GET /repositories/{id}/files`, `GET .../files/{file_id}` → `FileDetail`                                                | Backend Phase 16                                       |
| Phase 11 — Symbol panel            | Symbols per file                       | `GET .../files/{file_id}/symbols` → `SymbolResponse[]`                                                                  | Backend Phase 16                                       |
| Phase 12 — Graph visualization     | Dependency graph                       | `GET /repositories/{id}/graph`, `GET .../graph/node/{file_id}` → `{nodes, edges, metrics}`                              | Backend Phase 11                                       |
| Phase 13 — Semantic search         | Vector search                          | `POST /repositories/{id}/search` → `SearchResult[]`                                                                     | Backend Phase 13                                       |
| Phase 14 — Chat sessions           | Chat session + history                 | `POST .../chat/sessions`, `GET .../chat/sessions/{sid}/messages`                                                        | Backend Phase 15                                       |
| Phase 15 — Chat streaming          | Streamed, sourced answers              | `POST .../chat/sessions/{sid}/messages` → SSE token stream + `__sources__`                                              | Backend Phase 15                                       |
| Phase 6 — Reactive auth            | Optional/enforced API key              | `X-API-Key` header, `401 {"error": {"code": "AUTH_REQUIRED"}}`                                                          | Backend Phase 2 (header accepted), Phase 20 (enforced) |

**Why this matters:** the frontend can be built and demoed end-to-end against the mock API (Phase 2) before any backend phase ships. When a real backend capability becomes available, the frontend swaps `mock.ts` for `client.ts` per-endpoint — see **Mock API Strategy** below — without needing to wait for "Backend Phase N" as a monolithic gate.

---

## Mock API Strategy

Early frontend phases build against `src/lib/api/mock.ts` so frontend development never blocks on backend availability.

- `src/lib/api/mock.ts` exports the same function signatures as `src/lib/api/client.ts` (both implement a shared `ApiClient` interface defined in `src/lib/api/types.ts`).
- Fixture data in `src/lib/api/fixtures/` mirrors `BACKEND.md → API Contract — Source of Truth` exactly: same field names, same enum values, same pagination shape, same error shape.
- A single environment flag (`VITE_USE_MOCK_API`, default `true` in local dev without a backend) selects which implementation `src/lib/api/index.ts` exports.
- **Mock data must never diverge from the contract.** Whenever `BACKEND.md`'s API Contract changes, update the fixtures in the same phase that consumes the change.
- Mock SSE/streaming (search progress, chat tokens) is simulated with `setInterval`/`setTimeout` chains that emit the same event shapes real SSE would.

---

## API Key Storage

- **Local/self-hosted (default):** the backend's `REQUIRE_AUTH=false`, so the frontend does not need a key at all; the settings panel's API-key field is optional and, if left blank, nothing breaks.
- **Hosted/production:** if a user points the frontend at a `REQUIRE_AUTH=true` backend, the frontend prompts for a key reactively (see Phase 6) and stores it. Store it in memory (Zustand store) for the session by default; only persist to `localStorage` if the user explicitly opts in via a "remember this key on this device" toggle, and label that toggle with a one-line warning that the key will be stored unencrypted in the browser. Never persist a key to `localStorage` silently.

---

> **Self-contained phase reminder:** every phase below follows the same template — Phase Objective, Why This Phase Exists, Prerequisites, Current Repository Expectations, Implementation Tasks, Files/Directories, Technical Requirements, Integration Requirements, API Contract Requirements, Testing, Verification, Completion Criteria — so the coding agent never needs to ask what to do. If the actual repository differs from "Current Repository Expectations," inspect it and adapt rather than assuming this roadmap is already correct.

---

## Phase 1: Project Scaffold & Tooling

### 1. Phase Objective

Initialize the Vite + React + TypeScript project with all core dependencies, linting/formatting/type-checking configured, and a directory structure ready for the design system and application code that follow.

### 2. Why This Phase Exists

Every later phase needs a working build pipeline and consistent tooling. Splitting scaffolding from the API client layer (Phase 2) keeps this phase pure setup — fast to execute and easy to verify (does it build, does it lint) before any application logic exists.

### 3. Prerequisites

None. This is the first phase of the frontend roadmap. Does not require any backend phase.

### 4. Current Repository Expectations

Expect an empty or near-empty repository, or one that already contains a `backend/` directory from `BACKEND.md`'s phases. If a `frontend/` directory already exists with partial scaffolding, inspect and complete/repair it rather than starting over.

### 5. Implementation Tasks

- Scaffold with `npm create vite@latest frontend -- --template react-ts`.
- Install and configure: `tanstack-router` (or `@tanstack/react-router`), `@tanstack/react-query`, `zustand`, `tailwindcss` (v4 or latest stable), `zod`, `react-hook-form`, `@hookform/resolvers`.
- Install dev dependencies: `vitest`, `@testing-library/react`, `@testing-library/user-event`, `jsdom`, `@playwright/test`, `eslint`, `prettier`, `typescript-eslint`.
- Configure `tsconfig.json` with `strict: true`, path alias `@/* -> src/*`.
- Configure ESLint + Prettier (consistent with the strict TypeScript setup).
- Configure `vite.config.ts`: path alias resolution, dev server proxy for `/api` → backend (`http://localhost:8000`) to avoid CORS friction in local dev.
- Build the base directory structure (see §6).
- Add a root `.gitignore` covering `node_modules/`, `dist/`, `.env.local`.

### 6. Files / Directories

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   │   ├── ui/              # design-system primitives (Phase 3-4)
│   │   └── layout/          # shell components (Phase 5)
│   ├── features/            # feature-organized modules (populated Phase 7+)
│   ├── lib/
│   │   ├── api/              # API client + mock (Phase 2)
│   │   └── utils/
│   ├── stores/               # Zustand stores (populated Phase 6)
│   ├── styles/
│   │   └── globals.css
│   └── types/
├── tests/
│   └── setup.ts
├── e2e/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── .eslintrc.cjs
└── package.json
```

### 7. Technical Requirements

- React 18+, TypeScript 5+, Vite 5+.
- Tailwind configured with the project's design tokens deferred to Phase 3 (empty/default theme for now).
- `vitest.config.ts` (or merged into `vite.config.ts`) with `environment: "jsdom"` and `tests/setup.ts` for Testing Library matchers.

### 8. Integration Requirements

None — this is the foundation. Nothing to integrate with yet.

### 9. API Contract Requirements

None. No API calls exist yet.

### 10. Testing

- A single placeholder test (`src/App.test.tsx`) confirming Vitest + Testing Library render a trivial component.

### 11. Verification

```bash
cd frontend
npm install
npm run dev          # starts without errors
npm run build        # builds without errors
npm run lint
npx tsc --noEmit
npm run test
```

### 12. Completion Criteria

- [ ] `npm run dev` starts without errors
- [ ] `npm run build` produces a `dist/` output with no errors
- [ ] `npm run lint` and `npx tsc --noEmit` pass with zero errors
- [ ] Placeholder test passes
- [ ] Directory structure from §6 exists

---

## Phase 2: API Client Layer & Mock API Foundation

### 1. Phase Objective

Build the typed API client, the mock API implementation with contract-matching fixtures, and the environment-driven switch between them — establishing how every later feature phase will talk to the backend (real or mocked).

### 2. Why This Phase Exists

Nearly every feature phase from Phase 7 onward calls into this layer via TanStack Query hooks. Building it once, matched exactly against `BACKEND.md`'s API Contract, means later phases never re-derive response shapes — they just consume `src/lib/api/index.ts`.

### 3. Prerequisites

Phase 1 complete: project scaffold, TanStack Query installed, directory structure exists.

### 4. Current Repository Expectations

`src/lib/api/` exists but is empty. No types, client, or mock implementation exist yet.

### 5. Implementation Tasks

**Shared types** (`src/lib/api/types.ts`):

- Mirror every schema in `BACKEND.md → API Contract — Source of Truth`: `Repository`, `CodeFile`, `Symbol`, `SearchResult`, `GraphResponse`, `ChatMessage`, `PaginatedResponse<T>`, `ApiError`.
- Define the `ApiClient` interface with one method per backend endpoint (even ones not implemented until later phases — stub the later ones to `throw new Error("not implemented")` in `client.ts`/`mock.ts`, filled in as each feature phase lands).

**Real client** (`src/lib/api/client.ts`):

- `fetch`-based implementation using `VITE_API_BASE_URL` env var (default `http://localhost:8000`).
- Attaches `X-API-Key` header from the auth store (Phase 6) if one is configured — does not assume one is required.
- Centralized error handling: parses the canonical `{"error": {...}}` shape, throws a typed `ApiClientError`.
- Pagination helper: builds `?page=&page_size=` query params.

**Mock client** (`src/lib/api/mock.ts`):

- Implements the same `ApiClient` interface using in-memory fixture data from `src/lib/api/fixtures/`.
- Simulates network latency (`await delay(200-500ms)`) so loading states are visible during development.
- Simulates the processing pipeline for a newly "uploaded" mock repo: `status` progresses `pending → ingesting → parsing → indexing → ready` over a few seconds when polled or subscribed to.

**Selector** (`src/lib/api/index.ts`):

- Exports `apiClient: ApiClient = import.meta.env.VITE_USE_MOCK_API === "false" ? realClient : mockClient` (mock is the default so the app runs standalone).

**Fixtures** (`src/lib/api/fixtures/`): 2–3 realistic mock repositories with files, symbols, a small graph, and canned search/chat responses — matching contract shapes exactly.

### 6. Files / Directories

```
frontend/
└── src/
    └── lib/
        └── api/
            ├── types.ts
            ├── client.ts
            ├── mock.ts
            ├── index.ts
            ├── errors.ts
            └── fixtures/
                ├── repositories.ts
                ├── files.ts
                ├── graph.ts
                └── chat.ts
```

### 7. Technical Requirements

- No axios — use native `fetch` (keeps bundle small, consistent with Vite defaults).
- `ApiClientError extends Error` with `code`, `message`, `details`, `status` fields matching the backend's error shape.

### 8. Integration Requirements

- TanStack Query's `QueryClient` will be created in Phase 6 and will call into `apiClient` from this layer — this phase only builds the client itself, not the hooks that consume it (those land per-feature in Phases 7–15).

### 9. API Contract Requirements

This phase's `types.ts` is a direct mirror of `BACKEND.md → API Contract — Source of Truth`. Whenever that contract changes in a later backend phase, this file (and the matching fixtures) must be updated in the frontend phase that first consumes the change.

### 10. Testing

- `mock.test.ts`: assert mock client returns data matching the shapes in `types.ts`; assert a mock repository's `status` progresses over time when polled.
- `client.test.ts`: mock `fetch`, assert correct URL construction, header attachment, and error parsing.

### 11. Verification

```bash
npm run test -- api
npx tsc --noEmit
```

### 12. Completion Criteria

- [ ] `ApiClient` interface covers every endpoint in the API Contract
- [ ] Mock client implements the full interface with contract-matching fixtures
- [ ] Real client correctly builds requests, attaches `X-API-Key` when present, and parses errors
- [ ] `VITE_USE_MOCK_API` switch works
- [ ] `npm run test -- api` passes

---

## Phase 3: Design Tokens & Core Primitives

### 1. Phase Objective

Establish the visual design language (colors, spacing, typography) as Tailwind/CSS tokens, and build the smallest set of reusable primitives: Button, Input, Badge, Card, Spinner, Tooltip.

### 2. Why This Phase Exists

Every UI phase from Phase 5 onward composes these primitives. Splitting tokens + primitives from composite components (Phase 4) keeps this phase small and lets the visual foundation be reviewed/adjusted before more complex components are built on top of it.

### 3. Prerequisites

Phase 1 complete: Tailwind installed and configured.

### 4. Current Repository Expectations

`tailwind.config.ts` has default theme only. `src/components/ui/` is empty.

### 5. Implementation Tasks

- Define design tokens in `tailwind.config.ts` and/or `src/styles/globals.css` (CSS variables): color palette (including a semantic scale — background, foreground, muted, accent, destructive, border), spacing scale, typography scale, border radius scale, shadow scale.
- Support light/dark mode via CSS variables + a `data-theme` attribute (theme switching UI itself is optional for this phase; the variables must exist).
- Build primitives in `src/components/ui/`, each with variants via `class-variance-authority` (or a hand-rolled `cva`-style helper):
  - `Button` (variants: primary, secondary, ghost, destructive; sizes: sm, md, lg)
  - `Input` (text, with error state)
  - `Badge` (variants: default, success, warning, error, info)
  - `Card`
  - `Spinner`
  - `Tooltip`
- Every primitive is fully typed, forwards `ref`, and accepts `className` for composition.

### 6. Files / Directories

```
frontend/
└── src/
    ├── styles/
    │   └── globals.css       # CSS variable tokens
    ├── lib/
    │   └── utils/
    │       └── cn.ts          # className merge helper (clsx + tailwind-merge)
    └── components/
        └── ui/
            ├── button.tsx
            ├── input.tsx
            ├── badge.tsx
            ├── card.tsx
            ├── spinner.tsx
            └── tooltip.tsx
```

### 7. Technical Requirements

- Use `clsx` + `tailwind-merge` for the `cn()` className utility.
- Follow the project's frontend-design guidance for distinctive, intentional visual choices rather than generic defaults — pick a real accent color and type scale, don't leave Tailwind's stock palette untouched.

### 8. Integration Requirements

None yet — Phase 4 builds composite components on top of these; Phase 5 uses them in the app shell.

### 9. API Contract Requirements

None. Pure UI.

### 10. Testing

- Render test for each primitive: `Button` renders children and responds to `onClick`; `Input` shows error state; `Badge` renders each variant.

### 11. Verification

```bash
npm run test -- components/ui
npm run build
```

Visually confirm via Storybook-less manual check: temporarily render each primitive in `App.tsx` or a dev-only route, or wait for Phase 4's kitchen-sink page.

### 12. Completion Criteria

- [ ] Design tokens defined as CSS variables, light + dark mode both work
- [ ] All 6 primitives implemented, typed, and forward refs
- [ ] `cn()` utility in place and used consistently
- [ ] Render tests pass for every primitive

---

## Phase 4: Composite UI Components & Kitchen Sink

### 1. Phase Objective

Build the composite components the rest of the app needs (Modal, Tabs, ProgressBar, CodeBlock, EmptyState, ErrorState, Skeleton, Toast) on top of Phase 3's primitives, and add a dev-only kitchen-sink page to visually verify the whole design system at once.

### 2. Why This Phase Exists

These composites are shared across many later feature phases (file viewer needs CodeBlock, processing UI needs ProgressBar, every list needs EmptyState/ErrorState/Skeleton). Building them once here, and visually verifying them together, avoids each feature phase re-inventing loading/error/empty patterns inconsistently.

### 3. Prerequisites

Phase 3 complete: design tokens and core primitives exist.

### 4. Current Repository Expectations

`src/components/ui/` has the 6 primitives from Phase 3. No composite components exist yet.

### 5. Implementation Tasks

Build in `src/components/ui/`:

- `Modal` (portal-based, focus-trapped, closes on Escape/backdrop click)
- `Tabs` (keyboard-navigable, ARIA-compliant)
- `ProgressBar` (determinate, used by the processing UI in Phase 9)
- `CodeBlock` (syntax-highlighted via Shiki, used by the file viewer in Phase 10 and chat source citations in Phase 15)
- `EmptyState` (icon + message + optional action button, used by every list/empty view)
- `ErrorState` (icon + message + retry action, used by every error boundary)
- `Skeleton` (loading placeholder, used everywhere data is fetched)
- `Toast` (notification system — provider + `useToast()` hook)

**Dev-only kitchen sink** (`src/routes/dev/kitchen-sink.tsx` or equivalent, only mounted when `import.meta.env.DEV`):

- Renders every primitive and composite with all its variants/states on one page, for fast visual QA of the whole design system.

### 6. Files / Directories

```
frontend/
└── src/
    └── components/
        └── ui/
            ├── modal.tsx
            ├── tabs.tsx
            ├── progress-bar.tsx
            ├── code-block.tsx
            ├── empty-state.tsx
            ├── error-state.tsx
            ├── skeleton.tsx
            ├── toast.tsx
            └── dev/
                └── kitchen-sink.tsx
```

### 7. Technical Requirements

- Shiki for `CodeBlock` syntax highlighting (matches the roadmap's chosen library — do not substitute Prism).
- `Modal` should use a portal (`createPortal`) to `document.body`.
- `Toast` provider wraps the app in Phase 5's shell.

### 8. Integration Requirements

- `CodeBlock` will be consumed by Phase 10 (file viewer) and Phase 15 (chat source citations).
- `ProgressBar` will be consumed by Phase 9 (processing UI).
- `Toast` provider mounted in the app shell built in Phase 5.

### 9. API Contract Requirements

None. Pure UI.

### 10. Testing

- Render tests: `Modal` traps focus and closes on Escape; `Tabs` switches panels on click/arrow keys; `ProgressBar` reflects the `value` prop; `Toast` shows and auto-dismisses.

### 11. Verification

```bash
npm run test -- components/ui
npm run dev   # visit the kitchen-sink route, visually confirm every component
```

### 12. Completion Criteria

- [ ] All 8 composite components implemented
- [ ] Kitchen-sink dev page renders every component/variant without errors
- [ ] Render tests pass for Modal, Tabs, ProgressBar, Toast
- [ ] Shiki-based CodeBlock highlights at least Python, TypeScript, and JavaScript correctly

---

## Phase 5: Routing & Application Shell Layout

### 1. Phase Objective

Set up TanStack Router with the application's route tree, and build the persistent application shell (Sidebar, Header, AppShell layout) that every page renders inside.

### 2. Why This Phase Exists

Routing and the shell are the skeleton every feature page (Phases 7–15) mounts into. Splitting them from global state/auth (Phase 6) keeps this phase about layout and navigation structure only — no data-fetching or auth concerns yet.

### 3. Prerequisites

Phase 4 complete: composite components (including `Toast`) exist.

### 4. Current Repository Expectations

No router configuration or shell layout exists yet. `App.tsx` renders a placeholder.

### 5. Implementation Tasks

**Route tree** (TanStack Router, file-based or code-based — choose code-based for explicitness):

- `/` — repository list (Phase 7)
- `/repositories/:repoId` — repository overview, nested routes for tabs:
  - `/repositories/:repoId/files` (Phase 10–11)
  - `/repositories/:repoId/graph` (Phase 12)
  - `/repositories/:repoId/search` (Phase 13)
  - `/repositories/:repoId/chat` (Phase 14–15)
- `/settings` — connection settings (Phase 6)
- `/dev/kitchen-sink` — dev-only (Phase 4), excluded from production route tree when `!import.meta.env.DEV`

**Application shell** (`src/components/layout/`):

- `AppShell`: persistent layout wrapping all routes — `Sidebar` + `Header` + main content outlet.
- `Sidebar`: repository quick-switcher, nav links to Settings.
- `Header`: current repository name/status badge, breadcrumb.
- `ToastProvider` mounted at the shell root (from Phase 4).
- 404 route and a route-level `ErrorBoundary` using `ErrorState` from Phase 4.

### 6. Files / Directories

```
frontend/
└── src/
    ├── router.tsx
    ├── routes/
    │   ├── root.tsx
    │   ├── repositories/
    │   │   └── index.tsx        # placeholder, filled Phase 7
    │   ├── settings.tsx          # placeholder, filled Phase 6
    │   └── not-found.tsx
    └── components/
        └── layout/
            ├── app-shell.tsx
            ├── sidebar.tsx
            └── header.tsx
```

### 7. Technical Requirements

- `@tanstack/react-router` with a typed route tree (`createRootRoute`, `createRoute`).
- Nested layouts via TanStack Router's `Outlet`.

### 8. Integration Requirements

- Feature routes (`/repositories/:repoId/files`, `/graph`, `/search`, `/chat`) are stubbed with placeholder content in this phase and filled in by Phases 10–15.

### 9. API Contract Requirements

None yet — this phase only builds navigation structure.

### 10. Testing

- Router test: navigating to each top-level route renders the expected placeholder without crashing.
- `AppShell` render test: Sidebar and Header both render.

### 11. Verification

```bash
npm run dev   # click through every nav link, confirm shell persists, no console errors
npm run test -- routes layout
npx tsc --noEmit
```

### 12. Completion Criteria

- [ ] Route tree covers every path listed above
- [ ] AppShell (Sidebar + Header + Outlet) renders on every route
- [ ] 404 route and route-level error boundary work
- [ ] Kitchen-sink route excluded from production builds
- [ ] `npm run test -- routes layout` passes

---

## Phase 6: Global State, Connection Settings & Reactive Auth

### 1. Phase Objective

Set up Zustand stores and the TanStack Query client, build the `/settings` page for configuring the backend URL and API key, and implement the reactive-401 auth flow that works whether or not the backend enforces authentication.

### 2. Why This Phase Exists

This is the last foundation phase before feature work begins — it establishes how the app manages client state and reacts to auth requirements it can't know about in advance (the backend may have `REQUIRE_AUTH` on or off; see `BACKEND.md → API Contract → Authentication strategy`). Every feature phase depends on the `QueryClient` and stores created here.

### 3. Prerequisites

Phase 5 complete: shell and `/settings` route stub exist. Phase 2 complete: `apiClient` exists.

### 4. Current Repository Expectations

`/settings` route renders a placeholder. No Zustand stores or `QueryClient` exist yet.

### 5. Implementation Tasks

**Stores** (`src/stores/`):

- `useConnectionStore`: `apiBaseUrl`, `apiKey` (nullable), `useMockApi` (bool) — persisted to `localStorage` **except** `apiKey`, which is only persisted if the user opts in (see `API Key Storage` above).
- `useUiStore`: sidebar collapsed state, theme (light/dark/system).

**TanStack Query setup**:

- `QueryClient` created in `main.tsx` with sane defaults (`staleTime`, `retry: false` for mutations, `retry: 1` for queries).
- Global error handling: a `QueryCache`/`MutationCache` `onError` that inspects `ApiClientError.status`.

**Reactive 401 handling:**

- When any query/mutation fails with `401 {"code": "AUTH_REQUIRED"}`, show a non-blocking `Toast` prompting the user to add an API key, and surface an "Add API key" call-to-action rather than hard-redirecting — the app must remain usable for read-only/public data even when one write path needs a key.
- The app must not require an API key up front just because it might be needed — it reacts to the first 401 it actually receives, consistent with `BACKEND.md`'s local-vs-hosted authentication strategy where most deployments never send a 401 at all.

**Settings page** (`src/routes/settings.tsx`):

- Form (React Hook Form + Zod) for `apiBaseUrl`, `apiKey`, `useMockApi` toggle.
- "Remember this key on this device" checkbox controlling whether `apiKey` is persisted (see API Key Storage).
- "Test connection" button that calls `GET /health` and shows success/failure via Toast.

### 6. Files / Directories

```
frontend/
└── src/
    ├── stores/
    │   ├── connection-store.ts
    │   └── ui-store.ts
    ├── lib/
    │   └── query-client.ts
    └── routes/
        └── settings.tsx
```

### 7. Technical Requirements

- Zustand with the `persist` middleware, `partialize` to exclude `apiKey` unless the user opts in.
- React Hook Form + Zod resolver for the settings form.

### 8. Integration Requirements

- `apiClient` (Phase 2) reads `apiBaseUrl`/`apiKey` from `useConnectionStore` on every request.
- `QueryClient`'s global error handler references `useUiStore`/Toast to surface 401s.

### 9. API Contract Requirements

Consumes `GET /health` and reacts to the `401 {"error": {"code": "AUTH_REQUIRED"}}` shape from **API Contract → Authentication strategy**. No new backend endpoints introduced.

### 10. Testing

- Store tests: `apiKey` is excluded from persisted state unless the opt-in flag is set.
- Settings page test: submitting valid values updates the store; "Test connection" shows success/failure toast (mock `apiClient.health`).
- Reactive-401 test: a mocked 401 response triggers the "Add API key" toast without crashing the app or blocking other UI.

### 11. Verification

```bash
npm run test -- stores settings
npm run dev   # change settings, confirm persistence across reload (except key, unless opted in)
```

### 12. Completion Criteria

- [ ] `useConnectionStore` and `useUiStore` implemented; `apiKey` persistence is opt-in only
- [ ] `QueryClient` configured with global 401 handling that shows a non-blocking prompt
- [ ] Settings page lets the user configure base URL, key, and mock/real toggle
- [ ] "Test connection" works against both mock and real backend
- [ ] `npm run test -- stores settings` passes

---

## Phase 7: Repository List & Upload/Clone UI

### 1. Phase Objective

Build the repository list page and the upload/clone flow: users can see existing repositories and add a new one via zip upload or Git URL.

### 2. Why This Phase Exists

This is the first real product feature and the app's entry point. Splitting it from the overview page (Phase 8) keeps this phase focused purely on the "many repositories" list-and-create surface, while Phase 8 focuses on the "one repository" detail surface.

### 3. Prerequisites

Phase 6 complete: `apiClient`, `QueryClient`, and stores exist. Needs backend capability: Repository create (upload + git clone) and list — see Frontend ↔ Backend Dependency Matrix. Works fully against the mock API without a real backend.

### 4. Current Repository Expectations

`/` route renders a placeholder from Phase 5. No repository list or upload UI exists yet.

### 5. Implementation Tasks

**API hooks** (`src/features/repositories/hooks/`):

- `useRepositories()` — `useQuery` wrapping `apiClient.listRepositories()`, paginated.
- `useUploadRepository()` — `useMutation` wrapping `apiClient.uploadRepository(file)`, invalidates the list query on success.
- `useCloneRepository()` — `useMutation` wrapping `apiClient.cloneRepository(gitUrl)`.

**Components** (`src/features/repositories/components/`):

- `RepositoryList`: grid/list of `RepositoryCard` (name, primary language badge, status badge, file count, created date). Uses `Skeleton` while loading, `EmptyState` when there are none, `ErrorState` on failure.
- `RepositoryCard`: clickable, navigates to `/repositories/:repoId`.
- `UploadDropzone`: drag-and-drop + click-to-browse zip upload, client-side validation (file type, size ≤ 500MB matching `MAX_REPO_SIZE_MB`), shows upload progress.
- `CloneForm`: React Hook Form + Zod, validates `https://` URL, submit triggers `useCloneRepository`.
- `AddRepositoryModal`: tabs (Phase 4's `Tabs`) between Upload and Clone, using the `Modal` from Phase 4.

**Page** (`src/routes/repositories/index.tsx`): renders `RepositoryList` + an "Add Repository" button opening `AddRepositoryModal`. On successful create, navigate to the new repo's overview page.

### 6. Files / Directories

```
frontend/
└── src/
    └── features/
        └── repositories/
            ├── hooks/
            │   ├── use-repositories.ts
            │   ├── use-upload-repository.ts
            │   └── use-clone-repository.ts
            └── components/
                ├── repository-list.tsx
                ├── repository-card.tsx
                ├── upload-dropzone.tsx
                ├── clone-form.tsx
                └── add-repository-modal.tsx
```

### 7. Technical Requirements

- Client-side zip validation before upload: check `.zip` extension/MIME type and size, matching the backend's `MAX_REPO_SIZE_MB`/413 behavior so the user gets instant feedback instead of waiting for a round trip.
- Upload progress via `XMLHttpRequest` (native `fetch` doesn't expose upload progress) or a library if already in the dependency set — otherwise fall back to an indeterminate `Spinner` and document the limitation.

### 8. Integration Requirements

- Uses `apiClient` from Phase 2 (mock by default) and the reactive-401 handling from Phase 6.
- Card click navigates via TanStack Router to a route Phase 8 fills in.

### 9. API Contract Requirements

Consumes `POST /repositories`, `POST /repositories/clone`, `GET /repositories` per **BACKEND.md → API Contract**. No contract changes.

### 10. Testing

- `RepositoryList` renders cards from mock data, shows `EmptyState` when empty, `ErrorState` on a forced query error.
- `UploadDropzone`: rejects a non-zip file and an oversized file with a visible message; accepts a valid zip and triggers the mutation (mocked).
- `CloneForm`: rejects a non-`https://` URL; submits a valid URL and triggers the mutation (mocked).

### 11. Verification

```bash
npm run test -- features/repositories
npm run dev   # upload a zip against the mock API, confirm it appears in the list
```

### 12. Completion Criteria

- [ ] Repository list renders, with loading/empty/error states
- [ ] Upload flow works against the mock API end-to-end
- [ ] Clone flow works against the mock API end-to-end
- [ ] Client-side validation matches backend limits (zip type, size, `https://` only)
- [ ] `npm run test -- features/repositories` passes

---

## Phase 8: Repository Overview Page & API Hooks

### 1. Phase Objective

Build the repository overview page — the landing page for a single repository, showing summary metadata and navigation into the Files/Graph/Search/Chat tabs — plus the shared query hooks those later tabs will reuse.

### 2. Why This Phase Exists

This is the "hub" page every deeper feature (Phases 10–15) is reached from, and it's the natural place to establish the shared `useRepository(repoId)` hook and delete/rename actions once, rather than duplicating repository-detail fetching logic in each tab phase.

### 3. Prerequisites

Phase 7 complete: repositories can be created and listed. Needs backend capability: Repository detail — see Dependency Matrix.

### 4. Current Repository Expectations

`/repositories/:repoId` route exists as a stub from Phase 5. No overview page or detail hook exists yet.

### 5. Implementation Tasks

**Hooks** (`src/features/repositories/hooks/`):

- `useRepository(repoId)` — `useQuery` wrapping `apiClient.getRepository(repoId)`. Reused by every later tab phase for header context (name, status, language).
- `useDeleteRepository()` — `useMutation`, navigates back to `/` on success.

**Components:**

- `RepositoryOverview`: header (name, status badge, primary language, file count, created date), summary stats, "Delete repository" action (confirm via `Modal`).
- `RepositoryTabs`: uses Phase 4's `Tabs`, linking to Files / Graph / Search / Chat routes — renders as disabled/tooltip-explained when `repository.status !== "ready"` (except a Files tab, which may be viewable during processing depending on what's already extracted — implementer's call, document the decision).

**Page** (`src/routes/repositories/$repoId/index.tsx` or route index): renders `RepositoryOverview` + `RepositoryTabs`, with `Outlet` for the nested tab routes Phases 10–15 fill in.

### 6. Files / Directories

```
frontend/
└── src/
    └── features/
        └── repositories/
            ├── hooks/
            │   ├── use-repository.ts
            │   └── use-delete-repository.ts
            └── components/
                ├── repository-overview.tsx
                └── repository-tabs.tsx
```

### 7. Technical Requirements

- `useRepository` should be structured so later tab phases can call it again without an extra network request (TanStack Query's cache handles this automatically given a consistent query key `["repository", repoId]`).

### 8. Integration Requirements

- `RepositoryTabs` links into the nested routes stubbed in Phase 5, filled in progressively by Phases 10–15.

### 9. API Contract Requirements

Consumes `GET /repositories/{id}`, `DELETE /repositories/{id}` per **BACKEND.md → API Contract**. No contract changes.

### 10. Testing

- `RepositoryOverview` renders correct metadata from mock data; delete flow confirms then navigates away (mocked mutation).
- Tabs correctly disable/enable based on `status`.

### 11. Verification

```bash
npm run test -- features/repositories
npm run dev   # open a mock repository, confirm overview + tabs render
```

### 12. Completion Criteria

- [ ] Repository overview renders name/status/language/stats
- [ ] Delete flow works with confirmation
- [ ] Tabs link correctly into nested routes and reflect processing status
- [ ] `useRepository(repoId)` is reused (not re-implemented) by later phases
- [ ] `npm run test -- features/repositories` passes

---

## Phase 9: Processing Status UI (Live Progress)

### 1. Phase Objective

Build the processing/progress view shown while a repository is being ingested, extracted, parsed, graphed, and indexed — using live SSE updates with a polling fallback.

### 2. Why This Phase Exists

Repositories aren't usable until processing finishes, so this is a blocking, high-visibility UI that every uploaded/cloned repository passes through. It's split out as its own phase because the SSE-with-polling-fallback transport logic is a self-contained concern independent of any specific downstream feature (files, graph, search, chat).

### 3. Prerequisites

Phase 8 complete: repository overview page exists. Needs backend capability: status polling and/or SSE — see Dependency Matrix. Works against the mock API's simulated progress from Phase 2.

### 4. Current Repository Expectations

`RepositoryOverview` shows a static status badge only. No live progress stepper or SSE hook exists yet.

### 5. Implementation Tasks

**Hook** (`src/features/processing/hooks/use-repository-progress.ts`):

- Connects to `GET /repositories/{id}/events` (SSE) using `fetch` + `ReadableStream` (not the native `EventSource`, since it can't send `X-API-Key` — see `BACKEND.md → Backend → Frontend Handoff → WebSocket/SSE`).
- Falls back to polling `GET /repositories/{id}/status` every 2 seconds if the SSE connection fails to open or drops.
- Exposes `{status, progress, phase, error}` reactively; updates the `["repository", repoId]` query cache directly so `useRepository` reflects live state without a manual refetch.
- Auto-stops (closes stream / stops polling) once `status` is `"ready"` or `"error"`.

**Component** (`src/features/processing/components/processing-stepper.tsx`):

- Five-stage stepper matching `BACKEND.md`'s canonical `phase` list exactly: Ingestion → Extraction → Parsing → Graph → Indexing. Each stage shows pending/active/done/error state and the current stage shows the `ProgressBar` from Phase 4.
- On `status: "error"`, show `ErrorState` with the `error_message` and a "Retry" action (re-triggers processing if the backend exposes that, otherwise suggests re-uploading).

**Integration into overview:** `RepositoryOverview` renders `ProcessingStepper` instead of tabs while `status !== "ready"`.

### 6. Files / Directories

```
frontend/
└── src/
    └── features/
        └── processing/
            ├── hooks/
            │   └── use-repository-progress.ts
            └── components/
                └── processing-stepper.tsx
```

### 7. Technical Requirements

- SSE via `fetch` + `ReadableStream` + a manual `TextDecoder`/line-buffer parser for `data: ...\n\n` frames — do not use `EventSource`.
- Parse both `{"status": ..., "progress": ..., "phase": ...}` data frames and `:ping` keepalive comments (ignore pings).
- Reconnection: on stream error, wait 1s and fall back to polling rather than retrying SSE in a tight loop.

### 8. Integration Requirements

- Writes directly into the `["repository", repoId]` TanStack Query cache (via `queryClient.setQueryData`) so `useRepository` from Phase 8 updates live without polling duplication.

### 9. API Contract Requirements

Consumes `GET /repositories/{id}/status` and `GET /repositories/{id}/events` exactly per **BACKEND.md → API Contract → Repository status vs. pipeline phase** and **→ SSE / event formats**. The five `phase` values used in the stepper must match the backend's canonical list verbatim.

### 10. Testing

- `use-repository-progress` test: simulate an SSE stream (mock `fetch` returning a `ReadableStream` of frames) and assert state updates correctly; simulate a dropped stream and assert fallback to polling.
- `ProcessingStepper` renders correct stage states for each `phase` value, and the error state on `status: "error"`.

### 11. Verification

```bash
npm run test -- features/processing
npm run dev   # upload against the mock API, watch the stepper progress through all 5 stages to ready
```

### 12. Completion Criteria

- [ ] Stepper shows all 5 canonical phases in correct order
- [ ] SSE connection works via fetch+ReadableStream (not EventSource)
- [ ] Polling fallback engages when SSE fails/drops
- [ ] Stream/polling stops automatically at `ready`/`error`
- [ ] Error state shows `error_message` with a retry action
- [ ] `npm run test -- features/processing` passes

---

## Phase 10: File Tree & Code Viewer

### 1. Phase Objective

Build the file explorer: a navigable file tree and a syntax-highlighted code viewer for the selected file.

### 2. Why This Phase Exists

File browsing is one of four independent product surfaces reachable once a repository is ready (alongside graph, search, chat — see Phase Dependency Map). Splitting the tree+viewer from the symbol panel (Phase 11) keeps this phase focused on file navigation and content display only.

### 3. Prerequisites

Phase 9 complete: a repository can reach `status: "ready"`. Needs backend capability: file listing + content — see Dependency Matrix.

### 4. Current Repository Expectations

The Files tab route is a stub from Phase 5. No file tree or code viewer exists yet.

### 5. Implementation Tasks

**Hooks** (`src/features/files/hooks/`):

- `useFiles(repoId)` — `useQuery` wrapping `apiClient.listFiles(repoId)`, paginated (fetch in pages, build the tree client-side, or fetch all if the backend page size allows — implementer's call given actual repo sizes).
- `useFileContent(repoId, fileId)` — `useQuery` wrapping `apiClient.getFile(repoId, fileId)`, enabled only when a file is selected.

**Components** (`src/features/files/components/`):

- `FileTree`: builds a nested tree from the flat file-path list, collapsible directories, file-type icons, virtualized if the repo is large (windowing library already in the stack, or a simple custom virtualization if not — document the choice).
- `CodeViewer`: renders file content via Phase 4's `CodeBlock`, shows line numbers, handles the binary-file case (`{"error": "..."}` response) with an appropriate placeholder instead of a crash.
- `FileExplorer`: composes `FileTree` (sidebar) + `CodeViewer` (main pane) with a selected-file state (local `useState` or a lightweight store — no need for global state).

**Page** (nested route `/repositories/:repoId/files`): renders `FileExplorer`.

### 6. Files / Directories

```
frontend/
└── src/
    └── features/
        └── files/
            ├── hooks/
            │   ├── use-files.ts
            │   └── use-file-content.ts
            └── components/
                ├── file-tree.tsx
                ├── code-viewer.tsx
                └── file-explorer.tsx
```

### 7. Technical Requirements

- Tree construction: split each `path` on `/` and reduce into a nested structure client-side — no backend tree endpoint exists, only a flat file list.
- Shiki language selection driven by `CodeFile.language` from the API, not re-guessed client-side.

### 8. Integration Requirements

- Selecting a file in `FileTree` sets the selected-file id consumed by `useFileContent` and, in Phase 11, by the symbol panel.

### 9. API Contract Requirements

Consumes `GET /repositories/{id}/files`, `GET .../files/{file_id}` per **BACKEND.md → API Contract**. No contract changes.

### 10. Testing

- `FileTree`: builds correct nested structure from a flat mock file list; expand/collapse works; selecting a file fires the callback.
- `CodeViewer`: renders highlighted content for a text file; renders a placeholder (not a crash) for the binary-file response shape.

### 11. Verification

```bash
npm run test -- features/files
npm run dev   # browse the mock repo's file tree, open several files
```

### 12. Completion Criteria

- [x] File tree correctly nests a flat file list and supports expand/collapse
- [x] Code viewer syntax-highlights based on the file's reported language
- [x] Binary files show a clear placeholder instead of crashing
- [x] `npm run test -- features/files` passes

---

## Phase 11: Symbol Panel & Resizable Explorer Layout

### 1. Phase Objective

Add a symbol panel (functions/classes/methods in the selected file, click-to-jump) and make the file explorer's three panes (tree, code, symbols) resizable.

### 2. Why This Phase Exists

Symbol navigation and resizable panes are meaningful UX additions on top of Phase 10's basic tree+viewer, but depend on it being in place first — pulling them into their own phase keeps Phase 10 focused on "can I see files" and this phase focused on "can I navigate within a file efficiently."

### 3. Prerequisites

Phase 10 complete: `FileExplorer` with tree + viewer works. Needs backend capability: symbols per file — see Dependency Matrix.

### 4. Current Repository Expectations

`FileExplorer` has a two-pane (tree + viewer) fixed layout. No symbol panel exists; panes are not resizable.

### 5. Implementation Tasks

**Hook** (`src/features/files/hooks/use-file-symbols.ts`):

- Wraps `apiClient.getFileSymbols(repoId, fileId)`, enabled only when a file is selected.

**Components:**

- `SymbolPanel` (`src/features/files/components/symbol-panel.tsx`): lists symbols grouped by kind (classes, functions, methods, etc.) with icons per kind, clicking a symbol scrolls `CodeViewer` to its `start_line` and briefly highlights the range.
- Resizable layout: convert `FileExplorer`'s fixed three-pane layout (tree | viewer | symbols) into resizable panes (drag handles between panes, persisted pane widths via `useUiStore` from Phase 6 or local storage).

**CodeViewer extension:** accept a `scrollToLine` prop / imperative handle so `SymbolPanel` can trigger scroll-and-highlight.

### 6. Files / Directories

```
frontend/
└── src/
    └── features/
        └── files/
            ├── hooks/
            │   └── use-file-symbols.ts
            └── components/
                ├── symbol-panel.tsx
                └── resizable-panes.tsx
```

### 7. Technical Requirements

- Resizable panes: a small custom implementation (pointer events + CSS `flex-basis`) is sufficient — no need to add a new dependency unless one is already common in this stack.
- Persist pane widths so the layout doesn't reset on every navigation.

### 8. Integration Requirements

- Reuses the selected-file state from Phase 10's `FileExplorer`.
- Extends `CodeViewer` from Phase 10 rather than duplicating it.

### 9. API Contract Requirements

Consumes `GET /repositories/{id}/files/{file_id}/symbols` per **BACKEND.md → API Contract**. No contract changes.

### 10. Testing

- `SymbolPanel`: renders symbols grouped by kind from mock data; clicking a symbol calls the scroll callback with the correct line.
- Resizable panes: dragging a handle updates pane width state (simulate pointer events); widths persist across a re-render.

### 11. Verification

```bash
npm run test -- features/files
npm run dev   # select a file, click a symbol, confirm the viewer scrolls/highlights; drag pane dividers
```

### 12. Completion Criteria

- [x] Symbol panel lists and groups symbols correctly from mock data
- [x] Clicking a symbol scrolls and highlights the corresponding code
- [x] All three panes are resizable and widths persist
- [x] `npm run test -- features/files` passes

---

## Phase 12: Dependency Graph Visualization

### 1. Phase Objective

Build the interactive dependency graph view using Sigma, showing files as nodes and imports as edges, with node detail on click.

### 2. Why This Phase Exists

Graph visualization is one of the four independent product surfaces reachable once a repository is ready (see Phase Dependency Map) and depends on a specific, non-trivial charting library (Sigma) — isolating it keeps that library's setup and performance concerns contained to one phase.

### 3. Prerequisites

Phase 9 complete (repository can be ready). Needs backend capability: dependency graph — see Dependency Matrix. Independent of Phases 10-11, 13, 14-15.

### 4. Current Repository Expectations

The Graph tab route is a stub from Phase 5. No graph visualization exists yet.

### 5. Implementation Tasks

**Hooks** (`src/features/graph/hooks/`):

- `useRepositoryGraph(repoId)` — `useQuery` wrapping `apiClient.getGraph(repoId)`.
- `useGraphNode(repoId, fileId)` — `useQuery`, enabled on node selection, wraps `apiClient.getGraphNode(repoId, fileId)`.

**Components** (`src/features/graph/components/`):

- `DependencyGraph`: renders the `{nodes, edges, metrics}` response using Sigma. Node size scaled by `pagerank`, color by `language`, entry points visually distinguished (`is_entry_point`). Supports pan/zoom, hover-to-highlight-neighbors, click-to-select.
- `GraphControls`: filter by language, toggle showing only entry points, a "fit to view" button, cycle-warning banner if `metrics.has_cycles`.
- `NodeDetailPanel`: shows the selected node's path, symbols, direct dependencies, and dependents (from `useGraphNode`), with a link into the Files tab for that file.

**Page** (nested route `/repositories/:repoId/graph`): renders `DependencyGraph` + `GraphControls` + `NodeDetailPanel` (side panel, shown on selection).

### 6. Files / Directories

```
frontend/
└── src/
    └── features/
        └── graph/
            ├── hooks/
            │   ├── use-repository-graph.ts
            │   └── use-graph-node.ts
            └── components/
                ├── dependency-graph.tsx
                ├── graph-controls.tsx
                └── node-detail-panel.tsx
```

### 7. Technical Requirements

- `sigma` + `graphology` for graph construction and rendering (matches the roadmap's chosen library — do not substitute d3 or another graph lib).
- For large graphs (the backend already caps serialized nodes at 500 — see `BACKEND.md → Phase 11`), no additional client-side downsampling should be necessary, but guard against pathological cases (e.g. don't re-render the whole graph on every hover; use Sigma's built-in reducers for highlight state).

### 8. Integration Requirements

- `NodeDetailPanel`'s "view in Files tab" link navigates to the route built in Phase 10.

### 9. API Contract Requirements

Consumes `GET /repositories/{id}/graph`, `GET .../graph/node/{file_id}` per **BACKEND.md → API Contract → Graph response structure**. No contract changes.

### 10. Testing

- `DependencyGraph`: renders the correct node/edge count from mock graph data (assert via Sigma's graphology instance, not pixel-level rendering).
- `GraphControls`: language filter updates the visible node set; cycle-warning banner shows only when `metrics.has_cycles`.
- `NodeDetailPanel`: shows correct data for a selected mock node.

### 11. Verification

```bash
npm run test -- features/graph
npm run dev   # open the graph tab for a mock repo, pan/zoom, click a node, confirm detail panel
```

### 12. Completion Criteria

- [x] Graph renders nodes/edges from the API response via Sigma
- [x] Node size/color reflect pagerank/language; entry points visually distinguished
- [x] Clicking a node shows correct detail (symbols, deps, dependents)
- [x] Cycle warning shown when applicable
- [x] `npm run test -- features/graph` passes

---

## Phase 13: Semantic Search UI

### 1. Phase Objective

Build the semantic search page: a query box and ranked results with code snippets and jump-to-file links.

### 2. Why This Phase Exists

Search is one of the four independent product surfaces reachable once a repository is ready (see Phase Dependency Map) and is small enough to be a single, focused phase — one query form, one results list.

### 3. Prerequisites

Phase 9 complete (repository can be ready). Needs backend capability: vector search — see Dependency Matrix. Independent of Phases 10-12, 14-15.

### 4. Current Repository Expectations

The Search tab route is a stub from Phase 5. No search UI exists yet.

### 5. Implementation Tasks

**Hook** (`src/features/search/hooks/use-search.ts`):

- `useMutation` (not `useQuery` — search is user-triggered, not cached-by-key in a way that benefits from query semantics) wrapping `apiClient.search(repoId, query, limit)`. Debounce-as-you-type is optional; explicit submit is required at minimum.

**Components** (`src/features/search/components/`):

- `SearchBar`: input + submit, recent-queries dropdown (stored in `useUiStore` or local component state, session-only).
- `SearchResults`: ranked list of `SearchResultCard` (file path, line range, score, snippet via `CodeBlock` from Phase 4 with the matched region emphasized).
- `SearchResultCard`: click navigates to the Files tab (Phase 10) with that file open and scrolled to `start_line`.

**Page** (nested route `/repositories/:repoId/search`): renders `SearchBar` + `SearchResults`, with `EmptyState` before the first search and `Skeleton` while a search is in flight.

### 6. Files / Directories

```
frontend/
└── src/
    └── features/
        └── search/
            ├── hooks/
            │   └── use-search.ts
            └── components/
                ├── search-bar.tsx
                ├── search-results.tsx
                └── search-result-card.tsx
```

### 7. Technical Requirements

- No new libraries required — composes Phase 4's `CodeBlock`/`Skeleton`/`EmptyState` and Phase 2's `apiClient`.

### 8. Integration Requirements

- `SearchResultCard` navigation into the Files tab reuses the route and file-selection mechanism built in Phase 10.

### 9. API Contract Requirements

Consumes `POST /repositories/{id}/search` per **BACKEND.md → API Contract → Search response structure**. No contract changes.

### 10. Testing

- `SearchBar`: submits the query and triggers the mutation; recent queries populate the dropdown.
- `SearchResults`: renders ranked mock results with snippets; `EmptyState` before first search, `ErrorState` on a forced failure.
- `SearchResultCard`: click navigates with the correct file id and line number.

### 11. Verification

```bash
npm run test -- features/search
npm run dev   # run a search against the mock API, click a result, confirm it opens the right file/line
```

### 12. Completion Criteria

- [x] Search submits and displays ranked results with snippets
- [x] Clicking a result opens the correct file at the correct line in the Files tab
- [x] Loading/empty/error states all present
- [x] `npm run test -- features/search` passes

---

## Phase 14: Chat Layout, Sessions & Message Rendering

### 1. Phase Objective

Build the chat UI shell: session management and static message rendering (no streaming yet — that's Phase 15).

### 2. Why This Phase Exists

Chat's layout/session/history concerns are substantial enough on their own (creating sessions, rendering a message list, markdown rendering) to warrant separation from the harder streaming-and-sources mechanics in Phase 15. This phase can be fully built and tested against the mock API's canned (non-streamed) history before tackling live streaming.

### 3. Prerequisites

Phase 9 complete (repository can be ready). Needs backend capability: chat session + history — see Dependency Matrix. Independent of Phases 10-13.

### 4. Current Repository Expectations

The Chat tab route is a stub from Phase 5. No chat UI exists yet.

### 5. Implementation Tasks

**Hooks** (`src/features/chat/hooks/`):

- `useChatSession(repoId)` — creates a session on first mount (`useMutation` + effect, or a lazy-create-on-first-message pattern — implementer's call, document it) via `apiClient.createChatSession(repoId)`.
- `useChatHistory(repoId, sessionId)` — `useQuery` wrapping `apiClient.getChatMessages(repoId, sessionId)`.

**Components** (`src/features/chat/components/`):

- `ChatLayout`: message list (scrollable, auto-scrolls to bottom on new message) + input area at the bottom.
- `MessageList` / `MessageBubble`: renders `role: "user"` vs `"assistant"` distinctly; assistant messages render markdown (code blocks via `CodeBlock` from Phase 4, inline code, lists, links).
- `ChatInput`: textarea with submit-on-Enter (Shift+Enter for newline), disabled while a response is in flight.

**Page** (nested route `/repositories/:repoId/chat`): renders `ChatLayout`, wiring `useChatSession`/`useChatHistory`. Message _sending_ itself (the mutation that actually talks to the backend) is stubbed to append the user message locally and echo a static placeholder assistant reply in this phase — Phase 15 replaces the placeholder with real streaming.

### 6. Files / Directories

```
frontend/
└── src/
    └── features/
        └── chat/
            ├── hooks/
            │   ├── use-chat-session.ts
            │   └── use-chat-history.ts
            └── components/
                ├── chat-layout.tsx
                ├── message-list.tsx
                ├── message-bubble.tsx
                └── chat-input.tsx
```

### 7. Technical Requirements

- Markdown rendering: a lightweight markdown-to-React renderer (whatever is already idiomatic for this stack; if none is installed, a minimal custom renderer handling code fences via `CodeBlock`, paragraphs, lists, and links is sufficient — avoid pulling in a heavy dependency for this alone).

### 8. Integration Requirements

- Session creation and history hooks will be reused unchanged by Phase 15, which only replaces the message-send mutation with a streaming implementation.

### 9. API Contract Requirements

Consumes `POST /repositories/{id}/chat/sessions`, `GET .../chat/sessions/{sid}/messages` per **BACKEND.md → API Contract → Chat contract**. No contract changes.

### 10. Testing

- `ChatLayout`/`MessageList`: renders mock message history correctly, distinguishing user vs assistant, auto-scrolls on new message.
- `ChatInput`: Enter submits, Shift+Enter inserts newline, input disabled while a response is "in flight" (mocked).

### 11. Verification

```bash
npm run test -- features/chat
npm run dev   # open the chat tab, confirm history renders and sending a message appends it
```

### 12. Completion Criteria

- [x] Chat session is created/retrieved correctly
- [x] Message history renders with correct role styling and markdown/code formatting
- [x] Input handles Enter/Shift+Enter and disables while a response is in flight
- [x] `npm run test -- features/chat` passes

---

## Phase 15: Streaming, Sources & Starter Suggestions

### 1. Phase Objective

Replace Phase 14's placeholder reply with real token-by-token streaming from the backend, render cited sources, and add starter question suggestions for new sessions.

### 2. Why This Phase Exists

Streaming is the product's headline interaction and depends on Phase 14's layout/session plumbing being solid first. Isolating it here means the harder transport work (parsing a raw SSE token stream, distinct from the JSON-event progress stream in Phase 9) doesn't block the simpler layout work in Phase 14.

### 3. Prerequisites

Phase 14 complete: chat layout, sessions, and history rendering work.

### 4. Current Repository Expectations

Chat sends a message and appends a static placeholder reply. No real streaming, source citation, or starter-suggestion UI exists yet.

### 5. Implementation Tasks

**Hook** (`src/features/chat/hooks/use-send-message.ts`):

- Connects to `POST /repositories/{id}/chat/sessions/{sid}/messages` via `fetch` + `ReadableStream` (same reasoning as Phase 9: needs to send `X-API-Key`, so not `EventSource`).
- Parses the plain-token SSE format from **BACKEND.md → API Contract → SSE / event formats → AI chat streaming**: appends each `data: <token>` frame to the in-progress assistant message; on `data: __sources__:[...]`, attaches parsed sources; on `data: [DONE]`, finalizes the message and refetches/updates history.
- **This is a different parser from Phase 9's** — the progress stream carries JSON objects per event, this one carries raw token fragments plus two sentinel event types. Do not try to unify them into one generic "SSE hook"; keep them as two purpose-built parsers sharing only the underlying fetch+ReadableStream+line-buffering utility if one naturally factors out.

**Components:**

- `MessageBubble` (extend from Phase 14): renders a `SourceCitation` list under assistant messages when `sources` is present — each citation links into the Files tab (Phase 10) at the cited file/line.
- `StreamingIndicator`: subtle typing/streaming indicator shown while tokens are still arriving.
- `StarterSuggestions` (`src/features/chat/components/starter-suggestions.tsx`): shown only when a session has no messages yet — 3–4 example questions (e.g. "What does the authentication module do?") that populate `ChatInput` on click. Suggestions can be static or derived from `Repository.primary_language`/`frameworks` if convenient; static is acceptable.

**Wiring:** `ChatInput`'s submit now calls `useSendMessage` instead of Phase 14's placeholder.

### 6. Files / Directories

```
frontend/
└── src/
    └── features/
        └── chat/
            ├── hooks/
            │   └── use-send-message.ts
            └── components/
                ├── source-citation.tsx
                ├── streaming-indicator.tsx
                └── starter-suggestions.tsx
```

### 7. Technical Requirements

- Same fetch+ReadableStream approach as Phase 9, but a distinct frame parser for this stream's token/`__sources__`/`[DONE]` format.
- Handle stream errors gracefully: if the connection drops mid-stream, finalize whatever content arrived and show an inline "response may be incomplete" note rather than losing the partial answer.

### 8. Integration Requirements

- Extends `MessageBubble` and `ChatInput` from Phase 14 rather than duplicating them.
- `SourceCitation` links reuse the Files tab navigation pattern from Phase 10/13.

### 9. API Contract Requirements

Consumes `POST /repositories/{id}/chat/sessions/{sid}/messages` (SSE) exactly per **BACKEND.md → API Contract → SSE / event formats → AI chat streaming**. No contract changes.

### 10. Testing

- `use-send-message`: simulate a token stream (mock `fetch` returning a `ReadableStream` of `data: ` frames including `__sources__` and `[DONE]`) and assert the message builds up token-by-token, sources attach correctly, and the stream finalizes.
- `StarterSuggestions`: renders only on an empty session; clicking a suggestion populates the input.
- Dropped-stream case: partial content is preserved and an incomplete-response note is shown.

### 11. Verification

```bash
npm run test -- features/chat
npm run dev   # send a message against the mock API's simulated stream, confirm token-by-token rendering and source links
```

### 12. Completion Criteria

- [ ] Assistant replies stream token-by-token from a real SSE response
- [ ] Sources render and link correctly into the Files tab
- [ ] Starter suggestions show on empty sessions and populate the input on click
- [ ] Dropped streams preserve partial content instead of losing it
- [ ] `npm run test -- features/chat` passes

---

## Phase 16: Polish, Accessibility & Responsive Design

### 1. Phase Objective

Pass over the whole application for keyboard navigation, screen-reader support, color contrast, loading/error consistency, and responsive layout down to tablet width.

### 2. Why This Phase Exists

Every feature phase above focused on making its own surface work; this phase is where the agent steps back and ensures the app is usable and consistent as a whole — the natural point to do this is once every screen exists, ahead of the testing and production phases that close out the roadmap.

### 3. Prerequisites

Phase 15 complete: every product surface (repositories, processing, files, graph, search, chat) exists.

### 4. Current Repository Expectations

All features work individually but have not been audited together for accessibility or responsive behavior.

### 5. Implementation Tasks

**Accessibility:**

- Keyboard navigation audit: every interactive element reachable and operable via keyboard (tab order, Enter/Space activation, Escape to close modals — most of this should already work from Phase 3-4's primitives, this phase verifies it holistically).
- ARIA labels/roles on icon-only buttons, the graph visualization's controls, and the chat input.
- Color contrast audit against the design tokens from Phase 3 (WCAG AA minimum for text).
- Focus management: focus moves sensibly on route change and modal open/close.

**Consistency pass:**

- Every data-fetching surface uses `Skeleton` while loading and `ErrorState` on failure (grep for any feature phase that missed one).
- Every list/collection uses `EmptyState` consistently.
- Toast notifications used consistently for background action feedback (upload complete, delete confirmed, connection test result).

**Responsive design:**

- Sidebar collapses to an icon rail or drawer below a defined breakpoint.
- File explorer's three-pane layout (Phase 11) collapses to a single-pane-with-tabs view on narrow viewports.
- Graph and chat views remain usable (not necessarily identical) down to tablet width (~768px). Full mobile phone support is not required for a developer tool — document this as a deliberate scope boundary if narrower widths are visibly broken.

### 6. Files / Directories

```
frontend/
└── src/
    (touches existing files across components/, features/, styles/ — no major new files expected;
     add small ones only where a genuine gap is found, e.g. a shared `visually-hidden.tsx` for
     screen-reader-only text if not already present)
```

### 7. Technical Requirements

- Use browser devtools / axe-core (as a dev-only lint pass, not a runtime dependency) to check for obvious accessibility violations if convenient; a careful manual pass is acceptable if not.

### 8. Integration Requirements

None new — this phase modifies existing components across every feature built so far.

### 9. API Contract Requirements

None.

### 10. Testing

- Spot-check keyboard-only navigation through the primary flows: add a repository, browse files, run a search, send a chat message.
- Automated: extend existing component tests with a couple of accessibility-focused assertions (e.g. icon buttons have `aria-label`) where practical, rather than introducing a whole new automated a11y suite.

### 11. Verification

```bash
npm run test
npm run dev   # manual keyboard-only pass through every major flow; resize to tablet width and check each tab
```

### 12. Completion Criteria

- [ ] Every primary flow is operable via keyboard alone
- [ ] Icon-only controls have accessible labels
- [ ] Color contrast meets WCAG AA for body text against the design tokens
- [ ] Loading/empty/error states are consistent across every feature
- [ ] Layout is usable down to tablet width (~768px); any deliberate narrower-width limitations are documented

---

## Phase 17: Frontend Testing Suite

### 1. Phase Objective

Fill remaining coverage gaps with shared test utilities, additional component/hook edge-case tests, and end-to-end Playwright tests covering the primary user flows.

### 2. Why This Phase Exists

Every prior phase already wrote focused tests for its own components; this phase is where the agent closes cross-cutting gaps and adds the E2E layer that proves the flows work together, mirroring `BACKEND.md → Phase 23-24`'s split between fast mocked tests and slower real-flow tests.

### 3. Prerequisites

Phase 16 complete. Per-phase component/hook tests exist from every earlier phase.

### 4. Current Repository Expectations

Component and hook tests exist per-feature but there's no shared test utility module, and no Playwright E2E suite yet.

### 5. Implementation Tasks

**Shared test utilities** (`src/test-utils/`):

- A custom `render()` wrapping Testing Library's with the app's providers (`QueryClientProvider` with a fresh `QueryClient` per test, router context, Zustand store reset between tests).
- Mock data factories reusing `src/lib/api/fixtures/` rather than duplicating fixture shapes in test files.

**Unit/component gap-filling** — review each feature module from Phases 7–15 and add tests for any state (loading/empty/error/edge case) not already covered.

**E2E tests** (`e2e/`, Playwright, run against the mock API by default so they don't require a live backend):

- `upload-and-explore.spec.ts`: upload a repo (mock) → wait for processing to complete → browse files → view graph → run a search.
- `chat-flow.spec.ts`: open a repo → start a chat session → send a message → see a streamed (mocked) reply with sources.
- `settings-flow.spec.ts`: change connection settings → confirm persistence → test connection.

### 6. Files / Directories

```
frontend/
├── src/
│   └── test-utils/
│       ├── render.tsx
│       └── factories.ts
└── e2e/
    ├── upload-and-explore.spec.ts
    ├── chat-flow.spec.ts
    └── settings-flow.spec.ts
```

### 7. Technical Requirements

- Playwright configured to run against `npm run dev` (or a `npm run preview` production build) with `VITE_USE_MOCK_API=true` so E2E tests are hermetic and don't require a running backend.
- Vitest coverage: `vitest --coverage`, target ≥ 75% (frontend UI code typically has lower meaningful coverage than backend logic — document the chosen target and why if it differs from `BACKEND.md`'s 80%).

### 8. Integration Requirements

None — this phase only adds/consolidates tests.

### 9. API Contract Requirements

None. If an E2E test reveals a genuine contract mismatch between `mock.ts` and `BACKEND.md`'s API Contract, fix the mock to match the contract.

### 10. Testing

This entire phase is testing — see Implementation Tasks above.

### 11. Verification

```bash
npm run test -- --coverage
npx playwright test
```

### 12. Completion Criteria

- [ ] Shared test utilities in place and used by at least the new tests in this phase
- [ ] Gap-filling unit/component tests added where coverage review found missing states
- [ ] All 3 E2E flows pass against the mock API
- [ ] Coverage target met and documented
- [ ] No flaky tests (run suite 3 times, all pass)

---

## Phase 18: Production Build & Docker

### 1. Phase Objective

Containerize the frontend with a production-optimized Docker build served via Nginx, wire it into the shared root `docker-compose.yml`, and finalize production configuration.

### 2. Why This Phase Exists

This is the final phase of the frontend roadmap — it packages everything built in Phases 1–17 into a deployable static bundle and documents how to run the whole stack together with the backend, matching `BACKEND.md → Phase 25`'s closing milestone.

### 3. Prerequisites

Phases 1–17 complete. All tests passing.

### 4. Current Repository Expectations

The app builds and runs via `npm run dev`/`npm run build`, but there is no Dockerfile or Nginx configuration yet, and `docker-compose.yml` (created in `BACKEND.md → Phase 25`) has no `frontend` service.

### 5. Implementation Tasks

**Dockerfile** (`frontend/Dockerfile`):

- Multi-stage build: `builder` stage runs `npm ci && npm run build`; `runtime` stage serves `dist/` via `nginx:alpine`.
- `nginx.conf`: SPA fallback (all routes → `index.html`), gzip compression, cache headers for hashed assets, a reverse-proxy pass-through for `/api` to the backend service name in Compose (avoids CORS in the containerized setup).

**Docker Compose integration:**

- Add a `frontend` service to the root `docker-compose.yml` created in `BACKEND.md → Phase 25`: build from `frontend/Dockerfile`, expose port 80 (mapped to a host port, e.g. `5173:80` or `80:80`), `depends_on: [api]`.
- Confirm `VITE_API_BASE_URL` at build time (or Nginx proxy at runtime) points requests correctly whether running via `docker-compose` or `npm run dev`.

**Production environment:**

- `.env.production` with `VITE_USE_MOCK_API=false` and the production API base URL.
- Verify no dev-only routes (`/dev/kitchen-sink` from Phase 4) ship in the production bundle.

**`README.md`** (frontend): setup instructions, env vars, how to run dev vs. production, how to run tests.

### 6. Files / Directories

```
frontend/
├── Dockerfile
├── nginx.conf
├── .env.production
└── README.md
```

### 7. Technical Requirements

- `nginx:alpine` base image for the runtime stage.
- Ensure the Nginx SPA fallback doesn't swallow real 404s for static assets (only fallback for non-file, non-`/api` routes).

### 8. Integration Requirements

- `docker-compose.yml` at the project root (created in `BACKEND.md → Phase 25`) gains a `frontend` service alongside `postgres`, `redis`, `api`, and `worker`.

### 9. API Contract Requirements

None — this phase is packaging only. Confirms the frontend correctly honors `BACKEND.md → Backend → Frontend Handoff`'s documented `API_BASE_URL`/CORS/auth guidance in a containerized environment.

### 10. Testing

```bash
docker build -t codegraph-frontend frontend/
docker run -p 8080:80 codegraph-frontend
curl http://localhost:8080   # returns the SPA shell
```

### 11. Verification

```bash
docker-compose up -d
docker-compose ps                       # frontend service healthy
curl -I http://localhost:5173           # 200, correct SPA response
# In the browser: full flow — add a repo, watch processing, browse, search, chat — against the real backend
```

### 12. Completion Criteria

- [ ] `docker-compose up` starts the frontend alongside the full backend stack
- [ ] Production build excludes dev-only routes
- [ ] SPA routing works correctly behind Nginx (deep links don't 404)
- [ ] `/api` requests correctly reach the backend service in the containerized network
- [ ] Full end-to-end flow works against the real (non-mock) backend in Docker
- [ ] `README.md` complete and accurate

---

## Cross-System Consistency Notes

This roadmap is built to stay consistent with `BACKEND.md` without duplicating it:

- **Schemas & error/pagination format:** always sourced from `BACKEND.md → API Contract — Source of Truth`. `src/lib/api/types.ts` (Phase 2) is a direct mirror; if the backend contract changes, update `types.ts` and the affected fixtures in the same frontend phase that consumes the change.
- **Status vs. phase vocabulary:** the processing stepper (Phase 9) uses the exact same five `phase` values as the backend's `AnalysisJob.phase` and SSE stream — `ingestion`, `extraction`, `parsing`, `graph`, `indexing` — never a frontend-invented set.
- **Two distinct SSE parsers:** repository progress (Phase 9, JSON events) and chat streaming (Phase 15, raw token + sentinel events) are deliberately separate parsers, matching `BACKEND.md`'s two distinct stream formats — they are not unified into one generic "SSE hook."
- **Authentication:** the frontend never assumes `REQUIRE_AUTH` is on or off — it sends `X-API-Key` when configured and reacts to `401` reactively (Phase 6), matching `BACKEND.md → API Contract → Authentication strategy`'s local-vs-hosted design.
- **Mock API fidelity:** `src/lib/api/mock.ts` and its fixtures must never diverge from the real contract — see **Mock API Strategy** above.

## Backend Startup Reference

See `BACKEND.md → Backend → Frontend Handoff` for how to run the backend locally or via Docker, the required environment variables, and the authentication/CORS/SSE details this frontend depends on. That section is authoritative; it is not repeated here.

## Frontend Startup

```bash
# Development (mock API, no backend required):
cd frontend
npm install
npm run dev                          # VITE_USE_MOCK_API defaults to true

# Development against a real local backend:
VITE_USE_MOCK_API=false npm run dev  # requires backend running per BACKEND.md

# Production build:
npm run build
npm run preview

# Full stack via Docker Compose (after BACKEND.md → Phase 25 and this file's Phase 18):
docker-compose up
```
