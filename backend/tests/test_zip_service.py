import tempfile
import zipfile
from pathlib import Path
import pytest
from fastapi import HTTPException
from app.services.zip_service import (
    delete_project_directory,
    extract_zip_safely,
    is_secret_file,
    should_ignore_path,
    validate_zip_entry,
)

def test_secret_file_detection():
    assert is_secret_file(".env") is True
    assert is_secret_file(".env.local") is True
    assert is_secret_file(".env.production") is True
    assert is_secret_file("id_rsa") is True
    assert is_secret_file("credentials.json") is True
    assert is_secret_file("main.py") is False
    assert is_secret_file("user.ts") is False

def test_ignored_path_detection():
    assert should_ignore_path("node_modules/react/index.js") is True
    assert should_ignore_path(".git/HEAD") is True
    assert should_ignore_path(".venv/bin/python") is True
    assert should_ignore_path("__pycache__/app.cpython-311.pyc") is True
    assert should_ignore_path("src/.env") is True
    assert should_ignore_path("src/App.tsx") is False
    assert should_ignore_path("routes/users.py") is False

def test_zip_slip_rejection():
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_dir = Path(tmp_dir) / "workspace"
        target_dir.mkdir()

        # Reject path traversal
        with pytest.raises(HTTPException) as exc:
            validate_zip_entry("../evil.py", target_dir)
        assert exc.value.status_code == 400

        # Reject absolute paths
        with pytest.raises(HTTPException) as exc:
            validate_zip_entry("/etc/passwd", target_dir)
        assert exc.value.status_code == 400

def test_safe_zip_extraction():
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = Path(tmp_dir) / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("app/main.py", "print('hello')")
            zf.writestr("app/.env", "SECRET=12345")
            zf.writestr("node_modules/fake/index.js", "fake")

        extracted_path, file_count = extract_zip_safely(zip_path, "test_proj_1")
        assert extracted_path.exists()
        assert (extracted_path / "app" / "main.py").exists()
        # Ensure secrets and node_modules were ignored
        assert not (extracted_path / "app" / ".env").exists()
        assert not (extracted_path / "node_modules").exists()

        # Test deletion
        assert delete_project_directory("test_proj_1") is True
        assert not extracted_path.exists()
