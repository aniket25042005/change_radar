import os
from pathlib import Path

# Paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BACKEND_DIR / "workspace" / "extracted"
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

SAMPLES_DIR = BACKEND_DIR / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

FRONTEND_DIST_DIR = BACKEND_DIR.parent / "frontend" / "dist"

DATABASE_PATH = BACKEND_DIR / "changeradar.db"

# Limits & Security
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_UNCOMPRESSED_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB zip bomb defense

# CORS Origins for local development
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Local Ollama LLM Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
