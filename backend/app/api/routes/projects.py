import os
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.config import MAX_UPLOAD_SIZE_BYTES, WORKSPACE_DIR, SAMPLES_DIR
from app.database import (
    delete_project_record,
    get_project_by_id,
    get_projects,
    insert_project,
)
from app.schemas.project import (
    DeleteResponse,
    ProjectDetailResponse,
    ProjectResponse,
    ScannedFileItem,
)
from app.services.fastapi_parser import parse_all_python_files
from app.services.scanner import scan_project_files
from app.services.zip_service import delete_project_directory, extract_zip_safely

router = APIRouter(prefix="/api/projects", tags=["projects"])

def ensure_sample_zip_exists() -> Path:
    sample_zip_path = SAMPLES_DIR / "sample_fullstack_app.zip"
    if sample_zip_path.exists():
        return sample_zip_path

    # Construct the sample full-stack project in memory/temp and zip it
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # 1. FastAPI backend
        backend_dir = tmp_path / "backend"
        backend_dir.mkdir()
        (backend_dir / "main.py").write_text(
            'from fastapi import FastAPI\n'
            'from routes.users import router as users_router\n\n'
            'app = FastAPI(title="Sample Store API")\n'
            'app.include_router(users_router)\n',
            encoding="utf-8",
        )
        routes_dir = backend_dir / "routes"
        routes_dir.mkdir()
        (routes_dir / "__init__.py").write_text("", encoding="utf-8")
        (routes_dir / "users.py").write_text(
            'from typing import List\n'
            'from fastapi import APIRouter, HTTPException\n'
            'from schemas.user import UserResponse, UserCreate\n\n'
            'router = APIRouter(prefix="/users")\n\n'
            '@router.get("", response_model=List[UserResponse])\n'
            'def list_users() -> List[UserResponse]:\n'
            '    return []\n\n'
            '@router.get("/{user_id}", response_model=UserResponse)\n'
            'def get_user(user_id: int) -> UserResponse:\n'
            '    return UserResponse(id=user_id, name="Alice", email="alice@example.com", role="admin")\n\n'
            '@router.post("", response_model=UserResponse)\n'
            'def create_user(payload: UserCreate) -> UserResponse:\n'
            '    return UserResponse(id=1, name=payload.name, email=payload.email, role="user")\n',
            encoding="utf-8",
        )
        schemas_dir = backend_dir / "schemas"
        schemas_dir.mkdir()
        (schemas_dir / "__init__.py").write_text("", encoding="utf-8")
        (schemas_dir / "user.py").write_text(
            'from pydantic import BaseModel\n\n'
            'class UserResponse(BaseModel):\n'
            '    id: int\n'
            '    name: str\n'
            '    email: str\n'
            '    role: str\n'
            '    is_active: bool = True\n\n'
            'class UserCreate(BaseModel):\n'
            '    name: str\n'
            '    email: str\n',
            encoding="utf-8",
        )

        # 2. React / TypeScript frontend
        frontend_dir = tmp_path / "frontend"
        src_dir = frontend_dir / "src"
        src_dir.mkdir(parents=True)

        types_dir = src_dir / "types"
        types_dir.mkdir()
        (types_dir / "user.ts").write_text(
            'export interface User {\n'
            '  id: number;\n'
            '  name: string;\n'
            '  email: string;\n'
            '  role: string;\n'
            '  is_active?: boolean;\n'
            '}\n',
            encoding="utf-8",
        )

        api_dir = src_dir / "api"
        api_dir.mkdir()
        (api_dir / "userClient.ts").write_text(
            'import { User } from "../types/user";\n\n'
            'export async function fetchUsers(): Promise<User[]> {\n'
            '  const res = await fetch("/users");\n'
            '  return res.json();\n'
            '}\n\n'
            'export async function fetchUserById(id: number): Promise<User> {\n'
            '  const res = await fetch(`/users/${id}`);\n'
            '  return res.json();\n'
            '}\n',
            encoding="utf-8",
        )

        components_dir = src_dir / "components"
        components_dir.mkdir()
        (components_dir / "UserProfile.tsx").write_text(
            'import React from "react";\n'
            'import { User } from "../types/user";\n\n'
            'interface UserProfileProps {\n'
            '  user: User;\n'
            '}\n\n'
            'export const UserProfile: React.FC<UserProfileProps> = ({ user }) => {\n'
            '  return (\n'
            '    <div className="user-card">\n'
            '      <h3>{user.name}</h3>\n'
            '      <p className="email-label">Email: {user.email}</p>\n'
            '      <span className="role-badge">{user.role}</span>\n'
            '    </div>\n'
            '  );\n'
            '};\n',
            encoding="utf-8",
        )

        (components_dir / "UserList.tsx").write_text(
            'import React from "react";\n'
            'import { User } from "../types/user";\n'
            'import { UserProfile } from "./UserProfile";\n\n'
            'export const UserList: React.FC<{ users: User[] }> = ({ users }) => (\n'
            '  <div className="user-grid">\n'
            '    {users.map(u => <UserProfile key={u.id} user={u} />)}\n'
            '  </div>\n'
            ');\n',
            encoding="utf-8",
        )

        tests_dir = src_dir / "__tests__"
        tests_dir.mkdir()
        (tests_dir / "UserProfile.test.tsx").write_text(
            'import { render, screen } from "@testing-library/react";\n'
            'import { UserProfile } from "../components/UserProfile";\n'
            'import { User } from "../types/user";\n\n'
            'const mockUser: User = {\n'
            '  id: 101,\n'
            '  name: "Charlie",\n'
            '  email: "charlie@example.com",\n'
            '  role: "manager",\n'
            '};\n\n'
            'describe("UserProfile component", () => {\n'
            '  it("renders user name and email", () => {\n'
            '    render(<UserProfile user={mockUser} />);\n'
            '    expect(screen.getByText("Charlie")).toBeDefined();\n'
            '    expect(screen.getByText(/charlie@example.com/)).toBeDefined();\n'
            '    expect(mockUser.email).toBe("charlie@example.com");\n'
            '  });\n'
            '});\n',
            encoding="utf-8",
        )

        # Create zip archive
        with zipfile.ZipFile(sample_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(tmp_path):
                for f in files:
                    full_f = Path(root) / f
                    rel_f = full_f.relative_to(tmp_path).as_posix()
                    zf.write(full_f, arcname=rel_f)

    return sample_zip_path

@router.post("/upload", response_model=ProjectResponse)
async def upload_project_zip(file: UploadFile = File(...)):
    """
    Accepts and extracts a project ZIP safely into sandboxed workspace.
    """
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip archive files are accepted")

    project_id = f"proj_{uuid.uuid4().hex[:10]}"
    display_name = file.filename.rsplit(".", 1)[0]

    # Save uploaded file to temp file to check size
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        temp_zip_path = Path(tmp.name)
        try:
            total_bytes = 0
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=400,
                        detail="File exceeds maximum allowed upload size of 25MB",
                    )
                tmp.write(chunk)
            tmp.flush()
        except Exception:
            temp_zip_path.unlink(missing_ok=True)
            raise

    try:
        extracted_path, file_count = extract_zip_safely(temp_zip_path, project_id)
        scanned_files, detected_tech = scan_project_files(extracted_path)

        project_record = insert_project(
            project_id=project_id,
            name=display_name,
            extracted_path=str(extracted_path),
            file_count=len(scanned_files),
            detected_tech=detected_tech,
            status="ready",
        )
        return project_record
    finally:
        temp_zip_path.unlink(missing_ok=True)

