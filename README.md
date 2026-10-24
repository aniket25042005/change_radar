# ChangeRadar — Fullstack API Impact Radar

ChangeRadar is a local-first, developer-centric static analysis and flight-control tool that detects how backend API changes in FastAPI/Pydantic break frontend consumers in React + TypeScript applications.

---

## Key Features

1. **Deterministic Static Analysis (AST & Heuristic Parsing)**:
   - Uses Python's native `ast` to parse FastAPI routes (`@app.*`, `@router.*`), APIRouter prefixes, parameter types, response models, and Pydantic `BaseModel` field schemas.
   - Scans React/TypeScript `.ts`, `.tsx`, `.js`, and `.jsx` files for endpoint path references, API client wrappers, TypeScript interfaces, component object accessors, and unit test assertions.
2. **Interactive "Blast Radius" Visual Graph**:
   - An SVG node-link dependency tree showing `[Route] -> [Pydantic Model] -> [TS Type] -> [UI Component] -> [Unit Test]`.
   - Affected nodes dynamically pulse in amber/red when an API change is simulated, visually highlighting the blast radius.
3. **1-Click Frontend Migration Diff & In-App File Application**:
   - Generates syntax-highlighted unified `.diff` patches (for field removals, renames, type changes, or route shifts) across `.tsx`, `.ts`, and test files.
   - Includes **"⚡ Apply Directly to Files"** with automatic backup snapshots and an instant **"Undo / Revert Changes"** button, plus 1-click **"Copy Migration Patch"** for `git apply`.
4. **"Copy for GitHub PR" Markdown Export**:
   - 1-Click export of a beautifully formatted Markdown blast-radius audit table with risk badge, affected files, line numbers, and regression checklist, ready to paste straight into a GitHub or GitLab Pull Request description.
5. **LangGraph Agentic Copilot Studio (StateGraph 1.2 Pipeline)**:
   - Orchestrates a 6-node LangGraph state graph with conditional routing:
     - `START` &rarr; Conditional Entry (`route_by_mode`: interactive prompt vs full analysis)
     - `assess_architectural_risk`: Evaluates SemVer contract stability (Major/Minor/Patch) and failure modes.
     - `synthesize_migration_guide`: Generates human-like chronological developer migration steps across types, client wrappers, and components.
     - `synthesize_compatibility_code`: Synthesizes zero-downtime dual-read adapters (`normalizeContract`), TypeScript safe access wrappers, and Pydantic field aliases.
     - `draft_pr_review_comment`: Drafts Senior Staff AI PR review comments with strict approval checklists and risk labels.
     - `determine_autonomous_next_steps`: Plans autonomous flight-control execution steps and test targets.
     - `interactive_developer_assistant`: Answers developer questions grounded in AST blast radius context with quick-prompt chips (e.g. Zero-downtime deprecation, Vitest/Pytest specifications).
   - Real-time **Execution Trace Inspector** measuring exact latency (in milliseconds) and summaries for each executed LangGraph node.
   - Dedicated **LangGraph Studio Modal** and in-line Impact Report Copilot tabs.
6. **Git Diff / PR Inspector Mode**:
   - Either select changes interactively from dropdowns or paste a unified `git diff` from a GitHub/GitLab Pull Request to automatically detect breaking backend changes and compute the frontend blast radius.
7. **Local-First & Sandboxed**:
   - 100% offline local processing. Zero code execution of scanned repositories.
   - Built-in Zip Slip protection, 25MB file upload cap, 100MB zip bomb defense, and automated exclusion of secrets (`.env*`, `*.key`) and vendor folders (`node_modules`, `.venv`).
   - SQLite local persistence for project records and report histories.
8. **Bundled 1-Click Demo App**:
   - Includes a ready-to-test sample full-stack store application (`sample_fullstack_app.zip`) so you can explore all features with a single click.

---

## Architecture & Ports

- **Frontend**: `http://localhost:5173` (React 18 + TypeScript + Vite)
- **Backend**: `http://127.0.0.1:8000` (FastAPI + Uvicorn + SQLite3)
- **FastAPI Interactive Docs**: `http://127.0.0.1:8000/docs`
- **Local Ollama LLM** (Optional): `http://localhost:11434` (Default: `llama3.2`)

---

## 🦙 Local Ollama Integration

ChangeRadar includes native, zero-setup support for **Local Ollama**:
- Default host: `http://localhost:11434`
- Default model: `llama3.2` (or configure via `OLLAMA_MODEL=qwen2.5-coder` or any model installed in your Ollama library).

### Running with Ollama:
1. Ensure Ollama is installed and run your model:
   ```bash
   ollama run llama3.2
   ```
2. ChangeRadar's LangGraph Copilot will automatically detect the running daemon, display **`🦙 Ollama Online (llama3.2)`** in the UI, and route reasoning queries through your local GPU/CPU.
3. If Ollama is not running, ChangeRadar **automatically falls back to its deterministic AST engine** with zero crashes and instant responses.

---

## Getting Started

### Prerequisites

- **Python 3.11+** (Tested on Python 3.11 - 3.14)
- **Node.js v18+** (Tested on Node.js v22)
- **npm** (Tested on npm 10)

---

### Backend Setup

#### Windows PowerShell:
```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

#### macOS / Linux:
```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```

*The backend will initialize the SQLite database (`changeradar.db`) and be accessible at `http://127.0.0.1:8000`.*

---

### Frontend Setup

Open a separate terminal:

#### Windows PowerShell or macOS / Linux:
```bash
cd frontend
npm install
npm run dev
```

*The frontend development server will launch at `http://localhost:5173` with automatic API proxying to port 8000.*

---

## Running Tests & Verifications

