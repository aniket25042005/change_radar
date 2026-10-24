import os
import shutil
import zipfile
from pathlib import Path
from typing import Set, Tuple
from fastapi import HTTPException
from app.config import (
    MAX_UPLOAD_SIZE_BYTES,
    MAX_UNCOMPRESSED_SIZE_BYTES,
    WORKSPACE_DIR,
)

IGNORED_DIRS: Set[str] = {
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".next",
    ".nuxt",
    ".turbo",
    ".cache",
    ".idea",
    ".vscode",
}

IGNORED_FILE_EXTENSIONS: Set[str] = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".exe",
    ".bin",
    ".pem",
    ".key",
    ".crt",
    ".log",
    ".zip",
    ".tar",
    ".gz",
}

SECRET_FILE_PATTERNS: Set[str] = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.staging",
    "id_rsa",
    "id_ed25519",
    "credentials.json",
    "service-account.json",
}

def is_secret_file(filename: str) -> bool:
    lower_name = filename.lower()
    if lower_name in SECRET_FILE_PATTERNS or lower_name.startswith(".env"):
        return True
    return False

def should_ignore_path(rel_path_str: str) -> bool:
    normalized = rel_path_str.replace("\\", "/").strip("/")
    parts = normalized.split("/")
    
    # Check directory ignore
    for part in parts[:-1]:
        if part in IGNORED_DIRS or part.startswith("."):
            return True
            
    # Check filename ignore
    filename = parts[-1]
    if not filename:
        return True
        
    if is_secret_file(filename):
        return True
        
    ext = os.path.splitext(filename)[1].lower()
    if ext in IGNORED_FILE_EXTENSIONS:
        return True
        
    return False

def validate_zip_entry(member_name: str, target_dir: Path) -> Path:
    # Reject absolute paths or Windows drive letters
    if member_name.startswith("/") or member_name.startswith("\\") or (len(member_name) > 1 and member_name[1] == ":"):
        raise HTTPException(status_code=400, detail=f"Malicious zip entry with absolute path: {member_name}")

    if ".." in member_name.split("/") or ".." in member_name.split("\\"):
        raise HTTPException(status_code=400, detail=f"Zip slip path traversal detected: {member_name}")

    resolved_target = (target_dir / member_name).resolve()
    target_dir_resolved = target_dir.resolve()

    try:
        common = os.path.commonpath([str(resolved_target), str(target_dir_resolved)])
        if common != str(target_dir_resolved):
            raise HTTPException(status_code=400, detail=f"Zip entry escapes target extraction directory: {member_name}")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid cross-drive zip entry: {member_name}")

    return resolved_target

def extract_zip_safely(zip_path: Path, project_id: str) -> Tuple[Path, int]:
    """
    Safely extracts a ZIP archive into WORKSPACE_DIR / project_id,
    verifying path traversal, size limits, and filtering secrets/build artifacts.
    Returns (extracted_path, file_count).
    """
    if not zip_path.exists():
        raise HTTPException(status_code=400, detail="Zip file does not exist")

    file_size = zip_path.stat().st_size
    if file_size > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum allowed size of 25MB (got {file_size / (1024*1024):.1f}MB)")

    target_dir = WORKSPACE_DIR / project_id
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            total_uncompressed = 0
            for info in zf.infolist():
                total_uncompressed += info.file_size
                if total_uncompressed > MAX_UNCOMPRESSED_SIZE_BYTES:
                    shutil.rmtree(target_dir, ignore_errors=True)
                    raise HTTPException(status_code=400, detail="Zip archive uncompressed size exceeds 100MB limit (Zip bomb prevention)")

            extracted_files_count = 0
            for member in zf.infolist():
                # Skip directory entries
                if member.is_dir() or member.filename.endswith("/") or member.filename.endswith("\\"):
                    continue

                if should_ignore_path(member.filename):
                    continue

                dest_path = validate_zip_entry(member.filename, target_dir)
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                with zf.open(member) as source_file, open(dest_path, "wb") as target_file:
                    shutil.copyfileobj(source_file, target_file)
                extracted_files_count += 1

            return target_dir, extracted_files_count

    except zipfile.BadZipFile:
        shutil.rmtree(target_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid or readable ZIP archive")

def delete_project_directory(project_id: str) -> bool:
    """
    Safely deletes extracted project files, guaranteeing it only deletes
    within WORKSPACE_DIR.
    """
    target_dir = (WORKSPACE_DIR / project_id).resolve()
    workspace_resolved = WORKSPACE_DIR.resolve()

    try:
        common = os.path.commonpath([str(target_dir), str(workspace_resolved)])
        if common != str(workspace_resolved) or target_dir == workspace_resolved:
            raise ValueError(f"Unsafe directory deletion attempted: {target_dir}")
    except ValueError:
        raise ValueError(f"Cross-drive path deletion attempted: {target_dir}")

    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)
        return True
    return False
