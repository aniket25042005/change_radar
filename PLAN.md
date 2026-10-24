# ChangeRadar — Comprehensive Execution Plan & Roadmap (Enhanced Edition)

## 1. Executive Summary & Objective

**ChangeRadar** is a local-first, developer-centric static analysis and flight-control tool that detects how backend API changes in FastAPI/Pydantic break frontend consumers in React + TypeScript applications.

Beyond conventional static analysis, ChangeRadar acts as an **interactive pre-flight controller**:
1. It maps dependencies across Python backend and TypeScript frontend codebases using deterministic AST and heuristic parsing.
2. It visually highlights the **"Blast Radius"** on an interactive dependency graph.
3. It generates ready-to-apply **1-Click Migration Diff Patches** for affected frontend components and tests.
4. It accepts both structured changes (dropdowns) and **Git Diff paste/detection** to simulate pull requests.

---

## 2. System Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        ChangeRadar Frontend                            │
│           (React 18 + TypeScript + Vite + Developer Dark Theme)        │
│                                                                        │
│  ├── Privacy & Security Badge (100% local analysis, zero external data) │
│  ├── Project Ingestion:                                                │
│  │    ├── Safe ZIP Upload (Drag & Drop)                                │
│  │    └── 1-Click Bundled Sample Repository Loader                     │
│  ├── Interactive Visual Blast Radius Graph (Canvas / SVG Tree):        │
│  │    └── [Endpoint] ──► [Pydantic Model] ──► [TS Type] ──► [UI / Test]│
│  │         (Active nodes glow red/amber on simulated breaking changes) │
│  ├── Change Simulator & Git Diff Inspector:                            │
│  │    ├── Structured Change Form (remove/rename/type change/route)     │
│  │    └── Git Diff Mode (paste `git diff` to auto-extract changes)     │
│  ├── Traceable Impact Report:                                          │
│  │    ├── Evidence Cards (Exact file paths, line numbers, snippets)    │
│  │    ├── Confidence Badges (High, Medium, Low)                        │
│  │    └── Suggested Regression Tests                                   │
│  ├── 1-Click Migration Diff Generator:                                 │
│  │    └── Live `.diff` code preview with 1-click "Copy Migration Patch"│
│  └── Report History & Project Management Drawer                        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend Server                          │
│               (Python 3.11+ / 3.14+, Uvicorn, SQLite3)                 │
│                                                                        │
│  ├── API Routing Layer (/health, /api/projects, /api/reports, etc.)    │
│  ├── Storage Layer (SQLite database with parameterized queries)        │
│  ├── Sandboxed File Workspace (`backend/workspace/extracted/{id}`)     │
│  └── Analysis Engine:                                                  │
│       ├── ZipService: Zip Slip protection, 25MB cap, secret exclusion  │
│       ├── Scanner: Traverses source tree, filters ignore-lists         │
│       ├── FastAPIParser: Python `ast` route & Pydantic model extractor │
│       ├── TypeScriptParser: Regex/AST heuristic consumer scanner       │
│       ├── GitDiffParser: Parses unified diffs into structured changes  │
│       ├── BlastRadiusGraph: Builds cross-stack dependency node/edges   │
│       ├── MigrationPatchService: Generates unified frontend `.diff`s   │
│       └── ImpactAnalyzer: Cross-stack matcher, scorer & test generator │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack & Choices

| Area | Choice | Rationale |
| :--- | :--- | :--- |
| **Backend** | Python 3.11+ / FastAPI / Uvicorn | Native compatibility with target scanned language, fast async endpoints, built-in OpenAPI docs. |
| **Database** | SQLite (`sqlite3`) | Zero external dependencies, persists state across backend restarts, safe for local laptop use. |
| **Analysis** | Python `ast` + TS Heuristics | Fast, deterministic, no LLM required, offline-capable, exact line/column tracking. |
| **Frontend** | React 18, TypeScript, Vite | Modern developer tooling, fast HMR, type safety, low bundle size. |
| **UI / Theme** | Vanilla CSS (Developer Dark Theme) | Sleek slate/zinc palette, neon cyan/violet accents, monospace code blocks, high performance with no bulky CSS framework. |
| **Visual Graph** | Custom SVG / Canvas Graph | Lightweight, interactive node-link graph mapping backend routes to frontend consumers without heavy D3 bloat. |
| **Sample Data** | Bundled `sample_project.zip` | Allows instant 1-click test drive with realistic FastAPI routes + React consumers + unit tests. |

---

## 4. Key Value-Add Features (The Differentiators)

