from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import analysis, projects, reports
from fastapi.staticfiles import StaticFiles
from app.config import CORS_ORIGINS, FRONTEND_DIST_DIR
from app.database import init_db
from app.api.routes.projects import ensure_sample_zip_exists

# Ensure SQLite database schema is initialized at import
init_db()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_sample_zip_exists()
    yield

app = FastAPI(
    title="ChangeRadar API",
    version="1.0.0",
    description="Local-first static analysis tool detecting fullstack API breaking changes.",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint
@app.get("/health", tags=["system"])
def health_check():
    return {
        "status": "healthy",
        "app": "ChangeRadar",
        "version": "1.0.0",
        "local_mode": True,
        "security": "sandboxed_offline",
    }

# Ollama local LLM status
@app.get("/api/ollama/status", tags=["ai"])
def get_ollama_status():
    from app.services.ollama_service import check_ollama_status
    return check_ollama_status()

# Mount API routers
app.include_router(projects.router)
app.include_router(analysis.router)
app.include_router(reports.router)

# Serve built frontend UI directly from port 8000 if available
if FRONTEND_DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST_DIR), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