@router.post("/sample", response_model=ProjectResponse)
def load_sample_project():
    """
    1-Click loader that provisions the bundled sample full-stack application (FastAPI + React/TS).
    """
    sample_zip = ensure_sample_zip_exists()
    project_id = f"sample_{uuid.uuid4().hex[:8]}"
    display_name = "FastAPI + React Demo App (Sample)"

    extracted_path, file_count = extract_zip_safely(sample_zip, project_id)
    scanned_files, detected_tech = scan_project_files(extracted_path)

    project_record = insert_project(
        project_id=project_id,
        name=display_name,
        extracted_path=str(extracted_path),
        file_count=len(scanned_files),
        detected_tech=detected_tech,
        status="ready",
    )
    return project_record

@router.get("", response_model=List[ProjectResponse])
def list_projects():
    return get_projects()

@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project_details(project_id: str):
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    proj_dir = Path(project["extracted_path"])
    scanned_files = []
    endpoints_count = 0
    schemas_count = 0

    if proj_dir.exists():
        files, _ = scan_project_files(proj_dir)
        scanned_files = [
            ScannedFileItem(
                relative_path=f["relative_path"],
                file_type=f["file_type"],
                size_bytes=f["size_bytes"],
            )
            for f in files
        ]
        eps, schemas = parse_all_python_files(proj_dir)
        endpoints_count = len(eps)
        schemas_count = len(schemas)

    return ProjectDetailResponse(
        id=project["id"],
        name=project["name"],
        created_at=project["created_at"],
        extracted_path=project["extracted_path"],
        file_count=project["file_count"],
        detected_tech=project["detected_tech"],
        status=project["status"],
        files=scanned_files,
        endpoints_count=endpoints_count,
        schemas_count=schemas_count,
    )

@router.delete("/{project_id}", response_model=DeleteResponse)
def delete_project(project_id: str):
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Safely remove extracted files from workspace
    delete_project_directory(project_id)

    # Delete records from SQLite
    delete_project_record(project_id)

    return DeleteResponse(
        success=True,
        message=f"Project '{project['name']}' and all associated files/reports deleted successfully.",
        project_id=project_id,
    )