### 4.1 Interactive "Blast Radius" Visual Graph
- Renders an interactive node graph showing the full contract path:
  `FastAPI Route` &rarr; `Pydantic Schema` &rarr; `TypeScript Type` &rarr; `React Component` &rarr; `Test File`.
- When an API change is configured or simulated:
  - Affected nodes dynamically pulse in **amber (medium risk)** or **red (breaking risk)**.
  - Safe/unaffected nodes dim out.
  - Clicking any node zooms straight to the source evidence and line numbers.

### 4.2 1-Click Frontend Migration Diff Generator
- Instead of merely complaining that a component is broken, ChangeRadar acts as a companion refactoring assistant.
- For `rename_field` (e.g. `user.email` &rarr; `user.contact_email`):
  - Generates unified `.diff` patches replacing deprecated property accessors across all affected `.tsx`, `.ts`, and test files.
  - Provides a syntax-highlighted diff preview and a 1-click **"Copy Migration Patch"** button ready for `git apply`.

### 4.3 Git Diff / PR Inspector Mode
- Users can toggle between **"Manual Change Selector"** and **"Paste Git Diff"**.
- In Git Diff Mode, developers paste a `git diff` (e.g. from an open pull request modifying a backend Pydantic schema or route).
- ChangeRadar automatically parses the diff, infers the field renames/removals/route modifications, and instantly computes the frontend blast radius.

---

## 5. Security & Safety Model

