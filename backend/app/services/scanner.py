import os
from pathlib import Path
from typing import Any, Dict, List, Tuple
from app.services.zip_service import should_ignore_path

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript-react",
    ".js": "javascript",
    ".jsx": "javascript-react",
    ".json": "json",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
}

def is_test_file(rel_path_str: str) -> bool:
    lower = rel_path_str.lower().replace("\\", "/")
    filename = os.path.basename(lower)
    return (
        "test" in filename
        or "spec" in filename
        or "__tests__" in lower
        or "/tests/" in lower
    )

def scan_project_files(project_dir: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Recursively scans the project directory, returning:
    - List of scanned file metadata
    - Detected tech summary
    """
    files_list = []
    python_count = 0
    typescript_count = 0
    test_count = 0

    project_dir_resolved = project_dir.resolve()

    for root, dirs, files in os.walk(project_dir_resolved):
        # In-place filter out ignored directories
        dirs[:] = [d for d in dirs if not should_ignore_path(os.path.join(root, d).replace(str(project_dir_resolved), ""))]

        for file in files:
            full_path = Path(root) / file
            rel_path = full_path.relative_to(project_dir_resolved).as_posix()

            if should_ignore_path(rel_path):
                continue

            ext = full_path.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            file_type = SUPPORTED_EXTENSIONS[ext]
            size_bytes = full_path.stat().st_size

            is_test = is_test_file(rel_path)
            if is_test:
                test_count += 1

            if file_type == "python":
                python_count += 1
            elif "typescript" in file_type:
                typescript_count += 1

            files_list.append({
                "relative_path": rel_path,
                "file_type": file_type,
                "size_bytes": size_bytes,
                "is_test": is_test,
            })

    detected_tech = {
        "backend": "FastAPI (Python)" if python_count > 0 else "Unknown",
        "frontend": "React / TypeScript" if typescript_count > 0 else "Unknown",
        "python_files": python_count,
        "typescript_files": typescript_count,
        "test_files": test_count,
        "total_scanned_files": len(files_list),
    }

    return files_list, detected_tech