### 1. Backend Automated Tests (Pytest)
Run the full test suite (covering Zip Slip rejection, AST route/schema extraction, impact scoring, patch generation, and API endpoints):
```bash
python -m pytest backend/tests
```

### 2. Frontend Production Build & Type Check
Verify that all TypeScript types pass strict checks and produce an optimized bundle:
```bash
cd frontend
npm run build
```

---

## How to Use ChangeRadar

1. **Open the Web UI** at `http://localhost:5173`.
2. **Load a Project**:
   - Click **"Load Demo Sample"** for instant 1-click test drive, OR
   - Drag & drop your own repository ZIP file (up to 25 MB).
3. **Explore Discovered Inventory**:
   - Inspect all discovered FastAPI endpoints, HTTP methods, and Pydantic schemas.
   - View the **Blast Radius Graph** mapping routes to UI components and unit tests.
4. **Simulate an API Change**:
   - In the **Simulator panel**, choose a change type (e.g. `Remove Response Field` or `Rename Response Field`) and select target field `email`.
   - Alternatively, toggle to **Git Diff Mode** and paste a unified diff from a Pull Request.
   - Click **"Simulate Change & Generate Radar Report"**.
5. **Inspect the Impact Report**:
   - Check the **Risk Level** (`Breaking`, `Warning`, `Informational`) and confidence rating.
   - Inspect the affected frontend files and line numbers with code snippets.
   - Review discovered unit tests and suggested regression tests.
   - If available, click **"1-Click Migration Patch"** to view and copy a unified `.diff` patch ready to apply with `git apply`.
6. **Manage Stored Reports**:
   - View previous audit runs in the **Report History** list.
   - Delete projects and their associated workspace files with 1 click.

---

## Project Structure

```text
changeradar/
├── README.md                      # Project documentation and run guide
├── PLAN.md                        # Architectural roadmap & specifications
├── ChangeRadar_Antigravity.md     # Initial MVP specifications
├── .gitignore                     # Git ignore rules
├── backend/
│   ├── requirements.txt           # Python dependencies
│   ├── changeradar.db             # Local SQLite database
│   ├── samples/                   # Bundled sample fullstack project zip
│   ├── workspace/extracted/       # Sandboxed extracted project directories
│   ├── app/
│   │   ├── main.py                # FastAPI app entrypoint, CORS, lifespan
│   │   ├── config.py              # Configuration & safety limits
│   │   ├── database.py            # SQLite schema and parameterized CRUD
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── projects.py    # Upload, sample load, list, delete
│   │   │       ├── analysis.py    # Endpoints, graph, impact simulation
│   │   │       └── reports.py     # Historical reports retrieval
│   │   ├── schemas/
│   │   │   ├── project.py         # Pydantic project models
│   │   │   └── analysis.py        # Pydantic analysis & graph models
│   │   └── services/
│   │       ├── zip_service.py     # Safe zip extraction & Zip Slip defense
│   │       ├── scanner.py         # File tree scanner & tech detector
│   │       ├── fastapi_parser.py  # Python AST parser for routes & Pydantic
│   │       ├── typescript_parser.py# Heuristic scanner for TS/TSX consumers
│   │       ├── blast_radius.py    # Cross-stack dependency graph generator
│   │       ├── patch_service.py   # Unified .diff migration patch generator
│   │       ├── git_diff_parser.py # Pull request diff parser
│   │       └── impact_analyzer.py # Impact engine & test generator
│   └── tests/
│       ├── test_zip_service.py    # Zip Slip & security test suite
│       ├── test_fastapi_parser.py # AST parser test suite
│       ├── test_impact_analyzer.py# Impact engine & patch test suite
│       └── test_api_endpoints.py  # FastAPI integration test suite
└── frontend/
    ├── package.json               # Node dependencies & build scripts
    ├── index.html                 # HTML shell with Inter & JetBrains Mono
    ├── vite.config.ts             # Vite configuration with backend proxy
    ├── tsconfig.json              # TypeScript strict configuration
    └── src/
        ├── main.tsx               # React DOM entrypoint
        ├── App.tsx                # Main ChangeRadar application view
        ├── api/
        │   └── client.ts          # Typed REST client
        ├── styles/
        │   └── global.css         # Developer dark theme design system
        └── components/
            ├── Header.tsx         # Brand, privacy badge, project switcher
            ├── UploadPanel.tsx    # Drag-and-drop ZIP & sample loader
            ├── EndpointList.tsx   # Routes & Pydantic schemas inventory
            ├── BlastRadiusGraph.tsx# Interactive SVG blast radius graph
            ├── ChangeSimulator.tsx# Dual-mode change simulator (Form / Diff)
            ├── ImpactReport.tsx   # Impact audit report with evidence
            ├── MigrationPatchModal.tsx # Unified .diff viewer & copy modal
            ├── ReportHistory.tsx  # Historical reports list
            └── StatusMessage.tsx  # Alert banners
```

---

## Safety & Security Guarantees

- **No Code Execution**: Scanned repositories are strictly analyzed as static text and AST tokens. Neither `npm install`, `pip install`, nor any build/test scripts are executed on uploaded repositories.
- **Zip Slip Defense**: Path traversal attempts (e.g. `../../etc/passwd` or drive prefixes) are rejected at the archive extraction boundary.
- **Secret & Environment File Exclusion**: Files matching `.env*`, `*.pem`, `*.key`, `id_rsa`, or `credentials.json` are automatically skipped and never indexed.
- **Dependency Directory Exclusion**: `node_modules`, `.venv`, `.git`, `dist`, and `__pycache__` are excluded by default.
- **100% Local & Offline**: All processing happens on the user's machine; no repository code or metadata is sent to any cloud server or external service.