1. **Path Traversal / Zip Slip Prevention**:
   - Inspect every file path in uploaded ZIP archives.
   - Strictly reject any entry containing `..`, absolute paths (leading `/` or `C:\`), or symbolic links.
   - Validate resolved extraction paths stay strictly within `backend/workspace/extracted/{project_id}`.
2. **File Size & Memory Limits**:
   - Limit upload size to 25 MB.
   - Refuse extraction if uncompressed size exceeds safe bounds (Zip bomb protection).
3. **No Execution Guarantee**:
   - Repository code is treated as untrusted text data.
   - Never run `npm install`, `pip install`, build tools, or tests on scanned projects.
4. **Secret & Sensitive File Exclusion**:
   - Never parse or index: `.env`, `.env.*`, `*.pem`, `*.key`, `id_rsa`, `credentials.json`.
   - Skip vendor/build directories: `node_modules/`, `.git/`, `.venv/`, `venv/`, `dist/`, `build/`, `__pycache__/`, `.next/`.
5. **Localhost & CORS Confinement**:
   - CORS restricted to `http://localhost:5173` and local frontend origin.
   - Zero telemetry, zero external network requests.

---

## 6. Detailed Backend & Frontend Breakdown

### 6.1 Backend (`backend/`)

- **`app/config.py`**: Settings, upload folder, max size (25MB), database path.
- **`app/database.py`**: SQLite database with parameterized tables:
  - `projects`: `id`, `name`, `created_at`, `extracted_path`, `file_count`, `detected_tech`.
  - `reports`: `id`, `project_id`, `created_at`, `change_type`, `change_payload`, `report_data`.
- **`app/services/zip_service.py`**: Safe extraction, zip-slip checks, secret filtering.
- **`app/services/scanner.py`**: Discovers `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.json` files.
- **`app/services/fastapi_parser.py`**: Python `ast` parsing for routes (`@app.*`, `@router.*`), router prefixes, parameter types, response models, and Pydantic `BaseModel` field schemas.
- **`app/services/typescript_parser.py`**: Scans frontend files for API calls, fetch/axios URLs, TypeScript types, property accessors, and test cases.
- **`app/services/blast_radius.py`**: Builds the graph of nodes (`route`, `schema`, `type`, `component`, `test`) and edges for frontend visualization.
- **`app/services/patch_service.py`**: Computes unified `.diff` migration patches for affected files.
- **`app/services/git_diff_parser.py`**: Parses incoming git diff text into structured API change specifications.
- **`app/services/impact_analyzer.py`**: Correlates changes, calculates confidence ratings (`High`, `Medium`, `Low`), generates evidence snippets and regression test recommendations.
- **`app/api/routes/`**:
  - `projects.py`: Upload, sample project auto-load, list, inspect, delete.
  - `analysis.py`: Endpoint inventory, blast radius graph, impact analysis, git-diff analysis.
  - `reports.py`: Stored report history and exports.

### 6.2 Frontend (`frontend/`)

- **Developer Dark Theme Design System (`src/styles/global.css`)**:
  - Dark zinc/slate backdrop (`#090d16` / `#0f172a`), neon cyan accents (`#06b6d4`), violet badges (`#8b5cf6`), and high-contrast warning alerts (`#ef4444` / `#f59e0b`).
  - Monospace code diff viewers and smooth micro-animations.
- **Components (`src/components/`)**:
  - `Header.tsx`: Branding, local-only safety badge, project switcher.
  - `UploadPanel.tsx`: Drag-and-drop ZIP upload with 1-click **"Load Demo Sample"** button.
  - `EndpointList.tsx`: Searchable inventory of discovered backend routes with HTTP badges and response models.
  - `BlastRadiusGraph.tsx`: Interactive visual node graph displaying dependencies and active breaking pathways.
  - `ChangeSimulator.tsx`: Dual-mode form (Interactive Dropdowns or Git Diff paste).
  - `ImpactReport.tsx`: Severity summary, evidence cards with line numbers & code preview, confidence meters, and recommended regression tests.
  - `MigrationPatchModal.tsx`: Visual syntax-highlighted `.diff` preview with 1-click copy for `git apply`.
  - `ReportHistory.tsx`: History list of previous analyses with timestamps and change summaries.
  - `StatusMessage.tsx`: Local privacy notices and friendly error banners.

---

## 7. Bundled Sample Project (`sample_project.zip`)

ChangeRadar includes a ready-to-test sample project (`sample_fullstack_app.zip`):
- **FastAPI Backend**:
  - `main.py`: FastAPI server mounting routers.
  - `routes/users.py`: `GET /users`, `GET /users/{user_id}`, `POST /users`, `DELETE /users/{user_id}`.
  - `schemas/user.py`: `UserResponse` (`id`, `name`, `email`, `role`, `is_active`) and `UserCreate`.
- **React Frontend**:
  - `src/api/userClient.ts`: Fetch helper targeting `/users` and `/users/{user_id}`.
  - `src/types/user.ts`: `interface User { id: number; name: string; email: string; role: string; is_active: boolean; }`.
  - `src/components/UserProfile.tsx`: User card component referencing `user.email` and `user.role`.
  - `src/components/UserTable.tsx`: Table listing all users.
  - `src/__tests__/UserProfile.test.tsx`: Jest/Vitest test file testing user details and asserting on `email` rendering.

---

## 8. Implementation Steps & Milestones

1. **Milestone 1: Workspace Skeleton & Bundled Sample**
   - Create root `.gitignore`, `README.md`.
   - Create and package `sample_fullstack_app.zip`.
2. **Milestone 2: Backend Core, Database & Safe Upload**
   - Implement `config.py`, `database.py`, `zip_service.py`.
   - Setup `/health`, `/api/projects/upload`, `/api/projects/sample`, `/api/projects`, `DELETE /api/projects/{id}`.
3. **Milestone 3: Static Analysis & Graph Engine**
   - Implement `scanner.py`, `fastapi_parser.py`, `typescript_parser.py`.
   - Implement `blast_radius.py`, `patch_service.py`, `git_diff_parser.py`, `impact_analyzer.py`.
   - Implement `/api/projects/{id}/endpoints`, `/api/projects/{id}/graph`, `/api/projects/{id}/analyze`.
4. **Milestone 4: React + TypeScript Frontend**
   - Scaffold Vite React app in `frontend/`.
   - Build developer dark theme UI: Upload panel, Endpoint inventory, Blast Radius visual graph, Change Simulator (with Git Diff mode), Impact Report, and Migration Patch modal.
5. **Milestone 5: Automated Testing & Verification**
   - Write pytest test suite in `backend/tests/` (testing Zip Slip defense, AST parser, impact scoring, patch generation, and deletion safety).
   - Run backend tests and verify all passing.
   - Run frontend `npm run build` and TypeScript check.
6. **Milestone 6: Final Polish & Documentation**
   - Complete `README.md` with Windows PowerShell and Unix run instructions.

---

## 9. Verification & Quality Acceptance Criteria

- [ ] Path traversal attempts (`../../evil.py`) are strictly rejected.
- [ ] ZIP extraction skips `.env`, `node_modules`, `.git`, `.venv`.
- [ ] Sample project loads with 1-click and immediately discovers `/users` routes and `UserResponse` schema.
- [ ] Removing/renaming `email` correctly flags `UserProfile.tsx`, `user.ts`, and `UserProfile.test.tsx` with lines & code snippets.
- [ ] Interactive Blast Radius graph renders nodes and highlights broken paths in red/amber.
- [ ] Migration patch preview outputs clean unified `.diff` format with 1-click copy.
- [ ] Git Diff mode parses pasted unified diffs and detects breaking changes automatically.
- [ ] Database persists reports across backend restarts.
- [ ] Automated pytest test suite passes 100%.
- [ ] Frontend builds with zero TypeScript errors.
